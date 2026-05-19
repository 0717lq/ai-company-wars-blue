# 核心代码说明

## cli.py

| 函数 | 说明 |
|------|------|
| `build_parser()` | 构建 argparse 参数解析器，支持 5 个子命令 |
| `main()` | CLI 主入口，分派到各子命令处理函数 |
| `_run_organize(args)` | 执行文件整理（dry-run 或 execute） |
| `_run_init(args)` | 生成 .fcleanrc 配置文件 |
| `_run_stats(args)` | 目录文件统计（rich 表格 + 条形图） |
| `_run_config(args)` | 查看当前加载的配置 |
| `_run_rename(args)` | 批量重命名（dry-run 预览或 execute 执行） |
| `_print_dry_run(result)` | rich 彩色 dry-run 预览表格 |
| `_print_execute_result(result)` | 执行结果统计（按类别分组） |
| `_print_rename_preview(plan, pairs)` | 重命名预览（新旧文件名对照表） |
| `_print_rename_result(count)` | 重命名执行结果 |
| `_format_size(bytes)` | 将字节格式化为人类可读 |

## config.py

| 类/函数 | 说明 |
|---------|------|
| `Config` | 配置对象，封装 rules/exclude_patterns/exclude_dirs |
| `Config.classify(filename)` | 根据配置规则返回类别名 |
| `load_config(path)` | 自动检测并加载配置（优先级：CLI > 文件 > 默认） |
| `find_config_file(start_dir)` | 搜索 .fcleanrc（当前目录 → home） |
| `generate_example_config()` | 生成示例配置文件内容 |

## organizer.py

| 类/函数 | 说明 |
|---------|------|
| `FileInfo` | 文件信息，含分类结果和目标目录名 |
| `OrganizeResult` | 整理结果容器（files_moved, errors 等） |
| `scan_directory(target, exclude, config)` | 扫描目录（一级文件，排除隐藏和排除模式） |
| `organize(target_path, dry_run, execute)` | 核心整理函数 |
| `compute_stats(target_path, config)` | 按类别统计文件数量和大小 |
| `_safe_move(fi, dst_dir, result)` | 安全移动，自动处理重名冲突 |

## renamer.py (新增 v0.3.0)

| 类/函数 | 说明 |
|---------|------|
| `RenameItem` | 单个重命名项（旧路径 → 新路径） |
| `RenamePlan` | 重命名计划（匹配列表 + 执行 + undo 兼容） |
| `generate_rename_plan(directory, glob, template)` | 生成重命名计划 |
| `_resolve_template(template, index, file_path)` | 解析模板变量 `{n}`, `{date}`, `{ext}` |
| `_ensure_unique_path(target_dir, name)` | 确保目标路径唯一（冲突 + 数字后缀） |
| `_match_glob_pattern(directory, pattern)` | 使用 Path.glob 匹配文件 |

## rules.py

| 函数 | 说明 |
|------|------|
| `classify(filename, config)` | 根据扩展名返回类别 key |
| `get_dir_name(category_key, config)` | 类别 key → 中文目录名 |
| `get_all_categories(config)` | 返回完整类别列表（含自定义） |

## undo.py

| 函数 | 说明 |
|------|------|
| `record_operation(result)` | 记录操作到 ~/.fclean/undo/ |
| `undo_last()` | 回滚最近一次操作 |
| `list_undo_logs()` | 列出所有可用回滚记录 |
