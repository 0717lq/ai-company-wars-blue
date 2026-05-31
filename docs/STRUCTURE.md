# fclean v0.5.0 — 项目结构

```
project/
├── pyproject.toml                  # 项目配置、依赖、版本号
├── README.md                       # 中英双语文档（800+ 行）
├── CHANGELOG.md                    # 版本变更记录
├── CONTRIBUTING.md                 # 贡献指南
├── LICENSE                         # MIT 许可证
├── Dockerfile                      # Docker 容器化
├── .dockerignore                   # Docker 忽略文件
├── .pre-commit-hooks.yaml          # Pre-commit hook 定义
├── .fcleanrc.example               # 配置文件示例
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml                  # CI 流水线（ruff + pytest + Docker）
│       └── publish.yml             # PyPI 发布（OIDC Trusted Publisher）
├── docs/
│   ├── STRUCTURE.md                # 本文件
│   ├── FILES.md                    # 文件功能说明
│   └── CODE.md                     # 核心代码文档
├── src/
│   └── fclean/
│       ├── __init__.py             # 包初始化、版本号
│       ├── __main__.py             # python -m fclean 入口
│       ├── cli.py                  # CLI 命令行入口（argparse）
│       ├── config.py               # 配置系统（.fcleanrc 加载/合并）
│       ├── dupes.py                # 重复文件检测（SHA-256）
│       ├── ignore.py               # .fcleanignore 解析器
│       ├── organizer.py            # 核心整理逻辑
│       ├── renamer.py              # 批量重命名
│       ├── rules.py                # 分类规则
│       ├── stats_viz.py            # 统计可视化（ASCII 图表）
│       ├── undo.py                 # Undo 回滚系统
│       └── watcher.py              # 文件监控（watchdog）
└── tests/
    ├── __init__.py
    ├── test_cli.py                 # CLI 参数解析测试
    ├── test_config.py              # 配置系统测试
    ├── test_dupes.py               # 重复文件检测测试
    ├── test_edge_cases.py          # 边界条件测试
    ├── test_ignore.py              # .fcleanignore 测试
    ├── test_organizer.py           # 整理逻辑测试
    ├── test_renamer.py             # 批量重命名测试
    ├── test_rules.py               # 分类规则测试
    ├── test_stats_viz.py           # 可视化模块测试
    ├── test_undo.py                # Undo 系统测试
    └── test_watcher.py             # 文件监控测试
```

**测试统计**: 238 个测试，12 个测试文件，12 个源文件。
