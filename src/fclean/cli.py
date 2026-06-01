"""fclean 命令行入口。

使用 argparse 解析参数，支持子命令（init, stats, config, organize, rename, dupes, watch, plugin）。
核心逻辑委托给 commands.py、formatters.py 和各业务模块。
默认 dry-run，加上 --execute 才实际执行，--undo 回滚。

所有子命令支持 --json/-j 输出，供 AI Agent 解析。

用法:
    fclean ~/Downloads                  # dry-run 预览（默认 organize）
    fclean organize ~/Downloads         # 同上，显式子命令
    fclean organize ~/Downloads --execute # 实际整理
    fclean init                         # 生成配置文件
    fclean stats ~/Downloads            # 目录统计
    fclean stats --chart ~/Downloads    # ASCII 图表
    fclean stats --top 10 ~/Downloads   # 大文件 Top-N
    fclean config                       # 查看当前配置
    fclean --undo                       # 回滚
    fclean --history                    # undo 历史
    fclean dupes ~/Downloads            # 重复文件检测
    fclean rename "*.jpg" --pattern "vacation_{n:03d}"  # 批量重命名
    fclean watch ~/Downloads            # 文件监控
    fclean plugin list                  # 列出插件
    fclean plugin create my-plugin      # 创建插件模板
    fclean --json ~/Downloads           # JSON 输出
    fclean --install-completion         # 安装 shell 补全
"""

import argparse
import sys
from datetime import datetime, timezone

from fclean import __version__
from fclean.commands import (
    run_config,
    run_dupes,
    run_init,
    run_organize,
    run_plugin,
    run_rename,
    run_stats,
    run_watch,
)
from fclean.formatters import (
    history_to_json,
    print_json,
    print_undo_history,
    print_undo_result,
    undo_to_json,
)
from fclean.undo import list_undo_logs, undo_last

# 删除策略选项
DELETE_STRATEGIES = ["newest", "oldest", "path"]


