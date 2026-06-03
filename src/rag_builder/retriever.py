"""混合检索器 — BM25 + 向量检索 RRF 融合。

实现 Reciprocal Rank Fusion (RRF) 混合检索，组合 BM25 关键词检索
和向量语义检索的结果，提供比单一检索更高的召回质量。

用法:
    retriever = HybridRetriever(vector_store=store, embedding_provider=provider)
    retriever.index(documents)
    results = retriever.search("什么是 RAG？", top_k=10)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievalResult:
    """单条检索结果。"""
    id: str
    text: str
    score: float
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BM25Index:
    """BM25 关键词索引。

    基于 rank-bm25 库实现，支持中文分词。
    """

    def __init__(self):
        """初始化 BM25 索引。"""
        self._corpus: list[str] = []
        self._ids: list[str] = []
        self._sources: list[str] = []
        self._metadata: list[dict[str, Any]] = []
        self._bm25 = None
        self._tokenized_corpus: list[list[str]] = []

    def add(
        self,
        ids: list[str],
        texts: list[str],
        sources: list[str] | None = None,
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """添加文档到 BM25 索引。"""
        self._ids.extend(ids)
        self._corpus.extend(texts)
        self._sources.extend(sources or [""] * len(ids))
        self._metadata.extend(metadata or [{} for _ in ids])

        # 分词并重建索引
        self._tokenized_corpus = [self._tokenize(t) for t in self._corpus]
        self._rebuild_index()

    def search(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        """BM25 检索。"""
        if not self._bm25 or not self._corpus:
            return []

        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        # 取 top_k
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        results: list[RetrievalResult] = []
        for idx, score in ranked:
            if score > 0:
                results.append(RetrievalResult(
                    id=self._ids[idx],
                    text=self._corpus[idx],
                    score=float(score),
                    source=self._sources[idx],
                    metadata=self._metadata[idx],
                ))
        return results

    @property
    def count(self) -> int:
        """索引中的文档数。"""
        return len(self._corpus)

    def _rebuild_index(self) -> None:
        """重建 BM25 索引。"""
        try:
            from rank_bm25 import BM25Okapi
            self._bm25 = BM25Okapi(self._tokenized_corpus)
        except ImportError:
            self._bm25 = None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """中文分词（优先 jieba，回退字符级）。"""
        try:
            import jieba
            return list(jieba.cut(text))
        except ImportError:
            # 回退：按字符 + 空格分割
            tokens: list[str] = []
            for char in text:
                if char.strip():
                    tokens.append(char)
            return tokens


class HybridRetriever:
    """混合检索器 — BM25 + 向量 RRF 融合。

    RRF 公式: score = sum(1 / (k + rank_i))，k=60 是常用值。
    """

    def __init__(
        self,
        vector_store: Any = None,
        embedding_provider: Any = None,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        rrf_k: int = 60,
    ):
        """初始化混合检索器。

        Args:
            vector_store: VectorStore 实例
            embedding_provider: EmbeddingProvider 实例
            bm25_weight: BM25 权重
            vector_weight: 向量检索权重
            rrf_k: RRF 参数 k
        """
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider
        self._bm25_weight = bm25_weight
        self._vector_weight = vector_weight
        self._rrf_k = rrf_k
        self._bm25 = BM25Index()
        self._doc_map: dict[str, dict[str, Any]] = {}

    def index(self, documents: list[dict[str, Any]]) -> int:
        """索引文档列表。

        Args:
            documents: 文档列表，每项含 text/source/metadata/id

        Returns:
            索引的文档数
        """
        ids: list[str] = []
        texts: list[str] = []
        sources: list[str] = []
        metadata: list[dict[str, Any]] = []

        for i, doc in enumerate(documents):
            doc_id = doc.get("id", f"doc_{i:06d}")
            ids.append(doc_id)
            texts.append(doc["text"])
            sources.append(doc.get("source", ""))
            metadata.append(doc.get("metadata", {}))
            self._doc_map[doc_id] = doc

        # 添加到 BM25 索引
        self._bm25.add(ids, texts, sources, metadata)

        # 添加到向量库
        if self._vector_store and self._embedding_provider:
            embeddings = self._embedding_provider.embed_texts(texts)
            self._vector_store.add(ids=ids, texts=texts, embeddings=embeddings, metadata=metadata)

        return len(ids)

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_bm25: bool = True,
        use_vector: bool = True,
    ) -> list[RetrievalResult]:
        """混合检索。

        Args:
            query: 查询文本
            top_k: 返回数量
            use_bm25: 是否使用 BM25
            use_vector: 是否使用向量检索

        Returns:
            检索结果列表，按融合分数降序
        """
        # 收集各路检索结果
        bm25_results: list[RetrievalResult] = []
        vector_results: list[RetrievalResult] = []

        if use_bm25:
            bm25_results = self._bm25.search(query, top_k=top_k * 2)

        if use_vector and self._vector_store and self._embedding_provider:
            query_embedding = self._embedding_provider.embed_texts([query])[0]
            vs_results = self._vector_store.search(
                embedding=query_embedding, top_k=top_k * 2
            )
            vector_results = [
                RetrievalResult(
                    id=r.id, text=r.text, score=r.score,
                    metadata=r.metadata,
                )
                for r in vs_results
            ]

        # 单路检索时直接返回
        if use_bm25 and not use_vector:
            return bm25_results[:top_k]
        if use_vector and not use_bm25:
            return vector_results[:top_k]

        # RRF 融合
        return self._rrf_fusion(bm25_results, vector_results, top_k)

    def _rrf_fusion(
        self,
        bm25_results: list[RetrievalResult],
        vector_results: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        """RRF 融合排序。"""
        # 构建 ID -> 文档映射
        doc_map: dict[str, RetrievalResult] = {}

        # BM25 排名
        bm25_ranks: dict[str, int] = {}
        for rank, r in enumerate(bm25_results):
            bm25_ranks[r.id] = rank + 1
            doc_map[r.id] = r

        # 向量排名
        vector_ranks: dict[str, int] = {}
        for rank, r in enumerate(vector_results):
            vector_ranks[r.id] = rank + 1
            if r.id not in doc_map:
                doc_map[r.id] = r

        # 计算 RRF 分数
        rrf_scores: dict[str, float] = {}
        for doc_id in doc_map:
            score = 0.0
            if doc_id in bm25_ranks:
                score += self._bm25_weight / (self._rrf_k + bm25_ranks[doc_id])
            if doc_id in vector_ranks:
                score += self._vector_weight / (self._rrf_k + vector_ranks[doc_id])
            rrf_scores[doc_id] = score

        # 排序
        ranked_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results: list[RetrievalResult] = []
        for doc_id in ranked_ids[:top_k]:
            r = doc_map[doc_id]
            results.append(RetrievalResult(
                id=r.id,
                text=r.text,
                score=rrf_scores[doc_id],
                source=r.source,
                metadata=r.metadata,
            ))
        return results

    @property
    def doc_count(self) -> int:
        """已索引文档数。"""
        return self._bm25.count


def create_retriever(
    strategy: str = "hybrid",
    vector_store: Any = None,
    embedding_provider: Any = None,
    bm25_weight: float = 0.3,
    vector_weight: float = 0.7,
    rrf_k: int = 60,
) -> HybridRetriever:
    """工厂函数：创建检索器实例。

    Args:
        strategy: 检索策略 ("hybrid"/"bm25"/"vector")
        vector_store: VectorStore 实例
        embedding_provider: EmbeddingProvider 实例
        bm25_weight: BM25 权重
        vector_weight: 向量权重
        rrf_k: RRF 参数 k

    Returns:
        HybridRetriever 实例
    """
    retriever = HybridRetriever(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        bm25_weight=bm25_weight,
        vector_weight=vector_weight,
        rrf_k=rrf_k,
    )
    return retriever
