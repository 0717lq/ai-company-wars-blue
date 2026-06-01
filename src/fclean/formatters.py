"""输出格式化 — JSON 序列化和 Rich/纯文本显示函数。

从 cli.py 拆分出的显示逻辑，所有 *_to_json 和 _print_* 函数集中在此。
"""

import json
from datetime import datetime, timezone
from typing import Optional

# ── Rich 降级桩 ──────────────────────────────────────────────
try:
    from rich import box
    from rich.console import Console
    from rich.table import Table
    has_rich = True
except ImportError:
    has_rich = False
    Console = object  # type: ignore[assignment,misc]
    Table = object  # type: ignore[assignment,misc]
    box = object  # type: ignore[assignment,misc]


# ── 通用辅助 ────────────────────────────────────────────────


def format_size(size_bytes: int) -> str:
    """将字节格式化为人类可读的大小。"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


# ── JSON 输出辅助 ──────────────────────────────────────────


def make_json_envelope(command: str, data: dict) -> dict:
    """包装 JSON 输出，添加 tool/timestamp 元数据。"""
    return {
        "tool": "fclean",
        "command": command,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **data,
    }


def print_json(data: dict):
    """打印格式化的 JSON 输出。"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ── Organize 输出 ──────────────────────────────────────────


def organize_to_json(result) -> dict:
    """将 OrganizeResult 转为 JSON dict。"""
    categories = {}
    for fi, _dst in result.files_moved:
        cat = fi.target_dir_name
        if cat not in categories:
            categories[cat] = {"count": 0, "size_bytes": 0}
        categories[cat]["count"] += 1
        categories[cat]["size_bytes"] += fi.size

    return make_json_envelope("organize", {
        "status": "dry_run" if not result.executed else "executed",
        "scan_path": getattr(result, "scan_path", None),
        "total_scanned": result.total_scanned,
        "total_moved": result.total_moved,
        "total_skipped": result.total_skipped,
        "total_errors": result.total_errors,
        "categories": categories,
        "changes": [
            {"from": str(fi.path), "to": str(dst), "category": fi.target_dir_name}
            for fi, dst in result.files_moved
        ],
    })


def print_dry_run(result, json_output: bool = False):
    """显示 dry-run 预览结果。"""
    if json_output:
        print_json(organize_to_json(result))
        return

    if not has_rich:
        print_simple_dry_run(result)
        return

    from fclean.organizer import get_category_counts

    console = Console()
    console.print()
    console.print(f"📋 [bold cyan]fclean 预览[/] — 扫描 {result.total_scanned} 个文件")
    console.print()

    if not result.files_moved:
        console.print("[dim]所有文件已在正确位置，无需整理。[/]")
        console.print()
        return

    cat_counts = get_category_counts(result)
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("类别", style="cyan")
    table.add_column("数量", justify="right")
    table.add_column("大小", justify="right")
    table.add_column("示例文件")

    for cat, (count, size, examples) in sorted(cat_counts.items()):
        size_str = format_size(size)
        ex_str = ", ".join(examples[:3])
        if len(examples) > 3:
            ex_str += f" (+{len(examples) - 3})"
        table.add_row(cat, str(count), size_str, ex_str)

    console.print(table)
    console.print()

    if result.total_skipped > 0:
        console.print(f"[yellow]⏭  跳过 {result.total_skipped} 个文件（已在目标位置）[/]")
    if result.total_errors > 0:
        console.print(f"[red]❌ {result.total_errors} 个错误[/]")
    console.print(
        f"[bold]共 {result.total_moved} 个文件待移动[/] — "
        f"加上 [cyan]--execute[/] 执行"
    )
    console.print()


def print_simple_dry_run(result):
    """无 Rich 时的纯文本 dry-run 输出。"""
    print(f"\n📋 fclean 预览 — 扫描 {result.total_scanned} 个文件\n")

    if not result.files_moved:
        print("所有文件已在正确位置，无需整理。\n")
        return

    from fclean.organizer import get_category_counts
    cat_counts = get_category_counts(result)

    for cat, (count, size, examples) in sorted(cat_counts.items()):
        size_str = format_size(size)
        print(f"  {cat}: {count} 个文件 ({size_str})")
        for ex in examples[:3]:
            print(f"    → {ex.name}")
    print()

    if result.total_skipped > 0:
        print(f"⏭  跳过 {result.total_skipped} 个文件")
    print(f"共 {result.total_moved} 个文件待移动 — 加上 --execute 执行\n")


def print_execute_result(result, json_output: bool = False):
    """显示 execute 执行结果。"""
    if json_output:
        print_json(organize_to_json(result))
        return

    if not has_rich:
        print_simple_execute_result(result)
        return

    from fclean.organizer import get_category_counts

    console = Console()
    console.print()
    console.print(f"✅ [bold green]整理完成[/] — 移动 {result.total_moved} 个文件")
    console.print()

    if not result.files_moved:
        console.print("[dim]没有文件需要移动。[/]")
        console.print()
        return

    cat_counts = get_category_counts(result)
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("类别", style="cyan")
    table.add_column("数量", justify="right")
    table.add_column("大小", justify="right")

    for cat, (count, size, _) in sorted(cat_counts.items()):
        table.add_row(cat, str(count), format_size(size))

    console.print(table)
    console.print()

    if result.total_errors > 0:
        console.print(f"[red]❌ {result.total_errors} 个错误[/]")
    console.print("[dim]回滚: fclean --undo[/]")
    console.print()


