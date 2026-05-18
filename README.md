<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/tests-53%20passed-brightgreen?style=for-the-badge" alt="Tests: 53 passed">
  <img src="https://img.shields.io/badge/PRs-welcome-orange.svg?style=for-the-badge" alt="PRs Welcome">
</p>

<h1 align="center">
  🧹 fclean
</h1>

<p align="center">
  <strong>又安全又好看的命令行文件整理工具</strong><br>
  <em>一条命令，把乱糟糟的文件夹整理得井井有条。</em>
</p>

<p align="center">
  <code>pip install fclean</code> • <code>fclean ~/Downloads</code> • <code>fclean --undo</code>
</p>

---

## 📸 看看效果

```
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
│ ...                  │          │
└──────────────────────┴──────────┘

📁 文档
┌──────────────────────┬──────────┐
│ 文件名               │ 大小     │
├──────────────────────┼──────────┤
│ report.pdf           │  3.2MB   │
│ meeting_notes.docx   │  128.5KB │
│ README.txt           │  4.1KB   │
│ ...                  │          │
└──────────────────────┴──────────┘

📁 视频  📁 音频  📁 压缩包  📁 代码  📁 其他

总计: 将移动 128 个文件 (156.3MB)
提示: 加 --execute 执行整理
```

## ✨ 特性一览

| 特性 | 说明 |
|------|------|
| 🛡️ **默认安全** | 先 dry-run 预览，确认无误再加 `--execute` 执行 |
| ↩️ **可回滚** | 每次操作自动记录，`fclean --undo` 一键恢复到整理前 |
| 🎨 **好看** | 基于 rich 的彩色表格输出，不同类别不同颜色 |
| 🗂️ **智能分类** | 自动识别图片、文档、视频、音频、压缩包、代码、其他（100+ 扩展名） |
| 📊 **详细统计** | 移动了多少文件、每个类别多少、总大小一目了然 |
| 🔧 **灵活强大** | 支持排除文件/目录，支持自定义规则扩展 |
| ⚡ **零配置** | 安装即用，无需任何配置文件 |

## 🚀 安装

```bash
# 推荐：pip 安装
pip install fclean

# 或从源码安装
git clone https://github.com/0717lq/ai-company-wars-blue.git
cd ai-company-wars-blue
pip install -e .

# 开发模式（含测试依赖）
pip install -e ".[dev]"
```

## 💻 使用教程

### 快速上手 — 只需 3 步

```bash
# 第 1 步：预览整理效果（默认 dry-run，不会碰你的文件）
fclean ~/Downloads

# 第 2 步：确认无误，实际执行
fclean ~/Downloads --execute

# 第 3 步（可选）：后悔了？一键回滚
fclean --undo
```

### 更多用法

```bash
# 查看 undo 历史
fclean --history

# 排除特定文件类型和目录
fclean ~/Downloads --exclude "*.tmp" --exclude-dir node_modules

# 整理当前目录
fclean

# 查看帮助
fclean --help

# 查看版本
fclean --version
```

### 整理效果

运行后，目录结构会变成这样：

```
Downloads/
├── 图片/          # .jpg, .png, .gif, .svg, .webp ...
├── 文档/          # .pdf, .docx, .txt, .xlsx ...
├── 视频/          # .mp4, .avi, .mkv, .mov ...
├── 音频/          # .mp3, .wav, .flac, .aac ...
├── 压缩包/        # .zip, .rar, .7z, .tar.gz ...
├── 代码/          # .py, .js, .html, .css ...
└── 其他/          # 未识别的文件类型
```

## 🧪 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行全部测试（53 个测试全部通过 ✅）
pytest tests/ -v

# 运行测试含覆盖率
pytest tests/ --cov=src/fclean -v

# 贡献指南
# 欢迎提交 PR！请确保测试通过后再发起
```

## 🤔 为什么选 fclean？

**市面上的文件整理工具很多，但都有痛点：**

| 特性 | 🧹 **fclean** | `organize-cli` | `FileBot` | 手动整理 |
|------|:---:|:---:|:---:|:---:|
| Dry-run 预览 | ✅ **默认开启** | ✅ | ❌ | ❌ |
| 一键回滚 (undo) | ✅ **独家** | ❌ | ❌ | ❌ |
| 彩色 rich 输出 | ✅ **独家** | ❌ | ❌ | ❌ |
| 中文目录名 | ✅ **独家** | ❌ | ❌ | ❌ |
| 零配置即用 | ✅ **是** | ❌ 需配置 | ❌ | — |
| 安全第一设计 | ✅ **默认** | ⚠️ 危险 | ❌ | — |

**fclean 的核心设计哲学：安全比速度更重要。** 你永远不会因为误操作而丢失文件。

## 📦 支持的文件类型

| 类别 | 扩展名（部分） |
|------|---------------|
| 🖼️ 图片 | `.jpg` `.jpeg` `.png` `.gif` `.svg` `.webp` `.bmp` `.ico` |
| 📄 文档 | `.pdf` `.docx` `.doc` `.xlsx` `.pptx` `.txt` `.md` `.csv` |
| 🎬 视频 | `.mp4` `.avi` `.mkv` `.mov` `.wmv` `.flv` `.webm` |
| 🎵 音频 | `.mp3` `.wav` `.flac` `.aac` `.ogg` `.m4a` |
| 📦 压缩包 | `.zip` `.rar` `.7z` `.tar` `.gz` `.bz2` `.xz` |
| 💻 代码 | `.py` `.js` `.ts` `.html` `.css` `.java` `.cpp` `.go` `.rs` |
| ❓ 其他 | 以上未覆盖的文件类型 |

## 📄 许可

[MIT License](LICENSE) — 欢迎自由使用、修改和分发。

---

<p align="center">
  <b>fclean</b> — 安全第一，拒绝手滑<br>
  <a href="https://github.com/0717lq/ai-company-wars-blue">GitHub</a> •
  <a href="https://pypi.org/project/fclean/">PyPI</a> •
  <a href="LICENSE">MIT License</a>
</p>
