"""
fclean 命令行入口。

使用 argparse 解析参数，支持子命令（init, stats, config, organize, rename, dupes）。
核心逻辑委托给 organizer、config、undo、renamer、dupes 模块。
默认 dry-run，加上 --execute 才实际执行，--undo 回滚。

所有子命令支持 --json/-j 输出，供 AI Agent 解析。

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
    fclean dupes ~/Downloads           # 重复文件检测
    fclean rename "*.jpg" --pattern "vacation_{n:03d}"  # 批量重命名
    fclean --json ~/Downloads          # JSON 输出
    fclean --install-completion        # 安装 shell 补全
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fclean import __version__
from fclean.config import (
    Config,
    generate_example_config,
    load_config,
)
from fclean.dupes import find_duplicates
from fclean.ignore import load_ignore_rules
from fclean.organizer import OrganizeResult, compute_stats, organize
from fclean.renamer import generate_rename_plan
from fclean.undo import list_undo_logs, record_operation, undo_last

# 所有已知子命令名称
KNOWN_SUBCOMMANDS = {"init", "stats", "config", "organize", "rename", "dupes", "watch"}

# 删除策略选项
DELETE_STRATEGIES = ["newest", "oldest", "path"]


def _format_size(size_bytes: int) -> str:
    """将字节格式化为人类可读的大小。"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


# ── JSON 输出辅助 ──────────────────────────────────────────


def _make_json_envelope(command: str, data: dict) -> dict:
    """包装 JSON 输出，添加 tool/timestamp 元数据。

    参数:
        command: 子命令名
        data: 输出的数据字典

    返回:
        带元数据的完整 JSON 结构
    """
    return {
        "tool": "fclean",
        "command": command,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **data,
    }


