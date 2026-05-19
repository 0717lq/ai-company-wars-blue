# Changelog

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
