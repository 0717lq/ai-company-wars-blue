"""
fclean 命令行入口。

使用 argparse 解析参数，支持子命令（init, stats, config, organize）。
核心逻辑委托给 organizer、config 和 undo 模块。
默认 dry-run，加上 --execute 才实际执行，--undo 回滚。

用法:
    fclean ~/Downloads                  # dry-run 预览（默认 organize）
    fclean organize ~/Downloads         # 同上，显式子命令
    fclean organize ~/Downloads --execute # 实际整理
    fclean init                         # 生成配置文件
    fclean init --global               # 生成到 ~/.fcleanrc
    fclean stats ~/Downloads           # 目录统计
    fclean config                       # 查看当前配置
    fclean --undo                       # 回滚
    fclean --history                    # undo 历史
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from fclean import __version__
from fclean.config import (
    Config,
    generate_example_config,
    load_config,
)
from fclean.organizer import OrganizeResult, compute_stats, organize
from fclean.undo import list_undo_logs, record_operation, undo_last

# 所有已知子命令名称
KNOWN_SUBCOMMANDS = {"init", "stats", "config", "organize"}


def _format_size(size_bytes: int) -> str:
    """将字节格式化为人类可读的大小。"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def _print_dry_run(result: OrganizeResult):
    """用 rich 打印 dry-run 预览表格。"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
        console = Console()
    except ImportError:
        # fallback: 无 rich 时使用简单输出
        _print_simple_dry_run(result)
        return

    console.print()
    console.print(Text("🔍 fclean — Dry Run 预览 (不会实际移动)", style="bold cyan"))
    console.print(Text(f"扫描到 {result.total_scanned} 个文件，"
                       f"将移动 {result.total_moved} 个文件",
                       style="yellow"))
    console.print()

    if not result.files_moved:
        console.print(Text("✅ 所有文件已归类，无需整理！", style="green"))
        return

    # 按类别分组显示
    categories = result.get_category_counts()
    for cat_name in sorted(categories.keys()):
        table = Table(title=f"📁 {cat_name}", show_header=True,
                      header_style="bold magenta")
        table.add_column("文件名", style="white")
        table.add_column("大小", justify="right", style="cyan")

        # 找出该类别的文件
        for fi, dst in result.files_moved:
            if fi.target_dir_name == cat_name:
                table.add_row(fi.name, _format_size(fi.size))

        console.print(table)
        console.print()

    # 底部统计
    console.print(Text(f"总计: 将移动 {result.total_moved} 个文件 "
                       f"({_format_size(result.total_size_moved)})",
                       style="bold green"))
    console.print(Text("提示: 加 --execute 执行整理", style="dim"))
    console.print()


def _print_simple_dry_run(result: OrganizeResult):
    """不带 rich 的简单输出。"""
    print("\n🔍 fclean — Dry Run 预览")
    print(f"扫描到 {result.total_scanned} 个文件")
    print()

    if not result.files_moved:
        print("✅ 所有文件已归类，无需整理！")
        return

    categories = result.get_category_counts()
    for cat_name in sorted(categories.keys()):
        print(f"  [{cat_name}]")
        for fi, dst in result.files_moved:
            if fi.target_dir_name == cat_name:
                print(f"    {fi.name}")
        print()

    print(f"总计: 将移动 {result.total_moved} 个文件 "
          f"({_format_size(result.total_size_moved)})")
    print("提示: 加 --execute 执行整理")


def _print_execute_result(result: OrganizeResult):
    """打印实际执行后的结果。"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
        console = Console()
    except ImportError:
        _print_simple_execute_result(result)
        return

    console.print()
    if result.total_errors > 0:
        console.print(Text("⚠️  整理完成，但有错误", style="bold yellow"))
    else:
        console.print(Text("✅ 整理完成！", style="bold green"))

    table = Table(title="📊 整理统计", show_header=True, header_style="bold magenta")
    table.add_column("类别", style="cyan")
    table.add_column("数量", justify="right", style="white")
    table.add_column("大小", justify="right", style="green")

    cats = result.get_category_counts()
    sizes = result.get_category_sizes()
    for cat_name in sorted(cats.keys()):
        table.add_row(cat_name, str(cats[cat_name]), _format_size(sizes[cat_name]))

    table.add_row("合计", str(result.total_moved), _format_size(result.total_size_moved),
                  style="bold")

    console.print(table)
    console.print()

    if result.total_skipped > 0:
        for path, reason in result.files_skipped:
            console.print(Text(f"⏭ 跳过: {path} — {reason}", style="dim"))

    if result.total_errors > 0:
        console.print(Text("❌ 错误:", style="bold red"))
        for path, err in result.errors:
            console.print(Text(f"  {path}: {err}", style="red"))

    # 提示 undo
    if result.total_moved > 0:
        console.print(Text("💡 如需回滚: fclean --undo", style="dim"))
    console.print()


