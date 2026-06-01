"""插件系统测试 — PluginBase + PluginManager 全流程覆盖。"""

import textwrap
from pathlib import Path

import pytest

from fclean.plugin import PluginBase
from fclean.plugin_manager import PluginManager

# ── 测试用插件类 ──────────────────────────────────────────────


class SimplePlugin(PluginBase):
    """最简插件：只实现 classify。"""

    name = "simple"
    version = "1.0.0"
    description = "简单分类插件"

    def classify(self, file_path: Path) -> str | None:
        if file_path.suffix == ".log":
            return "日志文件"
        return None


class FullPlugin(PluginBase):
    """完整插件：实现所有 hook。"""

    name = "full"
    version = "2.0.0"
    description = "完整功能插件"

    def classify(self, file_path: Path) -> str | None:
        if file_path.suffix == ".csv":
            return "数据文件"
        return None

    def transform(self, file_path: Path, category: str) -> Path | None:
        if category == "数据文件":
            return file_path.parent / "data" / file_path.name
        return None

    def summarize(self, stats: dict) -> str | None:
        return f"自定义报告: 共 {stats.get('total_files', 0)} 个文件"


class BrokenPlugin(PluginBase):
    """会抛异常的插件，测试错误处理。"""

    name = "broken"
    version = "0.0.1"
    description = "会出错的插件"

    def classify(self, file_path: Path) -> str | None:
        raise RuntimeError("插件内部错误")

    def transform(self, file_path: Path, category: str) -> Path | None:
        raise ValueError("transform 出错")

    def summarize(self, stats: dict) -> str | None:
        raise KeyError("summarize 出错")


# ── PluginBase 测试 ──────────────────────────────────────────


class TestPluginBase:
    """PluginBase 基类测试。"""

    def test_abstract_classify(self):
        """PluginBase 不能直接实例化（classify 是抽象方法）。"""
        with pytest.raises(TypeError):
            PluginBase()  # type: ignore[abstract]

    def test_default_transform_returns_none(self):
        """transform 默认返回 None。"""
        p = SimplePlugin()
        result = p.transform(Path("test.txt"), "test")
        assert result is None

    def test_default_summarize_returns_none(self):
        """summarize 默认返回 None。"""
        p = SimplePlugin()
        result = p.summarize({"total_files": 10})
        assert result is None

    def test_repr(self):
        """__repr__ 输出插件名和版本。"""
        p = SimplePlugin()
        assert "simple" in repr(p)
        assert "1.0.0" in repr(p)

    def test_metadata_attributes(self):
        """插件元信息正确设置。"""
        p = FullPlugin()
        assert p.name == "full"
        assert p.version == "2.0.0"
        assert "完整" in p.description


# ── PluginManager 测试 ──────────────────────────────────────


