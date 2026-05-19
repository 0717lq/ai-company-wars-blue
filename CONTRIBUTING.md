# Contributing to fclean / 参与贡献

Thank you for your interest in contributing to **fclean**! We welcome contributions of all kinds — bug reports, feature requests, documentation improvements, and code contributions.

感谢你对 **fclean** 的兴趣！我们欢迎各种形式的贡献——错误报告、功能建议、文档改进和代码贡献。

## Table of Contents / 目录

- [Code of Conduct / 行为准则](#code-of-conduct--行为准则)
- [Project Structure / 项目结构](#project-structure--项目结构)
- [Development Setup / 开发环境搭建](#development-setup--开发环境搭建)
- [Running Tests / 运行测试](#running-tests--运行测试)
- [Code Style / 代码风格](#code-style--代码风格)
- [Pull Request Process / PR 流程](#pull-request-process--pr-流程)
- [Commit Message Guidelines / Commit 规范](#commit-message-guidelines--commit-规范)
- [Issue Templates / Issue 指南](#issue-templates--issue-指南)

## Code of Conduct / 行为准则

We are committed to providing a welcoming and inclusive experience for everyone. Please be respectful and considerate in all interactions.

我们致力于为所有人提供友好和包容的环境。请在交流中保持尊重和友善。

## Project Structure / 项目结构

```
fclean/
├── src/fclean/           # Source code / 源代码
│   ├── __init__.py       # Package version
│   ├── __main__.py       # Entry point
│   ├── cli.py            # CLI argument parsing and commands
│   ├── config.py         # .fcleanrc configuration system
│   ├── organizer.py      # Core file organization logic
│   ├── renamer.py        # Batch rename functionality
│   ├── rules.py          # File categorization rules
│   └── undo.py           # Undo/rollback system
├── tests/                # Test suite / 测试
│   ├── test_cli.py       # CLI tests
│   ├── test_config.py    # Config tests
│   ├── test_organizer.py # Organizer tests
│   ├── test_undo.py      # Undo tests
│   ├── test_renamer.py   # Rename tests
│   └── test_edge_cases.py# Edge case tests
├── docs/                 # Documentation / 文档
├── pyproject.toml        # Project configuration
├── README.md             # Bilingual README
└── CONTRIBUTING.md       # This file
```

## Development Setup / 开发环境搭建

### Prerequisites / 前提条件

- Python 3.9 or higher
- Git

### Setup Steps / 搭建步骤

```bash
# 1. Clone the repository / 克隆仓库
git clone https://github.com/0717lq/ai-company-wars-blue.git
cd ai-company-wars-blue

# 2. Create a virtual environment (recommended) / 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Install the package in development mode / 安装开发模式
pip install -e ".[dev]"

# 4. Verify installation / 验证安装
fclean --version
```

## Running Tests / 运行测试

```bash
# Run all tests / 运行全部测试
pytest tests/ -v

# Run with coverage / 运行测试并查看覆盖率
pytest tests/ --cov=src/fclean -v

# Run a specific test file / 运行特定测试文件
pytest tests/test_renamer.py -v

# Run a specific test / 运行特定测试用例
pytest tests/test_renamer.py::TestRenamer::test_basic_rename -v

# Run with verbose output / 详细输出模式
pytest tests/ -v --tb=long
```

**Requirements / 要求：**
- All tests must pass before submitting a PR / 提交 PR 前必须通过所有测试
- New features must include tests / 新功能必须包含测试
- Target code coverage: ≥ 80% / 目标覆盖率：≥ 80%

## Code Style / 代码风格

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

我们使用 [Ruff](https://github.com/astral-sh/ruff) 进行代码检查和格式化。

```bash
# Check code style / 检查代码风格
ruff check src/

# Auto-fix issues / 自动修复
ruff check --fix src/

# Format code / 格式化代码
ruff format src/
```

**Style guidelines / 风格指南：**

- Line length: max 100 characters / 最大行宽：100 字符
- Use type hints in function signatures / 函数签名使用类型提示
- Add Chinese comments for core logic / 核心逻辑添加中文注释
- Use descriptive variable names (English) / 使用描述性变量名（英文）
- Follow PEP 8 conventions / 遵循 PEP 8 规范

## Pull Request Process / PR 流程

1. **Fork the repository** / Fork 仓库
2. **Create a feature branch** / 创建功能分支

   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make your changes** / 进行修改
   - Write tests first (TDD approach) / 先写测试（TDD 方式）
   - Keep changes focused on one issue / 一次只解决一个问题
   - Update documentation if needed / 按需更新文档

4. **Run tests and linter** / 运行测试和代码检查

   ```bash
   pytest tests/ -v
   ruff check src/
   ```

5. **Commit your changes** / 提交修改

   ```bash
   git add .
   git commit -m "feat: description of your change"
   ```

6. **Push and create a PR** / 推送并创建 PR

   ```bash
   git push origin feat/your-feature-name
   ```

7. **Describe your PR** / 描述你的 PR
   - What does this PR do? / 这个 PR 做了什么？
   - Why is this change needed? / 为什么需要这个修改？
   - How was it tested? / 如何测试的？
   - Screenshots (if UI related) / 截图（如果是界面相关）

### Branch Naming / 分支命名

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New features | `feat/watch-mode` |
| `fix/` | Bug fixes | `fix/unicode-filename` |
| `docs/` | Documentation | `docs/api-docs` |
| `refactor/` | Code refactoring | `refactor/config-system` |
| `test/` | Test additions | `test/add-edge-cases` |

## Commit Message Guidelines / Commit 规范

We follow [Conventional Commits](https://www.conventionalcommits.org/):

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>: <short description>

[optional body]

[optional footer]
```

**Types / 类型：**

| Type | Usage |
|------|-------|
| `feat:` | New feature / 新功能 |
| `fix:` | Bug fix / 修复 Bug |
| `docs:` | Documentation / 文档 |
| `test:` | Tests / 测试 |
| `refactor:` | Code refactoring / 重构 |
| `style:` | Formatting / 格式调整 |
| `chore:` | Maintenance / 维护 |

**Examples / 示例：**

```
feat: add batch rename command with dry-run support

Implement `fclean rename` with glob pattern matching
and template variables ({n}, {date}, {ext}).

Closes #42
```

```
fix: handle Unicode filenames in organizer

Pathlib handles Unicode correctly; ensure test
coverage for CJK and special characters.
```

## Issue Templates / Issue 指南

### Bug Report / Bug 报告

When reporting a bug, please include:

报告 Bug 时请包含：

1. **fclean version** / fclean 版本: `fclean --version`
2. **Python version** / Python 版本: `python --version`
3. **OS** / 操作系统: Linux/macOS/Windows
4. **Steps to reproduce** / 复现步骤
5. **Expected behavior** / 预期行为
6. **Actual behavior** / 实际行为
7. **Error output (if any)** / 错误输出（如果有）

### Feature Request / 功能建议

When requesting a feature, please include:

建议功能时请包含：

1. **Problem description** / 问题描述
2. **Proposed solution** / 建议方案
3. **Alternative solutions** / 替代方案
4. **Use case / motivation** / 使用场景/动机

## Additional Resources / 其他资源

- [Project README](README.md) — Bilingual documentation / 双语文档
- [GitHub Issues](https://github.com/0717lq/ai-company-wars-blue/issues) — Bug tracker / Bug 跟踪
- [GitHub Discussions](https://github.com/0717lq/ai-company-wars-blue/discussions) — Discussion forum / 讨论区

---

<p align="center">
  Made with ❤️ by the fclean team<br>
  <a href="README.md">← Back to README</a>
</p>
