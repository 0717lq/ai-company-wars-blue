<div align="center">

# 🔍 rag-builder

### Build & optimize RAG pipelines — from PDF parsing to RAGAS evaluation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Tests](https://img.shields.io/badge/tests-172%20passed-brightgreen?style=flat&logo=pytest)]()
[![Ruff](https://img.shields.io/badge/lint-ruff-050505?style=flat&logo=ruff)](https://docs.astral.sh/ruff/)

**🇨🇳 中文** · [English](./README.en.md)

</div>

---

rag-builder 是一个 **Hermes Agent 技能 + Python 工具包**，帮助你从零构建或优化 RAG（检索增强生成）系统。

它覆盖 RAG 全链路知识：文档解析 → 分块策略 → 向量嵌入 → 混合检索 → Reranker 精排 → 查询分解 → RAGAS 评估。

附带 Python 工具：配置验证、项目骨架生成、文档入库、混合检索、健康诊断。

---

## 📸 效果一览

```text
$ rag-builder init -o rag_config.json
示例配置已生成: rag_config.json

$ rag-builder validate rag_config.json
配置验证通过 ✓

GPU 显存估算:
  Embedding: 1.0 GB
  Reranker:  1.5 GB
  总计:      2.5 GB
  8GB 显存:  ✓ 可用

$ rag-builder diagnose rag_config.json
rag-builder 健康检查
====================

  配置验证:  ✓ 通过
  依赖检测:
    sentence-transformers  ✓ 2.2.0
    pymilvus              ✓ 2.4.0
    pymupdf               ✓ 1.23.0
    rank-bm25             ✓ 0.2.0
    jieba                 ✓ 0.42.0
  GPU 检测:  ✓ RTX 4060 — 8192 MB
  网络连通:  ✓ Milvus (19530) 可达
```

---

## 🎉 What's New

### v0.3.0 — "Diagnose & Split" 🔧 *(2026-06-03)*

> 健康诊断 + SKILL.md 大瘦身 + batch bug 修复。

| 改进项 | 说明 | 对用户的价值 |
|--------|------|-------------|
| 🩺 **`diagnose` 命令** | 4 维度健康检查：配置/依赖/GPU/网络 | 部署前一键排查环境问题 |
| 📖 **SKILL.md 拆分** | 774 行 → 221 行主文件 + 6 个专题文件 | Agent 加载更快，知识按需查阅 |
| 🐛 **Batch bug 修复** | `embed_texts` 测试计数修复 | 测试更准确，开发更放心 |

### v0.2.0 — "Full Pipeline" 🚀 *(2026-06-03)*

> 从"配置工具"升级为"全链路 RAG 工具包"。

| 新功能 | 说明 | 操作 |
|--------|------|------|
| 📄 **文档解析器** | PDF / Markdown / 纯文本，支持目录批量扫描 | `rag-builder ingest --dir ./docs` |
| 🧩 **混合检索器** | BM25 + 向量检索 + RRF 融合 | `rag-builder query "问题"` |
| 🔌 **Embedding 抽象层** | sentence-transformers + OpenAI 兼容 API | `--provider openai` |
| 💾 **向量存储连接器** | Milvus + Chroma 双后端 | `--store milvus` |

### v0.1.0 — "RAG Builder Skill" 🚀 *(2026-05-30)*

> 首版发布 — RAG 全链路知识库 + 配置验证 + 项目脚手架 + 检索评估。

| 新功能 | 说明 | 操作 |
|--------|------|------|
| 📋 **SKILL.md 知识库** | 12 章节覆盖 RAG 全链路，含 13 个常见陷阱 | 作为 Hermes Agent 技能安装 |
| 🔍 **配置验证** | 检查参数兼容性 + GPU 显存估算 | `rag-builder validate config.json` |
| 🏗️ **项目脚手架** | 一键生成 ingest/query/config 骨架代码 | `rag-builder scaffold config.json` |
| 📊 **检索评估** | Precision/Recall/F1 + RAGAS 数据集生成 | `rag-builder benchmark gt.json` |

---

## 🚀 快速开始

```bash
# 1. 安装
pip install -e .

# 2. 生成示例配置
rag-builder init -o rag_config.json

# 3. 验证配置（含 GPU 显存估算）
rag-builder validate rag_config.json

# 4. 健康诊断
rag-builder diagnose rag_config.json

# 5. 生成项目骨架
rag-builder scaffold rag_config.json -o ./output -n my-rag
```

生成的项目包含 `ingest.py`（入库）、`query.py`（查询）、`config.py`（配置），直接可用。

---

## ❓ 为什么选 rag-builder？

| 场景 | 没有 rag-builder | 有 rag-builder |
|------|-----------------|----------------|
| 从零搭 RAG | 翻 10 篇博客拼凑方案 | 一个 SKILL.md 覆盖全链路 |
| 选 embedding 模型 | 不确定哪个适合中文 | 5 个模型对比 + 显存估算 |
| 分块参数怎么设 | 猜 chunk_size=512 | 按文档类型给经验值 |
| 检索效果差 | 盲目调 top_k | 混合检索 + Reranker 精排方案 |
| 评估 RAG 质量 | 自创对比方法（不专业） | RAGAS 行业标准 4 指标 |
| 8GB 显存够不够 | 跑了才发现 OOM | validate 命令提前算好 |
| 环境依赖对不对 | 手动逐个检查 | diagnose 一键诊断 |
| 文档入库 | 自己写脚本拼凑 | `rag-builder ingest` 一行搞定 |

---

## 🧰 功能特性

| 功能 | 说明 |
|------|------|
| ✅ **配置 Schema** | 5 大模块数据类：Chunking / Embedding / VectorStore / Retriever / Query |
| ✅ **GPU 显存估算** | 根据模型 + batch_size 估算显存，判断 8GB 是否够用 |
| ✅ **交叉验证** | chunk_size vs 模型最大序列长度、rerank_top_n vs top_k |
| ✅ **项目脚手架** | 根据配置生成完整的 ingest/query/config 骨架代码 |
| ✅ **文档解析** | PDF (pymupdf) / Markdown (header-aware) / 纯文本 + 目录批量扫描 |
| ✅ **混合检索** | BM25 + 向量语义检索 + Reciprocal Rank Fusion 融合 |
| ✅ **Embedding 抽象** | sentence-transformers 本地推理 + OpenAI 兼容 API |
| ✅ **向量存储** | Milvus + Chroma 双后端，工厂函数一键切换 |
| ✅ **健康诊断** | 4 维度检查：配置/依赖/GPU/网络，支持 JSON 输出 |
| ✅ **检索评估** | Precision / Recall / F1，支持自定义 retrieve 函数 |
| ✅ **RAGAS 数据集** | 生成 RAGAS 兼容的评估数据集，直接喂给 `ragas.evaluate()` |
| ✅ **CLI 工具** | 7 个子命令：init / validate / scaffold / benchmark / ingest / query / diagnose |
| ✅ **13 个陷阱** | Windows CUDA、Milvus 分页、Reranker OOM、API base_url 等 |

---

## 📚 SKILL.md 知识库覆盖范围

SKILL.md（221 行主文件）+ 6 个 `references/` 专题文件，覆盖 RAG 全链路：

| 文件 | 内容 |
|------|------|
| **SKILL.md**（主文件） | 快速开始、CLI 参考、配置说明、深入阅读链接 |
| `references/pdf-parsing.md` | pymupdf / marker-pdf / MinerU / unstructured 对比 |
| `references/embedding-models.md` | 5 个模型对比（bge 系列 + OpenAI API） |
| `references/chunking-strategies.md` | 4 种策略 + 参数经验值 + 表格特殊处理 |
| `references/vector-stores.md` | Milvus / Chroma / FAISS / Qdrant |
| `references/retrieval-methods.md` | 混合检索、BM25、RRF 融合、Reranker 精排 |
| `references/pitfalls.md` | 13 个实战踩坑经验 |

安装为 Hermes Agent 技能：
```bash
cp -r . ~/.hermes/skills/rag-builder/
```

---

## 🔧 CLI 命令

```bash
# 生成示例配置
rag-builder init -o my_config.json

# 验证配置（检查参数兼容性 + GPU 显存估算）
rag-builder validate my_config.json

# 健康诊断（配置 + 依赖 + GPU + 网络）
rag-builder diagnose my_config.json
rag-builder diagnose --json               # JSON 输出
rag-builder diagnose --skip-network       # 跳过网络检测

# 生成项目骨架
rag-builder scaffold my_config.json -o ./output -n my-rag

# 文档入库（解析 + 分块 + 嵌入 + 存储）
rag-builder ingest --dir ./docs --store milvus --provider st
rag-builder ingest --dir ./docs --preview  # 预览模式

# 混合检索查询
rag-builder query "什么是 RAG？" --store milvus
rag-builder query "什么是 RAG？" --json    # JSON 输出

# 运行评估
rag-builder benchmark ground_truth.json --config v1 -o report.json --json
```

---

## 🐍 Python API

```python
from rag_builder.config_schema import RAGConfig, estimate_gpu_vram
from rag_builder.scaffold import scaffold_project
from rag_builder.benchmark import run_benchmark, generate_ragas_dataset
from rag_builder.parsers import parse_pdf, parse_directory, chunk_text
from rag_builder.embeddings import get_provider
from rag_builder.vector_store import get_store
from rag_builder.retriever import create_retriever
from rag_builder.diagnose import diagnose

# 配置验证
config = RAGConfig.from_dict({"chunking": {"chunk_size": 512}, ...})
errors = config.validate()
vram = estimate_gpu_vram(config)

# 文档解析 + 分块
pages = parse_pdf("report.pdf")
chunks = chunk_text(pages, strategy="recursive", chunk_size=512)

# 嵌入 + 存储
provider = get_provider("st", model_name="bge-base-zh-v1.5")
store = get_store("milvus", collection="my_docs")
store.insert(chunks, embeddings=provider.embed_texts(chunks))

# 混合检索
retriever = create_retriever(store, provider, bm25_corpus=chunks)
results = retriever.search("查询问题", top_k=5)

# 健康诊断
report = diagnose(config)
print(report.format_text())
```

---

## 🏗️ 项目结构

```
rag-builder/
├── SKILL.md                        # Hermes Agent 技能主文件（221 行）
├── references/                     # 深度知识专题（6 个文件）
│   ├── pdf-parsing.md
│   ├── embedding-models.md
│   ├── chunking-strategies.md
│   ├── vector-stores.md
│   ├── retrieval-methods.md
│   └── pitfalls.md
├── pyproject.toml                  # 项目元数据 + 依赖
├── CHANGELOG.md                    # 版本变更日志
├── src/rag_builder/
│   ├── __init__.py                 # 版本号
│   ├── __main__.py                 # CLI 入口
│   ├── config_schema.py            # 配置 Schema + 验证 + 显存估算
│   ├── scaffold.py                 # 项目骨架生成（模板引擎）
│   ├── benchmark.py                # 检索评估 + RAGAS 数据集生成
│   ├── parsers.py                  # 文档解析（PDF/Markdown/文本）
│   ├── embeddings.py               # Embedding 抽象层（ST/OpenAI）
│   ├── vector_store.py             # 向量存储连接器（Milvus/Chroma）
│   ├── retriever.py                # 混合检索器（BM25 + 向量 + RRF）
│   ├── diagnose.py                 # 健康诊断（4 维度检查）
│   └── cli.py                      # CLI 命令（7 个子命令）
├── tests/
│   ├── test_config_schema.py       # 配置验证测试
│   ├── test_scaffold.py            # 骨架生成测试
│   ├── test_benchmark.py           # 评估工具测试
│   ├── test_parsers.py             # 文档解析测试
│   ├── test_embeddings.py          # Embedding 抽象测试
│   ├── test_vector_store.py        # 向量存储测试
│   ├── test_retriever.py           # 混合检索测试
│   ├── test_diagnose.py            # 健康诊断测试
│   ├── test_integration.py         # 集成测试
│   └── test_cli.py                 # CLI 集成测试
└── docs/
    ├── CODE.md                     # 代码文档
    ├── FILES.md                    # 文件说明
    └── STRUCTURE.md                # 结构说明
```

---

## 🔬 竞品对比

| 特性 | **rag-builder** 🏆 | LangChain | LlamaIndex |
|------|-------------------|-----------|------------|
| 配置验证 + 显存估算 | ✅ | ❌ | ❌ |
| 项目骨架生成 | ✅ | ❌ | ❌ |
| 健康诊断（配置/依赖/GPU/网络） | ✅ | ❌ | ❌ |
| 文档入库 CLI | ✅ (`ingest`) | 需写代码 | 需写代码 |
| 混合检索（BM25 + 向量 + RRF） | ✅ 内置 | 需组合 | 需组合 |
| RAG 全链路知识库 | ✅ (SKILL.md) | 文档分散 | 文档分散 |
| 检索质量评估 | ✅ (内置) | 需额外配置 | 需额外配置 |
| RAGAS 数据集生成 | ✅ | ❌ | ❌ |
| 中文 RAG 优化 | ✅ (bge/jieba) | 通用 | 通用 |
| 学习曲线 | 低（CLI + 知识库） | 高 | 中 |
| 依赖量 | 极少 | 重量级 | 中等 |

**定位**：rag-builder 不是框架，是**知识库 + 轻量工具**。它帮你做决策（选模型、定参数、避坑），然后生成你自己的 RAG 代码骨架。

---

## 🛠️ 开发

```bash
# 克隆
git clone https://github.com/0717lq/ai-company-wars-blue.git
cd ai-company-wars-blue

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试（172 个）
pytest tests/ -v

# 代码检查
ruff check src/ tests/
```

---

## 📄 License

[MIT](./LICENSE)

---

<p align="center">
  <b>rag-builder</b> — RAG pipeline 知识库 + 轻量工具<br>
  <a href="https://github.com/0717lq/ai-company-wars-blue">GitHub</a> •
  <a href="./CHANGELOG.md">Changelog</a> •
  <a href="./LICENSE">MIT License</a> •
  <a href="./README.en.md">English</a>
</p>
