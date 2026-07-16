# synth-rag

合成器理论知识库问答系统。基于 BM25 全文检索 + LLM 增强生成。

## 功能

- 知识库检索：296 个知识片段，覆盖合成器六大模块
- LLM 增强回答：接入 DeepSeek / OpenAI 兼容 API 生成自然语言回答
- 处理流程可视化：左侧面板展示检索 -> LLM 调用完整链路
- API Key 本地存储：写入 .env 文件，不提交 git

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
python -m app.app

# 打开 http://127.0.0.1:5050
```

Windows 下也可双击 `start.bat`。

## 配置 API Key

1. 复制 `.env.example` 为 `.env`
2. 填入你的 API Key：

```
LLM_API_KEY=sk-你的key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

3. 重启服务

不配置 Key 也可以使用检索模式，仅展示知识库片段。

## 项目结构

```
synth-rag/
├── app/
│   ├── app.py          Flask Web 服务
│   ├── indexer.py      知识库索引 (BM25)
│   └── retriever.py    检索 + LLM 调用
├── data/
│   └── chunks.json     知识片段 (296 条)
├── .env.example        API 配置模板
├── requirements.txt    依赖
└── start.bat           启动脚本 (Windows)
```

## 技术栈

- 检索：rank-bm25 + jieba 中文分词
- Web：Flask
- LLM：OpenAI 兼容 API (DeepSeek 等)
- 数据：Markdown 知识库，按标题切分