def _print_simple_execute_result(result: OrganizeResult):
    """简单模式执行结果。"""
    print(f"\n{'⚠️  整理完成，但有错误' if result.total_errors > 0 else '✅ 整理完成！'}")

    cats = result.get_category_counts()
    sizes = result.get_category_sizes()
    for cat_name in sorted(cats.keys()):
        print(f"  {cat_name}: {cats[cat_name]} 个文件 ({_format_size(sizes[cat_name])})")
    print(f"  合计: {result.total_moved} 个文件 ({_format_size(result.total_size_moved)})")

    if result.total_errors > 0:
        print("\n❌ 错误:")
        for path, err in result.errors:
            print(f"  {path}: {err}")

    if result.total_moved > 0:
        print("💡 如需回滚: fclean --undo")


def _print_undo_result(result: OrganizeResult):
    """打印 undo 回滚结果。"""
    try:
        from rich.console import Console
        from rich.text import Text
        console = Console()
    except ImportError:
        print(f"\n{'⚠️  回滚完成，但有错误' if result.total_errors > 0 else '✅ 回滚完成！'}")
        print(f"回滚了 {result.total_moved} 个文件")
        if result.total_errors > 0:
            for path, err in result.errors:
                print(f"  ❌ {path}: {err}")
        return

    console.print()
    if result.total_errors > 0:
        console.print(Text("⚠️  回滚完成，但有错误", style="bold yellow"))
    else:
        console.print(Text("↩️  已回滚到整理前的状态！", style="bold green"))
    console.print(Text(f"回滚了 {result.total_moved} 个文件", style="cyan"))
    console.print()

    if result.total_errors > 0:
        console.print(Text("❌ 错误:", style="bold red"))
        for path, err in result.errors:
            console.print(Text(f"  {path}: {err}", style="red"))
    console.print()


def _print_undo_history(logs: list[dict]):
    """打印 undo 历史。"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
        console = Console()
    except ImportError:
        if not logs:
            print("没有 undo 记录。")
            return
        print(f"共有 {len(logs)} 条 undo 记录:")
        for log in logs:
            print(f"  {log['timestamp']} — {log['total_moved']} 个文件")
        return

    console.print()
    console.print(Text("📋 Undo 历史", style="bold cyan"))

    if not logs:
        console.print(Text("没有 undo 记录。", style="dim"))
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("时间", style="cyan")
    table.add_column("文件数", justify="right", style="white")

    for log in logs:
        table.add_row(log["timestamp"], str(log["total_moved"]))

    console.print(table)
    console.print(Text("使用 fclean --undo 回滚最近一次", style="dim"))
    console.print()


def build_parser():
    """构建参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="fclean",
        description="又安全又好看的命令行文件整理工具 — 按文件类型自动归类",
        epilog="示例: fclean ~/Downloads              # 预览\n"
               "       fclean organize ~/Downloads     # 预览（显式子命令）\n"
               "       fclean organize ~/Downloads --execute  # 执行\n"
               "       fclean init                      # 生成配置\n"
               "       fclean stats ~/Downloads         # 统计\n"
               "       fclean config                     # 查看当前配置\n"
               "       fclean --undo                     # 回滚",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"fclean v{__version__}",
    )

    parser.add_argument(
        "--undo",
        action="store_true",
        help="回滚上一次整理操作",
    )

    parser.add_argument(
        "--history",
        action="store_true",
        help="查看 undo 历史记录",
    )

    # 第一个位置参数：可能是子命令，也可能是路径
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        help="子命令: init, stats, config, organize，或直接传入路径",
    )

    # 第二个位置参数：用于子命令的参数（如 stats <path>）
    parser.add_argument(
        "arg",
        nargs="?",
        default=None,
        help="子命令的参数（如 stats 的目标路径）",
    )

    # organize 子命令的选项
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        dest="dry_run",
        help="预览模式（默认启用），只显示拟操作，不实际移动文件",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="实际执行文件整理（默认只预览）",
    )

    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="排除匹配模式的文件（可多次使用），如 --exclude '*.tmp'",
    )

    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        dest="exclude_dirs",
        help="排除的目录名（可多次使用），如 --exclude-dir node_modules",
    )

    # init 子命令的选项
    parser.add_argument(
        "--global",
        action="store_true",
        dest="global_config",
        help="将配置文件写入 ~/.fcleanrc 而非当前目录",
    )

    return parser


