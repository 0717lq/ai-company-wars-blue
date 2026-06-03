# 文件功能说明

## 源代码 (src/rag_builder/)

### `__init__.py`
包初始化文件，定义 `__version__ = "0.1.0"`。

### `__main__.py`
CLI 入口点，允许 `python -m rag_builder` 直接运行。

### `config_schema.py`
**RAG pipeline 配置 schema 和验证引擎。**

- `EMBEDDING_PRESETS`: 嵌入模型预设配置字典（bge-base-zh-v1.5, bge-m3, bge-large-zh-v1.5, text-embedding-3-small/large）
- `RERANKER_PRESETS`: Reranker 预设配置字典（bge-reranker-base/large/v2-m3, cohere）
- `ChunkingConfig`: 分块策略配置（strategy/chunk_size/overlap/min_size）+ 验证
- `EmbeddingConfig`: 嵌入模型配置（model/batch_size/device/normalize）+ 验证 + preset 属性
- `VectorStoreConfig`: 向量存储配置（backend/collection/metric/index_type）+ 验证
- `RetrieverConfig`: 检索策略配置（strategy/top_k/rerank_top_n/weights）+ 验证
- `QueryConfig`: 查询处理配置（decompose/strategy/max_sub_queries）+ 验证
- `RAGConfig`: 完整 pipeline 配置聚合 + 交叉验证 + 序列化/反序列化
- `estimate_gpu_vram()`: GPU 显存估算函数

### `scaffold.py`
**项目骨架代码生成器。**

- `_render()`: 用 `$VAR` 占位符替换模板变量（避免与 Python f-string 的 `{}` 冲突）
- `INGEST_TEMPLATE`: ingest.py 模板（文档加载 + 分块 + 预览）
- `QUERY_TEMPLATE`: query.py 模板（查询分解 + 检索 + 精排 + 生成）
- `CONFIG_TEMPLATE`: config.py 模板
- `README_TEMPLATE`: README.md 模板
- `REQUIREMENTS_TEMPLATE`: requirements.txt 模板
- `scaffold_project()`: 根据 RAGConfig 生成完整项目骨架

### `benchmark.py`
**检索质量评估工具。**

- `BenchmarkResult`: 单条评估结果（query/retrieved/expected + P/R/F1）
- `BenchmarkReport`: 评估报告（聚合多条结果 + 平均指标 + JSON/文本输出）
- `load_ground_truth()`: 加载 ground truth JSON 文件
- `run_benchmark()`: 运行评估（接受 retrieve 函数回调）
- `generate_ragas_dataset()`: 生成 RAGAS 兼容评估数据集

### `cli.py`
**CLI 命令实现。**

- `cmd_init()`: 生成示例配置文件
- `cmd_validate()`: 验证配置 + GPU 显存估算
- `cmd_scaffold()`: 生成项目骨架
- `cmd_benchmark()`: 运行评估
- `main()`: argparse 入口 + 子命令路由

## 测试 (tests/)

### `test_config_schema.py`
配置验证的全面测试，覆盖所有 5 个 config class + GPU 显存估算。28 个测试。

### `test_scaffold.py`
骨架生成测试，验证文件生成、Python 语法正确性、配置值注入。12 个测试。

### `test_benchmark.py`
评估工具测试，覆盖 BenchmarkResult 指标计算、Report 聚合、RAGAS 数据集生成。15 个测试。

### `test_cli.py`
CLI 命令测试，覆盖 init/validate/scaffold/benchmark + 边界情况。13 个测试。

## 技能文件

### `SKILL.md`
Hermes Agent 技能文件。完整的 RAG 构建指南，覆盖：
1. Pipeline 架构 + 快速决策树
2. 文档解析（pymupdf/MinerU/Markdown）
3. 分块策略（4 种策略 + 参数经验值）
4. 嵌入模型选择（5 个模型对比）
5. 向量存储（Milvus/Chroma/FAISS/Qdrant）
6. 混合检索（BM25 + 向量 + RRF 融合）
7. Reranker 精排（bge-reranker + 显存管理）
8. 查询分解（3 种策略）
9. RAGAS 评估（v0.2+ API）
10. 常见陷阱（Windows CUDA、Milvus 分页、API URL 等）
11. 工具使用（CLI + Python API）
12. 嵌入模型微调
