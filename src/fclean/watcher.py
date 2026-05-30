"""
fclean 文件监控模块 — 基于 watchdog 监听目录变化。

当目录中出现新文件时，自动触发 organize 逻辑。
默认 dry-run 模式（只报告），加 --auto 才真正执行。

用法:
    from fclean.watcher import watch_directory
    watch_directory("/path/to/dir", auto_execute=False)
"""

import sys
import time
from pathlib import Path
from typing import Optional

from fclean.config import Config, load_config
from fclean.ignore import IgnoreRules, load_ignore_rules
from fclean.organizer import organize


def watch_directory(
    target_path: str | Path,
    auto_execute: bool = False,
    debounce_seconds: float = 2.0,
    config: Optional[Config] = None,
    ignore_rules: Optional[IgnoreRules] = None,
    json_output: bool = False,
):
    """
    监听目录变化，新文件出现时触发 organize。

    参数:
        target_path: 目标目录路径
        auto_execute: True 时自动执行（默认 dry-run）
        debounce_seconds: 防抖时间（秒），避免文件还在写入时就触发
        config: fclean 配置对象
        ignore_rules: 忽略规则
        json_output: JSON 输出模式
    """
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("❌ watchdog 未安装。请执行: pip install fclean[watch]", file=sys.stderr)
        sys.exit(1)

    target = Path(target_path).resolve()
    if not target.exists() or not target.is_dir():
        print(f"❌ 路径不存在或不是目录: {target}", file=sys.stderr)
        sys.exit(1)

    if config is None:
        config = load_config(str(target))
    if ignore_rules is None:
        ignore_rules = load_ignore_rules(target)

    class FcleanHandler(FileSystemEventHandler):
        """处理文件系统事件，新文件出现时触发 organize。"""

        def __init__(self):
            super().__init__()
            self._last_trigger = 0.0
            self._pending = False

        def on_created(self, event):
            """新文件创建时触发。"""
            if event.is_directory:
                return
            filepath = Path(event.src_path)
            # 忽略 .fcleanignore 中的文件
            relative = str(filepath.relative_to(target))
            if ignore_rules.matches(relative):
                return
            self._pending = True

        def maybe_process(self):
            """检查是否该触发 organize（防抖）。"""
            now = time.time()
            if self._pending and (now - self._last_trigger) >= debounce_seconds:
                self._pending = False
                self._last_trigger = now
                self._do_organize()

        def _do_organize(self):
            """执行 organize 操作。"""
            mode = "EXECUTE" if auto_execute else "DRY-RUN"
            print(f"\n🔄 [{time.strftime('%H:%M:%S')}] 检测到新文件，触发 organize ({mode})...")

            try:
                result = organize(
                    target_path=str(target),
                    dry_run=(not auto_execute),
                    execute=auto_execute,
                    config=config,
                )

                if result.total_moved > 0:
                    action = '已整理' if auto_execute else '将整理'
                    print(f"  📁 {action} {result.total_moved} 个文件")
                else:
                    print("  ✅ 无需整理")
            except (FileNotFoundError, PermissionError) as e:
                print(f"  ❌ 错误: {e}", file=sys.stderr)

    handler = FcleanHandler()
    observer = Observer()
    observer.schedule(handler, str(target), recursive=False)

    mode_str = "自动执行" if auto_execute else "预览 (dry-run)"
    print(f"👀 fclean watch — 监听 {target}")
    print(f"   模式: {mode_str}")
    print(f"   防抖: {debounce_seconds}s")
    print("   按 Ctrl+C 退出\n")

    observer.start()
    try:
        while True:
            handler.maybe_process()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n👋 已停止监听。")
    finally:
        observer.stop()
        observer.join()
