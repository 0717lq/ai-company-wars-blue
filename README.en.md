<div align="center">

# 🔍 rag-builder

### Build & optimize RAG pipelines — from PDF parsing to RAGAS evaluation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Tests](https://img.shields.io/badge/tests-172%20passed-brightgreen?style=flat&logo=pytest)]()
[![Ruff](https://img.shields.io/badge/lint-ruff-050505?style=flat&logo=ruff)](https://docs.astral.sh/ruff/)

[🇨🇳 中文](./README.md) · **English**

</div>

---

rag-builder is a **Hermes Agent skill + Python toolkit** for building and optimizing RAG (Retrieval-Augmented Generation) systems from scratch.

It covers the full RAG pipeline: document parsing → chunking → embedding → hybrid retrieval → reranker → query decomposition → RAGAS evaluation.

Includes Python tools: config validation, project scaffolding, document ingestion, hybrid retrieval, and health diagnostics.

---

## 📸 Quick Look

```text
$ rag-builder init -o rag_config.json
Sample config generated: rag_config.json

$ rag-builder validate rag_config.json
Config validation passed ✓

GPU VRAM estimation:
  Embedding: 1.0 GB
  Reranker:  1.5 GB
  Total:     2.5 GB
  8GB VRAM:  ✓ Sufficient

$ rag-builder diagnose rag_config.json
rag-builder health check
========================

  Config:    ✓ Passed
  Dependencies:
    sentence-transformers  ✓ 2.2.0
    pymilvus              ✓ 2.4.0
    pymupdf               ✓ 1.23.0
    rank-bm25             ✓ 0.2.0
    jieba                 ✓ 0.42.0
  GPU:       ✓ RTX 4060 — 8192 MB
  Network:   ✓ Milvus (19530) reachable
```

---

## 🎉 What's New

### v0.3.0 — "Diagnose & Split" 🔧 *(2026-06-03)*

> Health diagnostics + SKILL.md slim-down + batch bug fix.

| Improvement | Description | Value to Users |
|-------------|-------------|----------------|
| 🩺 **`diagnose` command** | 4-dimension health check: config/dependencies/GPU/network | One-click environment troubleshooting before deployment |
| 📖 **SKILL.md split** | 774 lines → 221-line main file + 6 topic files | Faster Agent loading, on-demand knowledge access |
| 🐛 **Batch bug fix** | `embed_texts` test count fix | More accurate tests, more confident development |

### v0.2.0 — "Full Pipeline" 🚀 *(2026-06-03)*

> From "config tool" to "full-stack RAG toolkit".

| New Feature | Description | Usage |
|-------------|-------------|-------|
| 📄 **Document parsers** | PDF / Markdown / text, with directory batch scanning | `rag-builder ingest --dir ./docs` |
| 🧩 **Hybrid retriever** | BM25 + vector search + RRF fusion | `rag-builder query "question"` |
| 🔌 **Embedding abstraction** | sentence-transformers + OpenAI-compatible API | `--provider openai` |
| 💾 **Vector store connectors** | Milvus + Chroma dual backends | `--store milvus` |

### v0.1.0 — "RAG Builder Skill" 🚀 *(2026-05-30)*

> Initial release — RAG knowledge base + config validation + project scaffolding + retrieval evaluation.

| New Feature | Description | Usage |
|-------------|-------------|-------|
| 📋 **SKILL.md knowledge base** | 12 chapters covering full RAG pipeline, 13 common pitfalls | Install as Hermes Agent skill |
| 🔍 **Config validation** | Parameter compatibility + GPU VRAM estimation | `rag-builder validate config.json` |
| 🏗️ **Project scaffolding** | One-click generate ingest/query/config boilerplate | `rag-builder scaffold config.json` |
| 📊 **Retrieval evaluation** | Precision/Recall/F1 + RAGAS dataset generation | `rag-builder benchmark gt.json` |

---

## 🚀 Quick Start

```bash
# 1. Install
pip install -e .

# 2. Generate sample config
rag-builder init -o rag_config.json

# 3. Validate config (with GPU VRAM estimation)
rag-builder validate rag_config.json

# 4. Health diagnostics
rag-builder diagnose rag_config.json

# 5. Generate project scaffold
rag-builder scaffold rag_config.json -o ./output -n my-rag
```

Generated project includes `ingest.py` (ingestion), `query.py` (retrieval), `config.py` (config) — ready to use.

---

## ❓ Why rag-builder?

| Scenario | Without rag-builder | With rag-builder |
|----------|-------------------|-----------------|
| Build RAG from scratch | Read 10 blog posts, piece together a plan | One SKILL.md covers the full pipeline |
| Choose embedding model | Not sure which fits Chinese | 5 models compared + VRAM estimation |
| Set chunking params | Guess chunk_size=512 | Empirical values by document type |
| Poor retrieval quality | Blindly tune top_k | Hybrid retrieval + Reranker approach |
| Evaluate RAG quality | Homebrew comparison (unprofessional) | RAGAS industry-standard 4 metrics |
| 8GB VRAM enough? | OOM at runtime | validate command estimates ahead |
| Dependencies correct? | Check one by one manually | diagnose checks everything |
| Document ingestion | Write your own script | `rag-builder ingest` one-liner |

---

## 🧰 Features

| Feature | Description |
|---------|-------------|
| ✅ **Config Schema** | 5 module dataclasses: Chunking / Embedding / VectorStore / Retriever / Query |
| ✅ **GPU VRAM Estimation** | Estimate VRAM by model + batch_size, check if 8GB is enough |
| ✅ **Cross Validation** | chunk_size vs max sequence length, rerank_top_n vs top_k |
| ✅ **Project Scaffolding** | Generate complete ingest/query/config boilerplate from config |
| ✅ **Document Parsing** | PDF (pymupdf) / Markdown (header-aware) / text + directory batch scan |
| ✅ **Hybrid Retrieval** | BM25 + vector semantic search + Reciprocal Rank Fusion |
| ✅ **Embedding Abstraction** | sentence-transformers local + OpenAI-compatible API remote |
| ✅ **Vector Stores** | Milvus + Chroma dual backends, factory function switching |
| ✅ **Health Diagnostics** | 4-dimension check: config/dependencies/GPU/network, JSON output |
| ✅ **Retrieval Evaluation** | Precision / Recall / F1, custom retrieve function support |
| ✅ **RAGAS Datasets** | Generate RAGAS-compatible evaluation datasets for `ragas.evaluate()` |
| ✅ **CLI** | 7 subcommands: init / validate / scaffold / benchmark / ingest / query / diagnose |
| ✅ **13 Pitfalls** | Windows CUDA, Milvus pagination, Reranker OOM, API base_url, etc. |

---

## 📚 SKILL.md Knowledge Base

SKILL.md (221-line main file) + 6 `references/` topic files covering the full RAG pipeline:

| File | Content |
|------|---------|
| **SKILL.md** (main) | Quick start, CLI reference, config guide, deep-dive links |
| `references/pdf-parsing.md` | pymupdf / marker-pdf / MinerU / unstructured comparison |
| `references/embedding-models.md` | 5 models compared (bge series + OpenAI API) |
| `references/chunking-strategies.md` | 4 strategies + empirical params + table handling |
| `references/vector-stores.md` | Milvus / Chroma / FAISS / Qdrant |
| `references/retrieval-methods.md` | Hybrid retrieval, BM25, RRF fusion, Reranker |
| `references/pitfalls.md` | 13 real-world pitfalls |

Install as Hermes Agent skill:
```bash
cp -r . ~/.hermes/skills/rag-builder/
```

---

## 🔧 CLI Reference

```bash
# Generate sample config
rag-builder init -o my_config.json

# Validate config (parameter compatibility + GPU VRAM estimation)
rag-builder validate my_config.json

# Health diagnostics (config + dependencies + GPU + network)
rag-builder diagnose my_config.json
rag-builder diagnose --json               # JSON output
rag-builder diagnose --skip-network       # Skip network check

# Generate project scaffold
rag-builder scaffold my_config.json -o ./output -n my-rag

# Document ingestion (parse + chunk + embed + store)
rag-builder ingest --dir ./docs --store milvus --provider st
rag-builder ingest --dir ./docs --preview  # Preview mode

# Hybrid retrieval query
rag-builder query "What is RAG?" --store milvus
rag-builder query "What is RAG?" --json    # JSON output

# Run evaluation
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

# Config validation
config = RAGConfig.from_dict({"chunking": {"chunk_size": 512}, ...})
errors = config.validate()
vram = estimate_gpu_vram(config)

# Document parsing + chunking
pages = parse_pdf("report.pdf")
chunks = chunk_text(pages, strategy="recursive", chunk_size=512)

# Embedding + storage
provider = get_provider("st", model_name="bge-base-zh-v1.5")
store = get_store("milvus", collection="my_docs")
store.insert(chunks, embeddings=provider.embed_texts(chunks))

# Hybrid retrieval
retriever = create_retriever(store, provider, bm25_corpus=chunks)
results = retriever.search("query", top_k=5)

# Health diagnostics
report = diagnose(config)
print(report.format_text())
```

---

## 🏗️ Project Structure

```
rag-builder/
├── SKILL.md                        # Hermes Agent skill main file (221 lines)
├── references/                     # Deep-dive topic files (6 files)
│   ├── pdf-parsing.md
│   ├── embedding-models.md
│   ├── chunking-strategies.md
│   ├── vector-stores.md
│   ├── retrieval-methods.md
│   └── pitfalls.md
├── pyproject.toml                  # Project metadata + dependencies
├── CHANGELOG.md                    # Version changelog
├── src/rag_builder/
│   ├── __init__.py                 # Version
│   ├── __main__.py                 # CLI entry
│   ├── config_schema.py            # Config Schema + validation + VRAM estimation
│   ├── scaffold.py                 # Project scaffolding (template engine)
│   ├── benchmark.py                # Retrieval evaluation + RAGAS dataset generation
│   ├── parsers.py                  # Document parsing (PDF/Markdown/text)
│   ├── embeddings.py               # Embedding abstraction (ST/OpenAI)
│   ├── vector_store.py             # Vector store connectors (Milvus/Chroma)
│   ├── retriever.py                # Hybrid retriever (BM25 + vector + RRF)
│   ├── diagnose.py                 # Health diagnostics (4-dimension check)
│   └── cli.py                      # CLI commands (7 subcommands)
├── tests/                          # 172 tests
└── docs/
    ├── CODE.md                     # Code documentation
    ├── FILES.md                    # File descriptions
    └── STRUCTURE.md                # Structure overview
```

---

## 🔬 Comparison

| Feature | **rag-builder** 🏆 | LangChain | LlamaIndex |
|---------|-------------------|-----------|------------|
| Config validation + VRAM estimation | ✅ | ❌ | ❌ |
| Project scaffolding | ✅ | ❌ | ❌ |
| Health diagnostics (config/deps/GPU/network) | ✅ | ❌ | ❌ |
| Document ingestion CLI | ✅ (`ingest`) | Code required | Code required |
| Hybrid retrieval (BM25 + vector + RRF) | ✅ Built-in | Needs combining | Needs combining |
| RAG knowledge base | ✅ (SKILL.md) | Scattered docs | Scattered docs |
| Retrieval quality evaluation | ✅ Built-in | Extra config needed | Extra config needed |
| RAGAS dataset generation | ✅ | ❌ | ❌ |
| Chinese RAG optimization | ✅ (bge/jieba) | Generic | Generic |
| Learning curve | Low (CLI + KB) | High | Medium |
| Dependencies | Minimal | Heavy | Medium |

**Positioning**: rag-builder is not a framework — it's a **knowledge base + lightweight toolkit**. It helps you make decisions (pick models, set params, avoid pitfalls), then generates your own RAG code skeleton.

---

## 🛠️ Development

```bash
# Clone
git clone https://github.com/0717lq/ai-company-wars-blue.git
cd ai-company-wars-blue

# Install dev dependencies
pip install -e ".[dev]"

# Run tests (172)
pytest tests/ -v

# Lint
ruff check src/ tests/
```

---

## 📄 License

[MIT](./LICENSE)

---

<p align="center">
  <b>rag-builder</b> — RAG pipeline knowledge base + lightweight toolkit<br>
  <a href="https://github.com/0717lq/ai-company-wars-blue">GitHub</a> •
  <a href="./CHANGELOG.md">Changelog</a> •
  <a href="./LICENSE">MIT License</a> •
  <a href="./README.md">中文</a>
</p>
