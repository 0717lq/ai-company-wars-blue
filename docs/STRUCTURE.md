# fclean 项目结构

```
project/
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI（3 版本 Python 矩阵）
├── .fcleanrc.example                 # 示例配置文件
├── CHANGELOG.md                      # 变更日志
├── LICENSE                           # MIT 许可证
├── README.md                         # 项目说明
├── pyproject.toml                    # 项目配置（依赖、工具配置）
├── src/
│   └── fclean/
│       ├── __init__.py               # 版本声明
│       ├── __main__.py               # python -m 入口
│       ├── cli.py                    # 命令行入口（子命令架构）
│       ├── config.py                 # .fcleanrc 配置系统
│       ├── organizer.py              # 核心整理模块
│       ├── rules.py                  # 分类规则定义
│       └── undo.py                   # 回滚模块
└── tests/
    ├── __init__.py
    ├── test_cli.py                   # CLI 参数解析测试
    ├── test_config.py                # 配置加载/合并测试
    ├── test_organizer.py             # 整理模块测试
    ├── test_rules.py                 # 分类规则测试
    └── test_undo.py                  # 回滚功能测试
```
