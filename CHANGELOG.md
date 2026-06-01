# Changelog

## [v0.6.0] — 2026-06-01 — Plugin Platform & Code Quality

### 🆕 新功能 / New Features

#### 🔌 插件系统 (P0) — 可扩展平台
- **`fclean plugin list`**: 列出已安装插件
- **`fclean plugin info <name>`**: 查看插件详情（版本、描述、支持的 hooks）
- **`fclean plugin install <file.py>`**: 安装插件文件到 `~/.fclean/plugins/`
- **`fclean plugin create <name>`**: 生成插件模板（含 classify/transform/summarize 三个 hook）
- **`fclean plugin uninstall <name>`**: 卸载插件
- 所有 plugin 子命令支持 `--json` 输出
- **差异化设计**（vs 红队 dirsort 插件系统）：
  - `classify`: 文件分类（必须实现）
  - `transform`: 自定义移动目标路径（可选）— 红队无此 hook
  - `summarize`: 自定义统计报告格式（可选）— 红队无此 hook
- 插件异常不影响主流程（容错机制）

#### 📐 CLI 架构重构 (P1) — 消除"上帝文件"
- `cli.py` 从 1331 行拆分为 3 个模块：
  - `cli.py` (~280 行): 纯参数解析 + main() 入口
  - `commands.py` (~550 行): 所有 _run_* 命令执行逻辑
  - `formatters.py` (~310 行): JSON 序列化 + Rich/纯文本显示
- 职责清晰、可测试性提升、消除循环依赖风险

### ⚙️ 工程化 / Engineering
- **Ruff 配置升级**: 4 套规则 → 7 套（新增 N/命名规范、UP/pyupgrade、B/bugbear）
- 修复所有 B904（raise from）、B007（unused loop var）、UP015（unnecessary mode）问题
- 版本号更新至 v0.6.0
- `KNOWN_SUBCOMMANDS` 新增 `"plugin"`

### 🧪 测试强化 / Test Improvements
- **新增 test_plugin.py**: 35 个插件系统测试
  - PluginBase 抽象类测试（不能直接实例化、默认 hook 返回 None、元信息）
  - PluginManager 测试（加载、跳过下划线文件、损坏文件容错、安装/卸载/列出）
  - Hook 执行测试（classify/transform/summarize 匹配、异常容错、优先级）
  - 模板生成测试（合法 Python、包含所有 hook）
  - CLI 集成测试（list、info、JSON 输出）
- 总测试数：273 个（较 v0.5.0 的 238 个增加 35 个）

---

## [v0.5.0] — 2026-05-30 — Production Pipeline & Developer Integration

### 🆕 新功能 / New Features

#### 📦 PyPI 发布 (P0)
- **`pip install fclean`**：GitHub Actions + Trusted Publisher (OIDC) 自动发布
- tag push 触发 (`v*`)，无需手动操作

#### 🐳 Docker 容器化 (P0)
- `Dockerfile`：基于 `python:3.12-slim`，ENTRYPOINT 设为 fclean
- `docker run --rm -v ~/Downloads:/data fclean /data` 一行命令整理
- `.dockerignore` 排除测试/文档等非必要文件

#### 🪝 Pre-commit Hook 集成 (P0)
- `.pre-commit-hooks.yaml`：定义 `fclean-organize` hook
- 默认 dry-run（安全），用户加 `args: [--execute]` 才实际执行

#### 🚫 .fcleanignore 忽略规则 (P1)
- 类似 `.gitignore` 的忽略规则系统
- 支持 glob 模式（`*`, `**`, `?`）和 `!` 取反
- 目录模式（`/` 结尾）和路径模式（含 `/`）
- organize 和 watch 命令自动读取 `.fcleanignore`

#### 👀 fclean watch 文件监控 (P1)
- 基于 watchdog 监听目录变化，新文件自动触发 organize
- 防抖机制（默认 2 秒），避免文件写入中误触发
- `--auto` 模式自动执行（默认 dry-run 预览）
- 可选依赖：`pip install fclean[watch]`

