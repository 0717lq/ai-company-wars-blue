"""Integration tests - end-to-end pipeline (mock external dependencies)."""

from unittest.mock import MagicMock

from rag_builder.parsers import chunk_documents, chunk_text, parse_markdown
from rag_builder.retriever import BM25Index, HybridRetriever, RetrievalResult
from rag_builder.vector_store import SearchResult


class TestEndToEndPipeline:
    """End-to-end pipeline tests."""

    def test_parse_chunk_embed_store_flow(self, tmp_path):
        """parse -> chunk -> embed(mock) -> store(mock) complete flow."""
        # 1. create test doc
        doc = tmp_path / "test.md"
        doc.write_text(
            "# RAG Intro\n\nRAG is retrieval augmented generation.\n\n## Use Cases\n\nRAG can be used for QA." * 10,
            encoding="utf-8",
        )

        # 2. parse
        docs = parse_markdown(doc)
        assert len(docs) >= 1

        # 3. chunk
        chunks = chunk_documents(docs, chunk_size=100, min_chunk_size=1)
        assert len(chunks) >= 1
        assert all("text" in c for c in chunks)
        assert all("source" in c for c in chunks)

    def test_bm25_retrieval_flow(self):
        """BM25 index -> search complete flow."""
        idx = BM25Index()
        idx.add(
            ids=["1", "2", "3"],
            texts=["RAG retrieval augmented generation", "Vector database Milvus", "BM25 keyword search"],
            sources=["rag.md", "milvus.md", "bm25.md"],
        )
        assert idx.count == 3

    def test_hybrid_retriever_index_search(self):
        """HybridRetriever index -> search flow."""
        mock_store = MagicMock()
        mock_store.search.return_value = [
            SearchResult(id="1", text="RAG retrieval augmented generation", score=0.9),
            SearchResult(id="2", text="Vector database", score=0.7),
        ]
        mock_provider = MagicMock()
        mock_provider.embed_texts.return_value = [[0.1] * 768]

        retriever = HybridRetriever(
            vector_store=mock_store,
            embedding_provider=mock_provider,
            bm25_weight=0.3,
            vector_weight=0.7,
        )

        count = retriever.index([
            {"id": "1", "text": "RAG retrieval augmented generation", "source": "rag.md"},
            {"id": "2", "text": "Vector database Milvus", "source": "milvus.md"},
        ])
        assert count == 2
        assert retriever.doc_count == 2

    def test_chunk_text_strategies(self):
        """Different chunking strategies should produce different results."""
        text = "Paragraph one. " * 30 + "\n\n" + "Paragraph two. " * 30

        recursive = chunk_text(text, strategy="recursive", chunk_size=100, min_chunk_size=1)
        fixed = chunk_text(text, strategy="fixed_size", chunk_size=100, min_chunk_size=1)
        sentence = chunk_text(text, strategy="by_sentence", chunk_size=100, min_chunk_size=1)

        assert len(recursive) >= 1
        assert len(fixed) >= 1
        assert len(sentence) >= 1

    def test_rrf_fusion_balanced_weights(self):
        """RRF fusion with equal weights should treat both result sets fairly."""
        retriever = HybridRetriever(bm25_weight=0.5, vector_weight=0.5, rrf_k=60)

        bm25 = [
            RetrievalResult(id="1", text="doc1", score=0.9),
            RetrievalResult(id="2", text="doc2", score=0.7),
        ]
        vector = [
            RetrievalResult(id="2", text="doc2", score=0.95),
            RetrievalResult(id="3", text="doc3", score=0.8),
        ]

        # doc2 appears in both, should rank first
        fused = retriever._rrf_fusion(bm25, vector, top_k=3)
        assert len(fused) == 3
        assert fused[0].id == "2"
