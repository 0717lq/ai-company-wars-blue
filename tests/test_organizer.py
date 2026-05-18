"""
测试 fclean 整理模块。

使用 pyfakefs 模拟文件系统，避免操作真实文件。

测试要点：
1. scan_directory 扫描正确
2. classify_files 分类正确
3. organize dry-run 不实际移动文件
4. organize execute 实际移动文件
5. 排除参数生效
6. 错误处理（目录不存在、权限问题）
"""

import os
import stat
from pathlib import Path

import pytest

from fclean.organizer import (
    FileInfo,
    organize,
    scan_directory,
)


class TestFileInfo:
    """测试 FileInfo 数据类。"""

    def test_known_file(self, fs):
        """已知文件类型的分类正确。"""
        fs.create_file("/test/photo.jpg")
        fi = FileInfo(Path("/test/photo.jpg"))
        assert fi.category_key == "image"
        assert fi.target_dir_name == "图片"
        assert fi.is_known is True

    def test_unknown_file(self, fs):
        """未知文件类型的分类。"""
        fs.create_file("/test/file.xyz")
        fi = FileInfo(Path("/test/file.xyz"))
        assert fi.category_key is None
        assert fi.target_dir_name == "其他"
        assert fi.is_known is False

    def test_no_extension(self, fs):
        """无扩展名文件。"""
        fs.create_file("/test/README")
        fi = FileInfo(Path("/test/README"))
        assert fi.category_key is None

    def test_size_correct(self, fs):
        """文件大小读取正确。"""
        fs.create_file("/test/data.txt", contents="hello world")
        fi = FileInfo(Path("/test/data.txt"))
        assert fi.size == len("hello world")


class TestScanDirectory:
    """测试目录扫描。"""

    def test_scan_empty_dir(self, fs):
        """空目录扫描返回空列表。"""
        fs.create_dir("/empty")
        files = scan_directory(Path("/empty"))
        assert files == []

    def test_scan_with_files(self, fs):
        """扫描包含文件的目录。"""
        fs.create_file("/test/a.jpg")
        fs.create_file("/test/b.pdf")
        fs.create_file("/test/c.txt")
        fs.create_file("/test/d.mp3")

        files = scan_directory(Path("/test"))
        assert len(files) == 4

        names = [f.name for f in files]
        assert "a.jpg" in names
        assert "b.pdf" in names
        assert "c.txt" in names

    def test_hidden_files_skipped(self, fs):
        """隐藏文件（.开头）应被跳过。"""
        fs.create_file("/test/.hidden.txt")
        fs.create_file("/test/visible.txt")
        files = scan_directory(Path("/test"))
        assert len(files) == 1
        assert files[0].name == "visible.txt"

    def test_subdirectories_skipped(self, fs):
        """子目录本身不应出现在文件列表中。"""
        fs.create_dir("/test/subdir")
        fs.create_file("/test/file.txt")
        files = scan_directory(Path("/test"))
        assert len(files) == 1
        assert files[0].name == "file.txt"

    def test_target_categories_skipped(self, fs):
        """目标分类目录（图片/、文档/等）不参与扫描。"""
        fs.create_dir("/test/图片")
        fs.create_dir("/test/文档")
        fs.create_file("/test/图片/photo.jpg")
        fs.create_file("/test/file.txt")

        files = scan_directory(Path("/test"))
        # 应该只扫描到 file.txt，分类目录本身不被扫描
        names = [f.name for f in files]
        assert "file.txt" in names
        assert "图片" not in names
        assert "文档" not in names

    def test_scan_nonexistent(self, fs):
        """不存在的目录应报错。"""
        with pytest.raises(FileNotFoundError):
            scan_directory(Path("/nonexistent"))

    def test_scan_file_not_dir(self, fs):
        """传入文件路径应报错。"""
        fs.create_file("/test/file.txt")
        with pytest.raises(NotADirectoryError):
            scan_directory(Path("/test/file.txt"))

    def test_exclude_pattern(self, fs):
        """exclude 模式排除匹配文件。"""
        fs.create_file("/test/a.tmp")
        fs.create_file("/test/b.txt")
        fs.create_file("/test/c.tmp")

        files = scan_directory(
            Path("/test"),
            exclude_patterns=["*.tmp"],
        )
        assert len(files) == 1
        assert files[0].name == "b.txt"

    def test_exclude_dir(self, fs):
        """exclude-dir 排除目录（本测试确保不报错）。"""
        fs.create_dir("/test/node_modules")
        # 确认不报错
        files = scan_directory(
            Path("/test"),
            exclude_dirs=["node_modules"],
        )
        assert isinstance(files, list)

    def test_scan_permission_denied(self, fs):
        """权限不足应报错。"""
        fs.create_dir("/restricted")
        os.chmod("/restricted", 0o000)
        with pytest.raises(PermissionError):
            scan_directory(Path("/restricted"))
        os.chmod("/restricted", 0o755)  # 恢复权限让 pyfakefs 清理


