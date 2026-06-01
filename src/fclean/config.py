"""
fclean 配置系统模块。

负责加载、合并和验证 .fcleanrc YAML 配置文件。
支持从当前目录和用户目录自动检测配置文件。

用法:
    from fclean.config import Config, load_config

    config = load_config()          # 自动检测并加载
    config = load_config("/path")   # 从指定目录加载
"""

from pathlib import Path
from typing import Optional

import yaml

# 默认配置：与 rules.py 中的 CATEGORIES 一致
DEFAULT_CONFIG = {
    "rules": [
        {"category": "图片", "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp",
                                            ".bmp", ".svg", ".ico", ".tiff", ".tif",
                                            ".heic", ".heif", ".avif"]},
        {"category": "文档", "extensions": [".pdf", ".doc", ".docx", ".xls", ".xlsx",
                                            ".ppt", ".pptx", ".txt", ".md", ".csv",
                                            ".rtf", ".odt", ".ods", ".odp", ".pages",
                                            ".numbers", ".key", ".epub", ".mobi"]},
        {"category": "视频", "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv",
                                            ".flv", ".webm", ".m4v", ".3gp", ".mpeg",
                                            ".mpg"]},
        {"category": "音频", "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg",
                                            ".wma", ".m4a", ".opus", ".alac"]},
        {"category": "压缩包", "extensions": [".zip", ".rar", ".7z", ".tar", ".gz",
                                              ".bz2", ".xz", ".zst", ".tgz", ".tbz2"]},
        {"category": "代码", "extensions": [".py", ".js", ".ts", ".jsx", ".tsx",
                                            ".java", ".c", ".cpp", ".h", ".hpp",
                                            ".cs", ".go", ".rs", ".rb", ".php",
                                            ".swift", ".kt", ".scala", ".sh",
                                            ".bash", ".zsh", ".yaml", ".yml",
                                            ".json", ".xml", ".toml", ".ini",
                                            ".cfg", ".conf", ".sql", ".r", ".vue",
                                            ".svelte", ".css", ".scss", ".less",
                                            ".html", ".htm", ".dockerfile"]},
    ],
    "exclude_patterns": [],
    "exclude_dirs": [],
}

# 用户配置文件名
CONFIG_FILENAME = ".fcleanrc"


class Config:
    """fclean 配置对象，封装从 .fcleanrc 加载的配置。"""

    def __init__(self, data: Optional[dict] = None):
        """
        初始化配置。

        参数:
            data: 从 YAML 加载的原始配置字典。None 表示使用默认配置。
        """
        self._data = data or {}
        self._rules = self._parse_rules()
        self._exclude_patterns = self._data.get("exclude_patterns", []) or []
        self._exclude_dirs = self._data.get("exclude_dirs", []) or []

    def _parse_rules(self) -> dict[str, set[str]]:
        """解析 rules 配置为 {类别名: {扩展名集合}} 格式。"""
        raw_rules = self._data.get("rules") or DEFAULT_CONFIG["rules"]
        rules: dict[str, set[str]] = {}
        for rule in raw_rules:
            cat = rule.get("category", "其他")
            exts = set(e.lower() if e.startswith(".") else f".{e.lower()}"
                       for e in rule.get("extensions", []))
            if cat and exts:
                rules[cat] = exts
        return rules

    @property
    def rules(self) -> dict[str, set[str]]:
        """获取 {类别名: {扩展名集合}} 映射。"""
        return self._rules

    @property
    def exclude_patterns(self) -> list[str]:
        """获取排除文件模式列表。"""
        return self._exclude_patterns

    @property
    def exclude_dirs(self) -> list[str]:
        """获取排除目录名列表。"""
        return self._exclude_dirs

    def classify(self, filename: str) -> Optional[str]:
        """
        根据配置的规则对文件进行分类。

        参数:
            filename: 文件名（含扩展名）

        返回:
            类别名（如 "图片"），如果不匹配则返回 None
        """
        idx = filename.rfind(".")
        if idx == -1:
            return None
        ext = filename[idx:].lower()

        for cat_name, exts in self._rules.items():
            if ext in exts:
                return cat_name
        return None

    def to_dict(self) -> dict:
        """返回完整的配置字典（用于展示）。"""
        return {
            "rules": [
                {"category": cat, "extensions": sorted(list(exts))}
                for cat, exts in sorted(self._rules.items())
            ],
            "exclude_patterns": self._exclude_patterns,
            "exclude_dirs": self._exclude_dirs,
        }