def _run_organize(args, config: Optional[Config] = None):
    """执行 organize 操作（默认路径或子命令模式）。"""
    # 确定目标路径
    target = args.command or args.arg or "."
    if target in KNOWN_SUBCOMMANDS:
        target = args.arg or "."

    # 将相对路径转为绝对路径
    target_path = str(Path(target).expanduser().resolve())

    if not Path(target_path).exists():
        print(f"❌ 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not Path(target_path).is_dir():
        print(f"❌ 不是目录: {target}", file=sys.stderr)
        sys.exit(1)

    # 加载配置
    if config is None:
        config = load_config(target_path)

    try:
        result = organize(
            target_path=target_path,
            dry_run=(not args.execute),
            execute=args.execute,
            exclude=args.exclude or None,
            exclude_dirs=args.exclude_dirs or None,
            config=config,
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)

    if args.execute:
        # 实际执行，记录 undo
        _print_execute_result(result)
        if result.total_moved > 0:
            try:
                log_path = record_operation(result)
                _ = log_path
            except ValueError:
                pass  # 没有文件被移动，不记录
    else:
        # dry-run 预览
        _print_dry_run(result)

    # 如果有严重错误，退出码非零
    if result.total_errors > 0:
        sys.exit(1)


def _run_init(args):
    """执行 fclean init 命令。"""
    # 确定目标路径
    if args.global_config:
        target_dir = Path.home()
    else:
        # 使用 command 或 arg 作为目录，默认为当前目录
        dir_arg = None
        if args.arg and args.arg not in KNOWN_SUBCOMMANDS:
            dir_arg = args.arg
        elif args.command and args.command not in KNOWN_SUBCOMMANDS:
            dir_arg = args.command
        target_dir = Path(dir_arg).expanduser().resolve() if dir_arg else Path.cwd()

    config_path = target_dir / ".fcleanrc"

    # 如果文件已存在，询问是否覆盖
    if config_path.exists():
        print(f"⚠️  {config_path} 已存在。使用 --force 覆盖。")
        sys.exit(1)

    content = generate_example_config()
    config_path.write_text(content, encoding="utf-8")
    print(f"✅ 已生成配置文件: {config_path}")
    print(f"编辑 {config_path} 自定义分类规则后，运行 fclean <path> 即可使用新规则。")


def _run_stats(args):
    """执行 fclean stats 命令。"""
    # 确定目标路径
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

    # 加载配置用于分类
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

    if has_rich:
        console = Console()
        console.print()
        console.print(Text(f"📊 fclean stats — {target_path}", style="bold cyan"))
        console.print(Text(f"文件总数: {stats['total_files']}  |  "
                           f"总大小: {_format_size(stats['total_size'])}",
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
                _format_size(data["size"]),
                f"{pct:.1f}% {bar_chars}",
            )

        table.add_row(
            "合计",
            str(stats["total_files"]),
            _format_size(stats["total_size"]),
            "100%",
            style="bold",
        )

        console.print(table)
        console.print()
    else:
        print(f"\n📊 fclean stats — {target_path}")
        print(f"文件总数: {stats['total_files']}  |  总大小: {_format_size(stats['total_size'])}")
        print()

        cats = stats["categories"]
        for cat_name in sorted(cats.keys()):
            data = cats[cat_name]
            print(f"  {cat_name}: {data['count']} 个文件 ({_format_size(data['size'])})")


def _run_config(args):
    """执行 fclean config 命令，查看当前生效的完整配置。"""
    # 确定路径参数
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

        # 显示分类规则
        rules_table = Table(title="文件分类规则", show_header=True, header_style="bold magenta")
        rules_table.add_column("类别", style="cyan")
        rules_table.add_column("扩展名", style="white")

        for rule in config_data["rules"]:
            exts = ", ".join(rule["extensions"])
            rules_table.add_row(rule["category"], exts)

        console.print(rules_table)
        console.print()

        # 显示排除设置
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


def main():
    """CLI 主入口。"""
    parser = build_parser()
    args = parser.parse_args()

    # --undo 模式（单独处理，保持兼容）
    if args.undo:
        try:
            result = undo_last()
            _print_undo_result(result)
        except FileNotFoundError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        return

    # --history 模式
    if args.history:
        logs = list_undo_logs()
        _print_undo_history(logs)
        return

    # 没有参数 -> 默认当前目录 organize
    if args.command is None:
        _run_organize(args)
        return

    # 检查子命令
    cmd = args.command

    if cmd == "init":
        _run_init(args)
    elif cmd == "stats":
        _run_stats(args)
    elif cmd == "config":
        _run_config(args)
    elif cmd == "organize":
        # 显式 organize 子命令
        _run_organize(args)
    else:
        # 不是已知子命令，当作路径处理 -> organize
        _run_organize(args)


if __name__ == "__main__":
    main()