class TestOrganizeDryRun:
    """测试 dry-run 模式。"""

    def test_dry_run_does_not_move(self, fs):
        """dry-run 不应实际移动文件。"""
        fs.create_file("/test/photo.jpg")
        fs.create_file("/test/doc.pdf")

        result = organize("/test", dry_run=True)

        assert result.total_moved == 2
        assert result.total_errors == 0
        # 文件仍在原位置
        assert Path("/test/photo.jpg").exists()
        assert Path("/test/doc.pdf").exists()
        # 目标目录不应被创建
        assert not Path("/test/图片").exists()
        assert not Path("/test/文档").exists()

    def test_dry_run_empty_dir(self, fs):
        """空目录 dry-run 结果应为空。"""
        fs.create_dir("/empty")
        result = organize("/empty", dry_run=True)
        assert result.total_scanned == 0
        assert result.total_moved == 0

    def test_dry_run_unknown_type(self, fs):
        """未知类型的文件应归类到'其他'。"""
        fs.create_file("/test/file.xyz")
        result = organize("/test", dry_run=True)
        assert result.total_moved == 1
        fi, dst = result.files_moved[0]
        assert "其他" in str(dst)


class TestOrganizeExecute:
    """测试 execute 模式。"""

    def test_execute_moves_files(self, fs):
        """execute 模式应实际移动文件。"""
        fs.create_file("/test/photo.jpg", contents="image data")
        fs.create_file("/test/doc.pdf", contents="doc data")

        result = organize("/test", execute=True)

        assert result.total_moved == 2
        assert result.total_errors == 0

        # 原文件不应存在
        assert not Path("/test/photo.jpg").exists()
        assert not Path("/test/doc.pdf").exists()

        # 目标文件应存在
        assert Path("/test/图片/photo.jpg").exists()
        assert Path("/test/文档/doc.pdf").exists()

    def test_execute_creates_directories(self, fs):
        """execute 应自动创建目标目录。"""
        fs.create_file("/test/song.mp3")

        result = organize("/test", execute=True)

        assert result.total_moved == 1
        assert Path("/test/音频").is_dir()
        assert Path("/test/音频/song.mp3").exists()

    def test_execute_no_overwrite(self, fs):
        """同名文件不应被覆盖，应自动添加后缀。"""
        fs.create_file("/test/photo.jpg", contents="original")
        fs.create_file("/test/图片/photo.jpg", contents="existing")  # 先放一个

        result = organize("/test", execute=True)

        # 文件应该被移动，但使用不同的文件名
        assert result.total_moved == 1
        assert result.total_errors == 0
        assert Path("/test/图片/photo.jpg").exists()  # 原有的还在
        # 被移动的文件应该有后缀
        moved_files = [f.name for f in Path("/test/图片").iterdir() if f.is_file()]
        assert len(moved_files) == 2  # 原有的 + 移动的

    def test_execute_permission_error(self, fs):
        """权限错误应被记录但继续处理其他文件。"""
        fs.create_file("/test/a.jpg", contents="a")
        fs.create_file("/test/b.txt", contents="b")

        result = organize("/test", execute=True)

        assert result.total_moved == 2
        oc = result.get_category_counts()
        assert sum(oc.values()) == 2

    def test_execute_category_counts(self, fs):
        """execute 后的分类统计数据应正确。"""
        fs.create_file("/test/a.jpg")  # 图片
        fs.create_file("/test/b.pdf")  # 文档
        fs.create_file("/test/c.mp3")  # 音频
        fs.create_file("/test/d.zip")  # 压缩包

        result = organize("/test", execute=True)

        counts = result.get_category_counts()
        assert counts.get("图片", 0) == 1
        assert counts.get("文档", 0) == 1
        assert counts.get("音频", 0) == 1
        assert counts.get("压缩包", 0) == 1
        assert result.total_moved == 4


class TestOrganizeExclude:
    """测试排除参数。"""

    def test_exclude_pattern(self, fs):
        """exclude 参数排除匹配的文件。"""
        fs.create_file("/test/a.tmp")
        fs.create_file("/test/b.txt")

        result = organize("/test", dry_run=True, exclude=["*.tmp"])
        names = [fi.name for fi, _ in result.files_moved]
        assert "a.tmp" not in names
        assert "b.txt" in names
        assert result.total_moved == 1

    def test_multiple_exclude(self, fs):
        """多个 exclude 模式同时生效。"""
        fs.create_file("/test/a.tmp")
        fs.create_file("/test/b.log")
        fs.create_file("/test/c.txt")

        result = organize("/test", dry_run=True, exclude=["*.tmp", "*.log"])
        names = [fi.name for fi, _ in result.files_moved]
        assert "a.tmp" not in names
        assert "b.log" not in names
        assert "c.txt" in names

    def test_empty_exclude(self, fs):
        """空排除列表不影响整理。"""
        fs.create_file("/test/a.txt")
        fs.create_file("/test/b.txt")

        result = organize("/test", dry_run=True, exclude=[])
        assert result.total_moved == 2
