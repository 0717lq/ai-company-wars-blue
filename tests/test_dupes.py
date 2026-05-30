"""
测试 fclean dupes — 重复文件检测模块。

测试要点：
1. SHA-256 哈希计算
2. 重复文件检测
3. --min-size 参数
4. 空目录 / 无重复情况
5. 多种重复文件
6. 删除操作
7. 删除策略
8. JSON 输出
"""

import hashlib
import json
from pathlib import Path

import pytest

from fclean.dupes import (
    DupesResult,
    _format_size,
    _hash_file,
    _parse_size_arg,
    find_duplicates,
)


class TestFormatSize:
    """测试 _format_size 辅助函数。"""

    def test_bytes(self):
        assert _format_size(500) == "500.0B"

    def test_kb(self):
        result = _format_size(2048)
        assert "KB" in result
        assert "2.0" in result

    def test_mb(self):
        result = _format_size(1048576 * 5)
        assert "MB" in result
        assert "5.0" in result

    def test_gb(self):
        result = _format_size(1073741824 * 2)
        assert "GB" in result
        assert "2.0" in result

    def test_tb(self):
        result = _format_size(1099511627776 * 3)
        assert "TB" in result


class TestParseSizeArg:
    """测试 _parse_size_arg 函数。"""

    def test_bytes(self):
        assert _parse_size_arg("500") == 500

    def test_kb(self):
        assert _parse_size_arg("1KB") == 1024

    def test_kb_uppercase(self):
        assert _parse_size_arg("2KB") == 2048

    def test_mb(self):
        assert _parse_size_arg("1MB") == 1048576

    def test_gb(self):
        assert _parse_size_arg("1GB") == 1073741824

    def test_float_mb(self):
        assert _parse_size_arg("1.5MB") == 1572864

    def test_invalid(self):
        with pytest.raises(ValueError):
            _parse_size_arg("invalid")


