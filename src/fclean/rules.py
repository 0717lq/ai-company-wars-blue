"""
fclean 分类规则模块。

定义文件扩展名到类别文件夹的映射关系。
支持有序匹配（优先匹配更具体的规则）。
同时支持 Config 对象驱动规则（优先级更高）。

用法:
    from fclean.rules import classify, get_category_name

    category = classify("photo.jpg")  # 返回 "图片"
    cn_name = get_category_name("image")  # 返回 "图片"
"""

from typing import Optional

from fclean.config import Config

# 类别定义（有序——先匹配的优先）
# key 是内部别名，value 包含目录名、扩展名列表
CATEGORIES = [
    {
        "key": "image",
        "dir_name": "图片",
        "extensions": {
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
            ".svg", ".ico", ".tiff", ".tif", ".heic", ".heif",
            ".avif",
        },
    },
    {
        "key": "document",
        "dir_name": "文档",
        "extensions": {
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt",
            ".pptx", ".txt", ".md", ".csv", ".rtf", ".odt",
            ".ods", ".odp", ".pages", ".numbers", ".key",
            ".epub", ".mobi",
        },
    },
    {
        "key": "video",
        "dir_name": "视频",
        "extensions": {
            ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv",
            ".webm", ".m4v", ".3gp", ".mpeg", ".mpg",
        },
    },
    {
        "key": "audio",
        "dir_name": "音频",
        "extensions": {
            ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
            ".m4a", ".opus", ".alac",
        },
    },
    {
        "key": "archive",
        "dir_name": "压缩包",
        "extensions": {
            ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
            ".xz", ".zst", ".tgz", ".tbz2",
        },
    },
    {
        "key": "code",
        "dir_name": "代码",
        "extensions": {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java",
            ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs",
            ".rb", ".php", ".swift", ".kt", ".scala", ".sh",
            ".bash", ".zsh", ".yaml", ".yml", ".json", ".xml",
            ".toml", ".ini", ".cfg", ".conf", ".sql", ".r",
            ".vue", ".svelte", ".css", ".scss", ".less",
            ".html", ".htm", ".dockerfile", ".makefile",
        },
    },
]

# 通过扩展名快速查找类别（构建反向查找表）
EXTENSION_TO_CATEGORY: dict[str, dict] = {}
for cat in CATEGORIES:
    for ext in cat["extensions"]:
        EXTENSION_TO_CATEGORY[ext.lower()] = cat


def classify(filename: str, config: Optional[Config] = None) -> Optional[str]:
    """
    根据文件名返回类别 key。
    如果提供了 Config 对象，优先使用配置中的规则。

    参数:
        filename: 文件名（含扩展名）
        config: 可选的自定义配置对象

    返回:
        类别 key（如 "image"），如果不是已知类型则返回 None
    """
    # 如果有自定义配置，优先用配置中的规则
    if config is not None:
        cat_name = config.classify(filename)
        if cat_name is not None:
            # 将中文类别名映射回内部 key
            for cat in CATEGORIES:
                if cat["dir_name"] == cat_name:
                    return cat["key"]
            # 对于自定义配置中的新类别，直接返回目录名
            return cat_name

    # 使用默认规则
    idx = filename.rfind(".")
    if idx == -1:
        return None
    ext = filename[idx:].lower()
    cat = EXTENSION_TO_CATEGORY.get(ext)
    return cat["key"] if cat else None


def get_dir_name(category_key: str, config: Optional[Config] = None) -> str:
    """
    根据类别 key 返回中文目录名。
    如果提供了 Config，也检查配置中的类别（用于自定义规则）。

    参数:
        category_key: 类别 key（如 "image"）
        config: 可选的自定义配置对象

    返回:
        中文目录名（如 "图片"）
    """
    # 先检查默认类别
    for cat in CATEGORIES:
        if cat["key"] == category_key:
            return cat["dir_name"]

    # 如果是自定义配置中的类别名，直接作为目录名返回
    if config is not None and category_key in config.rules:
        return category_key

    return "其他"


def get_all_categories(config: Optional[Config] = None) -> list[dict]:
    """
    返回所有类别定义的副本。
    如果提供了 Config，合并自定义分类到结果中。

    参数:
        config: 可选的自定义配置对象

    返回:
        类别定义列表
    """
    cats = list(CATEGORIES)

    # 合并自定义配置中的类别
    if config is not None:
        existing_dirs = {c["dir_name"] for c in cats}
        for cat_name, exts in config.rules.items():
            if cat_name not in existing_dirs:
                cats.append({
                    "key": cat_name,
                    "dir_name": cat_name,
                    "extensions": exts,
                })
                existing_dirs.add(cat_name)

    return cats
