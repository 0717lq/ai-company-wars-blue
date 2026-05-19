"""
测试 fclean renamer 模块 — 批量重命名功能。

使用 pyfakefs 模拟文件系统，验证：
1. Glob 模式匹配正确
2. 模板变量解析（{n}, {n:03d}, {date}, {ext}）
3. Dry-run 和 execute 行为
4. 冲突处理
5. 无匹配文件时的行为
"""

from pathlib import Path

import pytest

from fclean.renamer import generate_rename_plan, RenamePlan, _resolve_template


class TestTemplateResolution:
    """测试模板变量解析。"""

    def test_simple_sequence(self, fs):
        """{n} 应解析为 1-based 序列号。"""
        fs.create_file("/test/photo.jpg")
        result = _resolve_template("vacation_{n}", 1, Path("/test/photo.jpg"))
        assert result == "vacation_1"

    def test_zero_padded(self, fs):
        """{n:03d} 应补零到 3 位。"""
        fs.create_file("/test/photo.jpg")
        result = _resolve_template("vacation_{n:03d}", 5, Path("/test/photo.jpg"))
        assert result == "vacation_005"

    def test_ext_variable(self, fs):
        """{ext} 应替换为小写扩展名（含前导点号）。"""
        fs.create_file("/test/photo.JPG")
        result = _resolve_template("file{ext}", 1, Path("/test/photo.JPG"))
        assert result == "file.jpg"

    def test_date_variable(self, fs):
        """{date} 应替换为 YYYY-MM-DD 格式。"""
        fs.create_file("/test/photo.jpg")
        result = _resolve_template("photo_{date}", 1, Path("/test/photo.jpg"))
        assert "20" in result  # 年份
        assert "-" in result   # 分隔符

    def test_complex_template(self, fs):
        """组合多个变量应正确解析。"""
        fs.create_file("/test/IMG_1234.jpg")
        result = _resolve_template("vacation_{n:03d}_{date}{ext}", 7,
                                   Path("/test/IMG_1234.jpg"))
        assert result.startswith("vacation_007_")
        assert result.endswith(".jpg")

    def test_no_template_vars(self, fs):
        """没有模板变量时应原样返回。"""
        fs.create_file("/test/photo.jpg")
        result = _resolve_template("fixed_name", 1, Path("/test/photo.jpg"))
        assert result == "fixed_name"


class TestGenerateRenamePlan:
    """测试重命名计划生成。"""

    def test_basic_rename_plan(self, fs):
        """基本的 glob 匹配 + 重命名计划（模板不含 ext 时新文件名无后缀）。"""
        fs.create_file("/test/photo1.jpg")
        fs.create_file("/test/photo2.jpg")
        fs.create_file("/test/readme.txt")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "vacation_{n:03d}"
        )

        assert plan.total == 2
        names = [item.new_path.name for item in plan.items]
        # 模板不含 {ext}，新文件名不带扩展名
        assert "vacation_001" in names
        assert "vacation_002" in names

    def test_rename_plan_with_ext(self, fs):
        """模板含 {ext} 时新文件名保留扩展名。"""
        fs.create_file("/test/photo1.jpg")
        fs.create_file("/test/photo2.jpg")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "vacation_{n:03d}{ext}"
        )

        assert plan.total == 2
        names = [item.new_path.name for item in plan.items]
        assert "vacation_001.jpg" in names
        assert "vacation_002.jpg" in names

    def test_no_matching_files(self, fs):
        """没有匹配文件时返回空计划。"""
        fs.create_file("/test/readme.txt")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "vacation_{n:03d}"
        )

        assert plan.total == 0
        assert plan.items == []

    def test_sorted_results(self, fs):
        """匹配结果应按文件名排序。"""
        fs.create_file("/test/b.jpg")
        fs.create_file("/test/a.jpg")
        fs.create_file("/test/c.jpg")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "img_{n}"
        )

        assert plan.total == 3
        assert plan.items[0].old_path.name == "a.jpg"
        assert plan.items[1].old_path.name == "b.jpg"
        assert plan.items[2].old_path.name == "c.jpg"

    def test_rename_with_ext_variable(self, fs):
        """使用 {ext} 变量时应保留原扩展名。"""
        fs.create_file("/test/photo.jpg")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "img_{n}{ext}"
        )

        assert plan.total == 1
        assert plan.items[0].new_path.name == "img_1.jpg"

    def test_conflict_handling(self, fs):
        """重名时新文件名应添加数字后缀。"""
        # 先创建一个目录，放两个文件进去
        # 测试：photo.jpg 重命名为 vacation_001，但 vacation_001 已存在
        fs.create_file("/test/photo.jpg")
        fs.create_file("/test/vacation_001")  # 已存在的冲突文件

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "vacation_{n:03d}"
        )

        # photo.jpg -> 应变为 vacation_001_1（因为 vacation_001 已存在）
        assert plan.total == 1
        new_name = plan.items[0].new_path.name
        assert new_name != "vacation_001"
        assert new_name.startswith("vacation_001")

    def test_unicode_filenames(self, fs):
        """Unicode 文件名应正常工作。"""
        fs.create_file("/test/照片.jpg")
        fs.create_file("/test/ファイル.png")
        fs.create_file("/test/émoji 🎉.txt")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "pic_{n:03d}{ext}"
        )

        assert plan.total == 1
        assert plan.items[0].new_path.name == "pic_001.jpg"

    def test_directory_not_found(self, fs):
        """不存在的目录应报错。"""
        with pytest.raises(FileNotFoundError):
            generate_rename_plan(Path("/nonexistent"), "*.jpg", "img_{n}")

    def test_not_a_directory(self, fs):
        """路径是文件而非目录应报错。"""
        fs.create_file("/test/file.txt")
        with pytest.raises(NotADirectoryError):
            generate_rename_plan(Path("/test/file.txt"), "*.jpg", "img_{n}")


