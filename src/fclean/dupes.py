"""
fclean dupes — 重复文件检测模块。

使用 SHA-256 哈希检测重复文件，支持：
- Size 预过滤（不同大小必不重复）
- 多线程并行哈希（最大 4 workers）
- rich.progress 进度条
- --min-size 跳过小文件
- --delete 安全删除（保留策略: newest/oldest/path）
- Undo 集成（删除操作可回滚）
- --json 结构化输出

用法:
    from fclean.dupes import find_duplicates

    result = find_duplicates("/path/to/folder")
    result.print_table()
    result.delete()  # 执行删除（保留策略: newest）
"""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _format_size(size_bytes: int) -> str:
    """将字节格式化为人类可读的大小。"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def _parse_size_arg(size_str: str) -> int:
    """解析大小参数，如 '1MB', '500KB', '2GB' 转为字节数。

    参数:
        size_str: 大小字符串

    返回:
        字节数
    """
    size_str = size_str.strip().upper()
    multipliers = {
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
        "K": 1024,
        "M": 1024 * 1024,
        "G": 1024 * 1024 * 1024,
    }
    for suffix, mult in sorted(multipliers.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(suffix):
            try:
                num = float(size_str[: -len(suffix)])
                return int(num * mult)  # type: ignore[return-value]
            except ValueError:
                raise ValueError(f"无法解析大小参数: {size_str}")
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"无法解析大小参数: {size_str}")


class DupesResult:
    """重复文件检测结果。"""

    def __init__(self):
        self.total_scanned: int = 0
        self.duplicate_groups: dict[str, list[Path]] = {}  # hash -> [paths]
        self.skipped_small: int = 0
        self.total_size_wasted: int = 0  # 可节省的字节数
        self.deleted: list[Path] = []  # 已删除的文件
        self.errors: list[tuple[str, str]] = []  # (path, error)
        self.min_size_bytes: int = 0
        self.scan_path: str = ""

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicate_groups) > 0

    @property
    def total_duplicate_files(self) -> int:
        """所有重复文件的数量（每组保留一个后冗余的文件数）。"""
        total = 0
        for paths in self.duplicate_groups.values():
            total += len(paths) - 1
        return total

    @property
    def total_duplicate_groups(self) -> int:
        return len(self.duplicate_groups)

    def to_dict(self) -> dict:
        """序列化为 dict，用于 JSON 输出和 undo 日志。"""
        groups = {}
        for file_hash, paths in self.duplicate_groups.items():
            group_paths = [str(p) for p in paths]
            try:
                size = paths[0].stat().st_size
            except OSError:
                size = 0
            groups[file_hash] = {
                "size_bytes": size,
                "size_human": _format_size(size),
                "files": group_paths,
                "count": len(group_paths),
            }

        return {
            "tool": "fclean",
            "command": "dupes",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": self.scan_path,
            "total_scanned": self.total_scanned,
            "skipped_small": self.skipped_small,
            "min_size_bytes": self.min_size_bytes,
            "duplicate_groups": len(groups),
            "duplicate_files": self.total_duplicate_files,
            "wasted_bytes": self.total_size_wasted,
            "wasted_human": _format_size(self.total_size_wasted),
            "groups": groups,
        }

    def to_json_str(self) -> str:
        """输出格式化的 JSON 字符串。"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def print_table(self):
        """用 rich 表格打印重复文件结果。"""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.text import Text
            from rich.panel import Panel
            console = Console()
            has_rich = True
        except ImportError:
            has_rich = False

        if not self.has_duplicates:
            if has_rich:
                console.print()
                console.print(Text("✅ 没有发现重复文件！", style="green"))
                console.print()
            else:
                print("\n✅ 没有发现重复文件！\n")
            return

        if has_rich:
            console.print()
            console.print(Text("🗂️  重复文件检测结果", style="bold cyan"))
            console.print(Text(
                f"扫描了 {self.total_scanned} 个文件，"
                f"发现 {self.total_duplicate_groups} 组重复，"
                f"共 {self.total_duplicate_files} 个冗余文件",
                style="yellow",
            ))
            if self.total_size_wasted > 0:
                console.print(Text(
                    f"可节省空间: {_format_size(self.total_size_wasted)}",
                    style="bold green",
                ))
            if self.skipped_small > 0:
                console.print(Text(
                    f"（跳过了 {self.skipped_small} 个小于 "
                    f"{_format_size(self.min_size_bytes)} 的文件）",
                    style="dim",
                ))
            console.print()

            for hash_val, paths in sorted(
                self.duplicate_groups.items(),
                key=lambda x: -x[1][0].stat().st_size if x[1][0].exists() else 0,
            ):
                try:
                    size = paths[0].stat().st_size
                except OSError:
                    size = 0

                panel = Panel(
                    f"[cyan]SHA-256:[/cyan] {hash_val[:16]}...\n"
                    f"[green]大小:[/green] {_format_size(size)}"
                    f"[yellow]  文件数:[/yellow] {len(paths)}",
                    title=f"重复组 #{list(self.duplicate_groups.keys()).index(hash_val) + 1}",
                )
                console.print(panel)

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("#", justify="right", style="dim", width=4)
                table.add_column("文件路径", style="white")

                for idx, p in enumerate(sorted(paths, key=lambda x: str(x)), 1):
                    table.add_row(str(idx), str(p))

                console.print(table)
                console.print()

            console.print(Text(
                "提示: 加 --delete 安全删除重复文件",
                style="dim",
            ))
            console.print(Text(
                "       --delete --strategy newest|oldest|path 选择保留策略",
                style="dim",
            ))
            console.print()
        else:
            print(f"\n🗂️  重复文件检测结果")
            print(f"扫描了 {self.total_scanned} 个文件，发现 {self.total_duplicate_groups} 组重复")
            if self.total_size_wasted > 0:
                print(f"可节省空间: {_format_size(self.total_size_wasted)}")
            print()

            for hash_val, paths in sorted(
                self.duplicate_groups.items(),
                key=lambda x: -x[1][0].stat().st_size if x[1][0].exists() else 0,
            ):
                print(f"  SHA-256: {hash_val[:16]}... ({_format_size(paths[0].stat().st_size)}, {len(paths)} files)")
                for p in sorted(paths, key=lambda x: str(x)):
                    print(f"    {p}")
                print()

            print("提示: 加 --delete 安全删除重复文件")

    def get_delete_plan(self, strategy: str = "newest") -> dict[str, list[tuple[Path, Path]]]:
        """生成删除计划：对每组重复，决定保留哪个文件，删除哪些文件。

        参数:
            strategy: 保留策略 — "newest" (默认, 保留最新的), "oldest" (保留最旧的), "path" (保留路径最先的)

        返回:
            {hash: [(保留路径, 要删除路径), ...]} 由于每组只保留一个，
            返回形式为 {hash: [(keep_path, delete_path_1), (keep_path, delete_path_2), ...]}
        """
        plan: dict[str, list[tuple[Path, Path]]] = {}

        for hash_val, paths in self.duplicate_groups.items():
            if len(paths) < 2:
                continue

            # 排序：按 mtime 或路径
            valid_paths = [p for p in paths if p.exists()]
            if len(valid_paths) < 2:
                continue

            if strategy == "newest":
                valid_paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            elif strategy == "oldest":
                valid_paths.sort(key=lambda p: p.stat().st_mtime)
            else:  # path
                valid_paths.sort(key=lambda p: str(p))

            keep = valid_paths[0]
            to_delete = valid_paths[1:]
            plan[hash_val] = [(keep, d) for d in to_delete]

        return plan

    def delete(
        self,
        strategy: str = "newest",
        interactive: bool = False,
    ) -> list[tuple[Path, Path]]:
        """执行删除操作。

        参数:
            strategy: 保留策略
            interactive: 是否逐组交互确认

        返回:
            [(keep_path, deleted_path)] 列表
        """
        plan = self.get_delete_plan(strategy)
        results: list[tuple[Path, Path]] = []

        for hash_val, pairs in plan.items():
            if not pairs:
                continue

            keep_path = pairs[0][0]
            to_delete_paths = [p for _, p in pairs]

            if interactive:
                print(f"\n重复组 (保留: {keep_path}):")
                for p in to_delete_paths:
                    print(f"    删除: {p}")
                response = input("删除这组文件? [Y/n] ").strip().lower()
                if response not in ("", "y", "yes"):
                    print("  跳过。")
                    continue

            for keep, delete_path in pairs:
                try:
                    os.remove(str(delete_path))
                    results.append((keep, delete_path))
                    self.deleted.append(delete_path)
                except (PermissionError, OSError) as e:
                    self.errors.append((str(delete_path), f"删除失败: {e}"))

        return results