def get_default_config() -> Config:
    """获取默认配置对象。"""
    return Config(DEFAULT_CONFIG)


def find_config_file(start_dir: Optional[str] = None) -> Optional[Path]:
    """
    查找 .fcleanrc 配置文件，优先级：当前目录 > 用户 home 目录。

    参数:
        start_dir: 起始搜索目录。默认为当前目录。

    返回:
        配置文件路径，没找到则返回 None
    """
    # 搜索顺序：当前目录 -> 用户 home 目录
    search_dirs = []
    if start_dir:
        search_dirs.append(Path(start_dir).expanduser().resolve())
    search_dirs.append(Path.cwd())
    search_dirs.append(Path.home())

    # 去重但保持顺序
    seen = set()
    for d in search_dirs:
        d = d.resolve()
        if d in seen:
            continue
        seen.add(d)
        config_path = d / CONFIG_FILENAME
        if config_path.exists() and config_path.is_file():
            return config_path

    return None


def load_config(path: Optional[str] = None) -> Config:
    """
    加载配置。如果有配置文件则加载并合并，否则返回默认配置。

    优先级: CLI 参数 > 配置文件 > 默认配置。

    参数:
        path: 指定目录路径（用于查找配置文件）

    返回:
        Config 对象
    """
    config_path = find_config_file(path)

    if config_path is None:
        return get_default_config()

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None or not isinstance(data, dict):
            return get_default_config()
        # 从默认配置开始，然后合并用户配置中的规则
        merged = dict(DEFAULT_CONFIG)
        if "rules" in data and isinstance(data["rules"], list):
            merged["rules"] = data["rules"]
        if "exclude_patterns" in data:
            merged["exclude_patterns"] = data["exclude_patterns"]
        if "exclude_dirs" in data:
            merged["exclude_dirs"] = data["exclude_dirs"]
        return Config(merged)
    except (yaml.YAMLError, OSError):
        return get_default_config()


def generate_example_config() -> str:
    """生成 .fcleanrc 示例配置文件内容。"""
    return """# fclean 配置文件 (.fcleanrc)
# 编辑此文件可自定义文件分类规则和排除模式。
#
# 配置优先级: CLI 参数 > .fcleanrc > 默认规则
#
# 存放位置:
#   - 当前工作目录的 .fcleanrc（优先级高）
#   - ~/.fcleanrc（用户全局，优先级低）
#
# 用法:
#   1. 运行 `fclean init` 生成此文件
#   2. 编辑规则
#   3. 运行 `fclean <path>` 按新规则整理

# === 文件分类规则 ===
# rules 是一个列表，每个规则包含:
#   - category: 目标目录名
#   - extensions: 属于该类别的文件扩展名列表
rules:
  # 图片类 — 默认目标目录: 图片/
  - category: 图片
    extensions:
      - .jpg
      - .jpeg
      - .png
      - .gif
      - .webp
      - .svg

  # 文档类 — 默认目标目录: 文档/
  - category: 文档
    extensions:
      - .pdf
      - .docx
      - .txt
      - .md
      - .csv

  # 视频类 — 默认目标目录: 视频/
  - category: 视频
    extensions:
      - .mp4
      - .mkv
      - .mov
      - .avi

  # 音频类 — 默认目标目录: 音频/
  - category: 音频
    extensions:
      - .mp3
      - .wav
      - .flac
      - .aac

  # 压缩包 — 默认目标目录: 压缩包/
  - category: 压缩包
    extensions:
      - .zip
      - .rar
      - .7z
      - .tar.gz

  # 代码类 — 默认目标目录: 代码/
  - category: 代码
    extensions:
      - .py
      - .js
      - .ts
      - .html
      - .css
      - .json
      - .yaml

  # === 你可以在这里添加自定义分类 ===
  # - category: 电子书
  #   extensions:
  #     - .epub
  #     - .mobi
  #     - .pdf

# === 排除模式 ===
# 整理时跳过匹配这些模式的文件（支持 glob 通配符）
exclude_patterns:
  # - "*.tmp"      # 跳过临时文件
  # - "*.log"      # 跳过日志文件
  # - "Thumbs.db"  # 跳过 Windows 缩略图缓存

# === 排除目录 ===
# 整理时跳过这些目录名
exclude_dirs:
  # - node_modules
  # - __pycache__
  # - .git
"""
