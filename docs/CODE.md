# fclean v0.6.0 — 核心代码文档

## 插件系统 API

### PluginBase (plugin.py)

```python
from fclean.plugin import PluginBase

class MyPlugin(PluginBase):
    name = "my-plugin"          # 插件名（必须）
    version = "1.0.0"           # 版本号（必须）
    description = "描述"        # 描述（必须）

    def classify(self, file_path: Path) -> str | None:
        """分类文件。返回类别名或 None（不处理）。"""

    def transform(self, file_path: Path, category: str) -> Path | None:
        """自定义移动目标。返回目标路径或 None（用默认规则）。"""

    def summarize(self, stats: dict) -> str | None:
        """自定义报告格式。返回报告文本或 None（用默认格式）。"""
```

### PluginManager (plugin_manager.py)

```python
from fclean.plugin_manager import PluginManager

manager = PluginManager(plugin_dir=Path("~/.fclean/plugins"))
manager.discover_and_load()          # 扫描并加载插件
manager.install_plugin(source_path)  # 安装插件
manager.uninstall_plugin("name")     # 卸载插件
manager.list_plugins()               # 列出所有插件
manager.get_plugin_info("name")      # 获取插件详情

# Hook 执行（链式调用，第一个非 None 结果胜出）
category = manager.run_classify(file_path)
target = manager.run_transform(file_path, category)
report = manager.run_summarize(stats)
```

## CLI 架构

### 入口 (cli.py)
- `build_parser()`: 构建 argparse 解析器
- `main()`: CLI 主入口，路由到 commands.py 的 run_* 函数
- `_install_completion()`: bash/zsh/fish 补全安装
- `_parse_plugin_args()`: plugin 子命令额外参数解析

### 命令执行 (commands.py)
- `run_organize(args, config)`: 文件整理
- `run_stats(args)`: 目录统计
- `run_rename(args)`: 批量重命名
- `run_dupes(args)`: 重复文件检测
- `run_watch(args)`: 文件监控
- `run_init(args)`: 生成配置文件
- `run_config(args)`: 查看当前配置
- `run_plugin(args)`: 插件管理

### 格式化 (formatters.py)
- `make_json_envelope(command, data)`: 统一 JSON 包装
- `print_json(data)`: JSON 输出
- `organize_to_json(result)`: OrganizeResult → JSON
- `stats_to_json(stats, path)`: 统计 → JSON
- `rename_to_json(plan, pairs)`: 重命名 → JSON
- `undo_to_json(result)`: Undo → JSON
- `history_to_json(logs)`: 历史 → JSON
- Rich/纯文本双模式显示函数（print_dry_run, print_execute_result 等）

## 核心业务模块

### organizer.py
- `organize(target_path, dry_run, execute, ...)`: 主入口
- `compute_stats(target_path, config)`: 统计计算
- `FileInfo`: 文件信息类
- `OrganizeResult`: 结果类

### config.py
- `load_config(target_path)`: 加载配置（当前目录 > 用户目录 > 默认）
- `Config.to_dict()`: 序列化
- `generate_example_config()`: 生成示例配置

### dupes.py
- `find_duplicates(target_path, min_size, ...)`: 查找重复文件
- `DupesResult.delete(strategy, interactive)`: 删除重复文件
- `_parse_size(size_str)`: 解析 "1MB" 等大小字符串

### renamer.py
- `generate_rename_plan(target_dir, glob_pattern, template)`: 生成重命名计划
- `RenamePlan.get_rename_pairs()`: 获取重命名对
- `RenamePlan.execute()`: 执行重命名
