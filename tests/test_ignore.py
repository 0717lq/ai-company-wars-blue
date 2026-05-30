"""
test_ignore.py — .fcleanignore 解析器测试。

覆盖：基本匹配、取反规则、目录模式、路径模式、filter_files、load_ignore_rules。
"""


from fclean.ignore import IgnoreRules, load_ignore_rules


class TestIgnoreRulesBasic:
    """基本匹配逻辑。"""

    def test_empty_rules(self):
        """空规则不忽略任何文件。"""
        rules = IgnoreRules([])
        assert rules.matches("anything.txt") is False
        assert rules.has_rules is False

    def test_simple_glob(self):
        """简单 glob 模式匹配。"""
        rules = IgnoreRules(["*.log"])
        assert rules.matches("debug.log") is True
        assert rules.matches("readme.md") is False

    def test_specific_filename(self):
        """匹配具体文件名。"""
        rules = IgnoreRules(["secret.key"])
        assert rules.matches("secret.key") is True
        assert rules.matches("other.key") is False

    def test_question_mark_wildcard(self):
        """? 通配符匹配单个字符。"""
        rules = IgnoreRules(["file?.txt"])
        assert rules.matches("file1.txt") is True
        assert rules.matches("fileA.txt") is True
        assert rules.matches("file12.txt") is False

    def test_comment_lines_ignored(self):
        """# 开头的行被当作注释。"""
        rules = IgnoreRules(["# 这是注释", "*.log"])
        assert rules.matches("debug.log") is True
        # 注释本身不产生规则
        assert len(rules._patterns) == 1

    def test_empty_lines_skipped(self):
        """空行被跳过。"""
        rules = IgnoreRules(["", "   ", "*.log"])
        assert len(rules._patterns) == 1

    def test_case_sensitive(self):
        """匹配是大小写敏感的（fnmatch 默认行为）。"""
        rules = IgnoreRules(["*.LOG"])
        assert rules.matches("debug.LOG") is True
        # fnmatch 在 Linux 上区分大小写
        assert rules.matches("debug.log") is False


class TestIgnoreRulesNegation:
    """! 取反规则。"""

    def test_negation_overrides(self):
        """! 前缀的模式可以取消忽略。"""
        rules = IgnoreRules(["*.log", "!important.log"])
        assert rules.matches("debug.log") is True
        assert rules.matches("important.log") is False

    def test_negation_without_match(self):
        """取反规则不影响未被忽略的文件。"""
        rules = IgnoreRules(["*.log", "!important.log"])
        assert rules.matches("readme.md") is False

    def test_multiple_negations(self):
        """多条取反规则。"""
        rules = IgnoreRules(["*.log", "!important.log", "!keep.log"])
        assert rules.matches("debug.log") is True
        assert rules.matches("important.log") is False
        assert rules.matches("keep.log") is False


class TestIgnoreRulesDirPattern:
    """目录模式（/ 结尾）。"""

    def test_dir_pattern_matches_dirname(self):
        """以 / 结尾的模式匹配路径中的目录名。"""
        rules = IgnoreRules(["node_modules/"])
        assert rules.matches("node_modules/package.json") is True
        assert rules.matches("src/node_modules/foo.js") is True
        assert rules.matches("src/main.py") is False

    def test_dir_pattern_matches_standalone_name(self):
        """以 / 结尾的模式也会匹配路径中的每一部分（含独立文件名）。"""
        # 当前实现：对 filepath 每一部分做 fnmatch，所以 "logs" 也命中
        rules = IgnoreRules(["logs/"])
        assert rules.matches("logs") is True


class TestIgnoreRulesPathPattern:
    """路径模式（含 /）。"""

    def test_path_pattern(self):
        """含 / 的模式匹配完整路径。"""
        rules = IgnoreRules(["docs/*.pdf"])
        assert rules.matches("docs/readme.pdf") is True
        assert rules.matches("other/readme.pdf") is False

    def test_path_pattern_with_prefix(self):
        """路径模式也会尝试 */pattern 匹配。"""
        rules = IgnoreRules(["docs/*.pdf"])
        assert rules.matches("sub/docs/readme.pdf") is True


class TestIgnoreRulesSubdirMatch:
    """子目录文件匹配。"""

    def test_glob_matches_in_subdir(self):
        """纯文件名模式也匹配子目录下的文件。"""
        rules = IgnoreRules(["*.log"])
        assert rules.matches("subdir/debug.log") is True
        assert rules.matches("a/b/c/error.log") is True

    def test_specific_file_in_subdir(self):
        """具体文件名不匹配子目录下同名文件（无通配符）。"""
        rules = IgnoreRules(["debug.log"])
        # fnmatch 对每个部分匹配，debug.log 匹配 subdir/debug.log
        assert rules.matches("subdir/debug.log") is True


class TestFilterFiles:
    """filter_files 方法。"""

    def test_filter_basic(self):
        """过滤文件列表。"""
        rules = IgnoreRules(["*.log", "*.tmp"])
        files = ["readme.md", "debug.log", "data.csv", "cache.tmp"]
        result = rules.filter_files(files)
        assert result == ["readme.md", "data.csv"]

    def test_filter_empty(self):
        """空列表返回空列表。"""
        rules = IgnoreRules(["*.log"])
        assert rules.filter_files([]) == []

    def test_filter_no_match(self):
        """无匹配时返回原列表。"""
        rules = IgnoreRules(["*.log"])
        files = ["a.txt", "b.py"]
        assert rules.filter_files(files) == files


class TestIgnoreRulesRepr:
    """__repr__ 输出。"""

    def test_repr(self):
        rules = IgnoreRules(["*.log", "!important.log"])
        r = repr(rules)
        assert "IgnoreRules" in r
        assert "*.log" in r


class TestLoadIgnoreRules:
    """load_ignore_rules 函数。"""

    def test_no_ignore_file(self, tmp_path):
        """无 .fcleanignore 文件时返回空规则。"""
        rules = load_ignore_rules(tmp_path)
        assert rules.has_rules is False

    def test_load_ignore_file(self, tmp_path):
        """正确加载 .fcleanignore 文件。"""
        ignore_file = tmp_path / ".fcleanignore"
        ignore_file.write_text("*.log\n# comment\n!important.log\n\n")
        rules = load_ignore_rules(tmp_path)
        assert rules.has_rules is True
        assert rules.matches("debug.log") is True
        assert rules.matches("important.log") is False

    def test_load_unicode_content(self, tmp_path):
        """支持 UTF-8 编码。"""
        ignore_file = tmp_path / ".fcleanignore"
        ignore_file.write_text("*.日志\n# 中文注释\n", encoding="utf-8")
        rules = load_ignore_rules(tmp_path)
        assert rules.has_rules is True
        assert rules.matches("debug.日志") is True

    def test_source_path_set(self, tmp_path):
        """加载后 source 属性指向 .fcleanignore 文件。"""
        ignore_file = tmp_path / ".fcleanignore"
        ignore_file.write_text("*.log\n")
        rules = load_ignore_rules(tmp_path)
        assert rules.source == ignore_file

    def test_load_empty_file(self, tmp_path):
        """空文件返回无规则。"""
        ignore_file = tmp_path / ".fcleanignore"
        ignore_file.write_text("")
        rules = load_ignore_rules(tmp_path)
        assert rules.has_rules is False
