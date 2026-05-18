"""
fclean undo 模块。

记录每一次整理操作到 ~/.fclean/undo/ 目录，支持回滚。
每次整理生成一个 JSON 日志文件，记录所有被移动文件的源路径和目标路径。

用法:
    from fclean.undo import record_operation, undo_last

    record_operation(result)  # 记录操作
    undo_last()               # 回滚上一次
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fclean.organizer import OrganizeResult

# undo 日志目录
UNDO_DIR = Path.home() / ".fclean" / "undo"


def _ensure_undo_dir():
    """确保 undo 目录存在。"""
    UNDO_DIR.mkdir(parents=True, exist_ok=True)


def _get_latest_log() -> Optional[Path]:
    """获取最新的 undo 日志文件路径。"""
    _ensure_undo_dir()
    logs = sorted(UNDO_DIR.iterdir(), reverse=True)
    for log in logs:
        if log.suffix == ".json" and log.is_file():
            return log
    return None


def record_operation(result: OrganizeResult) -> str:
    """
    记录一次整理操作到 undo 日志。

    参数:
        result: OrganizeResult 对象（必须是实际执行过移动的）

    返回:
        日志文件路径

    异常:
        ValueError: 如果没有文件被移动
    """
    if result.total_moved == 0:
        raise ValueError("没有文件被移动，无需记录")

    _ensure_undo_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = UNDO_DIR / f"undo_{timestamp}.json"

    log_data = {
        "timestamp": timestamp,
        "datetime": datetime.now().isoformat(),
        "files_moved": [
            {"source": str(fi.path), "target": str(dst)}
            for fi, dst in result.files_moved
        ],
        "category_counts": result.get_category_counts(),
        "total_moved": result.total_moved,
        "total_size": result.total_size_moved,
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    return str(log_path)


def undo_last() -> OrganizeResult:
    """
    回滚上一次整理操作。

    流程：
    1. 读取最新的 undo 日志
    2. 对每条记录，将文件从目标路径移回源路径
    3. 删除该日志文件

    返回:
        OrganizeResult 对象，包含回滚结果

    异常:
        FileNotFoundError: 没有可回滚的操作
    """
    log_path = _get_latest_log()
    if log_path is None:
        raise FileNotFoundError("没有找到 undo 记录，没有可回滚的操作")

    # 读取日志
    with open(log_path, "r", encoding="utf-8") as f:
        log_data = json.load(f)

    # 执行回滚
    result = OrganizeResult()
    for entry in log_data["files_moved"]:
        src = Path(entry["target"])   # 当前文件所在位置
        dst = Path(entry["source"])   # 原始位置

        if not src.exists():
            result.errors.append((str(src), "文件不存在，可能已被手动删除"))
            continue

        try:
            # 确保目标目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)

            # 如果目标已存在（原始位置已有新文件），添加后缀
            if dst.exists():
                base = dst.stem
                ext = dst.suffix
                counter = 1
                while dst.exists():
                    new_name = f"{base}_restored_{counter}{ext}"
                    dst = dst.parent / new_name
                    counter += 1

            shutil.move(str(src), str(dst))
            result.files_moved.append((src, dst))
        except (PermissionError, OSError) as e:
            result.errors.append((str(src), f"回滚失败: {e}"))

    # 删除 undo 日志
    try:
        log_path.unlink()
    except OSError:
        pass  # 删除失败不影响回滚结果

    return result


def list_undo_logs() -> list[dict]:
    """
    列出所有可用的 undo 日志。

    返回:
        日志信息列表，每条包含 timestamp 和 file_count
    """
    _ensure_undo_dir()
    logs: list[dict] = []
    for log in sorted(UNDO_DIR.iterdir(), reverse=True):
        if log.suffix == ".json" and log.is_file():
            try:
                with open(log, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logs.append({
                    "path": str(log),
                    "timestamp": data.get("timestamp", log.stem),
                    "total_moved": data.get("total_moved", 0),
                    "datetime": data.get("datetime", ""),
                })
            except (json.JSONDecodeError, OSError):
                logs.append({
                    "path": str(log),
                    "timestamp": log.stem.replace("undo_", ""),
                    "total_moved": 0,
                    "datetime": "",
                })
    return logs
