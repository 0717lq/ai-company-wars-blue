"""插件管理器 — 加载、注册、执行 fclean 插件生命周期。

负责：
1. 扫描插件目录（~/.fclean/plugins/）发现 .py 插件文件
2. 动态加载 PluginBase 子类并实例化
3. 提供 hook 执行接口（classify/transform/summarize）
4. 安装/卸载/列出插件

用法:
    manager = PluginManager()
    manager.discover_and_load()
    category = manager.run_classify(file_path)
"""

import importlib.util
import logging
import shutil
from pathlib import Path

from .plugin import PluginBase

# 插件默认目录
DEFAULT_PLUGIN_DIR = Path.home() / ".fclean" / "plugins"

logger = logging.getLogger("fclean.plugins")


class PluginManager:
    """插件管理器：加载、注册、执行插件 hook。"""

    def __init__(self, plugin_dir: Path | None = None):
        """初始化插件管理器。

        Args:
            plugin_dir: 插件目录路径，默认 ~/.fclean/plugins/
        """
        self.plugin_dir = plugin_dir or DEFAULT_PLUGIN_DIR
        self._plugins: dict[str, PluginBase] = {}  # name -> instance

    @property
    def plugins(self) -> dict[str, PluginBase]:
        """返回已加载的插件字典（只读副本）。"""
        return dict(self._plugins)

    def discover_and_load(self) -> int:
        """扫描插件目录并加载所有 .py 插件文件。

        Returns:
            成功加载的插件数量
        """
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            return 0

        loaded = 0
        for py_file in sorted(self.plugin_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue  # 跳过 __init__.py 等
            try:
                plugin = self._load_plugin_file(py_file)
                if plugin is not None:
                    self._plugins[plugin.name] = plugin
                    loaded += 1
                    logger.debug("已加载插件: %s v%s", plugin.name, plugin.version)
            except Exception as e:
                # 插件异常不影响主流程
                logger.warning("加载插件 %s 失败: %s", py_file.name, e)

        return loaded

    def _load_plugin_file(self, py_file: Path) -> PluginBase | None:
        """从单个 .py 文件加载插件实例。

        约定：文件中必须有一个继承 PluginBase 的类。
        如果有多个，取第一个。

        Args:
            py_file: .py 文件路径

        Returns:
            PluginBase 实例，或 None（无有效插件类）
        """
        spec = importlib.util.spec_from_file_location(
            f"fclean_plugin_{py_file.stem}", str(py_file)
        )
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.warning("执行插件文件 %s 时出错: %s", py_file.name, e)
            return None

        # 找到 PluginBase 子类并实例化
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PluginBase)
                and attr is not PluginBase
            ):
                try:
                    instance = attr()
                    return instance
                except Exception as e:
                    logger.warning("实例化插件类 %s 失败: %s", attr_name, e)
                    return None

        return None

    def install_plugin(self, source_path: Path) -> PluginBase:
        """安装插件文件到插件目录。

        Args:
            source_path: 源 .py 文件路径

        Returns:
            安装后加载的插件实例

        Raises:
            FileNotFoundError: 源文件不存在
            ValueError: 文件不是有效插件
        """
        if not source_path.exists():
            raise FileNotFoundError(f"插件文件不存在: {source_path}")

        if source_path.suffix != ".py":
            raise ValueError(f"插件文件必须是 .py 格式: {source_path}")

        # 确保插件目录存在
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

        # 先尝试加载验证
        plugin = self._load_plugin_file(source_path)
        if plugin is None:
            raise ValueError(f"文件中未找到 PluginBase 子类: {source_path}")

        # 复制到插件目录
        dest = self.plugin_dir / source_path.name
        shutil.copy2(str(source_path), str(dest))

        # 注册到内存
        self._plugins[plugin.name] = plugin
        logger.info("已安装插件: %s v%s", plugin.name, plugin.version)
        return plugin

    def uninstall_plugin(self, name: str) -> bool:
        """卸载插件。

        Args:
            name: 插件名称

        Returns:
            是否成功卸载
        """
        if name not in self._plugins:
            return False

        # 查找并删除插件文件
        for py_file in self.plugin_dir.glob("*.py"):
            try:
                plugin = self._load_plugin_file(py_file)
                if plugin and plugin.name == name:
                    py_file.unlink()
                    del self._plugins[name]
                    logger.info("已卸载插件: %s", name)
                    return True
            except Exception:
                continue

        # 内存中有但文件找不到，只清理内存
        del self._plugins[name]
        return True

    def get_plugin_info(self, name: str) -> dict | None:
        """获取指定插件的详细信息。

        Args:
            name: 插件名称

        Returns:
            插件信息字典，不存在返回 None
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            return None

        hooks = ["classify"]
        if type(plugin).transform is not PluginBase.transform:
            hooks.append("transform")
        if type(plugin).summarize is not PluginBase.summarize:
            hooks.append("summarize")

        return {
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.description,
            "hooks": hooks,
        }

    # ── Hook 执行接口 ──────────────────────────────────────────

    def run_classify(self, file_path: Path) -> str | None:
        """按优先级执行所有插件的 classify hook。

        返回第一个非 None 的分类结果。

        Args:
            file_path: 文件路径

        Returns:
            分类名，或 None（所有插件都不处理）
        """
        for plugin in self._plugins.values():
            try:
                result = plugin.classify(file_path)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning("插件 %s classify 失败: %s", plugin.name, e)
        return None

    def run_transform(self, file_path: Path, category: str) -> Path | None:
        """按优先级执行所有插件的 transform hook。

        返回第一个非 None 的目标路径。

        Args:
            file_path: 原始文件路径
            category: 分类名

        Returns:
            自定义目标路径，或 None（使用默认规则）
        """
        for plugin in self._plugins.values():
            try:
                result = plugin.transform(file_path, category)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning("插件 %s transform 失败: %s", plugin.name, e)
        return None

    def run_summarize(self, stats: dict) -> str | None:
        """按优先级执行所有插件的 summarize hook。

        返回第一个非 None 的报告文本。

        Args:
            stats: 统计结果字典

        Returns:
            报告文本，或 None（使用默认格式）
        """
        for plugin in self._plugins.values():
            try:
                result = plugin.summarize(stats)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning("插件 %s summarize 失败: %s", plugin.name, e)
        return None

    def list_plugins(self) -> list[dict]:
        """列出所有已加载插件的基本信息。"""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
            }
            for p in self._plugins.values()
        ]