class TestRenamePlanExecute:
    """测试重命名执行。"""

    def test_execute_renames_files(self, fs):
        """execute() 应实际重命名文件。"""
        fs.create_file("/test/photo.jpg", contents="data")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "vacation_{n:03d}{ext}"
        )
        assert plan.total == 1

        executed = plan.execute()
        assert len(executed) == 1

        assert not Path("/test/photo.jpg").exists()
        assert Path("/test/vacation_001.jpg").exists()

    def test_execute_multiple_files(self, fs):
        """execute() 应重命名所有匹配文件。"""
        fs.create_file("/test/a.jpg", contents="a")
        fs.create_file("/test/b.jpg", contents="b")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "img_{n}"
        )

        executed = plan.execute()
        assert len(executed) == 2

        assert Path("/test/img_1").exists()
        assert Path("/test/img_2").exists()
        assert not Path("/test/a.jpg").exists()

    def test_execute_with_date_template(self, fs):
        """使用 {date} 模板时执行应正确。"""
        fs.create_file("/test/photo.jpg", contents="data")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "photo_{date}{ext}"
        )

        assert plan.total == 1
        executed = plan.execute()
        assert len(executed) == 1
        # 验证新文件名包含日期
        new_name = executed[0].new_path.name
        assert new_name.startswith("photo_20")
        assert new_name.endswith(".jpg")

    def test_get_rename_pairs_returns_tuples(self, fs):
        """get_rename_pairs() 应返回 (old, new) 元组列表。"""
        fs.create_file("/test/photo.jpg")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "img_{n}{ext}"
        )

        pairs = plan.get_rename_pairs()
        assert len(pairs) == 1
        old_path, new_path = pairs[0]
        assert str(old_path).endswith("photo.jpg")
        assert str(new_path).endswith("img_1.jpg")


class TestRenamePlanProperties:
    """测试 RenamePlan 属性。"""

    def test_plan_initial_state(self, fs):
        """新计划的 executed 应为 False。"""
        fs.create_file("/test/photo.jpg")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "img"
        )

        assert plan.executed is False
        assert plan.directory == Path("/test").resolve()
        assert plan.pattern == "*.jpg"
        assert plan.format_template == "img"

    def test_execute_flags_executed(self, fs):
        """执行后 executed 应为 True。"""
        fs.create_file("/test/photo.jpg")

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "img"
        )
        plan.execute()
        assert plan.executed is True

    def test_empty_plan_execute(self, fs):
        """空计划执行不应报错。"""
        # 创建目录但不创建匹配的文件
        fs.create_dir("/test")
        fs.create_file("/test/readme.txt")  # 不匹配 *.jpg

        plan = generate_rename_plan(
            Path("/test"), "*.jpg", "img"
        )

        executed = plan.execute()
        assert executed == []
        assert plan.executed is True