#### 📊 stats 可视化增强 (P1)
- **`fclean stats --chart <path>`**: ASCII 饼图/柱状图，可视化文件类型分布
  - 按数量分布：水平条形图 + 百分比
  - 按大小分布：空间占用条形图 + 百分比
- **`fclean stats --top N <path>`**: 大文件 Top-N 排行
  - 按大小降序排列，显示文件名 + 大小 + 条形图
  - 递归扫描子目录

### ⚙️ 工程化 / Engineering
- 版本号更新至 v0.5.0
- `watchdog>=3.0` 作为可选依赖（extras: `watch`）
- pyproject.toml 新增 keywords: `file-watcher`, `ignore-rules`

### 🧪 测试强化 / Test Improvements
- **新增 test_ignore.py**: .fcleanignore 解析器测试（glob、取反、目录模式）— 25 个测试
- **新增 test_watcher.py**: watch 命令测试（事件处理、防抖、忽略规则集成）— 9 个测试
- **新增 test_stats_viz.py**: 可视化模块测试（饼图、柱状图、Top-N、边界条件）— 23 个测试
- **test_cli.py 新增**: --chart/--top 参数解析测试 — 7 个测试
- 总测试数：238 个（较 v0.4.0 的 176 个增加 62 个）

---

## [v0.4.0] — 2026-05-20 — AI Agent Era

### 🆕 新功能 / New Features

#### 🤖 AI Agent First (P0) — 所有命令支持 `--json` 输出
- **`fclean --json <path>`**: organize dry-run/execute 输出结构化 JSON
- **`fclean stats --json <path>`**: 目录统计 JSON 输出（含分类详情）
- **`fclean rename --json`**: 批量重命名 JSON 输出
- **`fclean dupes --json`**: 重复文件检测 JSON 输出
- **`fclean --json --undo`**: undo 回滚 JSON 输出
- **`fclean --json --history`**: undo 历史 JSON 输出
- 标准化 JSON schema: 所有输出含 `tool`, `command`, `timestamp` 元数据字段
- AI Agent 可直接解析决策，无需解析彩色表格

#### 🗂️ fclean dupes (P0) — 重复文件检测与清理
- **SHA-256 逐块哈希**：避免大文件一次性加载到内存
- **Size 预过滤**：不同大小的文件不哈希，显著提升性能
- **多线程并行**：`concurrent.futures.ThreadPoolExecutor` 最大 4 workers
- **Rich 进度条**：`rich.progress` 显示扫描和哈希进度
- **`--min-size`**：跳过小文件，如 `--min-size 1MB`
- **`--delete`**：安全删除重复文件，默认保留最新版本
- **`--strategy newest|oldest|path`**：自定义保留策略
- **Undo 集成**：删除操作自动记录到 undo 日志，可回滚
- **交互确认模式**：逐组确认删除（待实现）

#### 📦 Market Polish (P1)
- **Shell 自动补全**：`fclean --install-completion` 支持 bash/zsh/fish
- **Agent Skill**：`.hermes/skills/fclean.md` — AI Agent 可直接调用 fclean
- **GitHub Topics**：添加 `fclean`, `file-organizer`, `cli`, `python`, `file-management`, `productivity`, `duplicate-files`, `batch-rename`, `dry-run`
- **README 新增章节**：AI Agent Integration（JSON 用法、jq 示例、Hermes Agent 集成）

### 🧪 测试强化 / Test Improvements
- **新增 test_dupes.py**: 25+ 个重复文件检测测试用例
  - SHA-256 哈希正确性测试（文本、二进制、大文件、空文件）
  - 重复检测核心逻辑（无重复、单组、多组、三个副本）
  - 边界情况（空目录、隐藏文件、不同大小、空文件）
  - --min-size 参数测试
  - 删除操作测试（newest/oldest 策略）
  - JSON/dict 输出测试

### ⚙️ 工程化 / Engineering
- 版本号更新至 v0.4.0
- 新增 `src/fclean/dupes.py` 模块（~500 行）
- `cli.py` 重构：增加 JSON 输出函数、dupes 子命令、completion 安装

