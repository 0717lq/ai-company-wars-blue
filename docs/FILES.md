# fclean v0.6.0 — 文件功能说明

## 源文件 (src/fclean/)

| 文件 | 行数 | 功能 |
|------|------|------|
| `__init__.py` | 6 | 版本号定义 (`__version__ = "0.6.0"`) |
| `__main__.py` | 5 | `python -m fclean` 入口 |
| `cli.py` | 447 | 参数解析 (argparse) + main() 入口 + shell 补全安装 |
| `commands.py` | 689 | 所有子命令执行逻辑 (run_organize/stats/rename/dupes/watch/plugin) |
| `formatters.py` | 380 | JSON 序列化 + Rich/纯文本显示函数 |
| `config.py` | 294 | YAML 配置系统 (.fcleanrc 加载/合并/验证) |
| `dupes.py` | 489 | 重复文件检测 (SHA-256 + 多线程 + size 预过滤) |
| `ignore.py` | 142 | .fcleanignore 规则引擎 (glob + 取反 + 目录模式) |
| `organizer.py` | 356 | 核心整理逻辑 (扫描/分类/移动) |
| `plugin.py` | 84 | 插件基类 PluginBase (classify/transform/summarize hooks) |
| `plugin_manager.py` | 275 | 插件管理器 (加载/注册/执行/安装/卸载) |
| `renamer.py` | 228 | 批量重命名 (glob + 模板变量 + 冲突处理) |
| `rules.py` | 168 | 文件分类规则 (扩展名→类别映射) |
| `stats_viz.py` | 241 | ASCII 图表可视化 (饼图/柱状图/Top-N) |
| `undo.py` | 167 | 回滚系统 (JSON 日志记录 + 反向移动) |
| `watcher.py` | 125 | watchdog 文件监控 (防抖 + 忽略规则集成) |

**源文件总计**: 16 个文件, 4151 行

## 测试文件 (tests/)

| 文件 | 测试数 | 覆盖模块 |
|------|--------|----------|
| `test_cli.py` | ~30 | CLI 参数解析、版本输出、帮助信息 |
| `test_config.py` | ~20 | 配置加载、默认值、自定义规则 |
| `test_organizer.py` | ~25 | 文件扫描、分类、移动逻辑 |
| `test_renamer.py` | ~33 | 模板变量、glob 匹配、冲突处理 |
| `test_dupes.py` | ~25 | SHA-256 哈希、重复检测、删除策略 |
| `test_ignore.py` | ~25 | .fcleanignore 解析 (glob/取反/目录) |
| `test_watcher.py` | ~9 | watchdog 事件处理、防抖、忽略规则 |
| `test_stats_viz.py` | ~23 | 饼图、柱状图、Top-N、边界条件 |
| `test_plugin.py` | 35 | 插件基类、管理器、hook 执行、模板生成 |
| `test_edge_cases.py` | ~19 | 空目录、权限错误、Unicode 文件名 |
| `test_undo.py` | ~8 | 记录、回滚、历史查询 |
| `test_rules.py` | ~12 | 分类规则匹配、优先级 |

**测试总计**: 273 个测试, 13 个文件