def build_parser():
    """构建参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="fclean",
        description="又安全又好看的命令行文件整理工具 — 按文件类型自动归类",
        epilog="示例: fclean ~/Downloads              # 预览\n"
               "       fclean organize ~/Downloads     # 预览（显式子命令）\n"
               "       fclean organize ~/Downloads --execute  # 执行\n"
               "       fclean init                      # 生成配置\n"
               "       fclean stats ~/Downloads         # 统计\n"
               "       fclean config                     # 查看当前配置\n"
               "       fclean rename \"*.jpg\" --pattern \"vacation_{n:03d}\"  # 预览重命名\n"
               "       fclean rename \"*.jpg\" --pattern \"vacation_{n:03d}\" --execute  # 执行\n"
               "       fclean dupes ~/Downloads         # 重复文件检测\n"
               "       fclean watch ~/Downloads         # 文件监控\n"
               "       fclean plugin list               # 列出插件\n"
               "       fclean --json ~/Downloads        # JSON 输出\n"
               "       fclean --undo                     # 回滚\n"
               "       fclean --install-completion       # 安装 shell 补全",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"fclean v{__version__}",
    )

    parser.add_argument(
        "--undo",
        action="store_true",
        help="回滚上一次整理操作",
    )

    parser.add_argument(
        "--history",
        action="store_true",
        help="查看 undo 历史记录",
    )

    parser.add_argument(
        "--json", "-j",
        action="store_true",
        default=False,
        help="以 JSON 格式输出（供 AI Agent 解析）",
    )

    parser.add_argument(
        "--install-completion",
        action="store_true",
        dest="install_completion",
        help="安装 shell 自动补全（bash/zsh/fish）",
    )

    # 第一个位置参数：可能是子命令，也可能是路径
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        help="子命令: init, stats, config, organize, rename, dupes, watch, plugin，或直接传入路径",
    )

    # 第二个位置参数：用于子命令的参数
    parser.add_argument(
        "arg",
        nargs="?",
        default=None,
        help="子命令的参数（如 stats 的目标路径）",
    )

    # organize 子命令的选项
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        dest="dry_run",
        help="预览模式（默认启用），只显示拟操作，不实际移动文件",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="实际执行文件整理（默认只预览）",
    )

    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="排除匹配模式的文件（可多次使用），如 --exclude '*.tmp'",
    )

    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        dest="exclude_dirs",
        help="排除的目录名（可多次使用），如 --exclude-dir node_modules",
    )

    # init 子命令的选项
    parser.add_argument(
        "--global",
        action="store_true",
        dest="global_config",
        help="将配置文件写入 ~/.fcleanrc 而非当前目录",
    )

    # rename 子命令的选项
    parser.add_argument(
        "--pattern", "-p",
        default=None,
        help="命名模板（rename 子命令专用），如 'vacation_{n:03d}'",
    )

    # dupes 子命令的选项
    parser.add_argument(
        "--min-size",
        default=None,
        dest="min_size",
        help="最小文件大小（dupes 子命令专用），如 '1MB', '500KB'",
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        default=False,
        help="删除重复文件（dupes 子命令专用）",
    )

    parser.add_argument(
        "--strategy",
        default="newest",
        choices=DELETE_STRATEGIES,
        help="删除保留策略（dupes 子命令专用），默认 newest",
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        dest="no_progress",
        default=False,
        help="不显示进度条（dupes 子命令专用）",
    )

    # watch 子命令的选项
    parser.add_argument(
        "--auto",
        action="store_true",
        default=False,
        help="自动执行整理（watch 子命令专用，默认 dry-run）",
    )

    # stats 子命令的选项
    parser.add_argument(
        "--chart",
        action="store_true",
        default=False,
        help="输出 ASCII 图表可视化（stats 子命令专用）",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="列出占用空间最大的 N 个文件（stats 子命令专用）",
    )

    # plugin 子命令的选项
    parser.add_argument(
        "--plugin-action",
        default=None,
        dest="plugin_action",
        help=argparse.SUPPRESS,  # 内部使用，由 _parse_plugin_args 设置
    )

    parser.add_argument(
        "--plugin-name",
        default=None,
        dest="plugin_name",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--plugin-source",
        default=None,
        dest="plugin_source",
        help=argparse.SUPPRESS,
    )

    return parser


def _parse_plugin_args(args):
    """解析 plugin 子命令的额外参数。

    plugin 子命令格式: fclean plugin <action> [name/source]
    需要从 command + arg 中提取。
    """
    # plugin 子命令的 action 和参数都通过 arg 传递
    # 格式: fclean plugin list / fclean plugin info my-plugin / fclean plugin install file.py
    # 但 argparse 只有两个位置参数（command=plugin, arg=action）
    # 需要从 sys.argv 中额外提取
    raw_args = sys.argv[1:] if hasattr(sys, 'argv') else []

    # 找到 "plugin" 后面的参数
    plugin_idx = None
    for i, a in enumerate(raw_args):
        if a == "plugin":
            plugin_idx = i
            break

    if plugin_idx is not None and plugin_idx + 1 < len(raw_args):
        action = raw_args[plugin_idx + 1]
        if action not in ("--json", "-j"):
            args.plugin_action = action
        if plugin_idx + 2 < len(raw_args):
            next_arg = raw_args[plugin_idx + 2]
            if not next_arg.startswith("-"):
                if action in ("info", "create", "uninstall"):
                    args.plugin_name = next_arg
                elif action == "install":
                    args.plugin_source = next_arg


def _install_completion():
    """安装 shell 自动补全。"""
    import os as os_module

    shell = os_module.environ.get("SHELL", "")

    if "zsh" in shell:
        from pathlib import Path
        zsh_func_path = Path.home() / ".zsh" / "completion"
        zsh_func_path.mkdir(parents=True, exist_ok=True)

        comp_file = zsh_func_path / "_fclean"
        comp_file.write_text(
            "#compdef fclean\n"
            f"# fclean v{__version__} shell completion for zsh\n"
            "_fclean() {\n"
            '  local -a subcmds\n'
            '  subcmds=("init" "stats" "config" "organize" "rename" "dupes" "watch" "plugin")\n'
            '  _arguments \\\n'
            '    "--version[show version]" \\\n'
            '    "--undo[rollback last operation]" \\\n'
            '    "--history[view undo history]" \\\n'
            '    "--json[JSON output]" \\\n'
            '    "1: :->cmd" \\\n'
            '    "*::arg:->args"\n'
            '  case $state in\n'
            '    cmd) _describe "fclean subcommand" subcmds ;;\n'
            '  esac\n'
            "}\n"
            "_fclean \"$@\"\n",
            encoding="utf-8",
        )
        print(f"✅ 已安装 zsh 补全: {comp_file}")
        print("   将以下内容添加到 ~/.zshrc:")
        print(f"   fpath=({zsh_func_path} $fpath)")
        print("   autoload -Uz compinit && compinit")

    elif "fish" in shell:
        from pathlib import Path
        fish_completions = Path.home() / ".config" / "fish" / "completions"
        fish_completions.mkdir(parents=True, exist_ok=True)

        comp_file = fish_completions / "fclean.fish"
        comp_file.write_text(
            f"# fclean v{__version__} shell completion for fish\n"
            "complete -c fclean -f\n"
            'complete -c fclean -l version -d "Show version"\n'
            'complete -c fclean -l undo -d "Rollback last operation"\n'
            'complete -c fclean -l history -d "View undo history"\n'
            'complete -c fclean -l json -d "JSON output"\n'
            'complete -c fclean -l execute -d "Execute operation"\n'
            'complete -c fclean -n "__fish_use_subcommand" -a init -d "Generate config"\n'
            'complete -c fclean -n "__fish_use_subcommand" -a stats -d "Directory statistics"\n'
            'complete -c fclean -n "__fish_use_subcommand" -a config -d "Show current config"\n'
            'complete -c fclean -n "__fish_use_subcommand" -a organize -d "Organize files"\n'
            'complete -c fclean -n "__fish_use_subcommand" -a rename -d "Batch rename"\n'
            'complete -c fclean -n "__fish_use_subcommand" -a dupes -d "Find duplicates"\n'
            'complete -c fclean -n "__fish_use_subcommand" -a watch -d "Watch directory"\n'
            'complete -c fclean -n "__fish_use_subcommand" -a plugin -d "Manage plugins"\n',
            encoding="utf-8",
        )
        print(f"✅ 已安装 fish 补全: {comp_file}")

    else:
        # Bash 补全
        from pathlib import Path
        bash_completion = Path.home() / ".bash_completion.d"
        bash_completion.mkdir(parents=True, exist_ok=True)

        comp_file = bash_completion / "fclean"
        comp_file.write_text(
            f"# fclean v{__version__} shell completion for bash\n"
            "_fclean_completions() {\n"
            '  local cur prev\n'
            '  COMPREPLY=()\n'
            '  cur="${COMP_WORDS[COMP_CWORD]}"\n'
            '  prev="${COMP_WORDS[COMP_CWORD-1]}"\n'
            '  if [[ $COMP_CWORD -eq 1 ]]; then\n'
            '    local cmds="init stats config organize rename"\n'
            '    cmds="$cmds dupes watch plugin"\n'
            '    COMPREPLY=( $(compgen -W "$cmds" -- "$cur") )\n'
            '  fi\n'
            '  return 0\n'
            "}\n"
            "complete -F _fclean_completions fclean\n",
            encoding="utf-8",
        )
        print(f"✅ 已安装 bash 补全: {comp_file}")
        print("   将以下内容添加到 ~/.bashrc:")
        print(f"   source {comp_file}")


def main():
    """CLI 主入口。"""
    parser = build_parser()
    args = parser.parse_args()

    # --install-completion 模式
    if args.install_completion:
        _install_completion()
        return

    # --undo 模式
    if args.undo:
        try:
            result = undo_last()
            if args.json:
                print_json(undo_to_json(result))
            else:
                print_undo_result(result)
        except FileNotFoundError as e:
            if args.json:
                print_json({
                    "tool": "fclean",
                    "command": "undo",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "status": "error",
                    "error": str(e),
                })
            else:
                print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        return

    # --history 模式
    if args.history:
        logs = list_undo_logs()
        if args.json:
            print_json(history_to_json(logs))
        else:
            print_undo_history(logs)
        return

    # 没有参数 -> 默认当前目录 organize
    if args.command is None:
        run_organize(args)
        return

    # 检查子命令
    cmd = args.command

    if cmd == "init":
        run_init(args)
    elif cmd == "stats":
        run_stats(args)
    elif cmd == "config":
        run_config(args)
    elif cmd == "organize":
        run_organize(args)
    elif cmd == "rename":
        run_rename(args)
    elif cmd == "dupes":
        run_dupes(args)
    elif cmd == "watch":
        run_watch(args)
    elif cmd == "plugin":
        _parse_plugin_args(args)
        run_plugin(args)
    else:
        # 不是已知子命令，当作路径处理 -> organize
        run_organize(args)


if __name__ == "__main__":
    main()
