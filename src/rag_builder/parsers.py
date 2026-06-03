"""文档解析器 + 文本分块器。

支持 PDF（pymupdf）、Markdown、纯文本解析，以及多种分块策略。
所有解析函数返回统一的文档字典格式: {"text": str, "source": str, "metadata": dict}

用法:
    docs = parse_pdf("report.pdf")
    docs = parse_markdown("README.md")
    docs = parse_directory("./documents", glob="**/*.md")
    chunks = chunk_text(text, strategy="recursive", chunk_size=512)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ─────────────────────── 文档解析 ───────────────────────


def parse_pdf(path: str | Path, password: str = "") -> list[dict[str, Any]]:
    """解析 PDF 文件，按页提取文本。

    Args:
        path: PDF 文件路径
        password: PDF 密码（如果加密）

    Returns:
        文档列表，每个元素含 text/source/metadata(page)

    Raises:
        FileNotFoundError: 文件不存在
        ImportError: pymupdf 未安装
    """
    try:
        import pymupdf
    except ImportError as err:
        raise ImportError(
            "pymupdf 未安装。请执行: pip install rag-builder[pdf] 或 pip install pymupdf"
        ) from err

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    docs: list[dict[str, Any]] = []
    pdf = pymupdf.open(str(path))

    if password:
        pdf.authenticate(password)

    for page_num in range(len(pdf)):
        page = pdf[page_num]
        text = page.get_text("text")
        if text.strip():
            docs.append({
                "text": text.strip(),
                "source": str(path),
                "metadata": {"page": page_num + 1, "format": "pdf"},
            })

    pdf.close()
    return docs


def parse_markdown(path: str | Path) -> list[dict[str, Any]]:
    """解析 Markdown 文件。

    按一级/二级标题分段，每段作为一个文档。

    Args:
        path: Markdown 文件路径

    Returns:
        文档列表

    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")

    # 按一级/二级标题分段
    sections = _split_by_headers(text)

    docs: list[dict[str, Any]] = []
    for section_text in sections:
        section_text = section_text.strip()
        if section_text:
            docs.append({
                "text": section_text,
                "source": str(path),
                "metadata": {"format": "markdown"},
            })

    # 如果没有标题，整个文件作为一个文档
    if not docs:
        docs.append({
            "text": text.strip(),
            "source": str(path),
            "metadata": {"format": "markdown"},
        })

    return docs


def parse_text(path: str | Path) -> list[dict[str, Any]]:
    """解析纯文本文件。

    Args:
        path: 文本文件路径

    Returns:
        文档列表（单个元素）

    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    return [{
        "text": text.strip(),
        "source": str(path),
        "metadata": {"format": "text"},
    }]


def parse_directory(
    path: str | Path,
    glob: str = "**/*",
    extensions: list[str] | None = None,
) -> list[dict[str, Any]]:
    """解析目录下所有支持的文件。

    Args:
        path: 目录路径
        glob: glob 模式
        extensions: 文件扩展名过滤 (如 [".pdf", ".md"])

    Returns:
        所有文件解析结果的合并列表

    Raises:
        FileNotFoundError: 目录不存在
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"目录不存在: {path}")

    # 默认支持的扩展名
    default_exts = {".pdf", ".md", ".markdown", ".txt", ".text", ".rst"}
    ext_set = set(extensions) if extensions else default_exts

    all_docs: list[dict[str, Any]] = []
    for file_path in sorted(path.glob(glob)):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in ext_set:
            continue

        try:
            if file_path.suffix.lower() == ".pdf":
                docs = parse_pdf(file_path)
            elif file_path.suffix.lower() in (".md", ".markdown"):
                docs = parse_markdown(file_path)
            else:
                docs = parse_text(file_path)
            all_docs.extend(docs)
        except Exception:
            # 跳过解析失败的文件
            continue

    return all_docs


# ─────────────────────── 文本分块 ───────────────────────


