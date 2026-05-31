<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/github/actions/workflow/status/0717lq/ai-company-wars-blue/ci.yml?style=for-the-badge&logo=github" alt="CI">
  <img src="https://img.shields.io/badge/tests-238%20passed-brightgreen?style=for-the-badge&logo=pytest" alt="238 tests passed">
  <img src="https://img.shields.io/badge/PRs-welcome-orange.svg?style=for-the-badge" alt="PRs Welcome">
  <img src="https://img.shields.io/github/v/release/0717lq/ai-company-wars-blue?style=for-the-badge&logo=github" alt="Latest Release">
</p>

<h1 align="center">
  🧹 fclean
</h1>

<p align="center">
  <strong>Safe, beautiful CLI tool to organize messy folders by file type</strong><br>
  <em>又安全又好看的命令行文件整理工具 — 一条命令，把乱糟糟的文件夹整理得井井有条。</em>
</p>

<p align="center">
  <code>pip install fclean</code> •
  <code>fclean ~/Downloads</code> •
  <code>fclean rename "*.jpg" --pattern "vacation_{n:03d}"</code> •
  <code>fclean --undo</code>
</p>

---

[![CI](https://github.com/0717lq/ai-company-wars-blue/actions/workflows/ci.yml/badge.svg)](https://github.com/0717lq/ai-company-wars-blue/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-238%20passed-brightgreen)](https://github.com/0717lq/ai-company-wars-blue/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/0717lq/ai-company-wars-blue)](https://github.com/0717lq/ai-company-wars-blue/releases)

---

## 🎉 What's New

### v0.5.0 — "Production Pipeline" 🚀 *(2026-05-31)*

> From local tool to production-ready — PyPI, Docker, Pre-commit, and beautiful stats charts.

| New Feature | Description | How to Use |
|-------------|-------------|------------|
| 📊 **Stats Visualization** | ASCII pie chart + bar chart for file distribution | `fclean stats --chart ~/Downloads` |
| 📦 **Docker Support** | Official container image, one-line pull & run | `docker run --rm -v ~/Downloads:/data fclean /data` |
| 🪝 **Pre-commit Hook** | Auto-organize files before every commit | Add to `.pre-commit-config.yaml` |
| 👀 **Watch Mode** | Monitor directory, auto-classify new files | `pip install fclean[watch] && fclean watch ~/Downloads` |
| 🚫 **.fcleanignore** | Gitignore-style rules to skip files | Create `.fcleanignore` in target directory |

---

## English / 🇬🇧 English Documentation

### 📖 Overview

**fclean** is a safe, colorful command-line tool that organizes messy folders by file type. It automatically scans your directory, categorizes files (images, documents, videos, audio, archives, code, and more), and moves them into organized subdirectories.

**Design philosophy: Safety over speed.** fclean defaults to dry-run mode — you always preview before executing. Every operation is undoable with a single command.

### ✨ Features

| Feature | Description |
|---------|------------|
| 🛡️ **Safe by default** | Preview first (`dry-run`), execute with `--execute` |
| ↩️ **One-click undo** | Every operation is logged; `fclean --undo` restores everything |
| 🎨 **Beautiful output** | Rich color tables with categories and file sizes |
| 🗂️ **Smart categorization** | 7 categories, 100+ file extensions auto-detected |
| 📊 **Directory stats** | `fclean stats <path>` — file counts, sizes, categories |
| 🔧 **Customizable** | `.fcleanrc` config file for custom rules and exclusions |
| ✏️ **Batch rename** | `fclean rename "*.jpg" --pattern "vacation_{n:03d}"` |
| 🗂️ **Duplicate detection** | `fclean dupes` — SHA-256 hash, safe delete, undo |
| 🤖 **AI Agent native** | `--json` output on every command, Agent Skill file |
| ⚡ **Zero config** | Works out of the box, no setup needed |

### 🚀 Installation

```bash
# Recommended: pip install
pip install fclean

# With watch support (optional)
pip install fclean[watch]

# Docker
docker pull 0717lq/ai-company-wars-blue:latest
# Or build locally:
docker build -t fclean .
docker run --rm -v ~/Downloads:/data fclean /data

# Or from source
git clone https://github.com/0717lq/ai-company-wars-blue.git
cd ai-company-wars-blue
pip install -e .

# Dev mode (with test dependencies)
pip install -e ".[dev]"
```

### 💻 Usage

#### Quick Start — 3 Steps

```bash
# Step 1: Preview what will happen (dry-run, safe!)
fclean ~/Downloads

# Step 2: Confirm and execute
fclean ~/Downloads --execute

# Step 3 (optional): Made a mistake? One-click undo
fclean --undo
```

#### All Commands

| Command | Description |
|---------|-------------|
| `fclean <path>` | Preview organizing files in a directory |
| `fclean <path> --execute` | Execute the organization |
| `fclean init` | Generate `.fcleanrc` configuration |
| `fclean init --global` | Generate config to `~/.fcleanrc` |
| `fclean stats <path>` | Show directory file statistics |
| `fclean stats --chart <path>` | Stats with ASCII pie/bar chart |
| `fclean stats --top 10 <path>` | Top 10 largest files |
| `fclean config` | Display current configuration |
| `fclean rename "*.jpg" --pattern "vacation_{n:03d}"` | Preview batch rename |
| `fclean rename "*.jpg" --pattern "vacation_{n:03d}" --execute` | Execute batch rename |
| `fclean dupes <path>` | Find duplicate files (SHA-256) |
| `fclean dupes <path> --delete` | Delete duplicate files safely |
| `fclean --json <path>` | JSON output for AI Agent |
| `fclean --undo` | Rollback last operation |
| `fclean --history` | View undo history |
| `fclean --install-completion` | Install shell completion (bash/zsh/fish) |

#### Batch Rename

```bash
# Preview (default dry-run)
fclean rename "*.jpg" --pattern "vacation_{n:03d}"

# Output:
# 📋 Rename Preview (dry-run)
# ┌──────────────────────┬──────────────────────────┐
# │ 旧文件名              │ 新文件名                  │
# ├──────────────────────┼──────────────────────────┤
# │ photo_001.jpg        │ vacation_001.jpg         │
# │ beach_2024.jpg       │ vacation_002.jpg         │
# └──────────────────────┴──────────────────────────┘
# 将重命名 2 个文件
# 提示: 加 --execute 执行重命名

# Execute (also undoable!)
fclean rename "*.jpg" --pattern "vacation_{n:03d}" --execute
```

**Pattern variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `{n}` | Sequential number (1-based) | `1`, `2`, `3` |
| `{n:03d}` | Zero-padded number | `001`, `002`, `003` |
| `{date}` | File modification date | `2026-05-19` |
| `{ext}` | Original extension | `.jpg`, `.png` |

### 🤖 AI Agent Integration

fclean is designed from the ground up for **AI Agent native usage**. Every command supports `--json` / `-j` output that returns structured, machine-parseable JSON.

```bash
# AI Agent: preview organize as JSON
fclean --json ~/Downloads

# AI Agent: directory stats as JSON
fclean stats --json ~/Downloads

# AI Agent: check duplicates as JSON
fclean dupes --json ~/Downloads

# AI Agent: preview rename as JSON
fclean rename "*.jpg" --pattern "vacation_{n:03d}" --json

# AI Agent: undo result as JSON
fclean --json --undo
```

**JSON Schema — All outputs include:**
- `tool`: always `"fclean"`
- `command`: subcommand name (`organize`, `stats`, `rename`, `dupes`, `undo`, `history`)
- `timestamp`: ISO 8601 UTC timestamp
- Plus command-specific structured data

**Example:**
```bash
fclean --json ~/Downloads | jq '.summary'
# "42 files scanned, 38 files organized into 3 categories"
```

**Use with AI Agents:**
- [Hermes Agent](https://hermes-agent.nousresearch.com): Skill file at `.hermes/skills/fclean.md`
- Claude Code / Cursor Agent: Use `fclean --json <path>` for structured output
- Pipe to `jq` for filtering: `fclean dupes --json ~/Downloads | jq '.groups'`

**Shell Completion:**
```bash
fclean --install-completion
# Auto-detects bash/zsh/fish and installs completion scripts
```

### 🗂️ Duplicate Detection

```bash
# Scan for duplicates (dry-run, safe)
fclean dupes ~/Downloads

# Skip small files
fclean dupes ~/Downloads --min-size 1MB

# Example output:
# 🗂️  重复文件检测结果
# 扫描了 142 个文件，发现 3 组重复，共 4 个冗余文件
# 可节省空间: 256.0MB

# Delete duplicates (keep newest by default)
fclean dupes ~/Downloads --delete

# Keep oldest instead
fclean dupes ~/Downloads --delete --strategy oldest

# Undo is supported: fclean --undo

# JSON output for AI Agent
fclean dupes --json ~/Downloads
```

**How it works:**
1. Scans directory, groups files by size (different sizes can't be duplicates)
2. SHA-256 hashes same-size files in parallel (max 4 workers)
3. Groups files with identical hashes as duplicates
4. Default dry-run — preview before deleting
5. `--delete` safely removes duplicates, records undo history

#### Example

```bash
$ fclean ~/Downloads

🔍 fclean — Dry Run 预览 (不会实际移动)
扫描到 142 个文件，将移动 128 个文件

📁 图片
┌──────────────────────┬──────────┐
│ 文件名               │ 大小     │
├──────────────────────┼──────────┤
│ photo_2024.jpg       │  2.3MB   │
│ screenshot.png       │  1.1MB   │
│ logo_design.svg      │  45.2KB  │
└──────────────────────┴──────────┘

📁 文档
┌──────────────────────┬──────────┐
│ 文件名               │ 大小     │
├──────────────────────┼──────────┤
│ report.pdf           │  3.2MB   │
│ meeting_notes.docx   │  128.5KB │
│ README.txt           │  4.1KB   │
└──────────────────────┴──────────┘

总计: 将移动 128 个文件 (156.3MB)
提示: 加 --execute 执行整理
```

### ⚙️ Configuration

fclean supports custom configuration via `.fcleanrc` (YAML format).

```bash
# Generate a config file in the current directory
fclean init

# Or generate a global config in ~/
fclean init --global
```

**Config priority:** CLI arguments > `.fcleanrc` > default rules

**Example `.fcleanrc`:**

```yaml
rules:
  - category: 图片
    extensions:
      - .jpg
      - .jpeg
      - .png
      - .gif
      - .webp
      - .svg

  - category: 文档
    extensions:
      - .pdf
      - .docx
      - .txt
      - .md

exclude_patterns:
  - "*.tmp"
  - "*.log"

exclude_dirs:
  - node_modules
  - __pycache__
```

View your current configuration anytime:

```bash
fclean config
```

### 📦 Supported File Types

| Category | Extensions |
|----------|-----------|
| 🖼️ Images | `.jpg` `.jpeg` `.png` `.gif` `.svg` `.webp` `.bmp` `.ico` `.tiff` `.heic` `.avif` |
| 📄 Documents | `.pdf` `.doc` `.docx` `.xls` `.xlsx` `.ppt` `.pptx` `.txt` `.md` `.csv` `.epub` `.mobi` |
| 🎬 Videos | `.mp4` `.avi` `.mkv` `.mov` `.wmv` `.flv` `.webm` `.m4v` `.3gp` `.mpeg` |
| 🎵 Audio | `.mp3` `.wav` `.flac` `.aac` `.ogg` `.wma` `.m4a` `.opus` |
| 📦 Archives | `.zip` `.rar` `.7z` `.tar` `.gz` `.bz2` `.xz` `.zst` `.tgz` |
| 💻 Code | `.py` `.js` `.ts` `.html` `.css` `.java` `.cpp` `.go` `.rs` `.rb` `.php` `.yaml` `.json` `.toml` |
| ❓ Other | Any extension not listed above |

### 🤔 Why fclean?

| Feature | 🧹 **fclean** | `dirsort` (Red Team) | `organize-cli` | Manual |
|---------|:---:|:---:|:---:|:---:|
| Dry-run preview | ✅ **Default** | ✅ Default | ✅ | ❌ |
| One-click undo (organize) | ✅ **Built-in** | ❌ | ❌ | ❌ |
| One-click undo (rename) | ✅ **Built-in** | ❌ | ❌ | ❌ |
| Batch rename | ✅ **Yes** | ❌ | ❌ | — |
| Duplicate detection | ✅ **SHA-256** | ❌ | ❌ | — |
| AI Agent native (`--json`) | ✅ **Yes** | ❌ | ❌ | ❌ |
| Shell completion ($SHELL) | ✅ **Yes** | ❌ | ❌ | ❌ |
| Agent Skill file | ✅ **Hermes/Claude** | ❌ | ❌ | ❌ |
| Rich color output | ✅ **Exclusive** | ❌ | ❌ | ❌ |
| Chinese directory names | ✅ **Exclusive** | ❌ | ❌ | ❌ |
| Config system (`.fcleanrc`) | ✅ **Yes** | ❌ | ✅ | — |
| Directory stats | ✅ **Yes** | ❌ | ❌ | — |
| Stats visualization (charts) | ✅ **ASCII pie+bar** | ❌ | ❌ | — |
| Zero config out of box | ✅ **Yes** | ✅ | ❌ | — |
| Safety-first design | ✅ **Default dry-run** | ⚠️ Dry-run exists | ⚠️ | ❌ |
| Number of subcommands | **6 🏆** | 1 | ~8 | — |
| Test coverage | **238 tests ✅** | Good | Moderate | — |
| Docker support | ✅ **Yes** | ✅ | ❌ | — |
| Pre-commit hook | ✅ **Yes** | ✅ | ❌ | — |

### 🐳 Docker

```bash
# Build image
docker build -t fclean .

# Organize a directory (dry-run by default)
docker run --rm -v ~/Downloads:/data fclean /data

# Execute for real
docker run --rm -v ~/Downloads:/data fclean /data --execute

# JSON output for automation
docker run --rm -v ~/Downloads:/data fclean --json /data
```

### 🪝 Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/0717lq/ai-company-wars-blue
    rev: v0.5.0
    hooks:
      - id: fclean-organize
        # Add --execute to actually move files (default: dry-run)
        # args: [--execute]
```

### 🚫 .fcleanignore

Create a `.fcleanignore` file in your target directory (like `.gitignore`):

```
# Ignore all log files
*.log

# Ignore specific directory
node_modules/

# Except important logs
!important.log
```

Supported patterns: `*`, `**`, `?`, `!` (negation), directory suffix `/`.

### 👀 Watch (Auto-Organize)

Monitor a directory and auto-organize new files:

```bash
# Install watch support
pip install fclean[watch]

# Watch mode (dry-run by default)
fclean watch ~/Downloads

# Auto-execute mode
fclean watch ~/Downloads --auto

# JSON output
fclean watch --json ~/Downloads
```

Features:
- Debounce mechanism (2s default) — waits for file writes to complete
- Respects `.fcleanignore` rules
- Ctrl+C to stop gracefully

### 📊 Stats Visualization

```bash
# ASCII pie chart + bar chart
fclean stats --chart ~/Downloads

# Top 10 largest files
fclean stats --top 10 ~/Downloads

# Combine both
fclean stats --chart --top 10 ~/Downloads

# JSON output (includes top files data)
fclean stats --top 5 --json ~/Downloads
```

Features:
- **`--chart`**: Dual ASCII visualization — file count distribution + space usage distribution
- **`--top N`**: Top-N largest files ranking with size bars
- Works with `--json` (chart is ignored, top files data is included in JSON)

### 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/fclean -v

# Code linting
ruff check src/

# Check coding style
ruff format --check src/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

### 📄 License

[MIT License](LICENSE) — Free to use, modify, and distribute.

---

<p align="center">
  <b>fclean</b> — 安全第一，拒绝手滑 / Safety first, no regrets<br>
  <a href="https://github.com/0717lq/ai-company-wars-blue">GitHub</a> •
  <a href="https://pypi.org/project/fclean/">PyPI</a> •
  <a href="LICENSE">MIT License</a> •
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

---

## 中文 / 🇨🇳 中文文档

### 📖 概述

**fclean** 是一个安全、好看的命令行文件整理工具。它能自动扫描你的文件夹，按文件类型分类（图片、文档、视频、音频、压缩包、代码等），然后帮你整理得井井有条。

**设计理念：安全比速度更重要。** fclean 默认只预览不执行，确保你每次操作前都清楚会发生什么。每次操作都可一键回滚。

### ✨ 特性一览

| 特性 | 说明 |
|------|------|
| 🛡️ **默认安全** | 先 dry-run 预览，确认无误再加 `--execute` 执行 |
| ↩️ **一键回滚** | 每次操作自动记录，`fclean --undo` 一键恢复到整理前 |
| 🎨 **好看** | 基于 rich 的彩色表格输出，不同类别不同颜色 |
| 🗂️ **智能分类** | 自动识别图片、文档、视频、音频、压缩包、代码、其他（100+ 扩展名） |
| 📊 **详细统计** | `fclean stats <path>` 查看目录文件统计 |
| 🔧 **灵活强大** | 支持 `.fcleanrc` 配置文件自定义规则 |
| ✏️ **批量重命名** | `fclean rename "*.jpg" --pattern "vacation_{n:03d}"` 批量重命名 |
| 🗂️ **重复检测** | `fclean dupes <path>` SHA-256 哈希检测，安全删除，一键回滚 |
| 🤖 **AI Agent 原生** | 全命令 `--json` 输出，结构化数据，Agent Skill 文件 |
| ⌨️ **Shell 补全** | `fclean --install-completion` 支持 bash/zsh/fish |
| ⚡ **零配置** | 安装即用，无需任何配置文件 |

### 🚀 安装

```bash
# 推荐：pip 安装
pip install fclean

# 含 watch 支持（可选）
pip install fclean[watch]

# Docker
docker build -t fclean .
docker run --rm -v ~/Downloads:/data fclean /data

# 或从源码安装
git clone https://github.com/0717lq/ai-company-wars-blue.git
cd ai-company-wars-blue
pip install -e .

# 开发模式（含测试依赖）
pip install -e ".[dev]"
```

### 💻 使用教程

#### 快速上手 — 只需 3 步

```bash
# 第 1 步：预览整理效果（默认 dry-run，不会碰你的文件）
fclean ~/Downloads

# 第 2 步：确认无误，实际执行
fclean ~/Downloads --execute

# 第 3 步（可选）：后悔了？一键回滚
fclean --undo
```

#### 所有命令

| 命令 | 说明 |
|------|------|
| `fclean <path>` | 预览整理目录中的文件 |
| `fclean <path> --execute` | 执行整理 |
| `fclean init` | 生成 `.fcleanrc` 配置文件 |
| `fclean init --global` | 生成配置到 `~/.fcleanrc` |
| `fclean stats <path>` | 目录文件统计 |
| `fclean stats --chart <path>` | 带 ASCII 图表的统计 |
| `fclean stats --top 10 <path>` | Top 10 大文件排行 |
| `fclean config` | 查看当前配置 |
| `fclean rename "*.jpg" --pattern "vacation_{n:03d}"` | 预览批量重命名 |
| `fclean rename "*.jpg" --pattern "vacation_{n:03d}" --execute` | 执行批量重命名 |
| `fclean dupes <path>` | 检测重复文件（SHA-256） |
| `fclean dupes <path> --delete` | 安全删除重复文件 |
| `fclean --json <path>` | JSON 输出（AI Agent 友好） |
| `fclean --undo` | 回滚上一次操作 |
| `fclean --history` | 查看回滚历史 |
| `fclean --install-completion` | 安装 shell 自动补全 |

#### 批量重命名

```bash
# 预览（默认 dry-run）
fclean rename "*.jpg" --pattern "vacation_{n:03d}"

# 输出：
# 📋 Rename Preview (dry-run)
# ┌──────────────────────┬──────────────────────────┐
# │ 旧文件名              │ 新文件名                  │
# ├──────────────────────┼──────────────────────────┤
# │ photo_001.jpg        │ vacation_001.jpg         │
# │ beach_2024.jpg       │ vacation_002.jpg         │
# └──────────────────────┴──────────────────────────┘
# 将重命名 2 个文件
# 提示: 加 --execute 执行重命名

# 执行（同样可回滚）
fclean rename "*.jpg" --pattern "vacation_{n:03d}" --execute
```

**模板变量：**

| 变量 | 说明 | 示例 |
|------|------|------|
| `{n}` | 序列号（从 1 开始） | `1`, `2`, `3` |
| `{n:03d}` | 补零序列号 | `001`, `002`, `003` |
| `{date}` | 文件修改日期 | `2026-05-19` |
| `{ext}` | 原扩展名 | `.jpg`, `.png` |

### 🗂️ 重复文件检测

```bash
# 扫描重复文件（dry-run，安全模式）
fclean dupes ~/Downloads

# 跳过小文件
fclean dupes ~/Downloads --min-size 1MB

# 示例输出：
# 🗂️  重复文件检测结果
# 扫描了 142 个文件，发现 3 组重复，共 4 个冗余文件
# 可节省空间: 256.0MB

# 删除重复文件（默认保留最新版本）
fclean dupes ~/Downloads --delete

# 自定义保留策略
fclean dupes ~/Downloads --delete --strategy oldest

# 支持回滚：fclean --undo

# JSON 输出（AI Agent 友好）
fclean dupes --json ~/Downloads
```

**工作原理：**
1. 扫描目录，按文件大小分组（不同大小不可能是重复文件）
2. 对相同大小的文件并行计算 SHA-256 哈希（最多 4 workers）
3. 相同哈希的文件判定为重复
4. 默认 dry-run — 预览后再删除
5. `--delete` 安全删除冗余文件，自动记录 undo 历史

### 🤖 AI Agent 集成

fclean 专为 **AI Agent 原生调用**而设计。每条命令都支持 `--json` / `-j` 参数，返回结构化 JSON。

```bash
# AI Agent：预览整理结果（JSON）
fclean --json ~/Downloads

# AI Agent：目录统计（JSON）
fclean stats --json ~/Downloads

# AI Agent：重复检测（JSON）
fclean dupes --json ~/Downloads

# AI Agent：批量重命名预览（JSON）
fclean rename "*.jpg" --pattern "vacation_{n:03d}" --json

# AI Agent：回滚结果（JSON）
fclean --json --undo
```

**JSON Schema — 所有输出包含：**
- `tool`: 固定为 `"fclean"`
- `command`: 子命令名称（`organize`, `stats`, `rename`, `dupes`, `undo`, `history`）
- `timestamp`: ISO 8601 UTC 时间戳
- 以及命令特有的结构化数据

**示例：**
```bash
fclean --json ~/Downloads | jq '.summary'
# "42 files scanned, 38 files organized into 3 categories"
```

**AI Agent 对接：**
- [Hermes Agent](https://hermes-agent.nousresearch.com)：Skill 文件位于 `.hermes/skills/fclean.md`
- Claude Code / Cursor Agent：使用 `fclean --json <path>` 获取结构化输出
- 管道配合 `jq` 过滤：`fclean dupes --json ~/Downloads | jq '.groups'`

**Shell 自动补全：**
```bash
fclean --install-completion
# 自动检测 bash/zsh/fish 并安装补全脚本
```

### ⚙️ 配置系统

fclean 通过 `.fcleanrc`（YAML 格式）支持自定义配置。

```bash
# 在当前目录生成配置文件
fclean init

# 在用户目录生成全局配置文件
fclean init --global
```

**配置优先级：** CLI 参数 > `.fcleanrc` 配置 > 默认规则

**配置示例：**

```yaml
rules:
  - category: 图片
    extensions:
      - .jpg
      - .jpeg
      - .png
      - .gif

  - category: 文档
    extensions:
      - .pdf
      - .docx
      - .txt
      - .md

exclude_patterns:
  - "*.tmp"
  - "*.log"

exclude_dirs:
  - node_modules
  - __pycache__
```

随时查看当前配置：

```bash
fclean config
```

### 🐳 Docker

```bash
# 构建镜像
docker build -t fclean .

# 整理目录（默认 dry-run 预览）
docker run --rm -v ~/Downloads:/data fclean /data

# 实际执行
docker run --rm -v ~/Downloads:/data fclean /data --execute

# JSON 输出（供自动化脚本）
docker run --rm -v ~/Downloads:/data fclean --json /data
```

### 🪝 Pre-commit Hook

在 `.pre-commit-config.yaml` 中添加：

```yaml
repos:
  - repo: https://github.com/0717lq/ai-company-wars-blue
    rev: v0.5.0
    hooks:
      - id: fclean-organize
        # 加 --execute 才实际移动文件（默认 dry-run）
        # args: [--execute]
```

### 🚫 .fcleanignore 忽略规则

在目标目录创建 `.fcleanignore` 文件（类似 `.gitignore`）：

```
# 忽略所有日志文件
*.log

# 忽略特定目录
node_modules/

# 但保留重要日志
!important.log
```

支持的模式：`*`、`**`、`?`、`!`（取反）、`/` 结尾（目录模式）。

### 👀 Watch 自动监控

监控目录，新文件自动触发整理：

```bash
# 安装 watch 支持
pip install fclean[watch]

# watch 模式（默认 dry-run）
fclean watch ~/Downloads

# 自动执行模式
fclean watch ~/Downloads --auto

# JSON 输出
fclean watch --json ~/Downloads
```

功能特点：
- 防抖机制（默认 2 秒）— 等文件写入完成再触发
- 自动读取 `.fcleanignore` 规则
- Ctrl+C 优雅退出

### 📊 统计可视化

```bash
# ASCII 饼图 + 柱状图
fclean stats --chart ~/Downloads

# Top 10 大文件排行
fclean stats --top 10 ~/Downloads

# 组合使用
fclean stats --chart --top 10 ~/Downloads

# JSON 输出（包含 top files 数据）
fclean stats --top 5 --json ~/Downloads
```

功能特点：
- **`--chart`**：双维度 ASCII 可视化 — 文件数量分布 + 空间占用分布
- **`--top N`**：大文件 Top-N 排行，带大小条形图
- 与 `--json` 兼容（图表忽略，top files 数据包含在 JSON 中）

### 🧪 开发与贡献

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行全部测试
pytest tests/ -v

# 运行测试含覆盖率
pytest tests/ --cov=src/fclean -v

# 代码检查
ruff check src/
```

详见 [CONTRIBUTING.md](CONTRIBUTING.md) 贡献指南。

### 📄 许可

[MIT License](LICENSE) — 欢迎自由使用、修改和分发。

---

<p align="center">
  <b>fclean</b> — 安全第一，拒绝手滑<br>
  <a href="https://github.com/0717lq/ai-company-wars-blue">GitHub</a> •
  <a href="https://pypi.org/project/fclean/">PyPI</a> •
  <a href="LICENSE">MIT License</a> •
  <a href="CONTRIBUTING.md">参与贡献</a>
</p>
