"""合成器知识库 → BM25 全文检索引擎 (零网络依赖, 纯离线)"""

import os
import glob
import json
import hashlib
from pathlib import Path

from rank_bm25 import BM25Okapi
import jieba  # 中文分词提升搜索质量


KB_PATH = Path(__file__).parent.parent / ".." / "知识库"
DATA_PATH = Path(__file__).parent.parent / "data"
INDEX_FILE = DATA_PATH / "chunks.json"
BM25_CACHE = {}  # 全局缓存 BM25 实例


def _chunk_markdown(filepath: str) -> list[dict]:
    """把一个 md 文件按标题切分成多个片段"""
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    rel = os.path.relpath(filepath, KB_PATH)
    basename = os.path.splitext(os.path.basename(filepath))[0]

    chunks = []
    lines = text.split("\n")
    current_title = basename
    current_lines: list[str] = []
    section_idx = 0

    for line in lines:
        if line.startswith("## ") or line.startswith("### "):
            if current_lines:
                content = "\n".join(current_lines).strip()
                if len(content) > 20:
                    chunk_id = hashlib.md5(f"{rel}#{section_idx}".encode()).hexdigest()[:12]
                    chunks.append({
                        "id": chunk_id,
                        "title": current_title,
                        "content": content,
                        "source": rel,
                    })
                    section_idx += 1
            current_title = line.lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        content = "\n".join(current_lines).strip()
        if len(content) > 20:
            chunk_id = hashlib.md5(f"{rel}#{section_idx}".encode()).hexdigest()[:12]
            chunks.append({
                "id": chunk_id,
                "title": current_title,
                "content": content,
                "source": rel,
            })

    return chunks


def _tokenize(text: str) -> list[str]:
    """中文+英文分词"""
    # 小写化
    text = text.lower()
    # jieba 分词 (中文)
    words = jieba.lcut(text)
    # 过滤单字符标点
    return [w.strip() for w in words if len(w.strip()) > 0]


def build_index():
    """扫描知识库所有 md, 切分 → 保存为 JSON + 构建 BM25 索引"""
    print(f"📂 知识库路径: {KB_PATH}")

    all_chunks: list[dict] = []
    md_files = sorted(glob.glob(str(KB_PATH / "**" / "*.md"), recursive=True))

    for fp in md_files:
        chunks = _chunk_markdown(fp)
        all_chunks.extend(chunks)
        print(f"  ➕ {os.path.relpath(fp, KB_PATH)} → {len(chunks)} 片段")

    # 保存 chunks 到 JSON
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    # 构建 BM25 索引
    tokenized = [_tokenize(c["content"]) for c in all_chunks]
    bm25 = BM25Okapi(tokenized)

    # 缓存到全局 (或也可序列化保存, 但 BM25 重建很快)
    BM25_CACHE["chunks"] = all_chunks
    BM25_CACHE["bm25"] = bm25

    print(f"✅ 索引完成! 共 {len(all_chunks)} 条, BM25 就绪")


def query_index(query: str, top_k: int = 5) -> list[dict]:
    """检索: BM25 关键词匹配 → 返回 top-k"""
    # 如果缓存为空, 从文件加载
    if "bm25" not in BM25_CACHE:
        if INDEX_FILE.exists():
            with open(INDEX_FILE, encoding="utf-8") as f:
                BM25_CACHE["chunks"] = json.load(f)
            tokenized = [_tokenize(c["content"]) for c in BM25_CACHE["chunks"]]
            BM25_CACHE["bm25"] = BM25Okapi(tokenized)
        else:
            build_index()
            return query_index(query, top_k)

    bm25 = BM25_CACHE["bm25"]
    chunks = BM25_CACHE["chunks"]

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    # 按分数降序排列
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: x[1], reverse=True)

    hits = []
    for idx, score in indexed[:top_k]:
        if score > 0:  # 只返回有匹配的
            hits.append({
                "id": chunks[idx]["id"],
                "content": chunks[idx]["content"],
                "title": chunks[idx]["title"],
                "source": chunks[idx]["source"],
                "score": round(float(score), 3),
            })

    # 如果 BM25 没有匹配, 用简单的关键词包含作为后备
    if not hits:
        q_lower = query.lower()
        for idx, chunk in enumerate(chunks):
            if q_lower in chunk["content"].lower():
                hits.append({
                    "id": chunk["id"],
                    "content": chunk["content"],
                    "title": chunk["title"],
                    "source": chunk["source"],
                    "score": 0.0,
                })
                if len(hits) >= top_k:
                    break

    return hits


if __name__ == "__main__":
    build_index()
    # 简单测试
    print("\n🔍 测试检索:")
    for q in ["ADSR 包络", "Pluck 音色", "滤波器种类"]:
        print(f"\n--- 问题: {q} ---")
        for r in query_index(q)[:3]:
            print(f"  [{r['score']}] {r['title']} — {r['source']}")
