"""检索层：问题 → BM25 检索 → LLM 生成回答 → 返回结果+引用"""

import os
from app.indexer import query_index

# ── LLM 客户端 (延迟初始化) ──
_llm_client = None

def _get_llm():
    """读取环境变量, 初始化 LLM 客户端"""
    global _llm_client
    if _llm_client is not None:
        return _llm_client

    api_key = os.environ.get("LLM_API_KEY") or ""
    base_url = os.environ.get("LLM_BASE_URL") or "https://api.deepseek.com"
    model = os.environ.get("LLM_MODEL") or "deepseek-chat"

    if not api_key:
        print("⚠️  未设置 LLM_API_KEY, 使用纯检索模式")
        return None

    from openai import OpenAI
    _llm_client = OpenAI(api_key=api_key, base_url=base_url)
    _llm_client._model = model  # 挂载 model 名方便使用
    return _llm_client


SYSTEM_PROMPT = """你是一个专业的合成器知识助手。请基于提供的资料回答用户的问题。

要求：
1. 只基于资料中的信息回答，不要编造
2. 如果资料不足以回答，直接说"资料中没有相关信息"
3. 回答时标注引用来源编号，如 [1][2]
4. 用中文回答，简洁清晰"""


def search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """搜索知识库, 返回 top-k 片段"""
    return query_index(query, top_k=top_k)


def format_context(hits: list[dict]) -> str:
    """把检索结果拼成一段上下文"""
    parts = []
    for i, h in enumerate(hits, 1):
        parts.append(f"[{i}] 《{h['title']}》 (来源: {h['source']})\n{h['content']}\n")
    return "\n---\n".join(parts)


def _call_llm(query: str, context: str) -> str | None:
    """调用 LLM 生成回答, 失败返回 None"""
    client = _get_llm()
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=client._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"资料:\n{context}\n\n问题: {query}"},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"⚠️  LLM 调用失败: {e}")
        return None


def answer(query: str, top_k: int = 5) -> dict:
    """
    完整问答流程:
    1. BM25 检索知识库
    2. 拼上下文
    3. 调用 LLM 生成回答 (有 API Key 时)
    4. 返回回答 + 引用来源
    """
    hits = search_knowledge(query, top_k=top_k)
    context = format_context(hits)

    llm_answer = _call_llm(query, context)

    return {
        "query": query,
        "llm_answer": llm_answer,
        "references": [
            {
                "title": h["title"],
                "source": h["source"],
                "snippet": h["content"][:200] + ("…" if len(h["content"]) > 200 else ""),
                "score": round(h["score"], 3),
            }
            for h in hits
        ],
    }
