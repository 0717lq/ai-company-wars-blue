"""Tests for rag_builder.cli — CLI 命令测试。"""

import json
import sys

from rag_builder.cli import main

# 预定义测试配置字典，避免重复和长行
VALID_CONFIG = {
    "chunking": {
        "strategy": "recursive",
        "chunk_size": 512,
        "chunk_overlap": 128,
        "min_chunk_size": 50,
    },
    "embedding": {
        "model": "bge-base-zh-v1.5",
        "batch_size": 8,
        "device": "auto",
        "normalize": True,
    },
    "vector_store": {
        "backend": "milvus",
        "collection": "default",
        "metric": "cosine",
        "index_type": "HNSW",
    },
    "retriever": {
        "strategy": "hybrid",
        "top_k": 10,
        "rerank_top_n": 5,
        "bm25_weight": 0.3,
        "vector_weight": 0.7,
        "reranker_model": "bge-reranker-base",
    },
    "query": {
        "decompose": False,
        "decompose_strategy": "step_back",
        "max_sub_queries": 3,
        "synonym_expansion": True,
    },
}

INVALID_CONFIG = {
    "chunking": {
        "strategy": "invalid",
        "chunk_size": 10,
        "chunk_overlap": -1,
        "min_chunk_size": 5,
    },
    "embedding": {
        "model": "gpt-4",
        "batch_size": 0,
        "device": "tpu",
        "normalize": True,
    },
    "vector_store": {
        "backend": "pinecone",
        "collection": "",
        "metric": "manhattan",
        "index_type": "IVF_PQ",
    },
    "retriever": {
        "strategy": "dpr",
        "top_k": 0,
        "rerank_top_n": 100,
        "bm25_weight": 2.0,
        "vector_weight": -1,
        "reranker_model": "unknown",
    },
    "query": {
        "decompose": False,
        "decompose_strategy": "tree",
        "max_sub_queries": 0,
        "synonym_expansion": True,
    },
}


def _write_config(path, config):
    """将配置字典写入 JSON 文件。"""
    path.write_text(json.dumps(config), encoding="utf-8")


class TestCLIInit:
    """init 命令测试。"""

    def test_init_creates_config_file(self, tmp_path):
        """init 应生成示例配置文件。"""
        output = tmp_path / "config.json"
        sys.argv = ["rag-builder", "init", "-o", str(output)]
        result = main()
        assert result == 0
        assert output.exists()

        data = json.loads(output.read_text(encoding="utf-8"))
        assert "chunking" in data
        assert "embedding" in data
        assert "vector_store" in data
        assert "retriever" in data
        assert "query" in data

    def test_init_default_output(self, tmp_path, monkeypatch):
        """init 不指定 -o 时应生成 rag_config.json。"""
        monkeypatch.chdir(tmp_path)
        sys.argv = ["rag-builder", "init"]
        result = main()
        assert result == 0
        assert (tmp_path / "rag_config.json").exists()


class TestCLIValidate:
    """validate 命令测试。"""

    def test_validate_valid_config(self, tmp_path, capsys):
        """合法配置应通过验证。"""
        config = tmp_path / "config.json"
        _write_config(config, VALID_CONFIG)

        sys.argv = ["rag-builder", "validate", str(config)]
        result = main()
        assert result == 0

        captured = capsys.readouterr()
        assert "验证通过" in captured.out
        assert "GPU 显存估算" in captured.out

    def test_validate_invalid_config(self, tmp_path, capsys):
        """非法配置应报错。"""
        config = tmp_path / "config.json"
        _write_config(config, INVALID_CONFIG)

        sys.argv = ["rag-builder", "validate", str(config)]
        result = main()
        assert result == 1

        captured = capsys.readouterr()
        assert "验证失败" in captured.out

    def test_validate_nonexistent_file(self, capsys):
        """不存在的文件应报错。"""
        sys.argv = ["rag-builder", "validate", "/nonexistent/config.json"]
        result = main()
        assert result == 1


class TestCLIScaffold:
    """scaffold 命令测试。"""

    def test_scaffold_generates_project(self, tmp_path):
        """scaffold 应生成项目文件。"""
        config = tmp_path / "config.json"
        _write_config(config, VALID_CONFIG)

        output = tmp_path / "output"
        sys.argv = [
            "rag-builder", "scaffold", str(config),
            "-o", str(output), "-n", "test-rag",
        ]
        result = main()
        assert result == 0
        assert (output / "test-rag" / "ingest.py").exists()
        assert (output / "test-rag" / "query.py").exists()

    def test_scaffold_invalid_config_fails(self, tmp_path, capsys):
        """非法配置的 scaffold 应失败。"""
        config = tmp_path / "config.json"
        _write_config(config, {"chunking": {"strategy": "invalid"},
                               "embedding": {"model": "invalid"},
                               "vector_store": {},
                               "retriever": {},
                               "query": {}})

        sys.argv = ["rag-builder", "scaffold", str(config)]
        result = main()
        assert result == 1


class TestCLIBenchmark:
    """benchmark 命令测试。"""

    def test_benchmark_runs(self, tmp_path, capsys):
        """benchmark 命令应正常运行。"""
        gt = tmp_path / "gt.json"
        gt.write_text(json.dumps([
            {"query": "问题1", "expected_texts": ["答案1"]},
            {"query": "问题2", "expected_texts": ["答案2"]},
        ]), encoding="utf-8")

        sys.argv = [
            "rag-builder", "benchmark", str(gt),
            "--config", "test",
        ]
        result = main()
        assert result == 0

        captured = capsys.readouterr()
        assert "RAG Benchmark Report" in captured.out
        assert "test" in captured.out

    def test_benchmark_json_output(self, tmp_path, capsys):
        """benchmark --json 应输出合法 JSON。"""
        gt = tmp_path / "gt.json"
        gt.write_text(json.dumps([
            {"query": "q1", "expected_texts": ["a"]},
        ]), encoding="utf-8")

        sys.argv = ["rag-builder", "benchmark", str(gt), "--json"]
        result = main()
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "num_queries" in data
        assert data["num_queries"] == 1

    def test_benchmark_with_output_file(self, tmp_path):
        """benchmark -o 应保存报告到文件。"""
        gt = tmp_path / "gt.json"
        gt.write_text(json.dumps([
            {"query": "q1", "expected_texts": ["a"]},
        ]), encoding="utf-8")

        report_path = tmp_path / "report.json"
        sys.argv = [
            "rag-builder", "benchmark", str(gt),
            "-o", str(report_path),
        ]
        result = main()
        assert result == 0
        assert report_path.exists()

    def test_benchmark_nonexistent_gt(self, capsys):
        """不存在的 ground truth 文件应报错。"""
        sys.argv = ["rag-builder", "benchmark", "/nonexistent/gt.json"]
        result = main()
        assert result == 1

    def test_benchmark_empty_gt(self, tmp_path, capsys):
        """空 ground truth 应报错。"""
        gt = tmp_path / "gt.json"
        gt.write_text("[]", encoding="utf-8")

        sys.argv = ["rag-builder", "benchmark", str(gt)]
        result = main()
        assert result == 1


class TestCLINoCommand:
    """无子命令时应显示帮助。"""

    def test_no_command_shows_help(self, capsys):
        """无子命令应返回 1 并显示帮助。"""
        sys.argv = ["rag-builder"]
        result = main()
        assert result == 1