---

## [v0.3.0] — 2026-05-19 — Market-Ready

### 🆕 新功能 / New Features
- **Batch Rename**: `fclean rename "*.jpg" --pattern "vacation_{n:03d}"` — 批量重命名文件
  - 支持模板变量: `{n}` (序列号), `{n:03d}` (补零), `{date}` (修改日期), `{ext}` (扩展名)
  - 默认 dry-run 预览，加 `--execute` 执行
  - 重命名操作可通过 `fclean --undo` 回滚
  - 自动处理文件名冲突（添加数字后缀）
  - Glob 模式匹配（`*.jpg`, `IMG_*.png` 等）
- **Rename Undo 集成**: 重命名操作自动记录到 undo 系统，与 organize undo 共存

### 📖 文档升级 / Documentation Upgrade
- **中英双语 README**: 完整英文版 + 中文版，12KB+
- **CI Badge**: GitHub Actions workflow badge 在 README 顶部
- **对比表更新**: 增加 dirsort（红队项目）对比
- **配置系统文档**: 详细说明 `.fcleanrc` 使用流程
- **CONTRIBUTING.md**: 完整的开源贡献指南（中英双语）
  - 项目结构说明、开发环境搭建、测试指南
  - 代码风格（Ruff）、PR 流程、Commit 规范
  - Issue 模板指南

### 🧪 测试强化 / Test Improvements
- **新增 test_renamer.py**: 33 个重命名测试用例
  - 模板变量解析（{n}, {n:03d}, {date}, {ext}）
  - Glob 匹配、排序、防冲突
  - Unicode 文件名、空目录、权限错误
- **新增 test_edge_cases.py**: 19 个边界情况测试
  - 空目录整理、权限错误跳过
  - 隐藏文件排除、Unicode 文件名
  - 深层目录、超长文件名
  - 重命名冲突处理
- **CLI 测试新增**: rename 子命令参数解析测试

### ⚙️ 工程化 / Engineering
- 版本号更新至 v0.3.0

## [v0.2.0] — 2026-05-19 — 专业化与配置化

### 🆕 新增功能
- **配置系统 (.fcleanrc)**: 支持 YAML 配置文件自定义分类规则
  - `fclean init` 命令生成配置文件
  - `fclean init --global` 生成到 ~/.fcleanrc
  - 自动检测当前目录或用户目录的 .fcleanrc
  - 配置优先级: CLI 参数 > .fcleanrc > 默认规则
- **Stats 命令**: `fclean stats <path>` 显示目录文件统计
  - 按类别分组统计文件数量和大小
  - Rich 表格 + 条形图输出
- **Config 命令**: `fclean config` 查看当前生效的完整配置
- **Progress Spinner**: organize 和 stats 操作显示进度指示

### ⚙️ 工程化改进
- **CI 搭建**: GitHub Actions 支持 Python 3.9–3.12 三版本矩阵测试
- **Ruff 集成**: 添加 lint 检查和 CI 步骤
- **Coverage 配置**: pytest-cov 集成，覆盖率 ≥ 80%
- **测试文件拆分**: 从 3 个测试文件扩展到 5 个
  - 新增 `test_config.py` 配置加载测试
  - 新增 `test_cli.py` CLI 参数测试

### 🔧 内部重构
- `organizer.py` 支持可选的 `Config` 参数
- `rules.py` 支持配置驱动的分类规则
- `cli.py` 使用子命令架构（向后兼容）
- `pyproject.toml` 添加 PyYAML 依赖和 tool 配置

## [v0.1.0] — 2026-05-18 — MVP

### 🆕 首次发布
- 7 大类文件分类（图片、文档、视频、音频、压缩包、代码、其他）
- `fclean <path>` 整理命令
- Dry-run 预览模式（默认）
- `--execute` 实际执行
- `--undo` 回滚操作
- `--history` 查看操作历史
- Rich 彩色表格输出
- 文件排除模式 (`--exclude`, `--exclude-dir`)
- 自动重名处理（安全移动，不覆盖）
- 53 个 pytest 测试用例
