"""命令执行逻辑 — 所有 _run_* 函数集中在此。

从 cli.py 拆分出的子命令执行逻辑。
"""

import sys
from pathlib import Path
from typing import Optional

from fclean.config import Config, generate_example_config, load_config
from fclean.dupes import find_duplicates
from fclean.formatters import (
    format_size,
    print_dry_run,
    print_execute_result,
    print_json,
    print_rename_preview,
    print_rename_result,
    rename_to_json,
    stats_to_json,
)
from fclean.ignore import load_ignore_rules
from fclean.organizer import compute_stats, organize
from fclean.renamer import generate_rename_plan
from fclean.undo import record_operation

# 所有已知子命令名称
KNOWN_SUBCOMMANDS = {
    "init", "stats", "config", "organize", "rename", "dupes", "watch", "plugin",
}


def _resolve_target(args, require_path: bool = False) -> str:
    """从 args 中解析目标路径。"""
    target = args.arg or args.command
    if target in KNOWN_SUBCOMMANDS or target is None:
        if require_path:
            print("❌ 请指定目录路径", file=sys.stderr)
            sys.exit(1)
        target = "."
    return str(Path(target).expanduser().resolve())


def run_organize(args, config: Optional[Config] = None):
    """执行 organize 操作（默认路径或子命令模式）。"""
    target = args.command or args.arg or "."
    if target in KNOWN_SUBCOMMANDS:
        target = args.arg or "."

    target_path = str(Path(target).expanduser().resolve())

    if not Path(target_path).exists():
        print(f"❌ 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not Path(target_path).is_dir():
        print(f"❌ 不是目录: {target}", file=sys.stderr)
        sys.exit(1)

    if config is None:
        config = load_config(target_path)

    # 加载 .fcleanignore 规则，合并到 exclude 列表
    ignore = load_ignore_rules(target_path)
    extra_exclude = list(ignore._patterns) if ignore.has_rules else None
    effective_exclude = (args.exclude or []) + (extra_exclude or [])
    if not effective_exclude:
        effective_exclude = None

    try:
        result = organize(
            target_path=target_path,
            dry_run=(not args.execute),
            execute=args.execute,
            exclude=effective_exclude,
            exclude_dirs=args.exclude_dirs or None,
            config=config,
        )
        result.scan_path = target_path
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)

    if args.execute:
        print_execute_result(result, json_output=args.json)
        if result.total_moved > 0:
            try:
                record_operation(result)
            except ValueError:
                pass
    else:
        print_dry_run(result, json_output=args.json)

    if result.total_errors > 0:
        sys.exit(1)


def run_init(args):
    """执行 fclean init 命令。"""
    if args.global_config:
        target_dir = Path.home()
    else:
        dir_arg = None
        if args.arg and args.arg not in KNOWN_SUBCOMMANDS:
            dir_arg = args.arg
        elif args.command and args.command not in KNOWN_SUBCOMMANDS:
            dir_arg = args.command
        target_dir = Path(dir_arg).expanduser().resolve() if dir_arg else Path.cwd()

    config_path = target_dir / ".fcleanrc"

    if config_path.exists():
        print(f"⚠️  {config_path} 已存在。使用 --force 覆盖。")
        sys.exit(1)

    content = generate_example_config()
    config_path.write_text(content, encoding="utf-8")
    print(f"✅ 已生成配置文件: {config_path}")
    print(f"编辑 {config_path} 自定义分类规则后，运行 fclean <path> 即可使用新规则。")


