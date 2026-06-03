"""Integration tests - end-to-end pipeline (mock external dependencies)."""

import json
from unittest.mock import MagicMock

import pytest

from rag_builder.benchmark import BenchmarkResult, load_ground_truth, run_benchmark
from rag_builder.config_schema import RAGConfig
from rag_builder.parsers import chunk_documents, chunk_text, parse_markdown
from rag_builder.retriever import BM25Index, HybridRetriever, RetrievalResult
from rag_builder.scaffold import scaffold_project
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


# ── T3: 新增集成测试 ──


class TestScaffoldIntegration:
    """scaffold_project 端到端集成测试。"""

    def test_scaffold_creates_all_files(self, tmp_path):
        """scaffold 应生成完整的项目结构。"""
        config = RAGConfig()
        result = scaffold_project(config, str(tmp_path), "test-rag")

        # 验证返回值包含所有预期文件
        expected_files = {"ingest.py", "query.py", "config.py", "README.md", "requirements.txt", "rag_config.json"}
        assert set(result.keys()) == expected_files

        # 验证文件确实写入磁盘
        project_dir = tmp_path / "test-rag"
        assert project_dir.is_dir()
        for fname in expected_files:
            assert (project_dir / fname).is_file(), f"{fname} 未生成"

    def test_scaffold_config_substituted(self, tmp_path):
        """scaffold 生成的文件应包含配置中的实际值。"""
        config = RAGConfig()
        config.chunking.chunk_size = 512
        config.embedding.model = "bge-base-zh-v1.5"
        config.vector_store.collection = "my_docs"

        result = scaffold_project(config, str(tmp_path), "test-rag")

        # ingest.py 应包含实际的 chunk_size
        assert "512" in result["ingest.py"]
        # config.py 应包含模型名
        assert "bge-base-zh-v1.5" in result["config.py"]
        # rag_config.json 应是合法 JSON 且包含 collection
        cfg = json.loads(result["rag_config.json"])
        assert cfg["vector_store"]["collection"] == "my_docs"

    def test_scaffold_config_json_roundtrip(self, tmp_path):
        """scaffold 生成的 config.json 应可反序列化回 RAGConfig。"""
        config = RAGConfig()
        config.retriever.top_k = 20

        scaffold_project(config, str(tmp_path), "test-rag")
        cfg_path = tmp_path / "test-rag" / "rag_config.json"
        loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert loaded["retriever"]["top_k"] == 20


class TestDiagnoseIntegration:
    """diagnose 端到端集成测试。"""

    def test_run_diagnosis_no_config(self):
        """无配置文件时诊断应返回基本检查结果。"""
        from rag_builder.diagnose import format_report, run_diagnosis

        report = run_diagnosis(config_path=None, skip_network=True)
        # 应至少有 Python 版本检查
        assert len(report.checks) >= 1
        # 格式化为文本
        text = format_report(report)
        assert "Python" in text
        # 格式化为 JSON
        json_str = format_report(report, json_output=True)
        parsed = json.loads(json_str)
        assert "checks" in parsed

    def test_run_diagnosis_with_config(self, tmp_path):
        """有配置文件时应检查配置有效性。"""
        from rag_builder.diagnose import run_diagnosis

        config = RAGConfig()
        cfg_path = tmp_path / "rag_config.json"
        cfg_path.write_text(json.dumps(config.to_dict()), encoding="utf-8")

        report = run_diagnosis(config_path=str(cfg_path), skip_network=True)
        # 应有配置检查结果
        config_checks = [c for c in report.checks if c.name == "配置文件"]
        assert len(config_checks) == 1
        assert config_checks[0].status == "pass"


class TestBenchmarkIntegration:
    """benchmark 端到端集成测试。"""

    def test_benchmark_result_compute_metrics(self):
        """BenchmarkResult 应正确计算 precision/recall/f1。"""
        result = BenchmarkResult(
            query="What is RAG?",
            retrieved_texts=["RAG is retrieval augmented", "Vector DB"],
            expected_texts=["RAG is retrieval augmented"],
        )
        result.compute_metrics()
        assert result.precision == pytest.approx(0.5)  # 1/2
        assert result.recall == pytest.approx(1.0)  # 1/1
        assert result.f1 == pytest.approx(2 / 3)

    def test_benchmark_no_expected(self):
        """无 expected_texts 时 recall=1.0, precision 基于是否有结果。"""
        result = BenchmarkResult(
            query="test",
            retrieved_texts=["something"],
            expected_texts=[],
        )
        result.compute_metrics()
        assert result.recall == 1.0
        assert result.precision == 1.0

    def test_load_ground_truth(self, tmp_path):
        """load_ground_truth 应正确加载 JSON 文件。"""
        gt = [
            {"query": "What is RAG?", "expected": ["RAG doc"]},
            {"query": "How to chunk?", "expected": ["chunking guide"]},
        ]
        gt_path = tmp_path / "ground_truth.json"
        gt_path.write_text(json.dumps(gt), encoding="utf-8")

        loaded = load_ground_truth(str(gt_path))
        assert len(loaded) == 2
        assert loaded[0]["query"] == "What is RAG?"

    def test_run_benchmark_full_flow(self):
        """run_benchmark 完整流程：mock retrieve -> evaluate -> report。"""
        # 构造 mock retrieve 函数（返回 dict 列表）
        def mock_retrieve(query: str):
            return [
                {"text": "RAG is retrieval augmented generation", "source": "rag.md"},
                {"text": "Vector database stores embeddings", "source": "vector.md"},
            ]

        queries = [
            {"query": "What is RAG?", "expected_texts": ["RAG is retrieval augmented generation"]},
        ]

        report = run_benchmark(queries=queries, retrieve_fn=mock_retrieve)
        assert len(report.results) == 1
        assert report.results[0].precision > 0
        assert report.results[0].recall == pytest.approx(1.0)
        assert report.avg_precision > 0

    def test_run_benchmark_string_results(self):
        """retrieve_fn 返回字符串列表时也应正常工作。"""
        def mock_retrieve(query: str):
            return ["RAG doc", "Vector doc"]

        queries = [
            {"query": "test", "expected_texts": ["RAG doc"]},
        ]
        report = run_benchmark(queries=queries, retrieve_fn=mock_retrieve)
        assert len(report.results) == 1
        assert report.results[0].recall == pytest.approx(1.0)
