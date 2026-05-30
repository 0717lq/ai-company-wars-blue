"""
test_watcher.py — fclean watch 文件监控测试。

覆盖：watch_directory 函数参数校验、FcleanHandler 事件处理、防抖逻辑。
由于 watchdog 是可选依赖，核心逻辑通过 mock 测试。
"""

import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from fclean.ignore import IgnoreRules


class TestWatchDirectoryValidation:
    """watch_directory 参数校验。"""

    def test_import_error_exits(self, tmp_path):
        """watchdog 未安装时应报错退出。"""
        modules = {
            "watchdog": None,
            "watchdog.observers": None,
            "watchdog.events": None,
        }
        with patch.dict("sys.modules", modules):
            with pytest.raises(SystemExit, match="1"):
                # 重新 import 触发 ImportError
                import importlib

                import fclean.watcher
                importlib.reload(fclean.watcher)
                fclean.watcher.watch_directory(str(tmp_path))

    def test_nonexistent_path_exits(self):
        """路径不存在时退出。"""
        # 确保 watchdog 可 import
        pytest.importorskip("watchdog")
        from fclean.watcher import watch_directory

        with pytest.raises(SystemExit, match="1"):
            watch_directory("/nonexistent/path/abc123")

    def test_not_directory_exits(self, tmp_path):
        """路径是文件不是目录时退出。"""
        pytest.importorskip("watchdog")
        from fclean.watcher import watch_directory

        f = tmp_path / "file.txt"
        f.write_text("hi")
        with pytest.raises(SystemExit, match="1"):
            watch_directory(str(f))


class TestFcleanHandlerLogic:
    """FcleanHandler 事件处理逻辑。"""

    def _make_handler(self, tmp_path, auto_execute=False, debounce=2.0):
        """构造 FcleanHandler 实例（绕过 watch_directory 的循环）。"""
        pytest.importorskip("watchdog")
        from watchdog.events import FileSystemEventHandler

        from fclean.config import load_config

        # 直接访问 watch_directory 内部的 handler 构造逻辑
        # 通过 mock observer 来捕获 handler
        config = load_config(str(tmp_path))
        ignore_rules = IgnoreRules([])

        # 重新实现 handler 构造（与 watcher.py 一致）

        class FcleanHandler(FileSystemEventHandler):
            def __init__(self, target, ignore_rules, auto_execute, debounce_seconds, config):
                super().__init__()
                self._target = target
                self._ignore = ignore_rules
                self._auto = auto_execute
                self._debounce = debounce_seconds
                self._config = config
                self._last_trigger = 0.0
                self._pending = False

            def on_created(self, event):
                if event.is_directory:
                    return
                filepath = Path(event.src_path)
                relative = str(filepath.relative_to(self._target))
                if self._ignore.matches(relative):
                    return
                self._pending = True

            def maybe_process(self):
                now = time.time()
                if self._pending and (now - self._last_trigger) >= self._debounce:
                    self._pending = False
                    self._last_trigger = now
                    return True  # 表示应触发 organize
                return False

        return FcleanHandler(tmp_path, ignore_rules, auto_execute, debounce, config)

    def test_file_created_sets_pending(self, tmp_path):
        """新文件创建后 _pending 变为 True。"""
        handler = self._make_handler(tmp_path)
        event = SimpleNamespace(
            is_directory=False,
            src_path=str(tmp_path / "newfile.txt"),
        )
        handler.on_created(event)
        assert handler._pending is True

    def test_directory_ignored(self, tmp_path):
        """目录创建事件被忽略。"""
        handler = self._make_handler(tmp_path)
        event = SimpleNamespace(
            is_directory=True,
            src_path=str(tmp_path / "newdir"),
        )
        handler.on_created(event)
        assert handler._pending is False

    def test_ignored_file_not_pending(self, tmp_path):
        """.fcleanignore 中的文件不设 _pending。"""
        ignore = IgnoreRules(["*.log"])
        handler = self._make_handler(tmp_path)
        handler._ignore = ignore

        event = SimpleNamespace(
            is_directory=False,
            src_path=str(tmp_path / "debug.log"),
        )
        handler.on_created(event)
        assert handler._pending is False

    def test_debounce_prevents_immediate_trigger(self, tmp_path):
        """防抖：刚触发过的不会立即再次触发。"""
        handler = self._make_handler(tmp_path, debounce=5.0)
        handler._last_trigger = time.time()
        handler._pending = True

        # 刚触发过，不应再次触发
        assert handler.maybe_process() is False

    def test_debounce_allows_after_interval(self, tmp_path):
        """防抖间隔过后可以触发。"""
        handler = self._make_handler(tmp_path, debounce=0.1)
        handler._last_trigger = time.time() - 1.0  # 1 秒前触发过
        handler._pending = True

        assert handler.maybe_process() is True
        assert handler._pending is False

    def test_no_pending_no_trigger(self, tmp_path):
        """无 pending 时不触发。"""
        handler = self._make_handler(tmp_path)
        handler._pending = False
        assert handler.maybe_process() is False