def run_stats(args):
    """执行 fclean stats 命令。"""
    if args.arg and args.arg not in KNOWN_SUBCOMMANDS:
        target = args.arg
    elif args.command and args.command not in KNOWN_SUBCOMMANDS:
        target = args.command
    else:
        print("❌ 请指定目录路径: fclean stats <path>", file=sys.stderr)
        sys.exit(1)

    target_path = str(Path(target).expanduser().resolve())

    if not Path(target_path).exists():
        print(f"❌ 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not Path(target_path).is_dir():
        print(f"❌ 不是目录: {target}", file=sys.stderr)
        sys.exit(1)

    config = load_config(target_path)

    try:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich.table import Table
        from rich.text import Text
        has_rich = True
    except ImportError:
        has_rich = False

    try:
        if has_rich:
            console = Console()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("扫描中...", total=None)
                stats = compute_stats(target_path, config)
        else:
            print("扫描中...")
            stats = compute_stats(target_path, config)
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)

    # 处理 --top N
    top_files_data = None
    if args.top is not None and args.top > 0:
        from fclean.stats_viz import find_top_files
        top_files_data = find_top_files(target_path, args.top)

    # JSON 输出（忽略 --chart）
    if args.json:
        top_json = None
        if top_files_data:
            top_json = [
                {"path": f["path"], "name": f["name"],
                 "size_bytes": f["size"], "size_human": f["size_human"]}
                for f in top_files_data
            ]
        print_json(stats_to_json(stats, target_path, top_files=top_json))
        return

    # 基础统计表格
    if has_rich:
        console = Console()
        console.print()
        console.print(Text(f"📊 fclean stats — {target_path}", style="bold cyan"))
        console.print(Text(f"文件总数: {stats['total_files']}  |  "
                           f"总大小: {format_size(stats['total_size'])}",
                           style="yellow"))
        console.print()

        if stats["total_files"] == 0:
            console.print(Text("该目录为空。", style="dim"))
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("类别", style="cyan")
        table.add_column("文件数", justify="right", style="white")
        table.add_column("大小", justify="right", style="green")
        table.add_column("占比", justify="right", style="blue")

        cats = stats["categories"]
        for cat_name in sorted(cats.keys()):
            data = cats[cat_name]
            pct = data["count"] / stats["total_files"] * 100 if stats["total_files"] > 0 else 0
            bar_chars = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            table.add_row(
                cat_name,
                str(data["count"]),
                format_size(data["size"]),
                f"{pct:.1f}% {bar_chars}",
            )

        table.add_row(
            "合计",
            str(stats["total_files"]),
            format_size(stats["total_size"]),
            "100%",
            style="bold",
        )

        console.print(table)
        console.print()
    else:
        print(f"\n📊 fclean stats — {target_path}")
        print(f"文件总数: {stats['total_files']}  |  总大小: {format_size(stats['total_size'])}")
        print()

        if stats["total_files"] == 0:
            print("该目录为空。")
            return

        cats = stats["categories"]
        for cat_name in sorted(cats.keys()):
            data = cats[cat_name]
            print(f"  {cat_name}: {data['count']} 个文件 ({format_size(data['size'])})")
        print()

    # --chart
    if args.chart:
        from fclean.stats_viz import render_bar_chart, render_pie_chart
        pie = render_pie_chart(stats)
        bar = render_bar_chart(stats)
        print(pie)
        print()
        print(bar)
        print()

    # --top N
    if top_files_data:
        from fclean.stats_viz import render_top_files
        print(render_top_files(top_files_data))
        print()


