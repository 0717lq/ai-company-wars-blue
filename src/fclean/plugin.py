"""插件基类定义 — fclean 插件系统的核心接口。

所有 fclean 插件必须继承 PluginBase 并实现 hook 方法。
与红队 dirsort 的区别：蓝队插件支持 transform hook，
不仅能分类文件，还能自定义文件的移动目标路径。

示例:
    class DatePlugin(PluginBase):
        name = "date-sorter"
        version = "1.0.0"
        description = "按文件修改日期分类"

        def classify(self, file_path: Path) -> str | None:
            import datetime
            mtime = datetime.date.fromtimestamp(file_path.stat().st_mtime)
            return f"日期/{mtime.strftime('%Y-%m')}"
"""

from abc import ABC, abstractmethod
from pathlib import Path


class PluginBase(ABC):
    """fclean 插件抽象基类。

    所有自定义插件必须继承此类并实现以下 hook：
    - classify: 自定义文件分类规则（必须）
    - transform: 自定义文件移动目标路径（可选）
    - summarize: 自定义统计报告格式（可选）

    hook 执行顺序:
        1. classify(file_path) → 返回分类名或 None
        2. transform(file_path, category) → 返回目标路径或 None
        3. summarize(stats) → 返回报告文本或 None

    返回 None 表示"我不处理这个，交给下一个插件或内置规则"。
    """

    # 插件元信息（子类必须覆盖）
    name: str = "unnamed-plugin"
    version: str = "0.0.0"
    description: str = "未描述的插件"

    @abstractmethod
    def classify(self, file_path: Path) -> str | None:
        """对单个文件进行分类。

        Args:
            file_path: 文件路径

        Returns:
            分类名称字符串（如 "图片"、"文档"），返回 None 表示
            本插件不处理此文件，交给下一个插件或内置规则。
        """

    def transform(self, file_path: Path, category: str) -> Path | None:
        """自定义文件的移动目标路径。

        在 classify 确定分类后调用，允许插件覆盖默认的
        目标目录。例如：按日期子目录细分、按项目名分组等。

        Args:
            file_path: 原始文件路径
            category: classify 返回的分类名

        Returns:
            自定义的目标路径（含文件名），返回 None 表示
            使用默认的目标路径规则。
        """
        return None

    def summarize(self, stats: dict) -> str | None:
        """生成自定义统计报告。

        Args:
            stats: 统计结果字典，包含 categories、total_files、total_size 等

        Returns:
            报告文本，返回 None 表示使用默认报告格式。
        """
        return None

    def __repr__(self) -> str:
        return f"<Plugin '{self.name}' v{self.version}>"
