"""
fclean 统计可视化模块 — ASCII 饼图、柱状图、Top-N 大文件排行。

提供纯 ASCII 字符的图表渲染，兼容所有终端。
JSON 模式下忽略图表输出，只返回数据。

用法:
    from fclean.stats_viz import render_pie_chart, render_bar_chart, find_top_files
"""

import os
from pathlib import Path


def _format_size(size_bytes: int) -> str:
    """将字节格式化为人类可读的大小。"""
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024:
            return f"{size_float:.1f}{unit}"
        size_float /= 1024
    return f"{size_float:.1f}TB"


# ── ASCII 饼图 ──────────────────────────────────────────────


def render_pie_chart(stats: dict, width: int = 40) -> str:
    """渲染 ASCII 饼图。

    使用水平条形近似饼图效果（纯 ASCII 兼容所有终端）。

    参数:
        stats: compute_stats 返回的统计字典
        width: 图表宽度（字符数）

    返回:
        多行字符串，包含 ASCII 饼图
    """
    categories = stats.get("categories", {})
    total_files = stats.get("total_files", 0)
    total_size = stats.get("total_size", 0)

    if total_files == 0:
        return "(无数据)"

    # 按文件数量排序
    sorted_cats = sorted(
        categories.items(), key=lambda x: x[1]["count"], reverse=True
    )

    # 使用 Unicode 块字符绘制水平条形
    blocks = ["█", "▓", "▒", "░", "▪", "▫", "◆", "◇", "●", "○"]
    lines = []
    lines.append("┌" + "─" * (width + 2) + "┐")
    lines.append("│ 📊 文件类型分布（按数量）" + " " * max(0, width - 18) + " │")
    lines.append("├" + "─" * (width + 2) + "┤")

    max_count = sorted_cats[0][1]["count"] if sorted_cats else 1

    for i, (cat_name, data) in enumerate(sorted_cats):
        count = data["count"]
        pct = count / total_files * 100
        bar_len = int(count / max_count * width) if max_count > 0 else 0
        bar_len = max(1, bar_len)  # 至少显示 1 个字符

        block = blocks[i % len(blocks)]
        bar = block * bar_len

        # 格式：类别名 + 条形 + 百分比
        label = f"{cat_name:<12}"
        info = f" {pct:5.1f}% ({count})"
        line = f"│ {label}{bar}{'.' * (width - bar_len)}{info} │"
        lines.append(line)

    lines.append("└" + "─" * (width + 2) + "┘")

    # 按大小分布的饼图
    lines.append("")
    lines.append("┌" + "─" * (width + 2) + "┐")
    lines.append("│ 📦 空间占用分布（按大小）" + " " * max(0, width - 18) + " │")
    lines.append("├" + "─" * (width + 2) + "┤")

    sorted_by_size = sorted(
        categories.items(), key=lambda x: x[1]["size"], reverse=True
    )
    max_size = sorted_by_size[0][1]["size"] if sorted_by_size else 1

    for i, (cat_name, data) in enumerate(sorted_by_size):
        size = data["size"]
        pct = size / total_size * 100 if total_size > 0 else 0
        bar_len = int(size / max_size * width) if max_size > 0 else 0
        bar_len = max(1, bar_len)

        block = blocks[i % len(blocks)]
        bar = block * bar_len

        label = f"{cat_name:<12}"
        info = f" {pct:5.1f}% ({_format_size(size)})"
        line = f"│ {label}{bar}{'.' * (width - bar_len)}{info} │"
        lines.append(line)

    lines.append("└" + "─" * (width + 2) + "┘")

    return "\n".join(lines)


# ── ASCII 柱状图 ──────────────────────────────────────────────


def render_bar_chart(stats: dict, width: int = 40) -> str:
    """渲染 ASCII 垂直柱状图。

    参数:
        stats: compute_stats 返回的统计字典
        width: 图表宽度（字符数）

    返回:
        多行字符串，包含 ASCII 柱状图
    """
    categories = stats.get("categories", {})
    total_files = stats.get("total_files", 0)

    if total_files == 0:
        return "(无数据)"

    sorted_cats = sorted(
        categories.items(), key=lambda x: x[1]["count"], reverse=True
    )

    max_count = sorted_cats[0][1]["count"] if sorted_cats else 1
    max_bar_height = 12  # 最大柱高（行数）

    # 计算每个类别的柱高
    bars = []
    for cat_name, data in sorted_cats:
        count = data["count"]
        height = int(count / max_count * max_bar_height) if max_count > 0 else 0
        height = max(1, height)
        bars.append((cat_name, count, height))

    # 逐行绘制（从上到下）
    lines = []
    lines.append("📊 文件数量柱状图")
    lines.append("")

    for row in range(max_bar_height, 0, -1):
        line = "  "
        for cat_name, count, height in bars:
            if height >= row:
                line += "  ██   "
            else:
                line += "       "
        lines.append(line)

    # 底部分隔线
    separator = "  "
    for _ in bars:
        separator += "───────"
    lines.append(separator)

    # 类别名
    name_line = "  "
    for cat_name, count, height in bars:
        name_line += f"{cat_name[:6]:^7}"
    lines.append(name_line)

    # 数量
    count_line = "  "
    for cat_name, count, height in bars:
        count_line += f"{count:^7}"
    lines.append(count_line)

    return "\n".join(lines)


# ── Top-N 大文件排行 ─────────────────────────────────────────


def find_top_files(target_path: str, n: int = 10) -> list[dict]:
    """找出目录中最大的 N 个文件。

    参数:
        target_path: 目标目录路径
        n: 返回文件数量

    返回:
        按大小降序排列的文件信息列表
    """
    files = []
    target = Path(target_path)

    for root, _dirs, filenames in os.walk(target):
        for fname in filenames:
            fpath = Path(root) / fname
            try:
                stat = fpath.stat()
                files.append({
                    "path": str(fpath),
                    "name": fname,
                    "size": stat.st_size,
                    "size_human": _format_size(stat.st_size),
                })
            except (OSError, PermissionError):
                continue

    # 按大小降序排列，取前 N 个
    files.sort(key=lambda x: x["size"], reverse=True)
    return files[:n]


def render_top_files(files: list[dict], width: int = 60) -> str:
    """渲染 Top-N 大文件列表。

    参数:
        files: find_top_files 返回的文件列表
        width: 终端宽度

    返回:
        多行字符串，包含格式化的文件列表
    """
    if not files:
        return "(无文件)"

    max_size = files[0]["size"] if files else 1
    lines = []
    lines.append("📁 Top 大文件排行")
    lines.append("")

    for i, f in enumerate(files, 1):
        size = f["size"]
        name = f["name"]
        # 截断过长的文件名
        if len(name) > 30:
            name = name[:27] + "..."
        bar_len = int(size / max_size * 20) if max_size > 0 else 0
        bar_len = max(1, bar_len)
        bar = "█" * bar_len
        lines.append(f"  {i:>2}. {name:<30} {f['size_human']:>10}  {bar}")

    return "\n".join(lines)
