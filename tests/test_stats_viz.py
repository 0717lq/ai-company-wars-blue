"""测试 stats_viz 模块 — ASCII 饼图、柱状图、Top-N 大文件排行。"""

import pytest

from fclean.stats_viz import (
    find_top_files,
    render_bar_chart,
    render_pie_chart,
    render_top_files,
)

# ── 测试数据构造 ──────────────────────────────────────────


@pytest.fixture
def sample_stats():
    """构造模拟的统计字典。"""
    return {
        "total_files": 100,
        "total_size": 1024 * 1024 * 50,  # 50MB
        "categories": {
            "图片": {"count": 40, "size": 1024 * 1024 * 20},  # 20MB
            "文档": {"count": 30, "size": 1024 * 1024 * 15},  # 15MB
            "视频": {"count": 10, "size": 1024 * 1024 * 10},  # 10MB
            "音频": {"count": 20, "size": 1024 * 1024 * 5},   # 5MB
        },
    }


@pytest.fixture
def empty_stats():
    """空目录统计。"""
    return {
        "total_files": 0,
        "total_size": 0,
        "categories": {},
    }


@pytest.fixture
def sample_dir(tmp_path):
    """构造包含不同大小文件的测试目录。"""
    # 创建不同大小的文件
    files = [
        ("large.bin", 1024 * 100),   # 100KB
        ("medium.bin", 1024 * 50),   # 50KB
        ("small.bin", 1024 * 10),    # 10KB
        ("tiny.bin", 1024),          # 1KB
        ("large2.bin", 1024 * 80),   # 80KB
    ]
    for name, size in files:
        fpath = tmp_path / name
        fpath.write_bytes(b"\x00" * size)

    # 创建子目录中的文件
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.bin").write_bytes(b"\x00" * (1024 * 30))  # 30KB

    return tmp_path


# ── render_pie_chart 测试 ────────────────────────────────────


class TestRenderPieChart:
    """测试 ASCII 饼图渲染。"""

    def test_basic_pie_chart(self, sample_stats):
        """基本饼图应包含类别名和百分比。"""
        result = render_pie_chart(sample_stats)
        assert "图片" in result
        assert "文档" in result
        assert "视频" in result
        assert "音频" in result
        # 应包含百分比
        assert "%" in result
        # 应包含表格边框
        assert "┌" in result
        assert "└" in result

    def test_empty_stats_returns_message(self, empty_stats):
        """空统计应返回无数据提示。"""
        result = render_pie_chart(empty_stats)
        assert "无数据" in result

    def test_contains_both_charts(self, sample_stats):
        """应同时包含数量分布和大小分布两个图表。"""
        result = render_pie_chart(sample_stats)
        assert "按数量" in result
        assert "按大小" in result

    def test_custom_width(self, sample_stats):
        """自定义宽度参数应生效。"""
        result_wide = render_pie_chart(sample_stats, width=60)
        result_narrow = render_pie_chart(sample_stats, width=20)
        # 宽版本每行更长
        assert len(result_wide) > len(result_narrow)

    def test_single_category(self):
        """只有一个类别时也应正常渲染。"""
        stats = {
            "total_files": 10,
            "total_size": 1024,
            "categories": {
                "图片": {"count": 10, "size": 1024},
            },
        }
        result = render_pie_chart(stats)
        assert "图片" in result
        assert "100.0%" in result


# ── render_bar_chart 测试 ────────────────────────────────────


class TestRenderBarChart:
    """测试 ASCII 柱状图渲染。"""

    def test_basic_bar_chart(self, sample_stats):
        """基本柱状图应包含类别名。"""
        result = render_bar_chart(sample_stats)
        assert "图片" in result
        assert "文档" in result
        assert "柱状图" in result

    def test_empty_stats_returns_message(self, empty_stats):
        """空统计应返回无数据提示。"""
        result = render_bar_chart(empty_stats)
        assert "无数据" in result

    def test_contains_bar_characters(self, sample_stats):
        """柱状图应包含块字符。"""
        result = render_bar_chart(sample_stats)
        assert "█" in result

    def test_contains_counts(self, sample_stats):
        """柱状图底部应显示数量。"""
        result = render_bar_chart(sample_stats)
        assert "40" in result  # 图片数量
        assert "30" in result  # 文档数量


