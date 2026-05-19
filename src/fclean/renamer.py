"""
fclean 批量重命名模块。

支持通过 glob 模式匹配文件，按模板重命名。
模板变量：
  {n}       — 序列号（从 1 开始）
  {n:03d}   — 补零序列号（3 位）
  {date}    — 文件修改日期（YYYY-MM-DD）
  {ext}     — 原扩展名（小写）

用法:
    from fclean.renamer import RenamePlan, generate_rename_plan

    plan = generate_rename_plan(target_dir, "*.jpg", "vacation_{n:03d}")
    plan.execute()  # 执行重命名
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional


class RenameItem:
    """单个重命名项，记录旧路径和新路径。"""

    def __init__(self, old_path: Path, new_path: Path):
        self.old_path = old_path
        self.new_path = new_path

    def __repr__(self) -> str:
        return f"RenameItem({self.old_path.name} → {self.new_path.name})"


class RenamePlan:
    """
    重命名计划 — 包含匹配规则、待重命名列表、执行和回滚信息。

    属性:
        items: 重命名项列表
        directory: 目标目录
        pattern: glob 匹配模式
        format_template: 命名模板
        executed: 是否已执行
    """

    def __init__(self, directory: Path, pattern: str, format_template: str):
        self.directory = directory
        self.pattern = pattern
        self.format_template = format_template
        self.items: list[RenameItem] = []
        self.executed = False

    @property
    def total(self) -> int:
        """待重命名的文件数。"""
        return len(self.items)

    def execute(self) -> list[RenameItem]:
        """
        执行所有重命名操作。

        返回:
            成功重命名的 RenameItem 列表
        """
        executed: list[RenameItem] = []
        for item in self.items:
            try:
                # 确保目标路径的父目录存在
                item.new_path.parent.mkdir(parents=True, exist_ok=True)
                # 执行重命名
                item.old_path.rename(item.new_path)
                executed.append(item)
            except (PermissionError, OSError):
                # 跳过无法重命名的文件
                pass
        self.executed = True
        return executed

    def get_rename_pairs(self) -> list[tuple[Path, Path]]:
        """获取 (旧路径, 新路径) 列表，用于显示和 undo 记录。"""
        return [(item.old_path, item.new_path) for item in self.items]


def _match_glob_pattern(directory: Path, glob_pattern: str) -> list[Path]:
    """
    在目录中匹配 glob 模式的文件。

    参数:
        directory: 目标目录
        glob_pattern: glob 匹配模式（如 "*.jpg", "IMG_*.png"）

    返回:
        匹配的文件路径列表（按文件名排序）
    """
    # 使用 Path.glob() 匹配
    matched = list(directory.glob(glob_pattern))
    # 过滤掉目录，只保留文件
    matched = [p for p in matched if p.is_file()]
    # 按文件名排序，保证顺序一致
    matched.sort(key=lambda p: p.name)
    return matched


def _resolve_template(template: str, index: int, file_path: Path) -> str:
    """
    解析命名模板，替换模板变量。

    模板变量:
      {n}       — 序列号（从 1 开始）
      {n:03d}   — 补零 3 位（支持任意宽度，如 {n:05d}）
      {date}    — 文件修改日期（YYYY-MM-DD）
      {ext}     — 原扩展名（小写，含前导点号）

    参数:
        template: 命名模板
        index: 序列号（从 1 开始）
        file_path: 源文件路径（用于获取日期和扩展名）

    返回:
        解析后的文件名
    """
    # 处理 {n} 和 {n:03d} 等格式
    def replace_n(match):
        fmt = match.group(1)
        if fmt:
            # 如 {n:03d}
            width = fmt.replace("d", "").replace("0", "")
            if width:
                return f"{index:0{width}d}"
            else:
                return f"{index:03d}"
        else:
            return str(index)

    # 先处理 {n:xxx} 模式
    result = re.sub(r"\{n:(\d+d)\}", replace_n, template)
    # 再处理 {n} 模式
    result = re.sub(r"\{n\}", lambda m: str(index), result)

    # 替换 {date}
    if "{date}" in result:
        # 获取文件修改时间
        try:
            mtime = file_path.stat().st_mtime
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except OSError:
            date_str = datetime.now().strftime("%Y-%m-%d")
        result = result.replace("{date}", date_str)

    # 替换 {ext}
    if "{ext}" in result:
        ext = file_path.suffix.lower()  # 包含前导点号，如 ".jpg"
        result = result.replace("{ext}", ext)

    return result


def _ensure_unique_path(target_dir: Path, name: str) -> Path:
    """
    确保目标路径唯一——如果冲突则添加数字后缀。

    参数:
        target_dir: 目标目录
        name: 文件名

    返回:
        唯一的路径
    """
    dst = target_dir / name
    if not dst.exists():
        return dst

    # 从已有文件名提取 stem 和后缀
    stem = Path(name).stem
    ext = Path(name).suffix
    counter = 1
    while dst.exists():
        new_name = f"{stem}_{counter}{ext}"
        dst = target_dir / new_name
        counter += 1
    return dst


def generate_rename_plan(
    directory: Path,
    glob_pattern: str,
    format_template: str,
) -> RenamePlan:
    """
    生成重命名计划。

    流程：
    1. 在目录中匹配 glob 模式的所有文件
    2. 对每个匹配的文件，按模板生成新文件名
    3. 处理重名冲突（添加数字后缀）
    4. 返回 RenamePlan 对象（不执行）

    参数:
        directory: 目标目录
        glob_pattern: glob 匹配模式
        format_template: 命名模板（支持 {n}, {n:03d}, {date}, {ext}）

    返回:
        RenamePlan 对象，包含所有重命名项（尚未执行）

    异常:
        FileNotFoundError: 目录不存在
        NotADirectoryError: 路径不是目录
    """
    target_dir = Path(directory).expanduser().resolve()

    if not target_dir.exists():
        raise FileNotFoundError(f"目录不存在: {target_dir}")
    if not target_dir.is_dir():
        raise NotADirectoryError(f"不是目录: {target_dir}")

    # 匹配文件
    matched_files = _match_glob_pattern(target_dir, glob_pattern)

    plan = RenamePlan(target_dir, glob_pattern, format_template)

    # 对每个匹配的文件生成新文件名
    for idx, file_path in enumerate(matched_files, start=1):
        new_name = _resolve_template(format_template, idx, file_path)
        new_path = _ensure_unique_path(target_dir, new_name)
        plan.items.append(RenameItem(file_path, new_path))

    return plan
