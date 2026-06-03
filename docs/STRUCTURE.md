# 项目结构

```
project/
├── SKILL.md                        # RAG Builder 技能文件（Hermes Agent 可直接安装）
├── pyproject.toml                  # 项目配置 + 依赖
├── src/
│   └── rag_builder/
│       ├── __init__.py             # 包初始化，版本号
│       ├── __main__.py             # CLI 入口（python -m rag_builder）
│       ├── config_schema.py        # RAG pipeline 配置 schema + 验证 + GPU 显存估算
│       ├── scaffold.py             # 项目骨架代码生成器
│       ├── benchmark.py            # 检索质量评估工具 + RAGAS 数据集生成
│       └── cli.py                  # CLI 命令（init/validate/scaffold/benchmark）
├── tests/
│   ├── test_config_schema.py       # 配置验证测试（28 个）
│   ├── test_scaffold.py            # 骨架生成测试（12 个）
│   ├── test_benchmark.py           # 评估工具测试（15 个）
│   └── test_cli.py                 # CLI 命令测试（13 个）
└── docs/
    ├── STRUCTURE.md                # 本文件
    ├── FILES.md                    # 文件功能说明
    └── CODE.md                     # 核心代码说明
```

## 模块依赖关系

```
cli.py → config_schema.py (RAGConfig, estimate_gpu_vram)
       → scaffold.py (scaffold_project)
       → benchmark.py (run_benchmark, load_ground_truth)

scaffold.py → config_schema.py (RAGConfig, EMBEDDING_PRESETS)

benchmark.py (独立模块，不依赖其他内部模块)
```
