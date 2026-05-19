# 文件功能说明

## src/fclean/ — 源代码

| 文件 | 功能 |
|------|------|
| `__init__.py` | 包初始化，版本号 `0.3.0` |
| `__main__.py` | `python -m fclean` 入口 |
| `cli.py` | 命令行入口，argparse 解析参数，支持子命令：init, stats, config, organize, rename |
| `config.py` | `.fcleanrc` YAML 配置系统，支持自动检测、加载、合并默认配置 |
| `organizer.py` | 文件整理核心，扫描目录、分类、安全移动、统计 |
| `renamer.py` | 批量重命名模块，glob 匹配 + 模板变量解析 + 防冲突 |
| `rules.py` | 文件分类规则定义，7 大类 100+ 扩展名映射 |
| `undo.py` | 回滚系统，记录操作日志到 `~/.fclean/undo/` |

## tests/ — 测试用例

| 文件 | 功能 | 用例数 |
|------|------|--------|
| `test_cli.py` | CLI 参数解析测试 | 19 |
| `test_config.py` | 配置加载、合并、分类测试 | 14 |
| `test_edge_cases.py` | 空目录/权限/Unicode/冲突等边界测试 | 18 |
| `test_organizer.py` | 整理功能测试（dry-run, execute, 排除模式） | 21 |
| `test_renamer.py` | 重命名功能测试（模板、执行、冲突） | 18 |
| `test_rules.py` | 分类规则测试（扩展名匹配、大小写） | 19 |
| `test_undo.py` | 回滚日志记录、执行、列出测试 | 8 |

## docs/ — 文档

| 文件 | 说明 |
|------|------|
| `STRUCTURE.md` | 项目目录结构 |
| `FILES.md` | 各文件功能说明 |
| `CODE.md` | 核心类和函数说明 |