def run_config(args):
    """执行 fclean config 命令。"""
    target = None
    if args.arg and args.arg not in KNOWN_SUBCOMMANDS:
        target = args.arg
    elif args.command and args.command not in KNOWN_SUBCOMMANDS:
        target = args.command

    config = load_config(target)

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        has_rich = True
    except ImportError:
        has_rich = False

    if has_rich:
        console = Console()
        console.print()
        console.print(Text("⚙️  fclean 当前配置", style="bold cyan"))
        console.print()

        config_data = config.to_dict()

        rules_table = Table(title="文件分类规则", show_header=True, header_style="bold magenta")
        rules_table.add_column("类别", style="cyan")
        rules_table.add_column("扩展名", style="white")

        for rule in config_data["rules"]:
            exts = ", ".join(rule["extensions"])
            rules_table.add_row(rule["category"], exts)

        console.print(rules_table)
        console.print()

        ep = config_data['exclude_patterns']
        ed = config_data['exclude_dirs']
        patterns_txt = ', '.join(ep) if ep else '无'
        dirs_txt = ', '.join(ed) if ed else '无'
        exclude_text = f"排除模式: {patterns_txt}\n排除目录: {dirs_txt}"
        console.print(Panel(exclude_text, title="排除设置"))
        console.print()
    else:
        print("\n⚙️  fclean 当前配置")
        print()
        config_data = config.to_dict()
        print("文件分类规则:")
        for rule in config_data["rules"]:
            exts = ", ".join(rule["extensions"])
            print(f"  {rule['category']}: {exts}")
        print()
        ep = config_data['exclude_patterns']
        ed = config_data['exclude_dirs']
        patterns = ', '.join(ep) if ep else '无'
        dirs = ', '.join(ed) if ed else '无'
        print(f"排除模式: {patterns}")
        print(f"排除目录: {dirs}")


def run_rename(args):
    """执行 fclean rename 子命令。"""
    glob_pattern = args.arg or args.command
    if glob_pattern in KNOWN_SUBCOMMANDS or glob_pattern is None:
        print("❌ 请指定 glob 匹配模式: fclean rename \"*.jpg\" --pattern \"template\"",
              file=sys.stderr)
        sys.exit(1)

    format_template = args.pattern
    if not format_template:
        print("❌ 请指定命名模板: fclean rename \"*.jpg\" --pattern \"vacation_{n:03d}\"",
              file=sys.stderr)
        sys.exit(1)

    target = "."
    if args.command == "rename" and args.arg and args.arg not in KNOWN_SUBCOMMANDS:
        pass
    elif args.command not in KNOWN_SUBCOMMANDS and args.command != "rename":
        target = args.command

    target_dir = Path(target).expanduser().resolve()
    if not target_dir.exists():
        print(f"❌ 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not target_dir.is_dir():
        print(f"❌ 不是目录: {target}", file=sys.stderr)
        sys.exit(1)

    try:
        plan = generate_rename_plan(target_dir, glob_pattern, format_template)
        pairs = plan.get_rename_pairs()
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)

    if args.execute:
        if not pairs:
            print("没有匹配的文件，无需重命名。")
            return

        executed = plan.execute()
        executed_count = len(executed)

        if args.json:
            print_json(rename_to_json(plan, pairs, status="executed",
                                       executed_count=executed_count))

        if executed_count > 0:
            print_rename_result(executed_count, json_output=args.json)
            from fclean.organizer import FileInfo, OrganizeResult
            undo_result = OrganizeResult()
            for item in executed:
                try:
                    fi = FileInfo(item.old_path)
                except (FileNotFoundError, OSError):
                    fi = FileInfo.__new__(FileInfo)
                    fi.path = item.old_path
                    fi.name = item.old_path.name
                    fi.size = 0
                    fi.category_key = None
                    fi.target_dir_name = "rename"
                undo_result.files_moved.append((fi, item.new_path))
            try:
                record_operation(undo_result)
            except ValueError:
                pass
        else:
            print("没有文件被重命名。")

        if executed_count < len(pairs):
            print(f"⚠️  成功 {executed_count}/{len(pairs)} 个文件，部分文件可能因权限问题跳过。",
                  file=sys.stderr)
    else:
        print_rename_preview(plan, pairs, json_output=args.json)


