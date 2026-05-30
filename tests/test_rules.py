"""
测试 fclean 分类规则模块。

测试要点：
1. 已知扩展名的分类结果正确
2. 未知扩展名返回 None
3. 大小写不敏感
4. 无扩展名文件返回 None
5. 各分类目录名正确
"""

from fclean.rules import classify, get_all_categories, get_dir_name


class TestClassify:
    """测试 classify 函数 — 根据文件名返回类别 key。"""

    def test_image_extensions(self):
        """图片类扩展名应返回 'image'。"""
        assert classify("photo.jpg") == "image"
        assert classify("photo.jpeg") == "image"
        assert classify("photo.png") == "image"
        assert classify("photo.gif") == "image"
        assert classify("photo.webp") == "image"
        assert classify("photo.bmp") == "image"
        assert classify("photo.svg") == "image"
        assert classify("photo.ico") == "image"
        assert classify("photo.tiff") == "image"
        assert classify("photo.heic") == "image"

    def test_document_extensions(self):
        """文档类扩展名应返回 'document'。"""
        assert classify("report.pdf") == "document"
        assert classify("report.docx") == "document"
        assert classify("notes.txt") == "document"
        assert classify("readme.md") == "document"
        assert classify("data.csv") == "document"
        assert classify("slides.pptx") == "document"
        assert classify("sheet.xlsx") == "document"

    def test_video_extensions(self):
        """视频类扩展名应返回 'video'。"""
        assert classify("movie.mp4") == "video"
        assert classify("movie.avi") == "video"
        assert classify("movie.mkv") == "video"
        assert classify("movie.mov") == "video"
        assert classify("movie.webm") == "video"

    def test_audio_extensions(self):
        """音频类扩展名应返回 'audio'。"""
        assert classify("song.mp3") == "audio"
        assert classify("song.wav") == "audio"
        assert classify("song.flac") == "audio"
        assert classify("song.aac") == "audio"
        assert classify("song.ogg") == "audio"

    def test_archive_extensions(self):
        """压缩包类扩展名应返回 'archive'。"""
        assert classify("files.zip") == "archive"
        assert classify("files.rar") == "archive"
        assert classify("files.7z") == "archive"
        assert classify("files.tar.gz") == "archive"
        assert classify("files.tar") == "archive"

    def test_code_extensions(self):
        """代码类扩展名应返回 'code'。"""
        assert classify("script.py") == "code"
        assert classify("app.js") == "code"
        assert classify("style.css") == "code"
        assert classify("index.html") == "code"
        assert classify("config.json") == "code"
        assert classify("config.yaml") == "code"

    def test_case_insensitive(self):
        """分类应该大小写不敏感。"""
        assert classify("PHOTO.JPG") == "image"
        assert classify("Photo.Png") == "image"
        assert classify("README.MD") == "document"
        assert classify("Script.PY") == "code"

    def test_unknown_extension(self):
        """未知扩展名应返回 None。"""
        assert classify("file.xyz") is None
        assert classify("data.abc123") is None
        assert classify("file") is None

    def test_no_extension(self):
        """没有扩展名的文件应返回 None。"""
        assert classify("README") is None
        assert classify(".gitignore") is None
        assert classify("") is None

    def test_dotfile(self):
        """.开头文件视为无扩展名，返回 None。"""
        assert classify(".hidden") is None
        # 但如果有扩展名则正常分类
        assert classify(".hidden.txt") == "document"


class TestGetDirName:
    """测试 get_dir_name — 类别 key 到中文目录名。"""

    def test_image_dir(self):
        assert get_dir_name("image") == "图片"

    def test_document_dir(self):
        assert get_dir_name("document") == "文档"

    def test_video_dir(self):
        assert get_dir_name("video") == "视频"

    def test_audio_dir(self):
        assert get_dir_name("audio") == "音频"

    def test_archive_dir(self):
        assert get_dir_name("archive") == "压缩包"

    def test_code_dir(self):
        assert get_dir_name("code") == "代码"

    def test_unknown_dir(self):
        """未知类别返回 '其他'。"""
        assert get_dir_name("unknown") == "其他"
        assert get_dir_name("") == "其他"


class TestGetAllCategories:
    """测试 get_all_categories。"""

    def test_returns_list(self):
        cats = get_all_categories()
        assert isinstance(cats, list)
        assert len(cats) > 0

    def test_all_categories_have_keys(self):
        cats = get_all_categories()
        for cat in cats:
            assert "key" in cat
            assert "dir_name" in cat
            assert "extensions" in cat
            assert isinstance(cat["extensions"], set)
            assert len(cat["extensions"]) > 0

    def test_no_duplicate_extensions(self):
        """同一个扩展名不应该出现在多个分类中。"""
        cats = get_all_categories()
        all_exts = set()
        for cat in cats:
            for ext in cat["extensions"]:
                assert ext not in all_exts, f"扩展名重复: {ext}"
                all_exts.add(ext)
