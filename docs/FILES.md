# fclean 文件功能说明

## src/fclean/__init__.py
- 版本声明（当前 v0.2.0）

## src/fclean/cli.py
- 命令行主入口，使用 argparse 解析参数
- 支持子命令：organize（默认）、init、stats、config
- 支持 --undo 回滚、--history 历史查看
- 使用 rich 彩色输出（fallback 到纯文本）
- 支持 --execute 执行、--exclude 排除模式、--exclude-dir 排除目录

## src/fclean/config.py
- Config 类：封装 .fcleanrc YAML 配置文件
- 支持自动检测当前目录和用户目录的 .fcleanrc
- 配置合并策略：CLI 参数 > 配置文件 > 默认规则
- 支持自定义分类规则、排除模式
- 生成示例配置文件

## src/fclean/organizer.py
- FileInfo 类：存储文件路径、名称、大小、类别
- OrganizeResult 类：存储整理结果（移动、跳过、错误统计）
- scan_directory：扫描目录并返回 FileInfo 列表
- organize：执行整理操作（dry-run 或实际执行）
- compute_stats：计算目录文件统计信息
- 支持 Config 对象驱动自定义分类规则

## src/fclean/rules.py
- CATEGORIES：6 大默认类别定义（图片、文档、视频、音频、压缩包、代码）
- classify：根据扩展名分类文件
- get_dir_name：类别 key 转中文目录名
- 支持 Config 对象驱动的分类

## src/fclean/undo.py
- record_operation：记录操作到 ~/.fclean/undo/ 目录
- undo_last：回滚上一次操作
- list_undo_logs：列出所有可用的 undo 日志
