# 核心代码说明

## config_schema.py — 配置系统

- `ChunkingConfig`: 分块策略（recursive/semantic/by_title/fixed_size）
- `EmbeddingConfig`: 嵌入模型配置（bge/OpenAI 预设）
- `VectorStoreConfig`: 向量存储配置（Milvus/Chroma/FAISS/Qdrant）
- `RetrieverConfig`: 检索策略配置（hybrid/bm25/vector/rerank）
- `QueryConfig`: 查询处理配置（分解策略）
- `RAGConfig`: 顶层配置聚合 + `validate()` + `from_dict()`/`to_dict()`
- `estimate_gpu_vram()`: GPU 显存估算

## diagnose.py — 健康检查

- `run_diagnosis(config_path, skip_network)` → `DiagnosisReport`
- `_check_config()`: 配置文件有效性
- `_check_python()`: Python 版本
- `_check_dependencies()`: 7 个依赖包安装状态
- `_check_gpu()`: nvidia-smi GPU 检测
- `_check_gpu_vram()`: 显存 vs 配置需求对比
- `_check_network()`: TCP/HTTP 连通性
- `format_report()`: 文本/JSON 格式化

## embeddings.py — Embedding 抽象层

- `EmbeddingProvider` ABC: `embed_texts()` + `dimension()`
- `STProvider`: sentence-transformers 本地模型
- `OpenAIProvider`: OpenAI 兼容 API（含维度探测 + 批处理 + L2 归一化）
- `get_provider()`: 工厂函数

## parsers.py — 文档解析

- `parse_pdf()` / `parse_markdown()` / `parse_text()` / `parse_directory()`
- `chunk_text()`: 递归/fixed_size/by_sentence 分块
- `chunk_documents()`: 批量分块（保留 source + metadata）

## retriever.py — 混合检索

- `BM25Index`: BM25 关键词索引（jieba 分词）
- `HybridRetriever`: BM25 + 向量 RRF 融合检索
- `create_retriever()`: 工厂函数

## vector_store.py — 向量存储

- `VectorStore` ABC: `add_texts()` + `search()`
- `MilvusStore` / `ChromaStore`: 具体实现
- `get_store()`: 工厂函数

## cli.py — CLI 入口

7 个子命令：`init`, `validate`, `scaffold`, `benchmark`, `ingest`, `query`, `diagnose`
入口：`rag_builder.cli:main`
