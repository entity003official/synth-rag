"""知识库索引: 切分 + jieba分词 + BM25 + TF-IDF 混合索引 (零网络依赖)"""

import os
import glob
import json
import hashlib
import pickle
from pathlib import Path

import jieba
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── 路径 ──
KB_PATH = Path(__file__).parent.parent / ".." / "知识库"
DATA_PATH = Path(__file__).parent.parent / "data"
CHUNKS_FILE = DATA_PATH / "chunks.json"
BM25_FILE = DATA_PATH / "bm25.pkl"
TFIDF_FILE = DATA_PATH / "tfidf.pkl"
VECTORS_FILE = DATA_PATH / "vectors.pkl"
DICT_FILE = Path(__file__).parent / "synth_dict.txt"

# ── 全局缓存 ──
_cache = {"chunks": None, "bm25": None, "tfidf": None, "vectors": None}


def _init_jieba():
    if DICT_FILE.exists():
        jieba.load_userdict(str(DICT_FILE))


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    return [w.strip() for w in jieba.lcut(text) if len(w.strip()) > 0]


# ── 切分 ──
def _chunk_markdown(filepath: str) -> list[dict]:
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    rel = os.path.relpath(filepath, KB_PATH)
    basename = os.path.splitext(os.path.basename(filepath))[0]

    raw_chunks = []
    lines = text.split("\n")
    current_title = basename
    current_lines: list[str] = []
    hierarchy = []

    for line in lines:
        if line.startswith("# "):
            hierarchy = [line.lstrip("#").strip()]
            continue
        if line.startswith("## ") or line.startswith("### "):
            if current_lines:
                raw_chunks.append((current_title, "\n".join(current_lines).strip(), hierarchy.copy()))
            current_title = line.lstrip("#").strip()
            if line.startswith("## "):
                hierarchy = hierarchy[:1] + [current_title]
            else:
                hierarchy = hierarchy[:2] + [current_title]
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        raw_chunks.append((current_title, "\n".join(current_lines).strip(), hierarchy.copy()))

    # 合并短片段 + 重叠
    merged = []
    for i, (title, content, hier) in enumerate(raw_chunks):
        if not content or len(content) < 30:
            continue
        full_title = " > ".join(hier) if hier else title
        source = rel

        if len(content) < 200 and i + 1 < len(raw_chunks):
            next_title, next_content, next_hier = raw_chunks[i + 1]
            if next_content:
                merged_content = content + "\n\n" + next_content
                chunk_id = hashlib.md5(f"{rel}#{i}".encode()).hexdigest()[:12]
                merged.append({"id": chunk_id, "title": full_title, "content": merged_content, "source": source})
                raw_chunks[i + 1] = (title, "", [])
                continue

        chunk_id = hashlib.md5(f"{rel}#{i}".encode()).hexdigest()[:12]
        merged.append({"id": chunk_id, "title": full_title, "content": content, "source": source})

    final = []
    for i, chunk in enumerate(merged):
        final.append(chunk)
        if i + 1 < len(merged):
            overlap_len_a = max(100, len(chunk["content"]) // 6)
            overlap_len_b = max(100, len(merged[i + 1]["content"]) // 6)
            overlap_content = chunk["content"][-overlap_len_a:] + "\n" + merged[i + 1]["content"][:overlap_len_b]
            overlap_id = hashlib.md5(f"{rel}#overlap-{i}".encode()).hexdigest()[:12]
            final.append({
                "id": overlap_id,
                "title": f"{chunk['title']} ↔ {merged[i + 1]['title']}",
                "content": overlap_content,
                "source": source,
            })

    return final


# ── 构建 ──
def build_index():
    KB_PATH_resolved = KB_PATH.resolve()
    print(f"📂 知识库路径: {KB_PATH_resolved}")
    _init_jieba()

    all_chunks: list[dict] = []
    md_files = sorted(glob.glob(str(KB_PATH / "**" / "*.md"), recursive=True))

    for fp in md_files:
        chunks = _chunk_markdown(fp)
        all_chunks.extend(chunks)
        print(f"  + {os.path.relpath(fp, KB_PATH)} -> {len(chunks)}")

    print(f"\n总计 {len(all_chunks)} 个片段")

    DATA_PATH.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    texts = [c["content"] for c in all_chunks]
    tokenized = [_tokenize(t) for t in texts]

    # BM25
    bm25 = BM25Okapi(tokenized)
    with open(BM25_FILE, "wb") as f:
        pickle.dump(bm25, f)
    print(f"  BM25 索引已保存")

    # TF-IDF (使用预分词文本避免 pickle 问题)
    pre_tokenized = [" ".join(t) for t in tokenized]
    tfidf = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"(?u)\b\w+\b",
        max_features=5000,
        ngram_range=(1, 2),
    )
    vectors = tfidf.fit_transform(pre_tokenized)
    with open(TFIDF_FILE, "wb") as f:
        pickle.dump(tfidf, f)
    with open(VECTORS_FILE, "wb") as f:
        pickle.dump(vectors, f)
    print(f"  TF-IDF 索引已保存 (维度: {vectors.shape[1]})")

    print(f"完成! 共 {len(all_chunks)} 条")


def _load_index():
    if _cache["chunks"] is not None:
        return
    if not CHUNKS_FILE.exists():
        build_index()
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        _cache["chunks"] = json.load(f)
    with open(BM25_FILE, "rb") as f:
        _cache["bm25"] = pickle.load(f)
    with open(TFIDF_FILE, "rb") as f:
        _cache["tfidf"] = pickle.load(f)
    with open(VECTORS_FILE, "rb") as f:
        _cache["vectors"] = pickle.load(f)
    _init_jieba()


def search_bm25(query: str, top_k: int = 20) -> list[tuple[int, float]]:
    _load_index()
    tokens = _tokenize(query)
    scores = _cache["bm25"].get_scores(tokens)
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return [(i, s) for i, s in indexed[:top_k] if s > 0]


def search_tfidf(query: str, top_k: int = 20) -> list[tuple[int, float]]:
    _load_index()
    q_pre = " ".join(_tokenize(query))
    q_vec = _cache["tfidf"].transform([q_pre])
    scores = cosine_similarity(q_vec, _cache["vectors"]).flatten()
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return [(i, s) for i, s in indexed[:top_k] if s > 0]


def rrf_fusion(results: list[list[tuple[int, float]]], k: int = 60, top_n: int = 5) -> list[dict]:
    chunks = _cache["chunks"]
    rrf_scores: dict[int, float] = {}
    for rank_list in results:
        for rank, (idx, _) in enumerate(rank_list):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (k + rank)
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [{
        "id": chunks[idx]["id"],
        "title": chunks[idx]["title"],
        "content": chunks[idx]["content"],
        "source": chunks[idx]["source"],
        "score": round(score, 3),
    } for idx, score in ranked[:top_n]]


def query_index(query: str, top_k: int = 5) -> list[dict]:
    _load_index()
    bm25_hits = search_bm25(query, top_k=20)
    tfidf_hits = search_tfidf(query, top_k=20)
    hits = rrf_fusion([bm25_hits, tfidf_hits], top_n=top_k)
    if not hits:
        hits = rrf_fusion([search_bm25(query, top_k=top_k)], top_n=top_k)
    return hits


if __name__ == "__main__":
    build_index()
    print("\n测试检索:")
    for q in ["ADSR 包络的作用", "做温暖厚实的 Bass 音色", "滤波器种类和区别", "怎么做 Pluck 音色"]:
        print(f"\n--- {q} ---")
        for r in query_index(q, 3):
            print(f"  [{r['score']}] {r['title']}")
