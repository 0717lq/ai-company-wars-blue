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

    def test_add_texts_with_metadata(self):
        """add_texts 应传递 metadata。"""
        store = MagicMock(spec=VectorStore)
        store.add_texts = VectorStore.add_texts.__get__(store, VectorStore)
        store.add.return_value = None

        ids = store.add_texts(
            texts=["hello"],
            embeddings=[[0.1]],
            ids=["id1"],
            metadata=[{"page": 1}],
        )
        assert ids == ["id1"]
        store.add.assert_called_once()


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


# ── MilvusStore 完整测试（mock pymilvus） ──


def _make_pymilvus_mocks():
    """构造 pymilvus 模块的 mock 对象。"""
    mock_module = MagicMock()
    # Collection 类 mock
    mock_collection_cls = MagicMock()
    mock_collection_instance = MagicMock()
    mock_collection_cls.return_value = mock_collection_instance
    mock_module.Collection = mock_collection_cls
    mock_module.CollectionSchema = MagicMock()
    mock_module.DataType = MagicMock()
    mock_module.FieldSchema = MagicMock()
    mock_module.connections = MagicMock()
    mock_module.utility = MagicMock()
    return mock_module, mock_collection_instance


class TestMilvusStore:
    """MilvusStore 测试（mock pymilvus）。"""

    def test_import_error_without_pymilvus(self):
        """未安装 pymilvus 时应抛出 ImportError。"""
        with patch.dict("sys.modules", {"pymilvus": None}):
            with pytest.raises(ImportError, match="pymilvus 未安装"):
                MilvusStore(collection="test")

    def test_init_existing_collection(self):
        """已存在 collection 时应直接加载。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="existing", dimension=128)
            # 应该调用 Collection(name) 和 load()
            mock_module.utility.has_collection.assert_called_once_with("existing")
            mock_coll.load.assert_called_once()
            assert store._collection is mock_coll

    def test_init_creates_new_collection(self):
        """不存在 collection 时应创建新的。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = False

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="new_col", dimension=256, metric="L2")
            # _create_collection 应被调用
            assert store._collection is mock_coll
            mock_coll.create_index.assert_called_once()
            mock_coll.load.assert_called()

    def test_add_documents(self):
        """add 应调用 collection.insert + flush。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            store.add(
                ids=["doc1", "doc2"],
                texts=["hello", "world"],
                embeddings=[[0.1] * 128, [0.2] * 128],
            )
            mock_coll.insert.assert_called_once()
            mock_coll.flush.assert_called_once()
            # 验证传入的数据格式
            call_args = mock_coll.insert.call_args[0][0]
            assert call_args[0] == ["doc1", "doc2"]
            assert call_args[1] == ["hello", "world"]

    def test_add_with_metadata(self):
        """add 带 metadata 时仍正常工作。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            store.add(
                ids=["doc1"],
                texts=["hello"],
                embeddings=[[0.1] * 128],
                metadata=[{"page": 1}],
            )
            mock_coll.insert.assert_called_once()

    def test_search_basic(self):
        """search 应返回 SearchResult 列表。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True

        # 构造 search 返回值
        mock_hit = MagicMock()
        mock_hit.id = "doc1"
        mock_hit.entity = {"text": "hello world"}
        mock_hit.score = 0.95
        mock_hit.distance = 0.05
        mock_coll.search.return_value = [[mock_hit]]

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            results = store.search(embedding=[0.1] * 128, top_k=5)

            assert len(results) == 1
            assert results[0].id == "doc1"
            assert results[0].text == "hello world"
            assert results[0].score == 0.95
            assert results[0].metadata == {"distance": 0.05}

    def test_search_with_filter(self):
        """search 带 filter_expr 时应传入 expr 参数。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True
        mock_coll.search.return_value = [[]]

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            store.search(embedding=[0.1] * 128, filter_expr="id > 0")

            call_kwargs = mock_coll.search.call_args[1]
            assert call_kwargs["expr"] == "id > 0"

    def test_search_without_filter(self):
        """search 不带 filter_expr 时不应传入 expr。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True
        mock_coll.search.return_value = [[]]

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            store.search(embedding=[0.1] * 128)

            call_kwargs = mock_coll.search.call_args[1]
            assert "expr" not in call_kwargs

    def test_search_no_distance_attr(self):
        """search hit 没有 distance 属性时 metadata 为空。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True

        mock_hit = MagicMock()
        mock_hit.id = "doc1"
        mock_hit.entity = {"text": "hello"}
        mock_hit.score = 0.9
        del mock_hit.distance  # 没有 distance 属性
        mock_coll.search.return_value = [[mock_hit]]

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            results = store.search(embedding=[0.1] * 128)
            assert results[0].metadata == {}

    def test_delete(self):
        """delete 应返回删除数量。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True

        mock_result = MagicMock()
        mock_result.delete_count = 2
        mock_coll.delete.return_value = mock_result

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            count = store.delete(ids=["doc1", "doc2"])
            assert count == 2
            mock_coll.flush.assert_called()

    def test_delete_no_delete_count_attr(self):
        """delete 结果没有 delete_count 属性时回退到 len(ids)。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True

        mock_result = MagicMock(spec=[])  # 没有 delete_count
        mock_coll.delete.return_value = mock_result

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            count = store.delete(ids=["doc1", "doc2", "doc3"])
            assert count == 3

    def test_count(self):
        """count 应返回 num_entities。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = True
        mock_coll.num_entities = 42

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test")
            assert store.count() == 42
            mock_coll.flush.assert_called()

    def test_create_collection_params(self):
        """_create_collection 使用正确的参数名。"""
        mock_module, mock_coll = _make_pymilvus_mocks()
        mock_module.utility.has_collection.return_value = False

        with patch.dict("sys.modules", {"pymilvus": mock_module}):
            store = MilvusStore(collection="test", dimension=64, metric="IP")
            # 验证 _create_collection 使用了正确的 lowercase 参数
            assert store._dimension == 64
            assert store._metric == "IP"


# ── ChromaStore 完整测试（mock chromadb） ──


def _make_chromadb_mocks():
    """构造 chromadb 模块的 mock 对象。"""
    mock_module = MagicMock()
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_module.PersistentClient.return_value = mock_client
    mock_module.HttpClient.return_value = mock_client
    mock_client.get_or_create_collection.return_value = mock_collection
    return mock_module, mock_client, mock_collection


class TestChromaStore:
    """ChromaStore 测试（mock chromadb）。"""

    def test_import_error_without_chromadb(self):
        """未安装 chromadb 时应抛出 ImportError。"""
        with patch.dict("sys.modules", {"chromadb": None}):
            with pytest.raises(ImportError, match="chromadb 未安装"):
                ChromaStore(collection="test")

    def test_init_local_mode(self):
        """本地模式应使用 PersistentClient。"""
        mock_module, mock_client, mock_coll = _make_chromadb_mocks()

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test_col", path="/tmp/chroma")
            mock_module.PersistentClient.assert_called_once_with(path="/tmp/chroma")
            mock_client.get_or_create_collection.assert_called_once_with(
                name="test_col", metadata={"hnsw:space": "cosine"}
            )
            assert store._collection is mock_coll

    def test_init_remote_mode(self):
        """远程模式应使用 HttpClient。"""
        mock_module, mock_client, mock_coll = _make_chromadb_mocks()

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            ChromaStore(collection="test", host="192.168.1.1", port=9000)
            mock_module.HttpClient.assert_called_once_with(host="192.168.1.1", port=9000)

    def test_add_documents(self):
        """add 应调用 collection.add。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            store.add(
                ids=["doc1", "doc2"],
                texts=["hello", "world"],
                embeddings=[[0.1, 0.2], [0.3, 0.4]],
                metadata=[{"page": 1}, {"page": 2}],
            )
            mock_coll.add.assert_called_once_with(
                ids=["doc1", "doc2"],
                documents=["hello", "world"],
                embeddings=[[0.1, 0.2], [0.3, 0.4]],
                metadatas=[{"page": 1}, {"page": 2}],
            )

    def test_add_without_metadata(self):
        """add 不传 metadata 时应自动生成空 metadata。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            store.add(
                ids=["doc1"],
                texts=["hello"],
                embeddings=[[0.1]],
            )
            call_kwargs = mock_coll.add.call_args[1]
            assert call_kwargs["metadatas"] == [{}]

    def test_search_basic(self):
        """search 应返回正确的 SearchResult。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()
        mock_coll.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["hello", "world"]],
            "distances": [[0.1, 0.3]],
            "metadatas": [[{"page": 1}, {"page": 2}]],
        }

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            results = store.search(embedding=[0.1, 0.2], top_k=2)

            assert len(results) == 2
            assert results[0].id == "doc1"
            assert results[0].text == "hello"
            assert results[0].score == pytest.approx(0.9)  # 1.0 - 0.1
            assert results[1].score == pytest.approx(0.7)  # 1.0 - 0.3
            assert results[0].metadata == {"page": 1}

    def test_search_with_filter(self):
        """search 带 filter_expr 时应传入 where_document。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()
        mock_coll.query.return_value = {"ids": [[]]}

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            store.search(embedding=[0.1], filter_expr="keyword")

            call_kwargs = mock_coll.query.call_args[1]
            assert call_kwargs["where_document"] == {"$contains": "keyword"}

    def test_search_without_filter(self):
        """search 不带 filter_expr 时不应传入 where_document。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()
        mock_coll.query.return_value = {"ids": [[]]}

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            store.search(embedding=[0.1])

            call_kwargs = mock_coll.query.call_args[1]
            assert "where_document" not in call_kwargs

    def test_search_empty_results(self):
        """search 返回空结果时应返回空列表。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()
        mock_coll.query.return_value = {"ids": []}

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            results = store.search(embedding=[0.1])
            assert results == []

    def test_search_no_distances(self):
        """search 没有 distances 时 score 应为 1.0。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()
        mock_coll.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["hello"]],
            "distances": None,
            "metadatas": [[{}]],
        }

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            results = store.search(embedding=[0.1])
            assert results[0].score == 1.0

    def test_search_no_documents(self):
        """search 没有 documents 时 text 应为空字符串。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()
        mock_coll.query.return_value = {
            "ids": [["doc1"]],
            "documents": None,
            "distances": [[0.2]],
            "metadatas": None,
        }

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            results = store.search(embedding=[0.1])
            assert results[0].text == ""
            assert results[0].metadata == {}

    def test_delete(self):
        """delete 应返回删除数量。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()
        mock_coll.count.side_effect = [5, 3]  # before=5, after=3

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            count = store.delete(ids=["doc1", "doc2"])
            assert count == 2

    def test_count(self):
        """count 应返回 collection.count()。"""
        mock_module, _, mock_coll = _make_chromadb_mocks()
        mock_coll.count.return_value = 100

        with patch.dict("sys.modules", {"chromadb": mock_module}):
            store = ChromaStore(collection="test")
            assert store.count() == 100


# ── get_store 工厂函数测试 ──


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
