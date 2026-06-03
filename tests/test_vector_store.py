"""向量存储连接器测试。"""
from unittest.mock import MagicMock, patch

import pytest

from rag_builder.vector_store import (
    ChromaStore,
    MilvusStore,
    SearchResult,
    VectorStore,
    get_store,
)


class TestVectorStoreABC:
    """VectorStore 抽象基类测试。"""

    def test_cannot_instantiate_abc(self):
        """抽象基类不能直接实例化。"""
        with pytest.raises(TypeError):
            VectorStore()

    def test_add_texts_auto_generates_ids(self):
        """add_texts 应自动生成 ID。"""
        store = MagicMock(spec=VectorStore)
        store.add_texts = VectorStore.add_texts.__get__(store, VectorStore)
        store.add.return_value = None

        ids = store.add_texts(
            texts=["hello", "world"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
        )

        assert len(ids) == 2
        assert all(i.startswith("doc_") for i in ids)

    def test_add_texts_with_custom_ids(self):
        """add_texts 使用自定义 ID。"""
        store = MagicMock(spec=VectorStore)
        store.add_texts = VectorStore.add_texts.__get__(store, VectorStore)
        store.add.return_value = None

        ids = store.add_texts(
            texts=["hello"],
            embeddings=[[0.1]],
            ids=["custom_id"],
        )
        assert ids == ["custom_id"]


class TestSearchResult:
    """SearchResult 数据类测试。"""

    def test_basic_fields(self):
        """基本字段应正确设置。"""
        r = SearchResult(id="1", text="hello", score=0.95)
        assert r.id == "1"
        assert r.text == "hello"
        assert r.score == 0.95
        assert r.metadata == {}

    def test_with_metadata(self):
        """metadata 应正确传递。"""
        r = SearchResult(id="1", text="hi", score=0.8, metadata={"page": 1})
        assert r.metadata["page"] == 1


class TestMilvusStore:
    """MilvusStore 测试（mock pymilvus）。"""

    def test_import_error_without_pymilvus(self):
        """未安装 pymilvus 时应抛出 ImportError。"""
        with patch.dict("sys.modules", {"pymilvus": None}):
            with pytest.raises(ImportError, match="pymilvus 未安装"):
                MilvusStore(collection="test")


class TestChromaStore:
    """ChromaStore 测试（mock chromadb）。"""

    def test_import_error_without_chromadb(self):
        """未安装 chromadb 时应抛出 ImportError。"""
        with patch.dict("sys.modules", {"chromadb": None}):
            with pytest.raises(ImportError, match="chromadb 未安装"):
                ChromaStore(collection="test")


class TestGetStore:
    """工厂函数 get_store 测试。"""

    def test_milvus_store(self):
        """get_store('milvus') 应返回 MilvusStore。"""
        with patch("rag_builder.vector_store.MilvusStore") as mock_cls:
            mock_cls.return_value = MagicMock(spec=VectorStore)
            get_store("milvus", collection="test", dimension=768)
            mock_cls.assert_called_once()

    def test_chroma_store(self):
        """get_store('chroma') 应返回 ChromaStore。"""
        with patch("rag_builder.vector_store.ChromaStore") as mock_cls:
            mock_cls.return_value = MagicMock(spec=VectorStore)
            get_store("chroma", collection="test")
            mock_cls.assert_called_once()

    def test_unknown_backend_raises(self):
        """未知后端应抛出 ValueError。"""
        with pytest.raises(ValueError, match="未知向量存储后端"):
            get_store("unknown")