def chunk_text(
    text: str,
    strategy: str = "recursive",
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    min_chunk_size: int = 50,
) -> list[str]:
    """将文本分块。

    Args:
        text: 待分块的文本
        strategy: 分块策略 (recursive/fixed_size/by_sentence)
        chunk_size: 每块最大字符数
        chunk_overlap: 块间重叠字符数
        min_chunk_size: 最小块大小

    Returns:
        分块后的文本列表
    """
    if not text.strip():
        return []

    if strategy == "recursive":
        chunks = _recursive_split(text, chunk_size, chunk_overlap)
    elif strategy == "fixed_size":
        chunks = _fixed_size_split(text, chunk_size, chunk_overlap)
    elif strategy == "by_sentence":
        chunks = _sentence_split(text, chunk_size, chunk_overlap)
    else:
        # 默认递归分块
        chunks = _recursive_split(text, chunk_size, chunk_overlap)

    # 过滤过短的 chunk
    return [c for c in chunks if len(c.strip()) >= min_chunk_size]


def chunk_documents(
    documents: list[dict[str, Any]],
    strategy: str = "recursive",
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    min_chunk_size: int = 50,
) -> list[dict[str, Any]]:
    """将文档列表分块，保留 source 和 metadata。

    Args:
        documents: 文档列表（每项含 text/source/metadata）
        strategy: 分块策略
        chunk_size: 每块最大字符数
        chunk_overlap: 块间重叠字符数
        min_chunk_size: 最小块大小

    Returns:
        分块后的文档列表
    """
    chunks: list[dict[str, Any]] = []
    for doc in documents:
        text_chunks = chunk_text(
            doc["text"],
            strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
        )
        for i, chunk_str in enumerate(text_chunks):
            chunks.append({
                "text": chunk_str,
                "source": doc.get("source", ""),
                "metadata": {**doc.get("metadata", {}), "chunk_index": i},
            })
    return chunks


# ─────────────────────── 内部分块实现 ───────────────────────


def _split_by_headers(text: str) -> list[str]:
    """按 Markdown 标题（#、##）分段。"""
    # 匹配行首的 # 或 ## 标题
    pattern = re.compile(r"^(#{1,2})\s+", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        return []

    sections: list[str] = []
    # 第一段：标题之前的内容
    if matches[0].start() > 0:
        pre = text[: matches[0].start()].strip()
        if pre:
            sections.append(pre)

    # 各段
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append(text[start:end])

    return sections


def _recursive_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """递归文本分割：按段落 -> 换行 -> 句号 -> 空格 -> 字符。"""
    separators = ["\n\n", "\n", "。", ".", "！", "!", "？", "?", "；", ";", " "]
    return _do_recursive_split(text, separators, chunk_size, overlap)


def _do_recursive_split(
    text: str, separators: list[str], chunk_size: int, overlap: int
) -> list[str]:
    """递归分割核心实现。"""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    sep = separators[0] if separators else ""
    remaining = separators[1:] if len(separators) > 1 else []

    if sep:
        parts = text.split(sep)
    else:
        # 按字符硬切
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    result: list[str] = []
    current = ""

    for part in parts:
        candidate = current + sep + part if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                result.append(current)
            # 单个 part 超长时递归
            if len(part) > chunk_size and remaining:
                result.extend(_do_recursive_split(part, remaining, chunk_size, overlap))
            else:
                current = part

    if current:
        result.append(current)

    # 添加 overlap
    if overlap > 0 and len(result) > 1:
        overlapped = [result[0]]
        for i in range(1, len(result)):
            prev_tail = result[i - 1][-overlap:]
            overlapped.append(prev_tail + result[i])
        result = overlapped

    return result


def _fixed_size_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """按固定字符数分块。"""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def _sentence_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """按句子分块，尽量保持句子完整。"""
    # 中英文句子分隔符
    sentences = re.split(r"(?<=[。！？.!?；;])\s*", text)
    sentences = [s for s in sentences if s.strip()]

    chunks: list[str] = []
    current = ""

    for sent in sentences:
        candidate = current + " " + sent if current else sent
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # 单句超长时回退到递归分块
            if len(sent) > chunk_size:
                chunks.extend(_recursive_split(sent, chunk_size, overlap))
                current = ""
            else:
                current = sent

    if current:
        chunks.append(current)

    # 添加 overlap
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(prev_tail + chunks[i])
        chunks = overlapped

    return chunks