def print_simple_execute_result(result):
    """无 Rich 时的纯文本执行结果。"""
    print(f"\n✅ 整理完成 — 移动 {result.total_moved} 个文件\n")

    if not result.files_moved:
        print("没有文件需要移动。\n")
        return

    from fclean.organizer import get_category_counts
    cat_counts = get_category_counts(result)

    for cat, (count, size, _) in sorted(cat_counts.items()):
        print(f"  {cat}: {count} 个文件 ({format_size(size)})")
    print()
    print("回滚: fclean --undo\n")


def print_undo_result(result):
    """显示 undo 回滚结果。"""
    if not has_rich:
        print(f"\n↩️  已回滚 {result.total_moved} 个文件\n")
        return

    console = Console()
    console.print()
    console.print(f"↩️  [bold yellow]已回滚[/] {result.total_moved} 个文件")
    console.print()


def print_undo_history(logs: list[dict]):
    """显示 undo 历史记录。"""
    if not has_rich:
        for i, log in enumerate(logs, 1):
            print(f"  {i}. {log.get('timestamp', '?')} — {log.get('count', 0)} 个文件")
        if not logs:
            print("  无历史记录。")
        return

    console = Console()
    console.print()
    console.print("[bold cyan]📜 Undo 历史[/]")
    console.print()

    if not logs:
        console.print("[dim]无历史记录。[/]")
        console.print()
        return

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("#", justify="right", style="dim")
    table.add_column("时间", style="cyan")
    table.add_column("文件数", justify="right")
    table.add_column("日志文件", style="dim")

    for i, log in enumerate(logs, 1):
        table.add_row(
            str(i),
            log.get("timestamp", "?"),
            str(log.get("count", 0)),
            log.get("log_file", "?"),
        )

    console.print(table)
    console.print()


# ── Rename 输出 ──────────────────────────────────────────


def rename_to_json(plan, pairs: list[tuple], status: str = "dry_run",
                    executed_count: int = 0) -> dict:
    """将重命名结果转为 JSON dict。"""
    return make_json_envelope("rename", {
        "status": status,
        "total_matched": len(pairs),
        "executed": executed_count if status == "executed" else 0,
        "changes": [
            {"from": str(old), "to": str(new)} for old, new in pairs
        ],
    })


def print_rename_preview(plan, pairs: list[tuple], json_output: bool = False):
    """显示重命名预览。"""
    if json_output:
        print_json(rename_to_json(plan, pairs))
        return

    if not has_rich:
        print(f"\n📋 重命名预览 — {len(pairs)} 个文件\n")
        for old, new in pairs[:20]:
            print(f"  {old.name} → {new.name}")
        if len(pairs) > 20:
            print(f"  ... 还有 {len(pairs) - 20} 个文件")
        print("\n加上 --execute 执行重命名\n")
        return

    console = Console()
    console.print()
    console.print(f"📋 [bold cyan]重命名预览[/] — {len(pairs)} 个文件")
    console.print()

    if not pairs:
        console.print("[dim]没有匹配的文件。[/]")
        console.print()
        return

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("#", justify="right", style="dim")
    table.add_column("原文件名", style="white")
    table.add_column("→", style="dim")
    table.add_column("新文件名", style="green")

    for i, (old, new) in enumerate(pairs[:50], 1):
        table.add_row(str(i), old.name, "→", new.name)

    if len(pairs) > 50:
        table.add_row("...", f"还有 {len(pairs) - 50} 个", "", "")

    console.print(table)
    console.print()
    console.print("[bold]加上 --execute 执行重命名[/]")
    console.print()


def print_rename_result(executed_count: int, json_output: bool = False):
    """显示重命名执行结果。"""
    if json_output:
        return  # JSON 已在调用方输出

    if not has_rich:
        print(f"\n✅ 已重命名 {executed_count} 个文件\n")
        print("回滚: fclean --undo\n")
        return

    console = Console()
    console.print()
    console.print(f"✅ [bold green]已重命名[/] {executed_count} 个文件")
    console.print("[dim]回滚: fclean --undo[/]")
    console.print()


# ── Stats JSON ──────────────────────────────────────────────


def stats_to_json(stats: dict, path: str, top_files: Optional[list] = None) -> dict:
    """将统计结果转为 JSON dict。"""
    data = {
        "scan_path": path,
        "total_files": stats["total_files"],
        "total_size": stats["total_size"],
        "total_size_human": format_size(stats["total_size"]),
        "categories": {
            name: {
                "count": info["count"],
                "size": info["size"],
                "size_human": format_size(info["size"]),
            }
            for name, info in stats["categories"].items()
        },
    }
    if top_files is not None:
        data["top_files"] = top_files
    return make_json_envelope("stats", data)


# ── Undo/History JSON ──────────────────────────────────────


def undo_to_json(result) -> dict:
    """将 undo 结果转为 JSON dict。"""
    return make_json_envelope("undo", {
        "status": "rolled_back",
        "files_restored": result.total_moved,
        "changes": [
            {"from": str(dst), "to": str(fi.path)}
            for fi, dst in result.files_moved
        ],
    })


def history_to_json(logs: list[dict]) -> dict:
    """将 undo 历史转为 JSON dict。"""
    return make_json_envelope("history", {
        "total_logs": len(logs),
        "logs": logs,
    })
