# 文件功能说明

## 源码文件 (src/rag_builder/)

| 文件 | 功能 |
|------|------|
| `__init__.py` | 包初始化，定义 `__version__` |
| `__main__.py` | `python -m rag_builder` 入口 |
| `cli.py` | CLI 命令行接口（7 个子命令：init/validate/scaffold/benchmark/ingest/query/diagnose） |
| `config_schema.py` | 5 个配置 dataclass + 验证 + GPU 显存估算 |
| `diagnose.py` | 健康检查模块（配置+依赖+GPU+网络 4 维度检测） |
| `embeddings.py` | Embedding 抽象层（STProvider + OpenAIProvider + 工厂函数） |
| `parsers.py` | 文档解析器（PDF/Markdown/纯文本）+ 分块器（recursive/fixed_size/by_sentence） |
| `retriever.py` | 混合检索器（BM25 + 向量 RRF 融合） |
| `scaffold.py` | 项目骨架生成器 |
| `benchmark.py` | 检索质量评估 + RAGAS 数据集生成 |
| `vector_store.py` | 向量存储抽象层（MilvusStore + ChromaStore） |

## 测试文件 (tests/)

| 文件 | 测试数 | 覆盖模块 |
|------|--------|---------|
| `test_cli.py` | 8 | CLI 命令 |
| `test_config_schema.py` | 25 | 配置验证 |
| `test_diagnose.py` | 25 | 健康检查 |
| `test_embeddings.py` | 10 | Embedding 层 |
| `test_parsers.py` | 14 | 文档解析+分块 |
| `test_retriever.py` | 12 | 检索器 |
| `test_scaffold.py` | 12 | 骨架生成 |
| `test_benchmark.py` | 8 | 评估模块 |
| `test_vector_store.py` | 10 | 向量存储 |
| `test_integration.py` | 5 | 集成测试 |

## 文档文件

| 文件 | 说明 |
|------|------|
| `SKILL.md` | Hermes Agent 技能文件（精简版，221 行） |
| `references/*.md` | 6 个专题深入文档 |
| `CHANGELOG.md` | 版本变更日志 |
| `README.md` / `README.en.md` | 项目说明 |
