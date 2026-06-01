"""
fclean 核心整理模块。

负责：
1. 扫描目录，收集文件信息
2. 按规则分类文件（支持从配置文件加载自定义规则）
3. 执行文件移动操作（或 dry-run 预览）
4. 统计整理结果

用法:
    from fclean.organizer import organize

    result = organize("/path/to/folder", dry_run=True)
    result = organize("/path/to/folder", execute=True)
"""
import shutil
from pathlib import Path
from typing import Optional

from fclean.config import Config
from fclean.rules import classify, get_dir_name


class FileInfo:
    """单个文件的信息。"""

    def __init__(self, path: Path, config: Optional[Config] = None):
        self.path = path
        self.name = path.name
        self.size = path.stat().st_size
        self.category_key = classify(path.name, config)
        # 如果使用自定义配置，用配置中的中文名
        if config is not None:
            # 查找配置中是否有该类别
            for cat_name, exts in config.rules.items():
                ext = path.suffix.lower()
                if ext in exts:
                    self.target_dir_name = cat_name
                    break
            else:
                self.target_dir_name = (
                    get_dir_name(self.category_key, config) if self.category_key else "其他"
                )
        else:
            self.target_dir_name = (
                get_dir_name(self.category_key) if self.category_key else "其他"
            )

    @property
    def is_known(self) -> bool:
        """是否是已知文件类型。"""
        return self.category_key is not None

    def __repr__(self) -> str:
        return f"FileInfo({self.name} -> {self.target_dir_name})"


class OrganizeResult:
    """整理操作的结果。"""

    def __init__(self):
        self.files_scanned: list[FileInfo] = []     # 扫描到的所有文件
        self.files_moved: list[tuple[FileInfo, Path]] = []  # (FileInfo, 目标路径)
        self.files_skipped: list[tuple[Path, str]] = [] # (路径, 跳过原因)
        self.errors: list[tuple[str, str]] = []     # (文件路径, 错误信息)
        self.scan_path: str = ""                    # 被扫描的目录路径（用于 JSON 输出）

    @property
    def total_scanned(self) -> int:
        return len(self.files_scanned)

    @property
    def total_moved(self) -> int:
        return len(self.files_moved)

    @property
    def total_skipped(self) -> int:
        return len(self.files_skipped)

    @property
    def total_errors(self) -> int:
        return len(self.errors)

    @property
    def total_size_moved(self) -> int:
        """已移动文件的总大小（字节）。"""
        return sum(fi.size for fi, _ in self.files_moved)

    def get_category_counts(self) -> dict[str, int]:
        """按类别统计移动的文件数量。"""
        counts: dict[str, int] = {}
        for fi, _ in self.files_moved:
            cat = fi.target_dir_name
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def get_category_sizes(self) -> dict[str, int]:
        """按类别统计移动的文件总大小。"""
        sizes: dict[str, int] = {}
        for fi, _ in self.files_moved:
            cat = fi.target_dir_name
            sizes[cat] = sizes.get(cat, 0) + fi.size
        return sizes

    def to_dict(self) -> dict:
        """序列化为 dict，用于 undo 日志。"""
        return {
            "files_moved": [
                {"source": str(fi.path), "target": str(dst)}
                for fi, dst in self.files_moved
            ],
            "category_counts": self.get_category_counts(),
            "total_moved": self.total_moved,
            "total_size": self.total_size_moved,
        }


def _should_exclude(
    name: str,
    is_dir: bool,
    exclude_patterns: Optional[list[str]],
    exclude_dirs: Optional[list[str]],
) -> bool:
    """
    判断文件或目录是否应该被排除。

    参数:
        name: 文件/目录名
        is_dir: 是否是目录
        exclude_patterns: 排除文件模式列表（支持 glob）
        exclude_dirs: 排除目录名列表

    返回:
        True 表示应该排除
    """
    # 检查排除目录
    if is_dir and exclude_dirs:
        if name in exclude_dirs or name.startswith("."):
            return True

    # 检查排除模式（简单后缀匹配）
    if exclude_patterns:
        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern in name:
                return True

    return False


def scan_directory(
    target_dir: Path,
    exclude_patterns: Optional[list[str]] = None,
    exclude_dirs: Optional[list[str]] = None,
    config: Optional[Config] = None,
) -> list[FileInfo]:
    """
    扫描目录，返回所有文件（不递归到子目录，只处理一级文件）。

    参数:
        target_dir: 要扫描的目录路径
        exclude_patterns: 排除的文件模式列表
        exclude_dirs: 排除的目录名列表
        config: 自定义配置（用于分类）

    返回:
        FileInfo 列表
    """
    if not target_dir.exists():
        raise FileNotFoundError(f"目录不存在: {target_dir}")
    if not target_dir.is_dir():
        raise NotADirectoryError(f"不是目录: {target_dir}")

    files: list[FileInfo] = []
    try:
        for entry in target_dir.iterdir():
            # 跳过隐藏文件和 fclean 自身的目录
            if entry.name.startswith("."):
                continue
            if entry.name in ("图片", "文档", "视频", "音频", "压缩包", "代码", "其他"):
                continue

            if entry.is_file():
                if _should_exclude(entry.name, False, exclude_patterns, exclude_dirs):
                    continue
                files.append(FileInfo(entry, config))
            elif entry.is_dir():
                if _should_exclude(entry.name, True, exclude_patterns, exclude_dirs):
                    continue
                # 跳过空的隐藏目录
                if not entry.name.startswith("."):
                    continue
    except PermissionError as e:
        raise PermissionError(f"没有权限读取目录 {target_dir}: {e}") from e

    return files