class TestHashFile:
    """测试 _hash_file 函数。"""

    def test_hash_string(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert _hash_file(f) == expected

    def test_hash_binary(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_bytes(bytes(range(256)))
        expected = hashlib.sha256(bytes(range(256))).hexdigest()
        assert _hash_file(f) == expected

    def test_hash_large_file(self, tmp_path):
        """测试大文件逐块哈希。"""
        f = tmp_path / "large.bin"
        data = b"x" * (65536 * 3 + 1000)  # ~3.25 chunks
        f.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert _hash_file(f) == expected

    def test_hash_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        expected = hashlib.sha256(b"").hexdigest()
        assert _hash_file(f) == expected

    def test_hash_nonexistent(self):
        assert _hash_file(Path("/nonexistent/file.txt")) is None


class TestFindDuplicates:
    """测试 find_duplicates 核心功能。"""

    def test_no_duplicates(self, tmp_path):
        """无重复文件应返回空结果。"""
        (tmp_path / "a.txt").write_text("file a")
        (tmp_path / "b.txt").write_text("file b")
        result = find_duplicates(str(tmp_path), show_progress=False)
        assert result.total_scanned == 2
        assert not result.has_duplicates
        assert result.total_duplicate_files == 0

    def test_duplicates_found(self, tmp_path):
        """相同内容的文件应被检测为重复。"""
        content = "duplicate content"
        (tmp_path / "a.txt").write_text(content)
        (tmp_path / "b.txt").write_text(content)
        result = find_duplicates(str(tmp_path), show_progress=False)
        assert result.has_duplicates
        assert result.total_duplicate_groups == 1
        assert result.total_duplicate_files == 1  # 1 extra copy

    def test_multiple_duplicates(self, tmp_path):
        """多组重复应正确检测。"""
        (tmp_path / "a.txt").write_text("content a")
        (tmp_path / "b.txt").write_text("content a")
        (tmp_path / "c.txt").write_text("content c")
        (tmp_path / "d.txt").write_text("content c")
        result = find_duplicates(str(tmp_path), show_progress=False)
        assert result.total_duplicate_groups == 2
        assert result.total_duplicate_files == 2

    def test_three_copies(self, tmp_path):
        """三个相同文件应统计正确。"""
        content = "triple"
        (tmp_path / "a.txt").write_text(content)
        (tmp_path / "b.txt").write_text(content)
        (tmp_path / "c.txt").write_text(content)
        result = find_duplicates(str(tmp_path), show_progress=False)
        assert result.has_duplicates
        assert result.total_duplicate_groups == 1
        assert result.total_duplicate_files == 2  # 2 extra copies

    def test_empty_directory(self, tmp_path):
        """空目录应返回无重复。"""
        result = find_duplicates(str(tmp_path), show_progress=False)
        assert result.total_scanned == 0
        assert not result.has_duplicates

    def test_hidden_files_skipped(self, tmp_path):
        """隐藏文件应被跳过。"""
        (tmp_path / ".hidden.txt").write_text("secret")
        result = find_duplicates(str(tmp_path), show_progress=False)
        assert result.total_scanned == 0

    def test_different_sizes_not_duplicates(self, tmp_path):
        """不同大小的文件不应被误判为重复。"""
        (tmp_path / "small.txt").write_text("small")
        (tmp_path / "large.txt").write_text("large content here")
        result = find_duplicates(str(tmp_path), show_progress=False)
        assert not result.has_duplicates

    def test_empty_files_skipped(self, tmp_path):
        """空文件应被跳过。"""
        (tmp_path / "empty.txt").write_text("")
        (tmp_path / "also_empty.txt").write_text("")
        result = find_duplicates(str(tmp_path), show_progress=False)
        assert result.total_scanned == 2
        assert not result.has_duplicates


class TestMinSize:
    """测试 --min-size 参数。"""

    def test_min_size_excludes_small_files(self, tmp_path):
        """设置 min-size 后小文件应被跳过。"""
        (tmp_path / "small.txt").write_text("tiny")
        (tmp_path / "small2.txt").write_text("tiny")
        (tmp_path / "large.txt").write_text("x" * 2000000)  # ~2MB
        (tmp_path / "large2.txt").write_text("x" * 2000000)

        result = find_duplicates(str(tmp_path), min_size="1MB", show_progress=False)
        assert result.skipped_small == 2
        assert result.has_duplicates
        # Only large files should be in duplicate groups
        assert result.total_duplicate_files == 1

    def test_min_size_zero(self, tmp_path):
        """min_size=0 应包含所有文件。"""
        (tmp_path / "a.txt").write_text("same")
        (tmp_path / "b.txt").write_text("same")
        result = find_duplicates(str(tmp_path), min_size="0", show_progress=False)
        assert result.has_duplicates


class TestDeleteAndStrategy:
    """测试删除操作和保留策略。"""

    def test_delete_newest_strategy(self, tmp_path):
        """newest 策略应保留最新文件。"""
        (tmp_path / "old.txt").write_text("same content")
        (tmp_path / "new.txt").write_text("same content")

        result = find_duplicates(str(tmp_path), show_progress=False)
        assert result.has_duplicates

        deleted = result.delete(strategy="newest")
        assert len(deleted) == 1
        # The newest file should be kept (new.txt), oldest deleted
        kept_path = deleted[0][0]
        assert kept_path.exists()

    def test_delete_oldest_strategy(self, tmp_path):
        """oldest 策略应保留最旧文件。"""
        (tmp_path / "a.txt").write_text("same content")
        (tmp_path / "b.txt").write_text("same content")

        result = find_duplicates(str(tmp_path), show_progress=False)
        deleted = result.delete(strategy="oldest")
        assert len(deleted) == 1
        # The oldest file should be kept
        kept_path = deleted[0][0]
        assert kept_path.exists()

    def test_delete_all_removed(self, tmp_path):
        """删除后重复文件应从文件系统移除。"""
        content = "delete me"
        (tmp_path / "keep.txt").write_text(content)
        (tmp_path / "delete.txt").write_text(content)

        result = find_duplicates(str(tmp_path), show_progress=False)
        deleted = result.delete(strategy="newest")
        assert len(deleted) == 1
        # The deleted path should not exist
        for keep, delete_path in deleted:
            assert delete_path.exists() is False

    def test_no_delete_plan_no_duplicates(self):
        """无重复时 get_delete_plan 应返回空。"""
        result = DupesResult()
        plan = result.get_delete_plan(strategy="newest")
        assert plan == {}


class TestDupesResultDict:
    """测试 DupesResult 的 JSON/dict 输出。"""

    def test_to_dict_empty(self):
        """空结果应有默认字段。"""
        result = DupesResult()
        d = result.to_dict()
        assert d["tool"] == "fclean"
        assert d["command"] == "dupes"
        assert "timestamp" in d
        assert d["duplicate_groups"] == 0
        assert d["duplicate_files"] == 0

    def test_to_dict_with_data(self, tmp_path):
        """有重复时 dict 应包含分组信息。"""
        (tmp_path / "a.txt").write_text("same")
        (tmp_path / "b.txt").write_text("same")
        result = find_duplicates(str(tmp_path), show_progress=False)
        d = result.to_dict()
        assert d["duplicate_groups"] == 1
        assert d["duplicate_files"] == 1
        assert len(d["groups"]) == 1
        # Check group structure
        for hash_val, group in d["groups"].items():
            assert "files" in group
            assert "count" in group
            assert "size_bytes" in group
            assert len(group["files"]) == 2

    def test_to_json_str(self, tmp_path):
        """to_json_str 应输出有效 JSON。"""
        (tmp_path / "a.txt").write_text("json test")
        (tmp_path / "b.txt").write_text("json test")
        result = find_duplicates(str(tmp_path), show_progress=False)
        json_str = result.to_json_str()
        parsed = json.loads(json_str)
        assert parsed["tool"] == "fclean"
        assert parsed["command"] == "dupes"
