---
name: rag-builder
description: Build and optimize RAG systems — PDF parsing, chunking, hybrid retrieval, reranking, query decomposition, RAGAS evaluation. Includes config validation, project scaffolding, and benchmarking tools.
triggers:
  - RAG
  - retrieval augmented generation
  - PDF parsing
  - chunking
  - embedding
  - vector search
  - hybrid retrieval
  - BM25
  - reranker
  - query decomposition
  - RAGAS
  - Milvus
  - Chroma
  - FAISS
  - bge
  - knowledge base
---

# RAG Builder Skill

从零构建或优化 RAG（检索增强生成）系统。覆盖完整 pipeline：文档解析 → 分块 → 向量化 → 混合检索 → 精排 → 查询分解 → 评估。

## 快速决策树

```
你的场景是什么？
├── 从零搭建 RAG → 用 rag-builder scaffold 生成骨架
├── 检索效果差 → 跳转 references/retrieval-methods.md
├── 需要评估 → 跳转 references/pitfalls.md (RAGAS 章节)
└── PDF 解析问题 → 跳转 references/pdf-parsing.md
```

---

## 1. Pipeline 架构

```
文档 → 解析(PDF/MD/TXT) → 分块(Chunking) → 向量化(Embedding) → 存储(Milvus/Chroma)
                                                                              ↓
用户查询 → 查询理解 → 混合检索(BM25+Vector) → Reranker精排 → LLM生成 → 回答
```

---

## 2. CLI 命令参考

### 2.1 生成配置

```bash
# 生成示例配置
rag-builder init -o rag_config.json
```

### 2.2 验证配置

```bash
# 检查参数兼容性 + GPU 显存估算
rag-builder validate rag_config.json
```

### 2.3 健康检查（v0.3.0 新增）

```bash
# 一键检查：配置 + 依赖 + GPU + 网络
rag-builder diagnose rag_config.json

# JSON 输出（供 Agent 解析）
rag-builder diagnose rag_config.json --json

# 跳过网络检测
rag-builder diagnose rag_config.json --skip-network
```

输出示例：
```
🔍 RAG Builder 健康检查
━━━━━━━━━━━━━━━━━━━━━━━
✅ 配置文件: 有效
✅ Python: 3.11.5
✅ sentence-transformers: 2.2.2
❌ pymilvus: 未安装（配置要求 milvus）
✅ GPU: NVIDIA RTX 4060 (8.0 GB)
⚠️  Embedding 显存: 1.0 GB（剩余 7.0 GB 可用）
✅ Milvus 连通: localhost:19530
━━━━━━━━━━━━━━━━━━━━━━━
结果: 6/7 通过, 1 警告, 0 错误
```

### 2.4 生成项目骨架

```bash
rag-builder scaffold rag_config.json -o ./output -n my-rag
```

生成的项目包含 `ingest.py`（入库）、`query.py`（查询）、`config.py`（配置）。

### 2.5 运行评估

```bash
rag-builder benchmark ground_truth.json --config my_config -o report.json --json
```

ground_truth.json 格式：
```json
[
  {
    "query": "什么是 RAG？",
    "expected_texts": ["RAG 是检索增强生成..."],
    "answer": "RAG 是一种结合检索和生成的 AI 技术..."
  }
]
```

### 2.6 文档入库

```bash
# 解析 → 分块 → 向量化 → 入库
rag-builder ingest ./docs --config rag_config.json

# 预览分块结果
rag-builder ingest ./docs --config rag_config.json --preview

# 指定 embedding provider
rag-builder ingest ./docs --embedding-provider openai --api-key sk-xxx --base-url https://api.openai.com/v1
```

### 2.7 混合检索

```bash
# BM25 + 向量 RRF 融合检索
rag-builder query "什么是RAG？" --config rag_config.json --top-k 10

# JSON 输出
rag-builder query "什么是RAG？" --config rag_config.json --json
```

---

## 3. 配置文件说明

`rag_config.json` 结构：

```json
{
  "chunking": {
    "strategy": "recursive",      // recursive/fixed_size/by_sentence
    "chunk_size": 512,
    "chunk_overlap": 128,
    "min_chunk_size": 50
  },
  "embedding": {
    "model": "bge-base-zh-v1.5",  // 本地模型或 OpenAI 模型名
    "batch_size": 8,
    "device": "auto",             // auto/cpu/cuda
    "normalize": true
  },
  "vector_store": {
    "backend": "milvus",          // milvus/chroma
    "collection": "my_docs",
    "metric": "cosine",
    "index_type": "HNSW"
  },
  "retriever": {
    "strategy": "hybrid",         // hybrid/bm25_only/vector_only
    "top_k": 10,
    "rerank_top_n": 5,
    "bm25_weight": 0.3,
    "vector_weight": 0.7,
    "reranker_model": "bge-reranker-base"
  },
  "query": {
    "decompose": false,
    "decompose_strategy": "step_back",  // step_back/multi_query/sub_questions
    "max_sub_queries": 3,
    "synonym_expansion": true
  }
}
```

---

## 4. Python API

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

## 5. 深入阅读

详细的技术方案、代码示例和对比分析请参阅 references/ 目录：

| 文件 | 内容 |
|------|------|
| [pdf-parsing.md](references/pdf-parsing.md) | PDF 解析方案对比（pymupdf/MinerU/marker）、表格处理 |
| [embedding-models.md](references/embedding-models.md) | Embedding 模型选型、GPU 显存估算、查询指令 |
| [chunking-strategies.md](references/chunking-strategies.md) | 分块策略详解（recursive/semantic/by_title）、参数经验值 |
| [vector-stores.md](references/vector-stores.md) | Milvus/Chroma/FAISS 对比、配置示例、分页限制 |
| [retrieval-methods.md](references/retrieval-methods.md) | BM25+向量 RRF、Reranker 选型、查询分解策略 |
| [pitfalls.md](references/pitfalls.md) | 13 个常见陷阱（CUDA/Milvus/OOM/base_url/LightRAG/RAGAS） |
