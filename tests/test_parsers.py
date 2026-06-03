"""文档解析器 + 分块器测试。"""

import pytest

from rag_builder.parsers import (
    chunk_documents,
    chunk_text,
    parse_directory,
    parse_markdown,
    parse_text,
)


class TestParseMarkdown:
    """Markdown 解析测试。"""

    def test_parse_basic_markdown(self, tmp_path):
        """基本 Markdown 解析应返回文档列表。"""
        md = tmp_path / "test.md"
        md.write_text("# 标题1\n内容1\n\n## 标题2\n内容2", encoding="utf-8")
        docs = parse_markdown(md)
        assert len(docs) >= 1
        assert all("text" in d for d in docs)
        assert all("source" in d for d in docs)

    def test_parse_no_headers(self, tmp_path):
        """无标题的 Markdown 应作为单个文档返回。"""
        md = tmp_path / "flat.md"
        md.write_text("这是一段没有标题的文本。\n第二行。", encoding="utf-8")
        docs = parse_markdown(md)
        assert len(docs) == 1

    def test_parse_nonexistent_raises(self):
        """不存在的文件应抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            parse_markdown("/nonexistent/path.md")

    def test_parse_with_sections(self, tmp_path):
        """按标题分段的 Markdown 应返回多个文档。"""
        md = tmp_path / "sections.md"
        md.write_text(
            "# 第一章\n\n内容一\n\n## 第二章\n\n内容二\n\n## 第三章\n\n内容三",
            encoding="utf-8",
        )
        docs = parse_markdown(md)
        assert len(docs) >= 2


class TestParseText:
    """纯文本解析测试。"""

    def test_parse_basic_text(self, tmp_path):
        """基本文本解析。"""
        txt = tmp_path / "test.txt"
        txt.write_text("Hello World\nSecond line", encoding="utf-8")
        docs = parse_text(txt)
        assert len(docs) == 1
        assert docs[0]["text"] == "Hello World\nSecond line"
        assert docs[0]["metadata"]["format"] == "text"

    def test_parse_nonexistent_raises(self):
        """不存在的文件应抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            parse_text("/nonexistent/path.txt")


class TestParseDirectory:
    """目录解析测试。"""

    def test_parse_mixed_files(self, tmp_path):
        """解析包含多种文件类型的目录。"""
        (tmp_path / "a.md").write_text("# Title\nContent", encoding="utf-8")
        (tmp_path / "b.txt").write_text("Plain text", encoding="utf-8")
        (tmp_path / "c.py").write_text("print('hello')", encoding="utf-8")  # 不应被解析

        docs = parse_directory(tmp_path)
        # 至少解析到 md 和 txt
        assert len(docs) >= 2

    def test_parse_empty_dir(self, tmp_path):
        """空目录应返回空列表。"""
        docs = parse_directory(tmp_path)
        assert docs == []

    def test_parse_nonexistent_raises(self):
        """不存在的目录应抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            parse_directory("/nonexistent/dir")

    def test_extension_filter(self, tmp_path):
        """扩展名过滤应只解析指定类型。"""
        (tmp_path / "a.md").write_text("# MD", encoding="utf-8")
        (tmp_path / "b.txt").write_text("TXT", encoding="utf-8")

        docs = parse_directory(tmp_path, extensions=[".md"])
        assert all("markdown" in d["metadata"].get("format", "") for d in docs)


class TestChunkText:
    """分块器测试。"""

    def test_short_text_single_chunk(self):
        """短文本应返回单个 chunk。"""
        text = "这是一段短文本。"
        chunks = chunk_text(text, chunk_size=100, min_chunk_size=1)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text_returns_empty(self):
        """空文本应返回空列表。"""
        assert chunk_text("", chunk_size=100) == []
        assert chunk_text("   ", chunk_size=100) == []

    def test_recursive_split(self):
        """递归分块应按段落分割。"""
        text = "段落一。" * 50 + "\n\n" + "段落二。" * 50
        chunks = chunk_text(text, strategy="recursive", chunk_size=200, min_chunk_size=1)
        assert len(chunks) >= 2

    def test_fixed_size_split(self):
        """固定大小分块应产生均匀的 chunks。"""
        text = "a" * 1000
        chunks = chunk_text(text, strategy="fixed_size", chunk_size=200, chunk_overlap=0, min_chunk_size=1)
        assert len(chunks) == 5

    def test_sentence_split(self):
        """句子分块应保持句子完整。"""
        text = "第一句话。第二句话。第三句话。第四句话。第五句话。"
        chunks = chunk_text(text, strategy="by_sentence", chunk_size=20, min_chunk_size=1)
        assert len(chunks) >= 2

    def test_min_chunk_size_filter(self):
        """过短的 chunk 应被过滤。"""
        text = "abc"
        chunks = chunk_text(text, chunk_size=100, min_chunk_size=100)
        assert len(chunks) == 0

    def test_unknown_strategy_falls_back(self):
        """未知策略应回退到递归分块。"""
        text = "hello world " * 100
        chunks = chunk_text(text, strategy="unknown", chunk_size=50, min_chunk_size=1)
        assert len(chunks) >= 1

    def test_overlap_preserves_content(self):
        """overlap 应在 chunk 之间添加前文。"""
        text = "A" * 100 + "B" * 100
        chunks = chunk_text(text, strategy="fixed_size", chunk_size=100, chunk_overlap=20, min_chunk_size=1)
        if len(chunks) > 1:
            # 第二个 chunk 应包含前一个 chunk 的尾部
            assert chunks[1][:20] == "A" * 20


class TestChunkDocuments:
    """文档分块测试。"""

    def test_chunk_preserves_source(self, tmp_path):
        """分块应保留 source 字段。"""
        docs = [
            {"text": "第一段内容。" * 20, "source": "a.md", "metadata": {}},
            {"text": "第二段内容。" * 20, "source": "b.md", "metadata": {}},
        ]
        chunks = chunk_documents(docs, chunk_size=50, min_chunk_size=1)
        sources = set(c["source"] for c in chunks)
        assert "a.md" in sources
        assert "b.md" in sources

    def test_chunk_metadata_includes_index(self):
        """分块 metadata 应包含 chunk_index。"""
        docs = [{"text": "测试内容。" * 30, "source": "test.md", "metadata": {"page": 1}}]
        chunks = chunk_documents(docs, chunk_size=30, min_chunk_size=1)
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i
