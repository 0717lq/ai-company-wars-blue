# Changelog

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
