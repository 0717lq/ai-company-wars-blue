# fclean 核心代码说明

## cli.py

| 函数 | 作用 |
|------|------|
| `build_parser()` | 构建 argparse 参数解析器 |
| `main()` | CLI 主入口，路由到子命令 |
| `_run_organize(args, config)` | 执行 organize 操作 |
| `_run_init(args)` | 生成 .fcleanrc 配置文件 |
| `_run_stats(args)` | 显示目录统计信息 |
| `_run_config(args)` | 查看当前配置 |
| `_print_dry_run(result)` | 打印 dry-run 预览表格 |
| `_print_execute_result(result)` | 打印执行结果 |
| `_print_undo_result(result)` | 打印回滚结果 |
| `_print_undo_history(logs)` | 打印 undo 历史 |
| `_format_size(size_bytes)` | 字节格式化 |

## config.py

| 函数/类 | 作用 |
|---------|------|
| `Config` | 配置对象，封装 rules/exclude_patterns/exclude_dirs |
| `Config.classify(filename)` | 按配置规则分类文件 |
| `Config.rules` | {类别名: {扩展名集合}} 映射 |
| `load_config(path)` | 加载配置（自动检测 .fcleanrc） |
| `find_config_file(start_dir)` | 查找 .fcleanrc 文件 |
| `generate_example_config()` | 生成带注释的示例配置文件 |
| `get_default_config()` | 获取默认配置 |

## organizer.py

| 函数/类 | 作用 |
|---------|------|
| `FileInfo` | 文件信息对象（路径、名称、大小、类别） |
| `OrganizeResult` | 整理结果（统计、错误记录） |
| `scan_directory()` | 扫描目录，返回 FileInfo 列表 |
| `organize()` | 执行整理（dry-run 或 execute） |
| `compute_stats()` | 计算文件统计信息 |
| `_safe_move()` | 安全移动文件（不覆盖，自动重名） |
| `_should_exclude()` | 判断文件/目录是否应排除 |

## rules.py

| 函数 | 作用 |
|------|------|
| `classify(filename, config)` | 按扩展名分类文件 |
| `get_dir_name(category_key, config)` | 类别 key → 中文目录名 |
| `get_all_categories(config)` | 返回所有类别定义 |

## undo.py

| 函数 | 作用 |
|------|------|
| `record_operation(result)` | 记录操作到 JSON 日志 |
| `undo_last()` | 回滚最近一次操作 |
| `list_undo_logs()` | 列出所有 undo 日志 |