# ── find_top_files 测试 ────────────────────────────────────


class TestFindTopFiles:
    """测试 Top-N 大文件查找。"""

    def test_basic_top_files(self, sample_dir):
        """基本 Top-N 查找应返回正确排序。"""
        result = find_top_files(str(sample_dir), n=3)
        assert len(result) == 3
        # 第一个应该是最大的 (100KB)
        assert result[0]["size"] == 1024 * 100
        assert result[0]["name"] == "large.bin"
        # 按大小降序
        assert result[0]["size"] >= result[1]["size"] >= result[2]["size"]

    def test_top_files_includes_subdirs(self, sample_dir):
        """应包含子目录中的文件。"""
        result = find_top_files(str(sample_dir), n=10)
        names = [f["name"] for f in result]
        assert "nested.bin" in names

    def test_top_n_larger_than_file_count(self, sample_dir):
        """N 大于文件数时应返回全部文件。"""
        result = find_top_files(str(sample_dir), n=100)
        assert len(result) == 6  # 5 + 1 nested

    def test_top_files_has_required_fields(self, sample_dir):
        """每个结果应包含 path/name/size/size_human 字段。"""
        result = find_top_files(str(sample_dir), n=1)
        assert len(result) == 1
        f = result[0]
        assert "path" in f
        assert "name" in f
        assert "size" in f
        assert "size_human" in f
        assert f["size"] > 0

    def test_empty_directory(self, tmp_path):
        """空目录应返回空列表。"""
        result = find_top_files(str(tmp_path), n=5)
        assert result == []

    def test_n_equals_zero(self, sample_dir):
        """N=0 应返回空列表。"""
        result = find_top_files(str(sample_dir), n=0)
        assert result == []

    def test_nonexistent_path(self):
        """不存在的路径应返回空列表（不抛异常）。"""
        result = find_top_files("/nonexistent/path/12345", n=5)
        assert result == []


# ── render_top_files 测试 ────────────────────────────────────


class TestRenderTopFiles:
    """测试 Top-N 大文件列表渲染。"""

    def test_basic_render(self):
        """基本渲染应包含文件名和大小。"""
        files = [
            {"path": "/a/big.bin", "name": "big.bin",
             "size": 1024 * 100, "size_human": "100.0KB"},
            {"path": "/a/small.bin", "name": "small.bin",
             "size": 1024 * 10, "size_human": "10.0KB"},
        ]
        result = render_top_files(files)
        assert "big.bin" in result
        assert "small.bin" in result
        assert "100.0KB" in result
        assert "10.0KB" in result
        assert "排行" in result

    def test_contains_rank_numbers(self):
        """应包含排名序号。"""
        files = [
            {"path": f"/a/file{i}.bin", "name": f"file{i}.bin",
             "size": 1024 * i, "size_human": f"{i}KB"}
            for i in range(5, 0, -1)
        ]
        result = render_top_files(files)
        assert "1." in result
        assert "2." in result
        assert "5." in result

    def test_contains_bar_characters(self):
        """应包含条形图字符。"""
        files = [
            {"path": "/a/big.bin", "name": "big.bin", "size": 1024 * 100, "size_human": "100.0KB"},
        ]
        result = render_top_files(files)
        assert "█" in result

    def test_empty_files_returns_message(self):
        """空文件列表应返回无文件提示。"""
        result = render_top_files([])
        assert "无文件" in result

    def test_long_filename_truncated(self):
        """超长文件名应被截断。"""
        long_name = "a" * 50 + ".bin"
        files = [
            {"path": f"/a/{long_name}", "name": long_name, "size": 1024, "size_human": "1.0KB"},
        ]
        result = render_top_files(files)
        # 截断后应有 "..."
        assert "..." in result