def _hash_file(file_path: Path, chunk_size: int = 65536) -> Optional[str]:
    """计算文件的 SHA-256 哈希值。

    逐块读取，避免大文件一次性加载到内存。

    参数:
        file_path: 文件路径
        chunk_size: 每次读取的块大小 (默认 64KB)

    返回:
        SHA-256 十六进制字符串，失败则返回 None
    """
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, OSError):
        return None


def find_duplicates(
    target_path: str,
    min_size: Optional[str] = None,
    show_progress: bool = True,
) -> DupesResult:
    """查找指定目录中的重复文件。

    优化策略：
    1. 先收集所有文件大小，按 size 分组
    2. 只有同 size 的文件才需要哈希（不同大小必不重复）
    3. 多线程并行哈希（最大 4 workers）
    4. 按 hash 分组找出重复

    参数:
        target_path: 目标目录路径
        min_size: 最小文件大小（如 "1MB", "500KB"）
        show_progress: 是否显示进度条

    返回:
        DupesResult 对象
    """
    target = Path(target_path).expanduser().resolve()

    if not target.exists():
        raise FileNotFoundError(f"目录不存在: {target_path}")
    if not target.is_dir():
        raise NotADirectoryError(f"不是目录: {target_path}")

    min_size_bytes = 0
    if min_size:
        min_size_bytes = _parse_size_arg(min_size)

    result = DupesResult()
    result.scan_path = str(target)
    result.min_size_bytes = min_size_bytes

    # 第1步：扫描目录，收集所有文件
    files: list[Path] = []
    try:
        for entry in target.iterdir():
            if entry.name.startswith("."):
                continue
            if entry.is_file():
                files.append(entry)
    except PermissionError as e:
        raise PermissionError(f"没有权限读取目录 {target}: {e}")

    # 第2步：按 size 分组，跳过小文件
    size_groups: dict[int, list[Path]] = {}
    result.skipped_small = 0

    for f in files:
        try:
            fsize = f.stat().st_size
        except OSError:
            result.errors.append((str(f), "无法读取文件大小"))
            continue

        if min_size_bytes > 0 and fsize < min_size_bytes:
            result.skipped_small += 1
            continue

        # 跳过空文件
        if fsize == 0:
            continue

        size_groups.setdefault(fsize, []).append(f)

    result.total_scanned = len(files)

    # 第3步：对同 size 的文件进行哈希
    files_to_hash: list[Path] = []
    for size, paths in size_groups.items():
        if len(paths) > 1:
            files_to_hash.extend(paths)

    hash_map: dict[str, list[Path]] = {}

    if files_to_hash and show_progress:
        try:
            from rich.console import Console
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID

            console = Console()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"计算哈希 ({len(files_to_hash)} 个文件)...",
                    total=len(files_to_hash),
                )

                # 多线程哈希
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future_map = {
                        executor.submit(_hash_file, f): f for f in files_to_hash
                    }
                    for future in as_completed(future_map):
                        f = future_map[future]
                        try:
                            file_hash = future.result()
                            if file_hash:
                                hash_map.setdefault(file_hash, []).append(f)
                        except Exception as e:
                            result.errors.append((str(f), f"哈希计算失败: {e}"))
                        progress.advance(task)
        except ImportError:
            # 无 rich 时简单输出
            print(f"计算哈希 ({len(files_to_hash)} 个文件)...")
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_map = {
                    executor.submit(_hash_file, f): f for f in files_to_hash
                }
                for future in as_completed(future_map):
                    f = future_map[future]
                    try:
                        file_hash = future.result()
                        if file_hash:
                            hash_map.setdefault(file_hash, []).append(f)
                    except Exception:
                        pass
            print("完成。")
    else:
        # 无进度条模式
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_map = {
                executor.submit(_hash_file, f): f for f in files_to_hash
            }
            for future in as_completed(future_map):
                f = future_map[future]
                try:
                    file_hash = future.result()
                    if file_hash:
                        hash_map.setdefault(file_hash, []).append(f)
                except Exception:
                    pass

    # 第4步：筛选出有重复的组
    for file_hash, paths in hash_map.items():
        if len(paths) > 1:
            result.duplicate_groups[file_hash] = paths

    # 计算可节省空间
    for paths in result.duplicate_groups.values():
        try:
            size = paths[0].stat().st_size
        except OSError:
            size = 0
        result.total_size_wasted += size * (len(paths) - 1)

    return result
