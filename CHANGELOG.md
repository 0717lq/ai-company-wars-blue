# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-06-03

### Added
- **`rag-builder diagnose` 命令**: RAG 系统一键健康检查，检查 4 个维度：配置完整性、依赖可用性、GPU 显存、网络连通性。
- **`--json` 输出**: diagnose 命令支持 `--json` 标志，输出结构化 JSON 供 Agent 解析。
- **`--skip-network` 标志**: 跳过网络连通性检测（离线环境使用）。
- **SKILL.md 拆分**: 从 774 行精简至 ~150 行主文件 + 6 个 `references/` 专题文件（pdf-parsing, embedding-models, chunking-strategies, vector-stores, retrieval-methods, pitfalls）。
- `diagnose.py` 模块：配置验证、依赖检测（7 个包）、GPU/显存检测（nvidia-smi）、网络连通性（TCP/HTTP）。
- `test_diagnose.py`: 25 个测试覆盖 diagnose 所有检查维度。

### Fixed
- **OpenAIProvider batch_processing bug**: `embed_texts()` 的测试修复——`__init__` 维度探测调用与 batch 调用分离计数。142 个测试全部通过。

### Changed
- Version bumped from 0.2.0 to 0.3.0.
- CLI now has 7 subcommands: `init`, `validate`, `scaffold`, `benchmark`, `ingest`, `query`, `diagnose`.

## [0.2.0] - 2026-06-03

### Added
- **Embedding abstraction layer** (`embeddings.py`): `EmbeddingProvider` ABC with `STProvider` (sentence-transformers) and `OpenAIProvider` (OpenAI-compatible API). Factory function `get_provider()`.
- **Vector store connectors** (`vector_store.py`): `VectorStore` ABC with `MilvusStore` and `ChromaStore`. Factory function `get_store()`.
- **Document parsers** (`parsers.py`): `parse_pdf()` (pymupdf), `parse_markdown()` (header-aware), `parse_text()`, `parse_directory()`. Text chunking with recursive, fixed-size, and sentence-aware strategies.
- **Hybrid retriever** (`retriever.py`): `HybridRetriever` combining BM25 keyword search and vector semantic search with Reciprocal Rank Fusion (RRF). Factory function `create_retriever()`.
- **CLI `ingest` subcommand**: Parse documents, chunk, embed, and store in vector database. Supports `--preview` mode.
- **CLI `query` subcommand**: Hybrid retrieval with BM25 + vector RRF fusion. Supports `--json` output.
- MIT LICENSE file.
- README.en.md (English documentation).
- Optional dependency groups: `[st]`, `[openai]`, `[milvus]`, `[chromadb]`, `[pdf]`, `[bm25]`, `[all]`.

### Changed
- Version bumped from 0.1.0 to 0.2.0.
- CLI now has 6 subcommands: `init`, `validate`, `scaffold`, `benchmark`, `ingest`, `query`.
- Updated `pyproject.toml` with new optional dependencies and script entry point.

## [0.1.0] - 2026-05-30

### Added
- Initial release.
- Configuration validation (`config_schema.py`): 5 config dataclasses with validation and GPU VRAM estimation.
- Project scaffolding (`scaffold.py`): Generate complete RAG project boilerplate from config.
- Benchmarking (`benchmark.py`): Retrieval quality evaluation with RAGAS-compatible dataset generation.
- CLI: `init`, `validate`, `scaffold`, `benchmark` subcommands.
- 78 pytest tests.
