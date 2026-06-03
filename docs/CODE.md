# 核心代码说明

## config_schema.py

### 数据类 (5 个)

| 类 | 核心属性 | 验证逻辑 |
|---|---------|---------|
| `ChunkingConfig` | strategy, chunk_size, chunk_overlap, min_chunk_size | 策略合法性、size 范围、overlap < size |
| `EmbeddingConfig` | model, batch_size, device, normalize | 模型名在预设中、batch 范围、device 合法 |
| `VectorStoreConfig` | backend, collection, metric, index_type | 后端/度量/索引类型合法性、collection 非空 |
| `RetrieverConfig` | strategy, top_k, rerank_top_n, weights | 策略合法性、rerank ≤ top_k、权重范围 |
| `QueryConfig` | decompose, decompose_strategy, max_sub_queries | 策略合法性、sub_queries 范围 |

### `RAGConfig`
聚合 5 个子配置，提供：
- `validate()`: 收集所有子配置错误 + 交叉验证（chunk_size ≤ 模型 max_seq_length）
- `to_dict()` / `from_dict()`: 序列化往返

### `estimate_gpu_vram(config) -> dict`
根据嵌入模型预设 + batch_size + reranker 显存估算总需求。
返回 `{embedding, reranker, total, fits_8gb}`。

---

## scaffold.py

### `_render(template, **kwargs)`
用 `$VAR` 占位符替换模板变量。避免 Python f-string `{}` 与模板变量冲突。

### `scaffold_project(config, output_dir, project_name) -> dict`
根据 RAGConfig 生成 6 个文件：ingest.py, query.py, config.py, README.md, requirements.txt, rag_config.json。
返回 `{filename: content}` 字典。

---

## benchmark.py

### `BenchmarkResult.compute_metrics()`
计算 precision = |hits|/|retrieved|, recall = |hits|/|expected|, F1。
边界处理：expected 为空时 recall=1.0。

### `BenchmarkReport`
聚合多个 BenchmarkResult，计算 avg_precision/recall/f1。
提供 `to_json()` 和 `summary()` 两种输出格式。

### `run_benchmark(queries, retrieve_fn, config_name) -> BenchmarkReport`
接受 retrieve_fn 回调（接收 query，返回文本列表或 dict 列表），自动计算评估指标。

### `generate_ragas_dataset(queries, retrieve_fn, generate_fn) -> list[dict]`
生成 RAGAS `evaluate()` 兼容数据集：`{question, ground_truth, contexts, answer}`。

---

## cli.py

### 子命令

| 命令 | 功能 | 关键参数 |
|------|------|---------|
| `init` | 生成示例配置 | `-o output` |
| `validate` | 验证配置 + 显存估算 | `config.json` |
| `scaffold` | 生成项目骨架 | `config.json -o dir -n name` |
| `benchmark` | 运行评估 | `gt.json --config name --json -o report` |

### `cmd_benchmark`
使用 dummy retrieve function（打印到 stderr），实际用户需接入自己的检索函数。

---

## SKILL.md 技能文件

12 个章节，覆盖 RAG 全链路：
1. Pipeline 架构 + 快速决策树
2. 文档解析方案对比
3. 分块策略（4 种 + 参数经验值）
4. 嵌入模型选择（5 个模型 + 查询指令）
5. 向量存储（4 个方案 + 代码示例）
6. 混合检索（BM25 + RRF 融合）
7. Reranker 精排（显存管理）
8. 查询分解（3 种策略）
9. RAGAS 评估（v0.2+ API）
10. 常见陷阱（13 个）
11. 工具使用
12. 嵌入模型微调