def _print_json(data: dict):
    """打印格式化的 JSON 输出。"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ── Organize 输出函数 ──────────────────────────────────────


def _organize_to_json(result: OrganizeResult) -> dict:
    """将 OrganizeResult 转为 JSON dict。"""
    categories = {}
    for fi, dst in result.files_moved:
        cat = fi.target_dir_name
        if cat not in categories:
            categories[cat] = {"count": 0, "size_bytes": 0}
        categories[cat]["count"] += 1
        categories[cat]["size_bytes"] += fi.size

    changes = []
    for fi, dst in result.files_moved:
        changes.append({
            "from": str(fi.path),
            "to": str(dst),
            "category": fi.target_dir_name,
            "size": fi.size,
        })

    return _make_json_envelope("organize", {
        "path": str(result.scan_path) if hasattr(result, "scan_path") else "",
        "status": "executed" if result.total_moved > 0 else "dry_run",
        "files_scanned": result.total_scanned,
        "files_moved": result.total_moved,
        "files_skipped": result.total_skipped,
        "errors": result.total_errors,
        "categories_found": categories,
        "changes": changes,
        "summary": (
            f"{result.total_scanned} files scanned, "
            f"{result.total_moved} files organized into "
            f"{len(categories)} categories"
        ),
    })


def _print_dry_run(result: OrganizeResult, json_output: bool = False):
    """用 rich 打印 dry-run 预览表格。"""
    if json_output:
        _print_json(_organize_to_json(result))
        return

    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
        console = Console()
    except ImportError:
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

    categories = result.get_category_counts()
    for cat_name in sorted(categories.keys()):
        table = Table(title=f"📁 {cat_name}", show_header=True,
                      header_style="bold magenta")
        table.add_column("文件名", style="white")
        table.add_column("大小", justify="right", style="cyan")

        for fi, dst in result.files_moved:
            if fi.target_dir_name == cat_name:
                table.add_row(fi.name, _format_size(fi.size))

        console.print(table)
        console.print()

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


def _print_execute_result(result: OrganizeResult, json_output: bool = False):
    """打印实际执行后的结果。"""
    if json_output:
        _print_json(_organize_to_json(result))
        return

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


# ── Rename 输出函数 ────────────────────────────────────────


def _rename_to_json(plan, pairs: list[tuple], status: str = "dry_run",
                    executed_count: int = 0) -> dict:
    """将 rename 操作转为 JSON dict。"""
    renames = []
    for old_p, new_p in pairs:
        renames.append({
            "from": str(old_p),
            "to": str(new_p),
        })

    return _make_json_envelope("rename", {
        "status": status,
        "pattern": plan.pattern,
        "template": plan.format_template,
        "files_matched": len(pairs),
        "files_executed": executed_count,
        "renames": renames,
    })


def _print_rename_preview(plan, pairs: list[tuple], json_output: bool = False):
    """打印 rename dry-run 预览表格。"""
    if json_output:
        _print_json(_rename_to_json(plan, pairs, status="dry_run"))
        return

    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
        console = Console()
    except ImportError:
        print("\n📋 Rename Preview (dry-run)")
        print(f"模式: {plan.pattern} → {plan.format_template}")
        print()
        if not pairs:
            print("没有匹配的文件。")
            return
        print(f"{'旧文件名':<30} {'新文件名':<30}")
        print("-" * 60)
        for old_p, new_p in pairs:
            print(f"{old_p.name:<30} {new_p.name:<30}")
        print(f"\n将重命名 {len(pairs)} 个文件")
        print("提示: 加 --execute 执行重命名")
        return

    console.print()
    console.print(Text("📋 Rename Preview (dry-run)", style="bold cyan"))
    console.print(f"模式: {plan.pattern} → {plan.format_template}")
    console.print()

    if not pairs:
        console.print(Text("没有匹配的文件。", style="dim"))
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("旧文件名", style="white")
    table.add_column("新文件名", style="green")
    table.add_column("类型", justify="right", style="cyan")

    for old_p, new_p in pairs:
        table.add_row(old_p.name, new_p.name, old_p.suffix.lower())

    console.print(table)
    console.print(Text(f"将重命名 {len(pairs)} 个文件", style="yellow"))
    console.print(Text("提示: 加 --execute 执行重命名", style="dim"))


def _print_rename_result(executed_count: int, json_output: bool = False):
    """打印 rename 执行结果。"""
    if json_output:
        return  # JSON 在调用方已经输出

    try:
        from rich.console import Console
        from rich.text import Text
        console = Console()
    except ImportError:
        print(f"\n✅ 重命名完成！共处理 {executed_count} 个文件")
        print("💡 如需回滚: fclean --undo")
        return

    console.print()
    console.print(Text("✅ 重命名完成！", style="bold green"))
    console.print(Text(f"共处理 {executed_count} 个文件", style="cyan"))
    console.print(Text("💡 如需回滚: fclean --undo", style="dim"))


# ── Stats JSON 输出 ────────────────────────────────────────


def _stats_to_json(stats: dict, path: str) -> dict:
    """将 stats 结果转为 JSON dict。"""
    categories = {}
    for cat_name, data in stats["categories"].items():
        categories[cat_name] = {
            "count": data["count"],
            "size_bytes": data["size"],
        }

    return _make_json_envelope("stats", {
        "path": path,
        "total_files": stats["total_files"],
        "total_size_bytes": stats["total_size"],
        "total_size_human": _format_size(stats["total_size"]),
        "categories": categories,
    })


# ── Undo/History JSON 输出 ─────────────────────────────────


def _undo_to_json(result: OrganizeResult) -> dict:
    """将 undo 结果转为 JSON dict。"""
    changes = []
    for fi, dst in result.files_moved:
        changes.append({
            "from": str(fi.path) if hasattr(fi, "path") else str(fi),
            "to": str(dst),
        })

    return _make_json_envelope("undo", {
        "status": "executed" if result.total_moved > 0 else "noop",
        "files_restored": result.total_moved,
        "errors": result.total_errors,
        "changes": changes,
    })


def _history_to_json(logs: list[dict]) -> dict:
    """将 undo 历史转为 JSON dict。"""
    return _make_json_envelope("history", {
        "total_logs": len(logs),
        "logs": [
            {
                "timestamp": log.get("timestamp", ""),
                "datetime": log.get("datetime", ""),
                "total_moved": log.get("total_moved", 0),
                "path": log.get("path", ""),
            }
            for log in logs
        ],
    })


# ── 主 CLI 逻辑 ────────────────────────────────────────────


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
               "       fclean rename \"*.jpg\" --pattern \"vacation_{n:03d}\"  # 预览重命名\n"
               "       fclean rename \"*.jpg\" --pattern \"vacation_{n:03d}\" --execute  # 执行\n"
               "       fclean dupes ~/Downloads         # 重复文件检测\n"
               "       fclean dupes ~/Downloads --delete  # 删除重复文件\n"
               "       fclean --json ~/Downloads        # JSON 输出\n"
               "       fclean --undo                     # 回滚\n"
               "       fclean --install-completion       # 安装 shell 补全",
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

    parser.add_argument(
        "--json", "-j",
        action="store_true",
        default=False,
        help="以 JSON 格式输出（供 AI Agent 解析）",
    )

    parser.add_argument(
        "--install-completion",
        action="store_true",
        dest="install_completion",
        help="安装 shell 自动补全（bash/zsh/fish）",
    )

    # 第一个位置参数：可能是子命令，也可能是路径
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        help="子命令: init, stats, config, organize, rename, dupes，或直接传入路径",
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

    # rename 子命令的选项
    parser.add_argument(
        "--pattern",
        "-p",
        default=None,
        help="命名模板（rename 子命令专用），如 'vacation_{n:03d}'",
    )

    # dupes 子命令的选项
    parser.add_argument(
        "--min-size",
        default=None,
        dest="min_size",
        help="最小文件大小（dupes 子命令专用），如 '1MB', '500KB'",
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        default=False,
        help="删除重复文件（dupes 子命令专用）",
    )

    parser.add_argument(
        "--strategy",
        default="newest",
        choices=DELETE_STRATEGIES,
        help="删除保留策略（dupes 子命令专用），默认 newest",
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        dest="no_progress",
        default=False,
        help="不显示进度条（dupes 子命令专用）",
    )

    # watch 子命令的选项
    parser.add_argument(
        "--auto",
        action="store_true",
        default=False,
        help="自动执行整理（watch 子命令专用，默认 dry-run）",
    )

    return parser


def _install_completion():
    """安装 shell 自动补全。

    检测当前 shell (bash/zsh/fish) 并安装补全脚本。
    """
    import os as os_module
    shell = os_module.environ.get("SHELL", "")

    if "zsh" in shell:
        # Zsh 补全
        zsh_func_path = Path.home() / ".zsh" / "completion"
        zsh_func_path.mkdir(parents=True, exist_ok=True)

        # 生成 zsh 补全函数
        comp_file = zsh_func_path / "_fclean"
        comp_file.write_text(
            "#compdef fclean\n"
            f"# fclean v{__version__} shell completion for zsh\n"
            "_fclean() {\n"
            '  local -a subcmds\n'
            '  subcmds=("init" "stats" "config" "organize" "rename" "dupes")\n'
            '  _arguments \\\n'
            '    "--version[show version]" \\\n'
            '    "--undo[rollback last operation]" \\\n'
            '    "--history[view undo history]" \\\n'
            '    "--json[output as JSON]" \\\n'
            '    "--install-completion[install shell completion]" \\\n'
            '    "--execute[actually execute]" \\\n'
            '    "--dry-run[dry-run preview]" \\\n'
            '    "--exclude[exclude files]:pattern:" \\\n'
            '    "--exclude-dir[exclude directories]:dir:" \\\n'
            '    "--min-size[minimum file size for dupes]:size:" \\\n'
            '    "--delete[delete duplicates]" \\\n'
            '    "--strategy[delete strategy]:strategy:(newest oldest path)" \\\n'
            '    "--pattern[rename template]:template:" \\\n'
            '    ":subcommand:($subcmds)" \\\n'
            '    "*::arg:_files"\n'
            '}\n'
            '_fclean "$@"\n',
            encoding="utf-8",
        )

        # 添加到 .zshrc
        zshrc = Path.home() / ".zshrc"
        fpath_line = f'export FPATH="{zsh_func_path}:$FPATH"'
        autoload_line = "autoload -U compinit && compinit"

        zshrc_content = ""
        if zshrc.exists():
            zshrc_content = zshrc.read_text(encoding="utf-8")

        if fpath_line not in zshrc_content:
            with open(zshrc, "a", encoding="utf-8") as f:
                f.write(f"\n# fclean completion\n{fpath_line}\n{autoload_line}\n")

        print(f"✅ Zsh 补全已安装到 {comp_file}，已添加到 ~/.zshrc")
        print("   重新打开终端或执行 'source ~/.zshrc' 生效")

    elif "bash" in shell:
        # Bash 补全
        bash_comp_file = Path.home() / ".fclean_completion.bash"
        bash_comp_file.write_text(
            f"# fclean v{__version__} shell completion for bash\n"
            "_fclean_completion() {\n"
            '  local cur="${COMP_WORDS[COMP_CWORD]}"\n'
            '  local subcmds="init stats config organize rename dupes"\n'
            '  local opts="--version --undo --history --json --install-completion '
            '--execute --dry-run --exclude --exclude-dir '
            '--min-size --delete --strategy --pattern '
            '-V -j -p"\n'
            '  COMPREPLY=($(compgen -W "$subcmds $opts" -- "$cur"))\n'
            '  return 0\n'
            '}\n'
            'complete -F _fclean_completion fclean\n',
            encoding="utf-8",
        )

        bashrc = Path.home() / ".bashrc"
        source_line = "source ~/.fclean_completion.bash"
        bashrc_content = ""
        if bashrc.exists():
            bashrc_content = bashrc.read_text(encoding="utf-8")

        if source_line not in bashrc_content:
            with open(bashrc, "a", encoding="utf-8") as f:
                f.write(f"\n# fclean completion\n{source_line}\n")

        print(f"✅ Bash 补全已安装到 {bash_comp_file}，已添加到 ~/.bashrc")
        print("   重新打开终端或执行 'source ~/.bashrc' 生效")

    elif "fish" in shell:
        # Fish 补全
        fish_comp_dir = Path.home() / ".config" / "fish" / "completions"
        fish_comp_dir.mkdir(parents=True, exist_ok=True)
        fish_comp_file = fish_comp_dir / "fclean.fish"
        fish_comp_file.write_text(
            f"# fclean v{__version__} shell completion for fish\n"
            "complete -c fclean -f\n"
            "complete -c fclean -n '__fish_use_subcommand' -a 'init' -d 'Generate config file'\n"
            "complete -c fclean -n '__fish_use_subcommand' -a 'stats' -d 'Dir stats'\n"
            "complete -c fclean -n '__fish_use_subcommand' -a 'config' -d 'View config'\n"
            "complete -c fclean -n '__fish_use_subcommand' -a 'organize' -d 'Organize files'\n"
            "complete -c fclean -n '__fish_use_subcommand' -a 'rename' -d 'Batch rename files'\n"
            "complete -c fclean -n '__fish_use_subcommand' -a 'dupes' -d 'Find duplicate files'\n"
            "complete -c fclean -s V -l version -d 'Show version'\n"
            "complete -c fclean -l undo -d 'Rollback last operation'\n"
            "complete -c fclean -l history -d 'View undo history'\n"
            "complete -c fclean -s j -l json -d 'Output as JSON'\n"
            "complete -c fclean -l install-completion -d 'Install shell completion'\n"
            "complete -c fclean -l execute -d 'Actually execute'\n"
            "complete -c fclean -l dry-run -d 'Dry-run preview'\n"
            "complete -c fclean -l exclude -d 'Exclude files' -r\n"
            "complete -c fclean -l exclude-dir -d 'Exclude directories' -r\n"
            "complete -c fclean -l min-size -d 'Minimum file size for dupes' -r\n"
            "complete -c fclean -l delete -d 'Delete duplicates'\n"
            "complete -c fclean -l strategy -d 'Delete strategy' -x -a 'newest oldest path'\n"
            "complete -c fclean -s p -l pattern -d 'Rename template' -r\n",
            encoding="utf-8",
        )
        print(f"✅ Fish 补全已安装到 {fish_comp_file}")
        print("   重新打开终端或执行 'source' 命令生效")

    else:
        print(f"❌ 不支持的 shell: {shell}")
        print("   支持: bash, zsh, fish")
        sys.exit(1)


def _run_organize(args, config: Optional[Config] = None):
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
        # 将扫描路径保存到结果对象
        result.scan_path = target_path
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)

    if args.execute:
        _print_execute_result(result, json_output=args.json)
        if result.total_moved > 0:
            try:
                log_path = record_operation(result)
                _ = log_path
            except ValueError:
                pass
    else:
        _print_dry_run(result, json_output=args.json)

    if result.total_errors > 0:
        sys.exit(1)


def _run_init(args):
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


def _run_stats(args):
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

    # JSON 输出
    if args.json:
        _print_json(_stats_to_json(stats, target_path))
        return

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


def _run_rename(args):
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
            _print_json(_rename_to_json(plan, pairs, status="executed",
                                        executed_count=executed_count))

        if executed_count > 0:
            _print_rename_result(executed_count, json_output=args.json)
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
                log_path = record_operation(undo_result)
                _ = log_path
            except ValueError:
                pass
        else:
            print("没有文件被重命名。")

        if executed_count < len(pairs):
            print(f"⚠️  成功 {executed_count}/{len(pairs)} 个文件，部分文件可能因权限问题跳过。",
                  file=sys.stderr)
    else:
        _print_rename_preview(plan, pairs, json_output=args.json)


def _run_dupes(args):
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

    # --delete 模式
    if args.delete:
        if not result.has_duplicates:
            if args.json:
                _print_json(result.to_dict())
            else:
                print("\n✅ 没有发现重复文件。\n")
            return

        # 输出 JSON 或表格
        if args.json:
            dupes_data = result.to_dict()
        else:
            result.print_table()

        # 执行删除
        deleted = result.delete(strategy=args.strategy, interactive=False)

        if args.json:
            dupes_data["action"] = "deleted"
            dupes_data["files_deleted"] = len(deleted)
            dupes_data["errors"] = [
                {"path": p, "error": e} for p, e in result.errors
            ]
            _print_json(dupes_data)
        else:
            if deleted:
                print(f"✅ 已删除 {len(deleted)} 个重复文件")
                # 记录到 undo 日志
                from fclean.organizer import OrganizeResult
                undo_result = OrganizeResult()
                for keep, deleted_path in deleted:
                    from fclean.organizer import FileInfo
                    fi = FileInfo.__new__(FileInfo)
                    fi.path = keep
                    fi.name = keep.name
                    fi.size = keep.stat().st_size if keep.exists() else 0
                    fi.category_key = None
                    fi.target_dir_name = "dupes"
                    undo_result.files_moved.append((fi, keep))
                try:
                    log_path = record_operation(undo_result)
                    print("💡 如需回滚: fclean --undo")
                    _ = log_path
                except ValueError:
                    pass
            if result.errors:
                for path, err in result.errors:
                    print(f"  ❌ {path}: {err}")

        if result.errors:
            sys.exit(1)
    else:
        # dry-run 模式
        if args.json:
            _print_json(result.to_dict())
        else:
            result.print_table()

    if result.errors:
        sys.exit(1)


def _run_watch(args):
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


def main():
    """CLI 主入口。"""
    parser = build_parser()
    args = parser.parse_args()

    # --install-completion 模式
    if args.install_completion:
        _install_completion()
        return

    # --undo 模式
    if args.undo:
        try:
            result = undo_last()
            if args.json:
                _print_json(_undo_to_json(result))
            else:
                _print_undo_result(result)
        except FileNotFoundError as e:
            if args.json:
                _print_json({
                    "tool": "fclean",
                    "command": "undo",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "status": "error",
                    "error": str(e),
                })
            else:
                print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        return

    # --history 模式
    if args.history:
        logs = list_undo_logs()
        if args.json:
            _print_json(_history_to_json(logs))
        else:
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
        _run_organize(args)
    elif cmd == "rename":
        _run_rename(args)
    elif cmd == "dupes":
        _run_dupes(args)
    else:
        # 不是已知子命令，当作路径处理 -> organize
        _run_organize(args)


if __name__ == "__main__":
    main()