def _safe_move(fi: FileInfo, dst_dir: Path, result: OrganizeResult) -> bool:
    """
    安全移动文件：确保目标目录存在，不覆盖已有文件。

    参数:
        fi: 文件信息对象
        dst_dir: 目标目录
        result: 结果对象（记录错误）

    返回:
        True 表示移动成功，False 表示失败
    """
    try:
        # 创建目标目录
        dst_dir.mkdir(parents=True, exist_ok=True)

        dst = dst_dir / fi.name

        # 如果目标已存在，添加数字后缀
        if dst.exists():
            base = fi.path.stem
            ext = fi.path.suffix
            counter = 1
            while dst.exists():
                new_name = f"{base}_{counter}{ext}"
                dst = dst_dir / new_name
                counter += 1

        # 执行移动
        shutil.move(str(fi.path), str(dst))
        result.files_moved.append((fi, dst))
        return True
    except PermissionError as e:
        result.errors.append((str(fi.path), f"权限不足: {e}"))
        return False
    except OSError as e:
        result.errors.append((str(fi.path), f"文件操作错误: {e}"))
        return False


def organize(
    target_path: str,
    dry_run: bool = True,
    execute: bool = False,
    exclude: Optional[list[str]] = None,
    exclude_dirs: Optional[list[str]] = None,
    config: Optional[Config] = None,
) -> OrganizeResult:
    """
    整理指定目录的文件。

    流程：
    1. 加载配置（如果提供了 config 参数）
    2. 扫描目录获取文件列表
    3. 按扩展名分类到各类别
    4. 如果是 dry-run，只返回结果不移动
    5. 如果是 execute，实际移动文件
    6. 返回 OrganizeResult，包含详细统计

    参数:
        target_path: 要整理的目录路径
        dry_run: 是否只预览（默认 True）
        execute: 是否实际执行（为 True 时忽略 dry_run）
        exclude: 排除的文件模式
        exclude_dirs: 排除的目录名
        config: 自定义配置对象（用于分类）

    返回:
        OrganizeResult 对象
    """
    target = Path(target_path).expanduser().resolve()
    result = OrganizeResult()

    # 从配置中获取排除列表（如果 CLI 没有指定，使用配置中的值）
    effective_exclude = exclude if exclude else (
        config.exclude_patterns if config and config.exclude_patterns else None
    )
    effective_exclude_dirs = exclude_dirs if exclude_dirs else (
        config.exclude_dirs if config and config.exclude_dirs else None
    )

    # 扫描文件
    files = scan_directory(target, effective_exclude, effective_exclude_dirs, config)
    result.files_scanned = files

    if execute or not dry_run:
        # 实际执行移动操作
        for fi in files:
            # 已知类型的文件移动到对应分类目录
            if fi.category_key:
                dst_dir = target / fi.target_dir_name
                _safe_move(fi, dst_dir, result)
            else:
                # 未知类型放入"其他"
                dst_dir = target / "其他"
                _safe_move(fi, dst_dir, result)
    else:
        # dry-run：只记录拟移动的文件
        for fi in files:
            if fi.category_key:
                dst_dir = target / fi.target_dir_name
                result.files_moved.append((fi, dst_dir / fi.name))
            else:
                dst_dir = target / "其他"
                result.files_moved.append((fi, dst_dir / fi.name))

    return result


def compute_stats(
    target_path: str,
    config: Optional[Config] = None,
) -> dict:
    """
    计算指定目录的文件统计信息。

    参数:
        target_path: 目标目录路径
        config: 自定义配置（用于分类）

    返回:
        统计信息字典，包含:
        - total_files: 总文件数
        - total_size: 总大小（字节）
        - categories: {类别名: {"count": N, "size": N}} 按类分组
    """
    target = Path(target_path).expanduser().resolve()

    if not target.exists():
        raise FileNotFoundError(f"目录不存在: {target_path}")
    if not target.is_dir():
        raise NotADirectoryError(f"不是目录: {target_path}")

    # 构建类别统计
    categories: dict[str, dict] = {}
    total_files = 0
    total_size = 0

    for entry in target.iterdir():
        if entry.name.startswith("."):
            continue
        if entry.is_file():
            fi = FileInfo(entry, config)
            cat = fi.target_dir_name
            if cat not in categories:
                categories[cat] = {"count": 0, "size": 0}
            categories[cat]["count"] += 1
            categories[cat]["size"] += fi.size
            total_files += 1
            total_size += fi.size

    return {
        "total_files": total_files,
        "total_size": total_size,
        "categories": categories,
    }
