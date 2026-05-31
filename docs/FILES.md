# fclean v0.5.0 — 文件功能说明

## 源码文件（src/fclean/）

| 文件 | 行数 | 功能 |
|------|------|------|
| `__init__.py` | 7 | 包初始化，定义 `__version__ = "0.5.0"` |
| `__main__.py` | 5 | `python -m fclean` 入口 |
| `cli.py` | ~1300 | CLI 命令行入口，argparse 参数解析，子命令路由，JSON 输出封装 |
| `config.py` | ~200 | 配置系统：加载 .fcleanrc YAML，合并默认规则，支持全局/本地配置 |
| `dupes.py` | ~200 | 重复文件检测：SHA-256 哈希，size 预过滤，多线程，删除+undo |
| `ignore.py` | 142 | .fcleanignore 解析器：glob 模式、取反、目录模式、路径模式 |
| `organizer.py` | ~250 | 核心整理逻辑：扫描文件、分类、移动/预览、统计 |
| `renamer.py` | ~200 | 批量重命名：glob 匹配、模板变量（{n}, {date}, {ext}）、冲突处理 |
| `rules.py` | ~100 | 分类规则：扩展名→类别映射，7 大类（图片/文档/视频/音频/压缩包/代码/其他） |
| `stats_viz.py` | ~210 | 统计可视化：ASCII 饼图、柱状图、Top-N 大文件排行 |
| `undo.py` | ~150 | Undo 系统：JSON 日志记录、回滚、历史查看 |
| `watcher.py` | 125 | 文件监控：watchdog 事件处理、防抖、.fcleanignore 集成 |

## 测试文件（tests/）

| 文件 | 测试数 | 覆盖模块 |
|------|--------|----------|
| `test_cli.py` | ~20 | CLI 参数解析、--chart/--top/--json |
| `test_config.py` | ~15 | 配置加载、合并、验证 |
| `test_dupes.py` | ~15 | 重复文件检测、删除策略 |
| `test_edge_cases.py` | ~18 | 边界条件、Unicode、空目录 |
| `test_ignore.py` | 25 | .fcleanignore 全规则覆盖 |
| `test_organizer.py` | ~20 | 文件整理核心逻辑 |
| `test_renamer.py` | ~20 | 批量重命名、模板、冲突 |
| `test_rules.py` | ~15 | 分类规则、扩展名映射 |
| `test_stats_viz.py` | 23 | 饼图、柱状图、Top-N、边界 |
| `test_undo.py` | ~10 | Undo 记录、回滚、历史 |
| `test_watcher.py` | 9 | 文件监控、防抖、忽略规则 |

**总计**: 238 个测试

## 基础设施文件

| 文件 | 功能 |
|------|------|
| `pyproject.toml` | 项目元数据、依赖、构建配置 |
| `Dockerfile` | Docker 容器化（python:3.12-slim） |
| `.pre-commit-hooks.yaml` | Pre-commit hook 定义（dry-run 安全） |
| `.github/workflows/ci.yml` | CI 流水线 |
| `.github/workflows/publish.yml` | PyPI 自动发布 |
