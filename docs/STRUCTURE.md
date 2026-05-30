# fclean v0.5.0 — 项目结构

```
fclean/
├── pyproject.toml              # 项目元数据、依赖、版本号
├── Dockerfile                  # Docker 容器化配置
├── .dockerignore               # Docker 构建忽略
├── .pre-commit-hooks.yaml      # Pre-commit hook 定义
├── CHANGELOG.md                # 版本变更日志
├── README.md                   # 项目文档（中英双语）
├── CONTRIBUTING.md             # 贡献指南
├── LICENSE                     # MIT 许可证
├── .github/workflows/
│   ├── ci.yml                  # CI: 测试 + Ruff + Docker 构建
│   └── publish.yml             # PyPI 发布 (tag push → OIDC)
├── src/fclean/
│   ├── __init__.py             # 版本号 (__version__)
│   ├── __main__.py             # python -m fclean 入口
│   ├── cli.py                  # CLI 主入口 (argparse)
│   ├── config.py               # .fcleanrc 配置系统
│   ├── dupes.py                # 重复文件检测 (SHA-256)
│   ├── ignore.py               # .fcleanignore 解析器
│   ├── organizer.py            # 文件整理核心逻辑
│   ├── renamer.py              # 批量重命名
│   ├── rules.py                # 文件分类规则 (100+ 扩展名)
│   ├── undo.py                 # 操作回滚系统
│   └── watcher.py              # watchdog 文件监控
└── tests/
    ├── test_cli.py             # CLI 参数测试
    ├── test_config.py          # 配置系统测试
    ├── test_dupes.py           # 重复文件检测测试
    ├── test_edge_cases.py      # 边界情况测试
    ├── test_ignore.py          # .fcleanignore 测试
    ├── test_organizer.py       # 文件整理测试
    ├── test_renamer.py         # 批量重命名测试
    ├── test_rules.py           # 分类规则测试
    ├── test_undo.py            # 回滚系统测试
    └── test_watcher.py         # 文件监控测试
```
