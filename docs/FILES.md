# fclean v0.5.0 — 文件功能说明

## `src/fclean/__init__.py`
包初始化文件，定义 `__version__ = "0.5.0"`。

## `src/fclean/__main__.py`
允许 `python -m fclean` 运行。

## `src/fclean/cli.py`
CLI 主入口（argparse 架构）。注册所有子命令：organize、stats、config、rename、dupes、watch、init、undo、history。所有命令支持 `--json` 输出。支持 shell 补全安装（bash/zsh/fish）。

## `src/fclean/config.py`
.fcleanrc YAML 配置系统。Config 数据类、load_config() 加载函数、DEFAULT_CONFIG 默认值。支持自定义分类规则和排除模式。优先级：CLI 参数 > .fcleanrc > 默认。

## `src/fclean/dupes.py`
重复文件检测。SHA-256 逐块哈希、size 预过滤、多线程并行（ThreadPoolExecutor）。支持 --min-size、--delete、--strategy newest|oldest|path。Undo 集成。

## `src/fclean/ignore.py`
.fleanignore 解析器。IgnoreRules 类支持 glob 模式（*、**、?）、! 取反、目录模式（/ 结尾）、路径模式（含 /）。load_ignore_rules() 加载函数。

## `src/fclean/organizer.py`
文件整理核心逻辑。organize() 函数扫描目录、按规则分类移动文件。OrganizeResult 数据类记录结果。dry-run/execute 双模式。自动重名处理。

## `src/fclean/renamer.py`
批量重命名。RenamePlan 类、generate_rename_plan() 函数。模板变量：{n}（序列号）、{n:03d}（补零）、{date}（日期）、{ext}（扩展名）。冲突自动处理。Undo 集成。

## `src/fclean/rules.py`
文件分类规则。classify() 根据扩展名分类、get_dir_name() 获取目标目录名。7 大类 100+ 扩展名。支持配置驱动自定义规则。

## `src/fclean/undo.py`
操作回滚系统。UndoManager 管理 JSON 日志。record_operation() 记录、undo_last() 回滚、list_undo_logs() 列出历史。

## `src/fclean/watcher.py`
文件监控模块（watchdog）。watch_directory() 启动监听。FcleanHandler 处理 FileCreatedEvent。防抖机制（默认 2 秒）。.fcleanignore 集成。--auto 模式自动执行。
