# 项目结构

```
./.gitignore
./.ruff_cache/.gitignore
./.ruff_cache/0.15.15/10195653236098056378
./.ruff_cache/0.15.15/14303814808973274848
./.ruff_cache/0.15.15/6460985398272920039
./.ruff_cache/0.15.15/8619914391599093070
./.ruff_cache/CACHEDIR.TAG
./CHANGELOG.md
./LICENSE
./README.en.md
./README.md
./SKILL.md
./docs/CODE.md
./docs/FILES.md
./docs/STRUCTURE.md
./pyproject.toml
./references/chunking-strategies.md
./references/embedding-models.md
./references/pdf-parsing.md
./references/pitfalls.md
./references/retrieval-methods.md
./references/vector-stores.md
./src/rag_builder/__init__.py
./src/rag_builder/__main__.py
./src/rag_builder/benchmark.py
./src/rag_builder/cli.py
./src/rag_builder/config_schema.py
./src/rag_builder/diagnose.py
./src/rag_builder/embeddings.py
./src/rag_builder/parsers.py
./src/rag_builder/retriever.py
./src/rag_builder/scaffold.py
./src/rag_builder/vector_store.py
./tests/test_benchmark.py
./tests/test_cli.py
./tests/test_config_schema.py
./tests/test_diagnose.py
./tests/test_embeddings.py
./tests/test_integration.py
./tests/test_parsers.py
./tests/test_retriever.py
./tests/test_scaffold.py
./tests/test_vector_store.py
```

## 目录说明

| 目录 | 说明 |
|------|------|
| `src/rag_builder/` | 核心 Python 包（11 个模块） |
| `tests/` | pytest 测试（10 个文件） |
| `references/` | SKILL.md 拆分出的专题文档（6 个） |
| `docs/` | 项目自动生成文档 |
