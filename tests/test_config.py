"""
测试 fclean 配置系统模块。

测试要点：
1. 配置加载（YAML 解析、默认配置）
2. 配置合并（CLI 参数 > 配置文件 > 默认规则）
3. 自定义分类规则生效
4. 配置文件不存在时回退到默认
5. 错误配置处理
"""



from fclean.config import (
    DEFAULT_CONFIG,
    Config,
    generate_example_config,
    load_config,
)


class TestConfigDefaults:
    """测试默认配置。"""

    def test_default_config_has_rules(self):
        """默认配置应有分类规则。"""
        cfg = Config()
        assert len(cfg.rules) > 0

    def test_default_rules_contain_categories(self):
        """默认规则应包含基本类别。"""
        cfg = Config()
        assert "图片" in cfg.rules
        assert "文档" in cfg.rules
        assert "视频" in cfg.rules
        assert "音频" in cfg.rules
        assert "压缩包" in cfg.rules
        assert "代码" in cfg.rules

    def test_default_exclude_empty(self):
        """默认排除列表应为空。"""
        cfg = Config()
        assert cfg.exclude_patterns == []
        assert cfg.exclude_dirs == []


class TestConfigClassify:
    """测试自定义配置的分类功能。"""

    def test_classify_known_extension(self):
        """已知扩展名应返回对应类别。"""
        cfg = Config(DEFAULT_CONFIG)
        assert cfg.classify("photo.jpg") == "图片"
        assert cfg.classify("doc.pdf") == "文档"
        assert cfg.classify("video.mp4") == "视频"
        assert cfg.classify("song.mp3") == "音频"
        assert cfg.classify("archive.zip") == "压缩包"
        assert cfg.classify("script.py") == "代码"

    def test_classify_unknown_extension(self):
        """未知扩展名应返回 None。"""
        cfg = Config(DEFAULT_CONFIG)
        assert cfg.classify("file.xyz") is None
        assert cfg.classify("data.abc") is None

    def test_classify_case_insensitive(self):
        """分类应大小写不敏感。"""
        cfg = Config(DEFAULT_CONFIG)
        assert cfg.classify("PHOTO.JPG") == "图片"
        assert cfg.classify("Photo.Png") == "图片"

    def test_classify_no_extension(self):
        """无扩展名文件返回 None。"""
        cfg = Config(DEFAULT_CONFIG)
        assert cfg.classify("README") is None
        assert cfg.classify("") is None


class TestConfigCustomRules:
    """测试自定义分类规则。"""

    def test_custom_category(self):
        """自定义类别应生效。"""
        custom_data = {
            "rules": [
                {"category": "电子书", "extensions": [".epub", ".mobi"]},
            ]
        }
        cfg = Config(custom_data)
        assert "电子书" in cfg.rules
        assert ".epub" in cfg.rules["电子书"]
        assert ".mobi" in cfg.rules["电子书"]

    def test_custom_classify(self):
        """自定义规则分类正确。"""
        custom_data = {
            "rules": [
                {"category": "电子书", "extensions": [".epub", ".mobi"]},
            ]
        }
        cfg = Config(custom_data)
        assert cfg.classify("book.epub") == "电子书"
        assert cfg.classify("book.mobi") == "电子书"
        assert cfg.classify("book.pdf") is None

    def test_config_with_exclude(self):
        """配置中的排除模式生效。"""
        custom_data = {
            "rules": DEFAULT_CONFIG["rules"],
            "exclude_patterns": ["*.tmp", "*.log"],
            "exclude_dirs": ["node_modules", "__pycache__"],
        }
        cfg = Config(custom_data)
        assert "*.tmp" in cfg.exclude_patterns
        assert "*.log" in cfg.exclude_patterns
        assert "node_modules" in cfg.exclude_dirs


class TestLoadConfig:
    """测试配置加载。"""

    def test_load_with_config_file(self, fs):
        """从 YAML 文件加载配置。"""
        fs.create_file("/test/.fcleanrc", contents="""rules:
  - category: 电子书
    extensions:
      - .epub
      - .mobi
""")

        cfg = load_config("/test")
        assert "电子书" in cfg.rules
        assert ".epub" in cfg.rules["电子书"]

    def test_load_no_config_file(self):
        """没有配置文件时应返回默认配置。"""
        cfg = load_config("/nonexistent_directory_12345")
        assert len(cfg.rules) > 0
        assert "图片" in cfg.rules

    def test_load_invalid_yaml(self, fs):
        """YAML 解析失败应回退到默认。"""
        fs.create_file("/bad/.fcleanrc", contents="invalid: yaml: : : broken")

        cfg = load_config("/bad")
        assert len(cfg.rules) > 0

    def test_load_empty_config(self, fs):
        """空配置文件应回退到默认。"""
        fs.create_file("/empty/.fcleanrc", contents="")

        cfg = load_config("/empty")
        assert len(cfg.rules) > 0


class TestGenerateExample:
    """测试生成示例配置文件。"""

    def test_example_contains_rules(self):
        """示例配置包含规则部分。"""
        example = generate_example_config()
        assert "rules:" in example
        assert "图片" in example
        assert "文档" in example
        assert "代码" in example

    def test_example_contains_comments(self):
        """示例配置包含注释。"""
        example = generate_example_config()
        assert "#" in example
        assert "fclean" in example


class TestConfigToDict:
    """测试配置序列化。"""

    def test_to_dict_has_rules(self):
        """to_dict 包含规则。"""
        cfg = Config(DEFAULT_CONFIG)
        data = cfg.to_dict()
        assert "rules" in data
        assert len(data["rules"]) > 0

    def test_to_dict_has_exclude(self):
        """to_dict 包含排除设置。"""
        cfg = Config(DEFAULT_CONFIG)
        data = cfg.to_dict()
        assert "exclude_patterns" in data
        assert "exclude_dirs" in data
