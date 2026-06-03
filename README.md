<div align="center">

# 🔍 rag-builder

### Build & optimize RAG pipelines — from PDF parsing to RAGAS evaluation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Tests](https://img.shields.io/badge/tests-78%20passed-brightgreen?style=flat&logo=pytest)]()
[![Ruff](https://img.shields.io/badge/lint-ruff-050505?style=flat&logo=ruff)](https://docs.astral.sh/ruff/)

**🇨🇳 中文** · [English](./README.en.md)

</div>

---

rag-builder 是一个 **Hermes Agent 技能 + Python 工具包**，帮助你从零构建或优化 RAG（检索增强生成）系统。

它覆盖 RAG 全链路知识：文档解析 → 分块策略 → 向量嵌入 → 混合检索 → Reranker 精排 → 查询分解 → RAGAS 评估。

附带 Python 工具：配置验证、项目骨架生成、检索质量评估。

---

## 📸 效果一览

```text
$ python -m rag_builder init -o rag_config.json
示例配置已生成: rag_config.json

$ python -m rag_builder validate rag_config.json
配置验证通过 ✓

GPU 显存估算:
  Embedding: 1.0 GB
  Reranker:  1.5 GB
  总计:      2.5 GB
  8GB 显存:  ✓ 可用

$ python -m rag_builder scaffold rag_config.json -o ./output -n my-rag
生成了 7 个文件到 ./output/my-rag/:
  - ingest.py
  - query.py
  - config.py
  - README.md
  - requirements.txt
  - rag_config.json
```

---

## 🎉 What's New

### v0.1.0 — "RAG Builder Skill" 🚀 *(2026-06-03)*

> 首版发布 — RAG 全链路知识库 + 配置验证 + 项目脚手架 + 检索评估。

| 新功能 | 说明 | 操作 |
|--------|------|------|
| 📋 **SKILL.md 知识库** | 12 章节覆盖 RAG 全链路，含 13 个常见陷阱 | 作为 Hermes Agent 技能安装 |
| 🔍 **配置验证** | 检查参数兼容性 + GPU 显存估算 | `python -m rag_builder validate config.json` |
| 🏗️ **项目脚手架** | 一键生成 ingest/query/config 骨架代码 | `python -m rag_builder scaffold config.json` |
| 📊 **检索评估** | Precision/Recall/F1 + RAGAS 数据集生成 | `python -m rag_builder benchmark gt.json` |

---

## 🚀 快速开始

```bash
# 1. 安装
pip install -e .

# 2. 生成示例配置
python -m rag_builder init -o rag_config.json

# 3. 验证配置（含 GPU 显存估算）
python -m rag_builder validate rag_config.json

# 4. 生成项目骨架
python -m rag_builder scaffold rag_config.json -o ./output -n my-rag
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

---

## 🧰 功能特性

| 功能 | 说明 |
|------|------|
| ✅ **配置 Schema** | 5 大模块数据类：Chunking / Embedding / VectorStore / Retriever / Query |
| ✅ **GPU 显存估算** | 根据模型 + batch_size 估算显存，判断 8GB 是否够用 |
| ✅ **交叉验证** | chunk_size vs 模型最大序列长度、rerank_top_n vs top_k |
| ✅ **项目脚手架** | 根据配置生成完整的 ingest/query/config 骨架代码 |
| ✅ **检索评估** | Precision / Recall / F1，支持自定义 retrieve 函数 |
| ✅ **RAGAS 数据集** | 生成 RAGAS 兼容的评估数据集，直接喂给 `ragas.evaluate()` |
| ✅ **CLI 工具** | init / validate / scaffold / benchmark 四个子命令 |
| ✅ **13 个陷阱** | Windows CUDA、Milvus 分页、Reranker OOM、API base_url 等 |

---

## 📚 SKILL.md 知识库覆盖范围

SKILL.md 是一个 21KB 的 Hermes Agent 技能文件，覆盖 RAG 全链路：

| 章节 | 内容 |
|------|------|
| 完整 Pipeline 指南 | 架构图 + 配置验证 + 骨架生成 |
| 文档解析 | pymupdf / marker-pdf / MinerU / unstructured 对比 |
| 分块策略 | 4 种策略 + 参数经验值 + 表格特殊处理 |
| 嵌入模型 | 5 个模型对比（bge 系列 + OpenAI API） |
| 向量存储 | Milvus / Chroma / FAISS / Qdrant |
| 混合检索 | BM25 + 向量 + RRF 融合 |
| Reranker 精排 | bge-reranker + 显存管理 |
| 查询分解 | step_back / multi_query / sub_questions |
| RAGAS 评估 | 4 核心指标 + v0.2+ API |
| 常见陷阱 | 13 个实战踩坑经验 |
| 嵌入微调 | bge-base-zh-v1.5 微调（8GB 显存） |

安装为 Hermes Agent 技能：
```bash
cp SKILL.md ~/.hermes/skills/rag-builder/SKILL.md
```

---

## 🔧 CLI 命令

```bash
# 生成示例配置
python -m rag_builder init -o my_config.json

# 验证配置（检查参数兼容性 + GPU 显存估算）
python -m rag_builder validate my_config.json

# 生成项目骨架
python -m rag_builder scaffold my_config.json -o ./output -n my-rag

# 运行评估
python -m rag_builder benchmark ground_truth.json --config v1 -o report.json --json
```

---

## 🐍 Python API

```python
from rag_builder.config_schema import RAGConfig, estimate_gpu_vram
from rag_builder.scaffold import scaffold_project
from rag_builder.benchmark import run_benchmark, generate_ragas_dataset

# 创建配置
config = RAGConfig.from_dict({"chunking": {"chunk_size": 512}, ...})

# 验证
errors = config.validate()
vram = estimate_gpu_vram(config)

# 生成骨架
files = scaffold_project(config, "./output", "my-rag")

# 评估
report = run_benchmark(queries, my_retrieve_fn, config_name="v1")
print(report.summary())
```

---

## 🏗️ 项目结构

```
rag-builder/
├── SKILL.md                        # Hermes Agent 技能文件（21KB RAG 知识库）
├── pyproject.toml                  # 项目元数据 + 依赖
├── src/rag_builder/
│   ├── __init__.py                 # 版本号
│   ├── __main__.py                 # CLI 入口
│   ├── config_schema.py            # 配置 Schema + 验证 + 显存估算
│   ├── scaffold.py                 # 项目骨架生成（模板引擎）
│   ├── benchmark.py                # 检索评估 + RAGAS 数据集生成
│   └── cli.py                      # CLI 命令（init/validate/scaffold/benchmark）
├── tests/
│   ├── test_config_schema.py       # 配置验证测试
│   ├── test_scaffold.py            # 骨架生成测试
│   ├── test_benchmark.py           # 评估工具测试
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

# 运行测试
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
  <a href="./LICENSE">MIT License</a> •
  <a href="./CONTRIBUTING.md">Contribute</a>
</p>