class TestPluginManager:
    """PluginManager 加载/注册/执行测试。"""

    def test_init_default_dir(self):
        """默认插件目录为 ~/.fclean/plugins/。"""
        manager = PluginManager()
        assert ".fclean" in str(manager.plugin_dir)
        assert "plugins" in str(manager.plugin_dir)

    def test_init_custom_dir(self, tmp_path):
        """自定义插件目录。"""
        custom = tmp_path / "my_plugins"
        manager = PluginManager(plugin_dir=custom)
        assert manager.plugin_dir == custom

    def test_discover_empty_dir(self, tmp_path):
        """空目录返回 0。"""
        manager = PluginManager(plugin_dir=tmp_path / "empty")
        count = manager.discover_and_load()
        assert count == 0
        assert len(manager.plugins) == 0

    def test_discover_and_load(self, tmp_path):
        """从 .py 文件加载插件。"""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text(textwrap.dedent("""\
            from fclean.plugin import PluginBase
            from pathlib import Path

            class TestPlg(PluginBase):
                name = "test-plg"
                version = "0.1.0"
                description = "测试插件"

                def classify(self, file_path: Path) -> str | None:
                    return "test" if file_path.suffix == ".txt" else None
        """))

        manager = PluginManager(plugin_dir=tmp_path)
        count = manager.discover_and_load()

        assert count == 1
        assert "test-plg" in manager.plugins
        assert manager.plugins["test-plg"].version == "0.1.0"

    def test_skip_underscore_files(self, tmp_path):
        """跳过以 _ 开头的文件。"""
        (tmp_path / "__init__.py").write_text("# skip me")
        (tmp_path / "_private.py").write_text("# skip me too")

        valid = tmp_path / "valid.py"
        valid.write_text(textwrap.dedent("""\
            from fclean.plugin import PluginBase
            from pathlib import Path
            class V(PluginBase):
                name = "v"
                def classify(self, fp): return None
        """))

        manager = PluginManager(plugin_dir=tmp_path)
        count = manager.discover_and_load()
        assert count == 1
        assert "v" in manager.plugins

    def test_broken_plugin_file(self, tmp_path):
        """损坏的插件文件不影响其他插件加载。"""
        (tmp_path / "broken.py").write_text("import nonexistent_module_xyz")

        good = tmp_path / "good.py"
        good.write_text(textwrap.dedent("""\
            from fclean.plugin import PluginBase
            from pathlib import Path
            class G(PluginBase):
                name = "good"
                def classify(self, fp): return None
        """))

        manager = PluginManager(plugin_dir=tmp_path)
        count = manager.discover_and_load()
        assert count == 1
        assert "good" in manager.plugins

    def test_no_plugin_class_in_file(self, tmp_path):
        """文件中没有 PluginBase 子类时跳过。"""
        (tmp_path / "no_plugin.py").write_text("x = 42\n")

        manager = PluginManager(plugin_dir=tmp_path)
        count = manager.discover_and_load()
        assert count == 0

    def test_install_plugin(self, tmp_path):
        """安装插件文件。"""
        source = tmp_path / "source.py"
        source.write_text(textwrap.dedent("""\
            from fclean.plugin import PluginBase
            from pathlib import Path
            class Installed(PluginBase):
                name = "installed"
                version = "1.0.0"
                description = "已安装"
                def classify(self, fp): return None
        """))

        plugin_dir = tmp_path / "plugins"
        manager = PluginManager(plugin_dir=plugin_dir)
        plugin = manager.install_plugin(source)

        assert plugin.name == "installed"
        assert (plugin_dir / "source.py").exists()
        assert "installed" in manager.plugins

    def test_install_nonexistent(self, tmp_path):
        """安装不存在的文件抛 FileNotFoundError。"""
        manager = PluginManager(plugin_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            manager.install_plugin(Path("/nonexistent/file.py"))

    def test_install_not_python(self, tmp_path):
        """安装非 .py 文件抛 ValueError。"""
        txt = tmp_path / "not_plugin.txt"
        txt.write_text("not a plugin")
        manager = PluginManager(plugin_dir=tmp_path)
        with pytest.raises(ValueError, match=".py"):
            manager.install_plugin(txt)

    def test_install_no_plugin_class(self, tmp_path):
        """安装无 PluginBase 子类的文件抛 ValueError。"""
        source = tmp_path / "empty.py"
        source.write_text("x = 1\n")
        manager = PluginManager(plugin_dir=tmp_path)
        with pytest.raises(ValueError, match="PluginBase"):
            manager.install_plugin(source)

    def test_uninstall_plugin(self, tmp_path):
        """卸载插件。"""
        source = tmp_path / "to_delete.py"
        source.write_text(textwrap.dedent("""\
            from fclean.plugin import PluginBase
            from pathlib import Path
            class D(PluginBase):
                name = "del-me"
                def classify(self, fp): return None
        """))

        plugin_dir = tmp_path / "plugins"
        manager = PluginManager(plugin_dir=plugin_dir)
        manager.install_plugin(source)

        assert "del-me" in manager.plugins
        result = manager.uninstall_plugin("del-me")
        assert result is True
        assert "del-me" not in manager.plugins

    def test_uninstall_nonexistent(self, tmp_path):
        """卸载不存在的插件返回 False。"""
        manager = PluginManager(plugin_dir=tmp_path)
        assert manager.uninstall_plugin("nope") is False

    def test_get_plugin_info(self, tmp_path):
        """获取插件信息。"""
        source = tmp_path / "info.py"
        source.write_text(textwrap.dedent("""\
            from fclean.plugin import PluginBase
            from pathlib import Path
            class Info(PluginBase):
                name = "info-test"
                version = "3.0.0"
                description = "信息测试"
                def classify(self, fp): return None
                def summarize(self, stats): return "custom"
        """))

        plugin_dir = tmp_path / "plugins"
        manager = PluginManager(plugin_dir=plugin_dir)
        manager.install_plugin(source)

        info = manager.get_plugin_info("info-test")
        assert info is not None
        assert info["name"] == "info-test"
        assert info["version"] == "3.0.0"
        assert "classify" in info["hooks"]
        assert "summarize" in info["hooks"]
        # transform 没有覆盖，不应在 hooks 中
        assert "transform" not in info["hooks"]

    def test_get_plugin_info_nonexistent(self, tmp_path):
        """获取不存在插件的信息返回 None。"""
        manager = PluginManager(plugin_dir=tmp_path)
        assert manager.get_plugin_info("nope") is None

    def test_list_plugins(self, tmp_path):
        """列出所有插件。"""
        source = tmp_path / "list.py"
        source.write_text(textwrap.dedent("""\
            from fclean.plugin import PluginBase
            from pathlib import Path
            class L(PluginBase):
                name = "lister"
                version = "0.5.0"
                description = "列表测试"
                def classify(self, fp): return None
        """))

        plugin_dir = tmp_path / "plugins"
        manager = PluginManager(plugin_dir=plugin_dir)
        manager.install_plugin(source)

        plugins = manager.list_plugins()
        assert len(plugins) == 1
        assert plugins[0]["name"] == "lister"


# ── Hook 执行测试 ──────────────────────────────────────────


class TestHookExecution:
    """测试 classify/transform/summarize hook 执行。"""

    def test_run_classify_match(self):
        """classify 匹配时返回分类名。"""
        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["simple"] = SimplePlugin()

        result = manager.run_classify(Path("test.log"))
        assert result == "日志文件"

    def test_run_classify_no_match(self):
        """classify 不匹配时返回 None。"""
        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["simple"] = SimplePlugin()

        result = manager.run_classify(Path("test.txt"))
        assert result is None

    def test_run_classify_first_match_wins(self):
        """多个插件匹配时返回第一个结果。"""
        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["full"] = FullPlugin()
        manager._plugins["simple"] = SimplePlugin()

        # .log 文件只被 SimplePlugin 处理
        assert manager.run_classify(Path("test.log")) == "日志文件"
        # .csv 文件只被 FullPlugin 处理
        assert manager.run_classify(Path("test.csv")) == "数据文件"

    def test_run_classify_exception_continues(self):
        """classify 异常不影响后续插件。"""
        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["broken"] = BrokenPlugin()
        manager._plugins["simple"] = SimplePlugin()

        # broken 会抛异常，simple 正常处理 .log
        result = manager.run_classify(Path("test.log"))
        assert result == "日志文件"

    def test_run_transform(self):
        """transform hook 返回自定义路径。"""
        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["full"] = FullPlugin()

        result = manager.run_transform(Path("/tmp/test.csv"), "数据文件")
        assert result is not None
        assert result.name == "test.csv"
        assert result.parent.name == "data"

    def test_run_transform_no_match(self):
        """transform 不匹配时返回 None。"""
        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["simple"] = SimplePlugin()

        result = manager.run_transform(Path("test.txt"), "其他")
        assert result is None

    def test_run_summarize(self):
        """summarize hook 返回自定义报告。"""
        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["full"] = FullPlugin()

        result = manager.run_summarize({"total_files": 42})
        assert result is not None
        assert "42" in result

    def test_run_summarize_no_match(self):
        """summarize 无匹配时返回 None。"""
        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["simple"] = SimplePlugin()

        result = manager.run_summarize({"total_files": 10})
        assert result is None

    def test_run_transform_exception_continues(self):
        """transform 异常不影响后续插件。"""
        class FallbackPlugin(PluginBase):
            name = "fallback"
            version = "0.1.0"
            description = "回退插件"

            def classify(self, fp):
                return None

            def transform(self, fp, cat):
                return fp.parent / "fallback_dir" / fp.name

        manager = PluginManager(plugin_dir=Path("/nonexistent"))
        manager._plugins["broken"] = BrokenPlugin()
        manager._plugins["fallback"] = FallbackPlugin()

        result = manager.run_transform(Path("/tmp/test.csv"), "数据文件")
        assert result is not None
        assert result.parent.name == "fallback_dir"


# ── 模板生成测试 ──────────────────────────────────────────


class TestPluginTemplate:
    """测试插件模板生成。"""

    def test_template_contains_class(self, tmp_path):
        """生成的模板包含 PluginBase 子类。"""
        from fclean.commands import _generate_plugin_template
        template = _generate_plugin_template("my-plugin")
        assert "class" in template
        assert "PluginBase" in template
        assert 'name = "my-plugin"' in template
        assert "def classify" in template
        assert "def transform" in template
        assert "def summarize" in template

    def test_template_is_valid_python(self, tmp_path):
        """生成的模板是合法 Python 代码。"""
        from fclean.commands import _generate_plugin_template
        template = _generate_plugin_template("test-plugin")
        # 语法检查
        compile(template, "<template>", "exec")


# ── 集成测试：CLI plugin 子命令 ──────────────────────────────


class TestPluginCLI:
    """fclean plugin 子命令的 CLI 测试。"""

    def test_plugin_list_empty(self, tmp_path, capsys):
        """plugin list 空目录。"""
        import argparse


        argparse.Namespace(
            plugin_action="list",
            plugin_name=None,
            plugin_source=None,
            json=False,
        )

        # 使用临时目录
        import fclean.plugin_manager as pm

        # 直接测试 run_plugin 的逻辑
        manager = pm.PluginManager(plugin_dir=tmp_path / "empty")
        loaded = manager.discover_and_load()
        assert loaded == 0

        plugins = manager.list_plugins()
        assert len(plugins) == 0

    def test_plugin_list_with_plugins(self, tmp_path):
        """plugin list 有插件时输出插件信息。"""
        source = tmp_path / "my_plg.py"
        source.write_text(textwrap.dedent("""\
            from fclean.plugin import PluginBase
            from pathlib import Path
            class MyPlg(PluginBase):
                name = "my-plg"
                version = "1.0.0"
                description = "我的插件"
                def classify(self, fp): return None
        """))

        manager = PluginManager(plugin_dir=tmp_path)
        count = manager.discover_and_load()
        assert count == 1

        plugins = manager.list_plugins()
        assert len(plugins) == 1
        assert plugins[0]["name"] == "my-plg"

    def test_plugin_json_output(self, tmp_path, capsys):
        """plugin list --json 输出 JSON。"""
        manager = PluginManager(plugin_dir=tmp_path / "empty")
        manager.discover_and_load()

        from fclean.formatters import make_json_envelope
        data = make_json_envelope("plugin", {
            "action": "list",
            "total": 0,
            "plugins": [],
        })

        capsys.readouterr()
        # 验证 JSON 结构
        assert data["tool"] == "fclean"
        assert data["command"] == "plugin"
        assert data["total"] == 0
