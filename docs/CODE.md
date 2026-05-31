# fclean v0.5.0 — 核心代码文档

## cli.py — CLI 命令行入口

### 核心函数

| 函数 | 功能 |
|------|------|
| `build_parser()` | 构建 argparse 解析器，定义所有子命令和选项 |
| `main()` | CLI 主入口，路由到子命令处理函数 |
| `_run_organize(args)` | 处理 organize 子命令（默认 dry-run） |
| `_run_stats(args)` | 处理 stats 子命令，支持 --chart/--top/--json |
| `_run_init(args)` | 处理 init 子命令，生成 .fcleanrc |
| `_run_config(args)` | 处理 config 子命令，显示当前配置 |
| `_run_rename(args)` | 处理 rename 子命令，批量重命名 |
| `_run_dupes(args)` | 处理 dupes 子命令，重复文件检测 |
| `_run_watch(args)` | 处理 watch 子命令，文件监控 |
| `_install_completion()` | 安装 shell 自动补全（bash/zsh/fish） |

### JSON 输出函数

| 函数 | 输出 |
|------|------|
| `_make_json_envelope(cmd, data)` | 统一 JSON 包装（tool + timestamp） |
| `_organize_to_json(result)` | organize 结果 JSON |
| `_stats_to_json(stats, path, top_files)` | stats 结果 JSON（含 top files） |
| `_rename_to_json(plan, pairs)` | rename 结果 JSON |
| `_undo_to_json(result)` | undo 结果 JSON |
| `_history_to_json(logs)` | history 结果 JSON |

### 参数一览

| 参数 | 类型 | 说明 |
|------|------|------|
| `command` | str? | 子命令名或路径 |
| `arg` | str? | 子命令的参数 |
| `--json/-j` | flag | JSON 输出 |
| `--execute` | flag | 执行（默认 dry-run） |
| `--undo` | flag | 回滚 |
| `--history` | flag | 查看历史 |
| `--chart` | flag | stats ASCII 图表 |
| `--top N` | int? | stats Top-N 大文件 |
| `--pattern/-p` | str? | rename 模板 |
| `--delete` | flag | dupes 删除 |
| `--min-size` | str? | dupes 最小文件大小 |
| `--auto` | flag | watch 自动执行 |

---

## stats_viz.py — 统计可视化

### 核心函数

| 函数 | 功能 |
|------|------|
| `render_pie_chart(stats, width=40)` | 渲染 ASCII 饼图（双维度：数量+大小） |
| `render_bar_chart(stats, width=40)` | 渲染 ASCII 垂直柱状图 |
| `find_top_files(target_path, n=10)` | 查找 Top-N 大文件（递归扫描） |
| `render_top_files(files, width=60)` | 渲染大文件排行列表 |

### 数据结构

```python
# find_top_files 返回值
[
    {
        "path": "/absolute/path/to/file.bin",
        "name": "file.bin",
        "size": 102400,           # 字节
        "size_human": "100.0KB",  # 人类可读
    },
    ...
]
```

---

## organizer.py — 核心整理逻辑

### 核心类

| 类 | 功能 |
|------|------|
| `FileInfo` | 文件信息（path, name, size, category_key, target_dir_name） |
| `OrganizeResult` | 整理结果（files_moved, files_skipped, errors） |

### 核心函数

| 函数 | 功能 |
|------|------|
| `organize(target_path, ...)` | 执行文件整理（dry-run 或 execute） |
| `compute_stats(target_path, config)` | 计算目录统计信息 |

---

## config.py — 配置系统

| 函数 | 功能 |
|------|------|
| `load_config(target=None)` | 加载并合并配置（本地 > 全局 > 默认） |
| `generate_example_config()` | 生成示例 .fcleanrc 内容 |
| `Config` | 配置数据类（rules, exclude_patterns, exclude_dirs） |

---

## dupes.py — 重复文件检测

| 函数 | 功能 |
|------|------|
| `find_duplicates(target_path, ...)` | 查找重复文件（size→hash 两遍扫描） |
| `DupesResult` | 结果类（has_duplicates, delete, to_dict, print_table） |

---

## ignore.py — .fcleanignore

| 函数 | 功能 |
|------|------|
| `load_ignore_rules(directory)` | 从目录加载 .fcleanignore 规则 |
| `IgnoreRules` | 规则类（matches, filter_files, has_rules） |

---

## renamer.py — 批量重命名

| 函数 | 功能 |
|------|------|
| `generate_rename_plan(target_dir, glob_pattern, template)` | 生成重命名计划 |
| `RenamePlan` | 计划类（get_rename_pairs, execute, pattern, format_template） |

---

## undo.py — Undo 回滚

| 函数 | 功能 |
|------|------|
| `record_operation(result)` | 记录整理操作到 JSON 日志 |
| `undo_last()` | 回滚上一次操作 |
| `list_undo_logs()` | 列出所有 undo 日志 |

---

## watcher.py — 文件监控

| 函数 | 功能 |
|------|------|
| `watch_directory(target_path, ...)` | 启动文件监控（watchdog） |
| `FcleanHandler` | 事件处理器（防抖、忽略规则、触发 organize） |
