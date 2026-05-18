"""
fclean 命令行入口。

使用 argparse 解析参数，核心逻辑委托给 organizer 和 undo 模块。
默认 dry-run，加上 --execute 才实际执行，--undo 回滚。

用法:
    fclean ~/Downloads              # dry-run 预览
    fclean ~/Downloads --execute    # 实际整理
    fclean --undo                   # 回滚
    fclean ~/Downloads --exclude "*.tmp" --exclude-dir node_modules
"""

import argparse
import sys
from pathlib import Path

from fclean import __version__
from fclean.organizer import organize, OrganizeResult
from fclean.undo import record_operation, undo_last, list_undo_logs


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
    print(f"\n🔍 fclean — Dry Run 预览")
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


def main():
    """CLI 主入口。"""
    parser = argparse.ArgumentParser(
        prog="fclean",
        description="又安全又好看的命令行文件整理工具 — 按文件类型自动归类",
        epilog="示例: fclean ~/Downloads --dry-run    # 预览\n"
               "       fclean ~/Downloads --execute   # 执行\n"
               "       fclean --undo                   # 回滚",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="要整理的目录路径（默认：当前目录）",
    )

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
        "--undo",
        action="store_true",
        help="回滚上一次整理操作",
    )

    parser.add_argument(
        "--history",
        action="store_true",
        help="查看 undo 历史记录",
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

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"fclean v{__version__}",
    )

    args = parser.parse_args()

    # --undo 模式
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

    # 整理模式
    target = args.path or "."

    # 将相对路径转为绝对路径
    target_path = str(Path(target).expanduser().resolve())

    if not Path(target_path).exists():
        print(f"❌ 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not Path(target_path).is_dir():
        print(f"❌ 不是目录: {target}", file=sys.stderr)
        sys.exit(1)

    try:
        result = organize(
            target_path=target_path,
            dry_run=(not args.execute),
            execute=args.execute,
            exclude=args.exclude or None,
            exclude_dirs=args.exclude_dirs or None,
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
                # 静默记录成功，无需额外输出
                _ = log_path
            except ValueError:
                pass  # 没有文件被移动，不记录
    else:
        # dry-run 预览
        _print_dry_run(result)

    # 如果有严重错误，退出码非零
    if result.total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
