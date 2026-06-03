"""向量存储连接器 — 统一 Milvus 和 Chroma 的接口。

通过工厂函数 get_store() 按名称获取 store 实例。

用法:
    store = get_store("milvus", collection="my_docs", uri="http://localhost:19530")
    store.add(ids=["doc1"], texts=["你好"], embeddings=[[0.1, 0.2, ...]])
    results = store.search(embedding=[0.1, 0.2, ...], top_k=5)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    """单条检索结果。"""
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """向量存储抽象基类。"""

    @abstractmethod
    def add(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """添加文档到向量库。

        Args:
            ids: 文档 ID 列表
            texts: 文本列表
            embeddings: 向量列表
            metadata: 元数据列表（可选）
        """

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        top_k: int = 10,
        filter_expr: str = "",
    ) -> list[SearchResult]:
        """向量检索。

        Args:
            embedding: 查询向量
            top_k: 返回数量
            filter_expr: 过滤表达式（语法取决于后端）

        Returns:
            检索结果列表，按 score 降序
        """

    @abstractmethod
    def delete(self, ids: list[str]) -> int:
        """删除文档。

        Args:
            ids: 待删除的 ID 列表

        Returns:
            实际删除的数量
        """

    @abstractmethod
    def count(self) -> int:
        """返回向量库中的文档总数。"""

    def add_texts(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        ids: list[str] | None = None,
        metadata: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        """便捷方法：自动分配 ID 添加文档。

        Args:
            texts: 文本列表
            embeddings: 向量列表
            ids: 自定义 ID（可选，不提供则自动生成）
            metadata: 元数据列表

        Returns:
            分配的 ID 列表
        """
        import hashlib
        import time

        if ids is None:
            ids = []
            for text in texts:
                h = hashlib.md5(text.encode()).hexdigest()[:8]
                ts = int(time.time() * 1000) % 10000
                ids.append(f"doc_{h}_{ts}")

        self.add(ids=ids, texts=texts, embeddings=embeddings, metadata=metadata)
        return ids


class MilvusStore(VectorStore):
    """Milvus 向量存储连接器。"""

    def __init__(
        self,
        collection: str = "default",
        uri: str = "http://localhost:19530",
        token: str = "",
        metric: str = "COSINE",
        dimension: int = 768,
    ):
        """初始化 Milvus 连接。

        Args:
            collection: collection 名称
            uri: Milvus 服务地址
            token: 认证 token
            metric: 距离度量 (COSINE/L2/IP)
            dimension: 向量维度
        """
        try:
            from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections
        except ImportError as err:
            raise ImportError(
                "pymilvus 未安装。请执行: pip install rag-builder[milvus] 或 pip install pymilvus"
            ) from err

        self._collection_name = collection
        self._dimension = dimension
        self._metric = metric

        # 建立连接
        connections.connect(alias="default", uri=uri, token=token or None)

        # 检查 collection 是否存在，不存在则创建
        from pymilvus import utility
        if utility.has_collection(collection):
            self._collection = Collection(collection)
            self._collection.load()
        else:
            self._collection = self._create_collection(
                Collection, CollectionSchema, DataType, FieldSchema
            )

    def _create_collection(
        self, collection_cls: type, collection_schema_cls: type,
        data_type_cls: type, field_schema_cls: type,
    ) -> Any:
        """创建 Milvus collection。"""
        fields = [
            field_schema_cls(name="id", dtype=data_type_cls.VARCHAR, is_primary=True, max_length=128),
            field_schema_cls(name="text", dtype=data_type_cls.VARCHAR, max_length=65535),
            field_schema_cls(name="embedding", dtype=data_type_cls.FLOAT_VECTOR, dim=self._dimension),
        ]
        schema = collection_schema_cls(fields=fields, enable_dynamic_field=True)
        collection = collection_cls(self._collection_name, schema)

        # 创建 HNSW 索引
        index_params = {
            "metric_type": self._metric,
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 256},
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        collection.load()
        return collection

    def add(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """添加文档到 Milvus。"""
        data = [ids, texts, embeddings]
        self._collection.insert(data)
        self._collection.flush()

    def search(
        self,
        embedding: list[float],
        top_k: int = 10,
        filter_expr: str = "",
    ) -> list[SearchResult]:
        """从 Milvus 检索。"""
        search_params = {"metric_type": self._metric, "params": {"ef": 128}}
        kwargs: dict[str, Any] = {
            "data": [embedding],
            "anns_field": "embedding",
            "param": search_params,
            "limit": top_k,
            "output_fields": ["text"],
        }
        if filter_expr:
            kwargs["expr"] = filter_expr

        results = self._collection.search(**kwargs)

        search_results: list[SearchResult] = []
        for hit in results[0]:
            search_results.append(SearchResult(
                id=hit.id,
                text=hit.entity.get("text", ""),
                score=hit.score,
                metadata={"distance": hit.distance} if hasattr(hit, "distance") else {},
            ))
        return search_results

    def delete(self, ids: list[str]) -> int:
        """从 Milvus 删除文档。"""
        expr = f"id in {[repr(i) for i in ids]}"
        result = self._collection.delete(expr)
        self._collection.flush()
        return result.delete_count if hasattr(result, "delete_count") else len(ids)

    def count(self) -> int:
        """返回 Milvus collection 中的文档总数。"""
        self._collection.flush()
        return self._collection.num_entities


class ChromaStore(VectorStore):
    """Chroma 向量存储连接器。"""

    def __init__(
        self,
        collection: str = "default",
        path: str = "./chroma_db",
        host: str = "",
        port: int = 8000,
    ):
        """初始化 Chroma 连接。

        Args:
            collection: collection 名称
            path: 本地持久化路径（仅本地模式）
            host: Chroma 服务地址（远程模式）
            port: Chroma 服务端口
        """
        try:
            import chromadb
        except ImportError as err:
            raise ImportError(
                "chromadb 未安装。请执行: pip install rag-builder[chromadb] 或 pip install chromadb"
            ) from err

        if host:
            # 远程模式
            self._client = chromadb.HttpClient(host=host, port=port)
        else:
            # 本地持久化模式
            self._client = chromadb.PersistentClient(path=path)

        self._collection = self._client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """添加文档到 Chroma。"""
        metadatas = metadata or [{} for _ in ids]
        self._collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        embedding: list[float],
        top_k: int = 10,
        filter_expr: str = "",
    ) -> list[SearchResult]:
        """从 Chroma 检索。"""
        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": top_k,
        }
        if filter_expr:
            kwargs["where_document"] = {"$contains": filter_expr}

        results = self._collection.query(**kwargs)

        search_results: list[SearchResult] = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results.get("distances") else 0.0
                search_results.append(SearchResult(
                    id=doc_id,
                    text=results["documents"][0][i] if results.get("documents") else "",
                    score=1.0 - distance,  # Chroma 返回距离，转为相似度
                    metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                ))
        return search_results

    def delete(self, ids: list[str]) -> int:
        """从 Chroma 删除文档。"""
        before = self._collection.count()
        self._collection.delete(ids=ids)
        after = self._collection.count()
        return before - after

    def count(self) -> int:
        """返回 Chroma collection 中的文档总数。"""
        return self._collection.count()


def get_store(
    name: str,
    collection: str = "default",
    dimension: int = 768,
    **kwargs: Any,
) -> VectorStore:
    """工厂函数：按名称获取向量存储实例。

    Args:
        name: 后端名称 ("milvus" 或 "chroma")
        collection: collection 名称
        dimension: 向量维度
        **kwargs: 传递给具体 store 的参数

    Returns:
        VectorStore 实例

    Raises:
        ValueError: 未知后端名称
    """
    if name == "milvus":
        return MilvusStore(collection=collection, dimension=dimension, **kwargs)
    elif name == "chroma":
        return ChromaStore(collection=collection, **kwargs)
    else:
        raise ValueError(
            f"未知向量存储后端: {name!r}，可选: ['milvus', 'chroma']"
        )
