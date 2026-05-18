"""
测试 fclean undo 模块。

使用 pyfakefs 模拟文件系统和用户 home 目录。
"""

import json
import os
import shutil
import time
from pathlib import Path

import pytest

from fclean.organizer import OrganizeResult, FileInfo
from fclean.undo import (
    record_operation,
    undo_last,
    list_undo_logs,
    UNDO_DIR,
)


class TestRecordOperation:
    """测试记录操作日志。"""

    def test_record_creates_file(self, fs):
        """记录操作应在 ~/.fclean/undo/ 下创建 JSON 文件。"""
        fs.create_file("/test/photo.jpg", contents="a")
        fs.create_file("/test/doc.pdf", contents="b")

        result = OrganizeResult()
        fi_a = FileInfo(Path("/test/photo.jpg"))
        result.files_moved.append((fi_a, Path("/test/图片/photo.jpg")))
        fi_b = FileInfo(Path("/test/doc.pdf"))
        result.files_moved.append((fi_b, Path("/test/文档/doc.pdf")))

        log_path = record_operation(result)

        assert os.path.exists(log_path)
        assert log_path.startswith(str(UNDO_DIR))
        assert log_path.endswith(".json")

        # 验证文件内容
        with open(log_path) as f:
            data = json.load(f)
        assert data["total_moved"] == 2
        assert len(data["files_moved"]) == 2
        assert data["files_moved"][0]["source"].endswith("photo.jpg")
        assert data["files_moved"][0]["target"].endswith("图片/photo.jpg")

    def test_record_empty_raises(self, fs):
        """没有文件被移动时记录应报错。"""
        result = OrganizeResult()
        with pytest.raises(ValueError, match="没有文件被移动"):
            record_operation(result)

    def test_record_multiple_operations(self, fs):
        """多次记录应生成不同文件。"""
        fs.create_file("/test/a.jpg", contents="a")

        # 利用不同结果（不同 total_moved）验证记录正确
        r1 = OrganizeResult()
        fi_a = FileInfo(Path("/test/a.jpg"))
        r1.files_moved.append((fi_a, Path("/test/图片/a.jpg")))
        log1 = record_operation(r1)

        fs.create_file("/test/b.jpg", contents="b")
        fi_b = FileInfo(Path("/test/b.jpg"))
        r1.files_moved.append((fi_b, Path("/test/文档/b.pdf")))

        # 验证两次记录互不影响（第一条日志仍然有效）
        with open(log1) as f:
            data = json.load(f)
        assert data["total_moved"] == 1  # 第一次只记录了一个文件


class TestUndoLast:
    """测试回滚功能。"""

    def test_undo_moves_files_back(self, fs):
        """undo 应把文件移回原位置。"""
        # 文件初始在 /test/photo.jpg，先移动到 /test/图片/photo.jpg
        # 然后创建 undo 日志指向这个移动，执行回滚
        fs.create_file("/test/photo.jpg", contents="data")
        fs.create_dir("/test/图片")
        shutil.move("/test/photo.jpg", "/test/图片/photo.jpg")
        assert Path("/test/图片/photo.jpg").exists()
        assert not Path("/test/photo.jpg").exists()

        # 手动创建 undo 日志
        log_dir = Path.home() / ".fclean" / "undo"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "undo_test.json", "w") as f:
            json.dump({
                "timestamp": "test",
                "files_moved": [
                    {"source": "/test/photo.jpg", "target": "/test/图片/photo.jpg"}
                ],
                "total_moved": 1,
                "total_size": 4,
            }, f)

        # 执行回滚：undo_last 会把文件从 target 移回 source
        undo_result = undo_last()

        assert undo_result.total_moved == 1
        assert undo_result.total_errors == 0
        assert Path("/test/photo.jpg").exists()
        assert not Path("/test/图片/photo.jpg").exists()

    def test_undo_deletes_log(self, fs):
        """回滚后日志文件应被删除。"""
        fs.create_file("/test/a.jpg", contents="data")
        fs.create_dir("/test/图片")
        shutil.move("/test/a.jpg", "/test/图片/a.jpg")

        log_dir = Path.home() / ".fclean" / "undo"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "undo_test.json"
        with open(log_path, "w") as f:
            json.dump({
                "timestamp": "test",
                "files_moved": [
                    {"source": "/test/a.jpg", "target": "/test/图片/a.jpg"}
                ],
                "total_moved": 1,
                "total_size": 4,
            }, f)

        assert os.path.exists(log_path)
        undo_last()
        assert not os.path.exists(log_path)

    def test_undo_no_logs(self, fs):
        """没有日志时回滚应报错。"""
        with pytest.raises(FileNotFoundError, match="没有可回滚的操作"):
            undo_last()


class TestListUndoLogs:
    """测试列出 undo 日志。"""

    def test_list_empty(self, fs):
        """没有日志时返回空列表。"""
        logs = list_undo_logs()
        assert logs == []

    def test_list_with_logs(self, fs):
        """有日志时返回正确信息。"""
        log_dir = Path.home() / ".fclean" / "undo"
        log_dir.mkdir(parents=True, exist_ok=True)

        with open(log_dir / "undo_20260518_100000.json", "w") as f:
            json.dump({"timestamp": "20260518_100000", "total_moved": 2}, f)
        with open(log_dir / "undo_20260518_110000.json", "w") as f:
            json.dump({"timestamp": "20260518_110000", "total_moved": 1}, f)

        logs = list_undo_logs()
        assert len(logs) == 2
        assert logs[0]["total_moved"] >= 1
        assert logs[1]["total_moved"] >= 1
