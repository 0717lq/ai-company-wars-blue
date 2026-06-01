# fclean v0.6.0 — 项目结构

```
fclean/
├── pyproject.toml              # 项目配置 + 依赖 + Ruff 7套规则
├── CHANGELOG.md                # 版本记录
├── README.md                   # 中英双语文档
├── CONTRIBUTING.md             # 贡献指南
├── Dockerfile                  # 容器化 (python:3.12-slim)
├── .dockerignore
├── .pre-commit-hooks.yaml      # Pre-commit hook
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI: ruff + pytest + Docker build
│       └── publish.yml         # PyPI 发布 (OIDC Trusted Publisher)
├── src/
│   └── fclean/
│       ├── __init__.py         # 版本号 (__version__ = "0.6.0")
│       ├── __main__.py         # python -m fclean 入口
│       ├── cli.py              # 参数解析 + main() 入口 (~280行)
│       ├── commands.py         # 子命令执行逻辑 (~550行)
│       ├── formatters.py       # JSON/Rich/纯文本输出 (~310行)
│       ├── config.py           # YAML 配置系统
│       ├── rules.py            # 文件分类规则
│       ├── organizer.py        # 核心整理逻辑
│       ├── renamer.py          # 批量重命名
│       ├── dupes.py            # 重复文件检测
│       ├── undo.py             # 回滚系统
│       ├── ignore.py           # .fcleanignore 规则引擎
│       ├── watcher.py          # watchdog 文件监控
│       ├── stats_viz.py        # ASCII 图表可视化
│       ├── plugin.py           # 插件基类 (PluginBase)
│       └── plugin_manager.py   # 插件管理器 (PluginManager)
├── tests/
│   ├── __init__.py
│   ├── test_cli.py             # CLI 参数测试
│   ├── test_config.py          # 配置加载测试
│   ├── test_organizer.py       # 整理逻辑测试
│   ├── test_renamer.py         # 重命名测试
│   ├── test_dupes.py           # 重复文件测试
│   ├── test_ignore.py          # 忽略规则测试
│   ├── test_watcher.py         # 监控测试
│   ├── test_stats_viz.py       # 可视化测试
│   ├── test_plugin.py          # 插件系统测试 (35个)
│   ├── test_edge_cases.py      # 边界情况测试
│   ├── test_undo.py            # 回滚测试
│   └── test_rules.py           # 规则引擎测试
└── docs/
    ├── STRUCTURE.md            # 本文件
    ├── FILES.md                # 文件功能说明
    └── CODE.md                 # 核心代码文档
```

## 源文件统计

- 源文件: 16 个 .py
- 测试文件: 13 个 .py
- 总测试: 273 个
- 子命令: 8 个 (init, stats, config, organize, rename, dupes, watch, plugin)
