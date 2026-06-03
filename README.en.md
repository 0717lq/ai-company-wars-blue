# rag-builder

A lightweight RAG pipeline toolkit — from config validation to document ingestion and hybrid retrieval.

## Features

- **Config Validation**: Validate RAG pipeline configurations (chunking, embedding, vector store, retrieval)
- **Project Scaffolding**: Generate complete RAG project boilerplate from config
- **Benchmarking**: Retrieval quality evaluation with RAGAS-compatible dataset generation
- **Document Parsers**: PDF (pymupdf), Markdown (header-aware), plain text
- **Text Chunking**: Recursive, fixed-size, and sentence-aware strategies with overlap
- **Embedding Abstraction**: sentence-transformers (local) + OpenAI-compatible API (remote)
- **Vector Store Connectors**: Milvus + Chroma with unified interface
- **Hybrid Retrieval**: BM25 + vector search with Reciprocal Rank Fusion (RRF)
- **CLI**: 6 subcommands — `init`, `validate`, `scaffold`, `benchmark`, `ingest`, `query`

## Installation

```bash
# Core only (config validation + scaffolding + benchmarking)
pip install rag-builder

# With specific backends
pip install rag-builder[st]          # sentence-transformers
pip install rag-builder[openai]      # OpenAI-compatible API
pip install rag-builder[milvus]      # Milvus vector store
pip install rag-builder[chromadb]    # Chroma vector store
pip install rag-builder[pdf]         # PDF parsing (pymupdf)
pip install rag-builder[bm25]        # BM25 retrieval
pip install rag-builder[all]         # Everything
```

## Quick Start

```bash
# 1. Generate sample config
rag-builder init

# 2. Validate config
rag-builder validate rag_config.json

# 3. Generate project scaffold
rag-builder scaffold rag_config.json -o ./my-rag -n my-project

# 4. Preview document chunking
rag-builder ingest ./documents --preview

# 5. Ingest documents (requires embedding + vector store)
rag-builder ingest ./documents --config rag_config.json

# 6. Query
rag-builder query "What is RAG?" --config rag_config.json --json
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `rag-builder init [-o path]` | Generate sample config file |
| `rag-builder validate <config.json>` | Validate RAG pipeline config |
| `rag-builder scaffold <config.json> -o dir -n name` | Generate project boilerplate |
| `rag-builder benchmark <ground_truth.json> [--json]` | Run retrieval quality evaluation |
| `rag-builder ingest <path> [--preview] [--config json]` | Parse, chunk, embed, and store documents |
| `rag-builder query "question" [--json] [--config json]` | Hybrid retrieval (BM25 + vector RRF) |

## Architecture

```
rag_builder/
  config_schema.py   # 5 config dataclasses + validation + GPU VRAM estimation
  scaffold.py        # Template-based project scaffolding
  benchmark.py       # Retrieval quality evaluation + RAGAS dataset generation
  embeddings.py      # EmbeddingProvider ABC + STProvider + OpenAIProvider
  vector_store.py    # VectorStore ABC + MilvusStore + ChromaStore
  parsers.py         # PDF/Markdown/text parsers + text chunking
  retriever.py       # HybridRetriever (BM25 + vector RRF fusion)
  cli.py             # CLI entry point (6 subcommands)
```

## Optional Dependencies

| Group | Packages | Use Case |
|-------|----------|----------|
| `st` | sentence-transformers | Local embedding (GPU/CPU) |
| `openai` | openai | Remote embedding API (OpenAI, MIMO, DashScope) |
| `milvus` | pymilvus | Milvus vector store |
| `chromadb` | chromadb | Chroma vector store |
| `pdf` | pymupdf | PDF document parsing |
| `bm25` | rank-bm25, jieba | BM25 keyword retrieval with Chinese tokenization |
| `all` | all of the above | Full installation |

## License

MIT
