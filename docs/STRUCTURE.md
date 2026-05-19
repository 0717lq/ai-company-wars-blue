# 项目结构

```
project/
├── src/fclean/
│   ├── __init__.py           # v0.3.0 — 包信息
│   ├── __main__.py           # 入口点
│   ├── cli.py                # CLI 参数解析和命令分发
│   ├── config.py             # .fcleanrc 配置系统
│   ├── organizer.py          # 文件整理核心
│   ├── renamer.py            # 批量重命名（新增 v0.3.0）
│   ├── rules.py              # 文件分类规则
│   └── undo.py               # 回滚系统
├── tests/
│   ├── __init__.py
│   ├── test_cli.py           # CLI 参数测试
│   ├── test_config.py        # 配置系统测试
│   ├── test_edge_cases.py    # 边界情况测试（新增 v0.3.0）
│   ├── test_organizer.py     # 整理功能测试
│   ├── test_renamer.py       # 重命名测试（新增 v0.3.0）
│   ├── test_rules.py         # 分类规则测试
│   └── test_undo.py          # 回滚测试
├── docs/
│   ├── CODE.md               # 核心代码说明
│   ├── FILES.md              # 文件功能
│   └── STRUCTURE.md          # 项目结构
├── .github/workflows/
│   └── ci.yml                # GitHub Actions CI
├── CONTRIBUTING.md           # 贡献指南
├── README.md                 # 中英双语 README
├── CHANGELOG.md              # 版本更新日志
├── LICENSE                   # MIT 许可证
├── pyproject.toml            # 项目配置
└── .fcleanrc.example         # 配置示例
```