def run_dupes(args):
    """执行 fclean dupes 子命令。"""
    if args.arg and args.arg not in KNOWN_SUBCOMMANDS:
        target = args.arg
    elif args.command and args.command not in KNOWN_SUBCOMMANDS:
        target = args.command
    else:
        target = "."

    target_path = str(Path(target).expanduser().resolve())

    if not Path(target_path).exists():
        print(f"❌ 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not Path(target_path).is_dir():
        print(f"❌ 不是目录: {target}", file=sys.stderr)
        sys.exit(1)

    try:
        result = find_duplicates(
            target_path=target_path,
            min_size=args.min_size,
            show_progress=(not args.no_progress and not args.json),
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)

    if args.delete:
        if not result.has_duplicates:
            if args.json:
                print_json(result.to_dict())
            else:
                print("\n✅ 没有发现重复文件。\n")
            return

        if args.json:
            dupes_data = result.to_dict()
        else:
            result.print_table()

        deleted = result.delete(strategy=args.strategy, interactive=False)

        if args.json:
            dupes_data["action"] = "deleted"
            dupes_data["files_deleted"] = len(deleted)
            dupes_data["errors"] = [
                {"path": p, "error": e} for p, e in result.errors
            ]
            print_json(dupes_data)
        else:
            if deleted:
                print(f"✅ 已删除 {len(deleted)} 个重复文件")
                from fclean.organizer import FileInfo, OrganizeResult
                undo_result = OrganizeResult()
                for keep, _deleted_path in deleted:
                    fi = FileInfo.__new__(FileInfo)
                    fi.path = keep
                    fi.name = keep.name
                    fi.size = keep.stat().st_size if keep.exists() else 0
                    fi.category_key = None
                    fi.target_dir_name = "dupes"
                    undo_result.files_moved.append((fi, keep))
                try:
                    record_operation(undo_result)
                    print("💡 如需回滚: fclean --undo")
                except ValueError:
                    pass
            if result.errors:
                for path, err in result.errors:
                    print(f"  ❌ {path}: {err}")

        if result.errors:
            sys.exit(1)
    else:
        if args.json:
            print_json(result.to_dict())
        else:
            result.print_table()

    if result.errors:
        sys.exit(1)


def run_watch(args):
    """执行 fclean watch 子命令。"""
    from fclean.watcher import watch_directory

    target = args.arg or "."
    if target in KNOWN_SUBCOMMANDS:
        target = "."

    target_path = str(Path(target).expanduser().resolve())

    if not Path(target_path).exists():
        print(f"❌ 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not Path(target_path).is_dir():
        print(f"❌ 不是目录: {target}", file=sys.stderr)
        sys.exit(1)

    config = load_config(target_path)
    ignore = load_ignore_rules(target_path)

    watch_directory(
        target_path=target_path,
        auto_execute=args.auto,
        config=config,
        ignore_rules=ignore,
        json_output=args.json,
    )


def run_plugin(args):
    """执行 fclean plugin 子命令。"""

    from fclean.formatters import make_json_envelope, print_json
    from fclean.plugin_manager import PluginManager

    manager = PluginManager()
    manager.discover_and_load()

    subcmd = args.plugin_action or "list"

    if subcmd == "list":
        plugins = manager.list_plugins()
        if args.json:
            print_json(make_json_envelope("plugin", {
                "action": "list",
                "total": len(plugins),
                "plugins": plugins,
            }))
        else:
            try:
                from rich.console import Console
                from rich.table import Table
                console = Console()
                console.print()
                console.print("[bold cyan]🔌 fclean 插件列表[/]")
                console.print()
                if not plugins:
                    console.print("[dim]未安装插件。使用 'fclean plugin create' 创建插件模板。[/]")
                else:
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("名称", style="cyan")
                    table.add_column("版本")
                    table.add_column("描述")
                    for p in plugins:
                        table.add_row(p["name"], p["version"], p["description"])
                    console.print(table)
                console.print()
            except ImportError:
                print(f"\n🔌 fclean 插件列表 ({len(plugins)} 个)\n")
                if not plugins:
                    print("未安装插件。使用 'fclean plugin create' 创建插件模板。")
                for p in plugins:
                    print(f"  {p['name']} v{p['version']} — {p['description']}")
                print()

    elif subcmd == "info":
        name = args.plugin_name
        if not name:
            print("❌ 请指定插件名: fclean plugin info <name>", file=sys.stderr)
            sys.exit(1)
        info = manager.get_plugin_info(name)
        if info is None:
            print(f"❌ 插件未找到: {name}", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print_json(make_json_envelope("plugin", {
                "action": "info",
                "plugin": info,
            }))
        else:
            print(f"\n🔌 插件: {info['name']} v{info['version']}")
            print(f"   描述: {info['description']}")
            print(f"   Hooks: {', '.join(info['hooks'])}")
            print()

    elif subcmd == "install":
        source = args.plugin_source
        if not source:
            print("❌ 请指定插件文件: fclean plugin install <file.py>", file=sys.stderr)
            sys.exit(1)
        source_path = Path(source).expanduser().resolve()
        try:
            plugin = manager.install_plugin(source_path)
            if args.json:
                print_json(make_json_envelope("plugin", {
                    "action": "install",
                    "status": "success",
                    "plugin": manager.get_plugin_info(plugin.name),
                }))
            else:
                print(f"✅ 已安装插件: {plugin.name} v{plugin.version}")
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

    elif subcmd == "create":
        name = args.plugin_name
        if not name:
            print("❌ 请指定插件名: fclean plugin create <name>", file=sys.stderr)
            sys.exit(1)
        # 生成插件模板
        template = _generate_plugin_template(name)
        dest = manager.plugin_dir / f"{name}.py"
        if dest.exists():
            print(f"⚠️  插件文件已存在: {dest}", file=sys.stderr)
            sys.exit(1)
        manager.plugin_dir.mkdir(parents=True, exist_ok=True)
        dest.write_text(template, encoding="utf-8")
        if args.json:
            print_json(make_json_envelope("plugin", {
                "action": "create",
                "status": "success",
                "path": str(dest),
            }))
        else:
            print(f"✅ 已创建插件模板: {dest}")
            print(f"   编辑 {dest} 实现你的插件逻辑。")

    elif subcmd == "uninstall":
        name = args.plugin_name
        if not name:
            print("❌ 请指定插件名: fclean plugin uninstall <name>", file=sys.stderr)
            sys.exit(1)
        if manager.uninstall_plugin(name):
            if args.json:
                print_json(make_json_envelope("plugin", {
                    "action": "uninstall",
                    "status": "success",
                    "name": name,
                }))
            else:
                print(f"✅ 已卸载插件: {name}")
        else:
            print(f"❌ 插件未找到: {name}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"❌ 未知 plugin 子命令: {subcmd}", file=sys.stderr)
        sys.exit(1)


def _generate_plugin_template(name: str) -> str:
    """生成插件模板代码。"""
    return f'''"""fclean 插件: {name}

自定义插件模板 — 编辑 classify/transform/summarize 实现你的逻辑。
"""

from pathlib import Path

from fclean.plugin import PluginBase


class {name.replace("-", "_").title().replace("_", "")}Plugin(PluginBase):
    """自定义插件。"""

    name = "{name}"
    version = "0.1.0"
    description = "自定义 fclean 插件"

    def classify(self, file_path: Path) -> str | None:
        """对文件进行分类。

        返回分类名字符串，返回 None 表示不处理。
        示例:
            if file_path.suffix == ".pdf":
                return "PDF文档"
            return None
        """
        # TODO: 实现你的分类逻辑
        return None

    def transform(self, file_path: Path, category: str) -> Path | None:
        """自定义文件移动目标路径（可选）。

        返回自定义目标路径，返回 None 使用默认规则。
        示例:
            return file_path.parent / "自定义目录" / file_path.name
        """
        return None

    def summarize(self, stats: dict) -> str | None:
        """自定义统计报告格式（可选）。

        返回报告文本，返回 None 使用默认格式。
        """
        return None
'''
