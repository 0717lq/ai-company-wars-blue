"""
fcleanignore — .fcleanignore 文件解析器。

类似 .gitignore 的忽略规则：
- 每行一个 glob 模式
- # 开头为注释
- 空行被忽略
- 支持 *、**、? 通配符
- 支持 ! 前缀取反（不忽略匹配文件）

用法:
    ignore = load_ignore_rules("/path/to/dir")
    ignore.matches("debug.log")     # True（如果 .fcleanignore 里有 *.log）
    ignore.matches("readme.md")     # False
"""

import fnmatch
from pathlib import Path
from typing import Optional

# 默认忽略文件名
IGNORE_FILENAME = ".fcleanignore"


class IgnoreRules:
    """忽略规则集合，支持正向匹配和 ! 取反。"""

    def __init__(self, patterns: list[str], source: Optional[Path] = None):
        """
        参数:
            patterns: glob 模式列表（原始行，含 # 注释和空行）
            source: .fcleanignore 文件路径（可选，用于错误信息）
        """
        self.source = source
        # 分离正向模式和取反模式
        self._patterns: list[str] = []
        self._negations: list[str] = []

        for raw in patterns:
            line = raw.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            if line.startswith("!"):
                self._negations.append(line[1:])
            else:
                self._patterns.append(line)

    def matches(self, filepath: str) -> bool:
        """
        判断文件路径是否应被忽略。

        参数:
            filepath: 相对于忽略文件所在目录的路径（如 "debug.log" 或 "subdir/file.txt"）

        返回:
            True 表示应忽略该文件
        """
        # 统一用 / 分隔
        filepath = filepath.replace("\\", "/")

        # 1. 正向匹配：任一模式命中则忽略
        ignored = False
        for pattern in self._patterns:
            if self._match_pattern(pattern, filepath):
                ignored = True
                break

        # 2. 取反匹配：! 模式命中则不忽略（覆盖正向）
        if ignored:
            for neg in self._negations:
                if self._match_pattern(neg, filepath):
                    ignored = False
                    break

        return ignored

    def _match_pattern(self, pattern: str, filepath: str) -> bool:
        """用 glob 模式匹配路径。"""
        # 统一路径分隔
        pattern = pattern.replace("\\", "/")
        filepath = filepath.replace("\\", "/")

        # 目录模式：以 / 结尾表示只匹配目录名
        if pattern.endswith("/"):
            # 去掉尾部 /，对每一级目录名做匹配
            dir_pattern = pattern.rstrip("/")
            parts = filepath.split("/")
            for part in parts:
                if fnmatch.fnmatch(part, dir_pattern):
                    return True
            return False

        # 包含 / 的模式：对完整路径做 fnmatch（类似 gitignore 的路径匹配）
        if "/" in pattern:
            return fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(
                filepath, f"*/{pattern}"
            )

        # 纯文件名模式：对路径中每个部分做 fnmatch
        # 这样 *.log 能匹配 "subdir/debug.log" 和 "debug.log"
        parts = filepath.split("/")
        for part in parts:
            if fnmatch.fnmatch(part, pattern):
                return True
        return False

    def filter_files(self, files: list[str]) -> list[str]:
        """过滤文件列表，返回不被忽略的文件。"""
        return [f for f in files if not self.matches(f)]

    @property
    def has_rules(self) -> bool:
        """是否有有效的忽略规则。"""
        return len(self._patterns) > 0

    def __repr__(self) -> str:
        return f"IgnoreRules(patterns={self._patterns}, negations={self._negations})"


def load_ignore_rules(directory: str | Path) -> IgnoreRules:
    """
    加载目录下的 .fcleanignore 文件。

    参数:
        directory: 目录路径

    返回:
        IgnoreRules 实例（无文件时返回空规则）
    """
    dir_path = Path(directory)
    ignore_file = dir_path / IGNORE_FILENAME

    if not ignore_file.exists():
        return IgnoreRules([])

    try:
        lines = ignore_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return IgnoreRules([])

    return IgnoreRules(lines, source=ignore_file)
