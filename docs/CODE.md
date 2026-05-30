# fclean v0.5.0 — 核心代码概览

## cli.py — CLI 主入口
- `build_parser()` — argparse 解析器，注册所有子命令
- `main()` — 入口函数
- `_run_organize()` — organize 子命令逻辑
- `_run_stats()` — stats 子命令逻辑
- `_run_rename()` — rename 子命令逻辑
- `_run_dupes()` — dupes 子命令逻辑
- `_run_watch()` — watch 子命令逻辑
- JSON 输出：所有子命令支持 `--json` 参数

## config.py — 配置系统
- `Config` — 配置数据类
- `load_config()` — 加载 .fcleanrc 配置
- `DEFAULT_CONFIG` — 默认配置字典

## dupes.py — 重复文件检测
- `find_duplicates()` — 核心查找函数（size 预过滤 → SHA-256 哈希）
- `DupesResult` — 检测结果数据类
- `delete_duplicates()` — 安全删除（支持 newest/oldest/path 策略）
- 多线程并行哈希（ThreadPoolExecutor, max 4 workers）

## ignore.py — .fcleanignore 解析器
- `IgnoreRules` — 规则集合类（正向匹配 + ! 取反）
- `load_ignore_rules()` — 加载 .fcleanignore 文件
- 支持 glob、目录模式、路径模式
- `filter_files()` — 过滤文件列表

## organizer.py — 文件整理
- `organize()` — 核心整理函数
- `OrganizeResult` — 整理结果数据类
- dry-run/execute 双模式，自动重名处理

## renamer.py — 批量重命名
- `RenamePlan` — 重命名计划类
- `generate_rename_plan()` — 生成重命名方案
- 模板变量：{n}, {n:03d}, {date}, {ext}
- 冲突自动处理（数字后缀）

## rules.py — 文件分类规则
- `classify()` — 根据扩展名分类
- `get_dir_name()` — 获取目标目录名
- 7 大类 100+ 扩展名

## undo.py — 操作回滚
- `UndoManager` — 回滚管理器
- `record_operation()` — 记录操作到 JSON 日志
- `undo_last()` — 回滚最近操作
- `list_undo_logs()` — 列出所有历史操作

## watcher.py — 文件监控
- `watch_directory()` — 启动文件监控
- watchdog Observer + FcleanHandler（继承 FileSystemEventHandler）
- 防抖机制（默认 2 秒 debounce）
- .fcleanignore 集成
- --auto 模式自动执行（默认 dry-run）
