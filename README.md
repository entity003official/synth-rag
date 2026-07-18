# 🎛️ 合成器助手 — Synth RAG

> 基于「汪叔聊音源《合成器理论大全》」30 节课程知识库的 RAG 问答系统 + ADSR 可视化工具箱。

```
   ╭──────────────────────────────────╮
   │  🎛️  合成器助手                   │
   │  ┌──────┐ ┌────────┐ ┌──────┐  │
   │  │ 💬 问答│ │ 📊 ADSR │ │ ⚙️ 设置│  │
   │  └──────┘ └────────┘ └──────┘  │
   │                                  │
   │  问：怎么做 Pluck 音色？          │
   │  → 检索知识库 → LLM 生成回答     │
   │  → 同时展示引用片段              │
   ╰──────────────────────────────────╯
```

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| **💬 RAG 问答** | BM25 全文检索 + LLM 增强回答，知识来源可追溯 |
| **📊 ADSR 可视化编辑器** | 拖拽 Attack/Decay/Sustain/Release 控制点，实时曲线 + 智能音色匹配 |
| **⚡ 流程可视化** | 左侧面板逐步展示检索 → LLM 调用完整链路 |
| **🔌 灵活配置** | 支持 DeepSeek / OpenAI 兼容 API，Key 可运行时配置 |

### ADSR 编辑器

- 3 个可拖拽控制手柄：Attack 峰值点、Decay/Sustain 拐点、Release 终点
- 彩色分段曲线（🟠Attack / 🟢Decay / 🔵Sustain / 🟣Release）
- 实时匹配 7 种音色类型（Lead / Pad / Bass / Pluck / Bell / Synth / Chord）
- 触屏支持
- 完全离线运行，无需后端

---

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动
python -m app.app

# 3. 打开浏览器
#    http://127.0.0.1:5050
```

Windows 下也可双击 `start.bat`。

---

## ⚙️ 配置 API Key

两种方式：

### 方式一：Web 界面（推荐）
点击右上角 **⚙️ 设置** → 填入 API Key、Base URL、模型名 → **保存**

### 方式二：编辑 .env 文件
复制 `.env.example` 为 `.env`，填入配置：

```env
LLM_API_KEY=sk-你的key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

> ⚠️ `.env` 已在 `.gitignore` 中，不会被提交。

不配置 Key 也可以使用检索模式（仅展示知识库片段，无 LLM 回答）。

---

## 🏗️ 项目结构

```
synth-rag/
├── app/
│   ├── app.py              Flask Web 服务 + 前端页面
│   ├── indexer.py          知识库索引（BM25 + jieba 分词）
│   ├── retriever.py        检索 + LLM 调用
│   ├── synth_dict.txt      自定义分词词典
│   └── static/
│       └── adsr-editor.html  ADSR 可视化编辑器
├── data/
│   └── chunks.json         知识片段（296 条）
├── .env.example            API 配置模板
├── requirements.txt        Python 依赖
├── start.bat               Windows 启动脚本
└── README.md               本文件
```

---

## 🧠 技术栈

| 层 | 选型 |
|----|------|
| 检索 | rank-bm25 + jieba 中文分词 |
| 后端 | Flask |
| LLM 调用 | OpenAI 兼容 API（DeepSeek / GPT / Claude 等） |
| 前端 | 原生 HTML + Vanilla JS + Canvas |
| 知识库 | 30 节 PDF → Markdown → 按标题切分为 296 个片段 |

---

## 📚 数据来源

全部知识来自「汪叔聊音源《合成器理论大全》」系列课程，涵盖：

- **基础篇**：发展史、减法合成、合成器分类
- **核心模块**：振荡器、滤波器、放大器、包络发生器、LFO
- **波形与调制**：波形塑型、FM/AM/RM、调制矩阵
- **音序与演奏**：琶音器、步进音序器
- **声学原理**：泛音与谐波、傅里叶变换
- **音色设计**：长音类（Lead/Bass/Pad）、短音类（Bell/Pluck）、效果类

---

## 🧪 开发

```bash
# 重建索引（修改了知识库后）
python -c "from app.indexer import build_index; build_index()"

# 纯检索测试（不调 LLM）
python -c "from app.retriever import answer; print(answer('ADSR 各阶段的作用'))"
```

---

## 📄 许可证

MIT
