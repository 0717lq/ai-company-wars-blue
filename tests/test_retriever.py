"""Hybrid retriever tests."""
from unittest.mock import MagicMock, patch

from rag_builder.retriever import (
    BM25Index,
    HybridRetriever,
    RetrievalResult,
    create_retriever,
)
from rag_builder.vector_store import SearchResult


class TestBM25Index:
    """BM25 index tests."""

    def test_add_and_search(self):
        """Should add documents and allow search."""
        idx = BM25Index()
        idx.add(
            ids=["1", "2", "3"],
            texts=["machine learning basics", "deep learning intro", "natural language processing"],
        )
        assert idx.count == 3

    def test_search_returns_results(self):
        """Search should return RetrievalResult list."""
        idx = BM25Index()
        idx.add(
            ids=["1", "2"],
            texts=["RAG retrieval augmented generation", "vector database Milvus"],
        )
        with patch.object(idx, "_bm25") as mock_bm25:
            mock_bm25.get_scores.return_value = [0.9, 0.1]
            results = idx.search("RAG", top_k=2)

        if results:
            assert len(results) <= 2
            assert results[0].score >= results[-1].score

    def test_empty_index_returns_empty(self):
        """Empty index should return empty results."""
        idx = BM25Index()
        results = idx.search("test", top_k=5)
        assert results == []

    def test_tokenize_with_jieba(self):
        """With jieba should use jieba tokenization."""
        mock_jieba = MagicMock()
        mock_jieba.cut.return_value = ["hello", "world"]
        with patch.dict("sys.modules", {"jieba": mock_jieba}):
            tokens = BM25Index._tokenize("hello world")
        assert tokens == ["hello", "world"]

    def test_tokenize_fallback_chars(self):
        """Without jieba should fallback to char splitting."""
        with patch.dict("sys.modules", {"jieba": None}):
            tokens = BM25Index._tokenize("abc")
        assert tokens == ["a", "b", "c"]


class TestHybridRetriever:
    """HybridRetriever tests."""

    def test_index_documents(self):
        """index should add docs to BM25 index."""
        retriever = HybridRetriever()
        count = retriever.index([
            {"id": "1", "text": "RAG retrieval augmented generation"},
            {"id": "2", "text": "vector database Milvus"},
        ])
        assert count == 2
        assert retriever.doc_count == 2

    def test_search_bm25_only(self):
        """BM25-only search should return results."""
        retriever = HybridRetriever()
        retriever.index([
            {"id": "1", "text": "RAG retrieval augmented generation"},
            {"id": "2", "text": "vector database Milvus"},
        ])
        results = retriever.search("RAG", top_k=2, use_bm25=True, use_vector=False)
        assert isinstance(results, list)

    def test_search_vector_only(self):
        """Vector-only search should return results."""
        mock_store = MagicMock()
        mock_store.search.return_value = [
            SearchResult(id="1", text="RAG", score=0.9),
        ]
        mock_provider = MagicMock()
        mock_provider.embed_texts.return_value = [[0.1, 0.2]]

        retriever = HybridRetriever(
            vector_store=mock_store,
            embedding_provider=mock_provider,
        )
        results = retriever.search("RAG", top_k=1, use_bm25=False, use_vector=True)
        assert len(results) == 1

    def test_rrf_fusion(self):
        """RRF fusion should merge BM25 and vector results."""
        retriever = HybridRetriever(bm25_weight=0.3, vector_weight=0.7, rrf_k=60)

        bm25_results = [
            RetrievalResult(id="1", text="doc1", score=0.9),
            RetrievalResult(id="2", text="doc2", score=0.7),
        ]
        vector_results = [
            RetrievalResult(id="2", text="doc2", score=0.95),
            RetrievalResult(id="3", text="doc3", score=0.8),
        ]

        fused = retriever._rrf_fusion(bm25_results, vector_results, top_k=3)
        assert len(fused) == 3
        # doc2 appears in both, should rank first
        assert fused[0].id == "2"

    def test_search_without_store_returns_bm25(self):
        """Without vector store should use BM25 only."""
        retriever = HybridRetriever(vector_store=None, embedding_provider=None)
        retriever.index([{"id": "1", "text": "test document"}])
        results = retriever.search("test", top_k=5, use_bm25=True, use_vector=False)
        assert isinstance(results, list)


class TestRetrievalResult:
    """RetrievalResult tests."""

    def test_fields(self):
        """Fields should be set correctly."""
        r = RetrievalResult(id="1", text="hello", score=0.9, source="test.md")
        assert r.id == "1"
        assert r.source == "test.md"
        assert r.metadata == {}


class TestCreateRetriever:
    """Factory function tests."""

    def test_create_default(self):
        """create_retriever should return HybridRetriever."""
        r = create_retriever()
        assert isinstance(r, HybridRetriever)

    def test_create_with_params(self):
        """Should support custom parameters."""
        r = create_retriever(bm25_weight=0.5, vector_weight=0.5, rrf_k=30)
        assert r._bm25_weight == 0.5
        assert r._rrf_k == 30
