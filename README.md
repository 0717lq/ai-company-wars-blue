# fclean — 又安全又好看的命令行文件整理工具

> 一条命令，把乱糟糟的文件夹整理得井井有条。

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 特性

- 🛡️ **默认安全**: 先 dry-run 预览，再加 `--execute` 执行
- ↩️ **可回滚**: 每次操作自动记录，`fclean --undo` 随时回滚
- 🎨 **好看**: 彩色表格输出，不同文件类别不同颜色
- 🗂️ **智能分类**: 自动按文件类型归类（图片、文档、视频、音频、压缩包、代码）
- 📊 **详细统计**: 移动了多少文件、每个类别多少、总大小
- 🔧 **灵活**: 支持排除文件/目录，支持自定义规则

## 安装

```bash
# 开发模式安装
pip install -e .

# 或安装包含测试依赖
pip install -e ".[dev]"
```

## 用法

```bash
# 预览整理效果（默认 dry-run，不实际移动）
fclean ~/Downloads

# 实际执行整理
fclean ~/Downloads --execute

# 回滚上一次整理
fclean --undo

# 查看 undo 历史
fclean --history

# 排除特定文件
fclean ~/Downloads --exclude "*.tmp" --exclude-dir node_modules

# 查看帮助
fclean --help
```

### 整理效果

运行后，目录结构会变成这样：

```
Downloads/
├── 图片/          # .jpg, .png, .gif ...
├── 文档/          # .pdf, .docx, .txt ...
├── 视频/          # .mp4, .avi, .mkv ...
├── 音频/          # .mp3, .wav, .flac ...
├── 压缩包/        # .zip, .rar, .7z ...
├── 代码/          # .py, .js, .html ...
└── 其他/          # 未识别的文件类型
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 运行测试（含覆盖率）
pytest tests/ --cov=src/fclean -v
```

## 为什么用 fclean？

| 特性 | fclean | organize-cli | FileBot |
|------|--------|-------------|---------|
| Dry-run 模式 | ✅ 默认开启 | ✅ | ❌ |
| 回滚 (undo) | ✅ | ❌ | ❌ |
| 彩色输出 | ✅ (rich) | ❌ | ❌ |
| 中文支持 | ✅ | ❌ | ❌ |
| 简单直观 | ✅ 一条命令 | ❌ 需配置文件 | ❌ |
