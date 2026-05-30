"""
测试 fclean CLI 命令行参数解析（直接调用 main 函数，支持 coverage）。

测试要点：
1. 子命令解析正确
2. 版本、帮助输出
3. init/stats/config 子命令
4. 错误处理
"""


import pytest

from fclean.cli import build_parser


class TestCLIVersion:
    """测试 --version 参数。"""

    def test_version_output(self, capsys):
        """fclean --version 应输出版本号。"""
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--version"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "fclean v" in captured.out

    def test_version_short(self, capsys):
        """fclean -V 也应输出版本号。"""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-V"])
        captured = capsys.readouterr()
        assert "fclean v" in captured.out

    def test_version_contains_v(self, capsys):
        """输出版本信息。"""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])
        captured = capsys.readouterr()
        assert "0.5.0" in captured.out


class TestCLIHelp:
    """测试 --help 参数。"""

    def test_help_contains_prog_name(self):
        """帮助信息应包含 fclean 程序名。"""
        parser = build_parser()
        help_text = parser.format_help()
        assert "fclean" in help_text
        assert "init" in help_text
        assert "stats" in help_text

    def test_help_contains_subcommands(self):
        """帮助信息应提及子命令。"""
        parser = build_parser()
        help_text = parser.format_help()
        assert "init" in help_text or "stats" in help_text or "config" in help_text


class TestCLIInitSubcommand:
    """测试 init 子命令解析。"""

    def test_init_parses_correctly(self):
        """fclean init 解析正确。"""
        parser = build_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"

    def test_init_help(self, capsys):
        """init --help 可解析。"""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["init", "--help"])


class TestCLIStatsSubcommand:
    """测试 stats 子命令解析。"""

    def test_stats_parses_correctly(self):
        """fclean stats /path 解析正确。"""
        parser = build_parser()
        args = parser.parse_args(["stats", "/some/path"])
        assert args.command == "stats"
        assert args.arg == "/some/path"


class TestCLIConfigSubcommand:
    """测试 config 子命令解析。"""

    def test_config_parses_correctly(self):
        """fclean config 解析正确。"""
        parser = build_parser()
        args = parser.parse_args(["config"])
        assert args.command == "config"


class TestCLIOrganizePath:
    """测试直接传路径的 organize 模式。"""

    def test_organize_default_path(self):
        """fclean ~/Downloads 应正确解析为 organize 模式。"""
        parser = build_parser()
        args = parser.parse_args(["/some/path"])
        assert args.command == "/some/path"
        # command 不是已知子命令 -> 当作路径
        assert args.command not in {"init", "stats", "config", "organize"}

    def test_organize_explicit_subcommand(self):
        """fclean organize /path 应正确解析。"""
        parser = build_parser()
        args = parser.parse_args(["organize", "/some/path"])
        assert args.command == "organize"
        assert args.arg == "/some/path"


class TestCLIUndoHistoryArgs:
    """测试 undo/history 参数解析。"""

    def test_undo_flag(self):
        """fclean --undo 应设置 undo=True。"""
        parser = build_parser()
        args = parser.parse_args(["--undo"])
        assert args.undo is True

    def test_history_flag(self):
        """fclean --history 应设置 history=True。"""
        parser = build_parser()
        args = parser.parse_args(["--history"])
        assert args.history is True


class TestCLIExecuteFlag:
    """测试 --execute 标志。"""

    def test_execute_flag_default(self):
        """默认 --execute 应为 False。"""
        parser = build_parser()
        args = parser.parse_args(["/path"])
        assert args.execute is False

    def test_execute_flag_set(self):
        """fclean /path --execute 应设置 execute=True。"""
        parser = build_parser()
        args = parser.parse_args(["/path", "--execute"])
        assert args.execute is True


class TestCLIExcludeArgs:
    """测试排除参数。"""

    def test_exclude_pattern(self):
        """--exclude '*.tmp' 应正确解析。"""
        parser = build_parser()
        args = parser.parse_args(["/path", "--exclude", "*.tmp"])
        assert "*.tmp" in args.exclude

    def test_exclude_multiple(self):
        """多次 --exclude 应累积。"""
        parser = build_parser()
        args = parser.parse_args(["/path", "--exclude", "*.tmp", "--exclude", "*.log"])
        assert len(args.exclude) == 2

    def test_exclude_dir(self):
        """--exclude-dir node_modules 应正确解析。"""
        parser = build_parser()
        args = parser.parse_args(["/path", "--exclude-dir", "node_modules"])
        assert "node_modules" in args.exclude_dirs


class TestCLIInitGlobal:
    """测试 init --global 参数。"""

    def test_init_global_flag(self):
        """fclean init --global 应设置 global_config=True。"""
        parser = build_parser()
        args = parser.parse_args(["init", "--global"])
        assert args.global_config is True
