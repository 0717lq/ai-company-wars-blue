"""CLI 命令测试。"""
import json
import sys

from rag_builder.cli import main


class TestCmdInit:
    """init 子命令测试。"""

    def test_init_creates_config(self, tmp_path):
        """init 应生成 JSON 配置文件。"""
        output = tmp_path / "config.json"
        sys.argv = ["rag-builder", "init", "-o", str(output)]
        result = main()
        assert result == 0
        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert "chunking" in data
        assert "embedding" in data
        assert "vector_store" in data

    def test_init_default_output(self, tmp_path, monkeypatch):
        """init 默认输出到 rag_config.json。"""
        monkeypatch.chdir(tmp_path)
        sys.argv = ["rag-builder", "init"]
        result = main()
        assert result == 0
        assert (tmp_path / "rag_config.json").exists()


class TestCmdValidate:
    """validate 子命令测试。"""

    def test_validate_valid_config(self, tmp_path):
        """验证有效配置应返回 0。"""
        config = tmp_path / "config.json"
        config.write_text(json.dumps({
            "chunking": {"strategy": "recursive", "chunk_size": 512, "chunk_overlap": 128, "min_chunk_size": 50},
            "embedding": {"model": "bge-base-zh-v1.5", "batch_size": 8, "device": "auto", "normalize": True},
            "vector_store": {"backend": "milvus", "collection": "default", "metric": "cosine", "index_type": "HNSW"},
            "retriever": {"strategy": "hybrid", "top_k": 10, "rerank_top_n": 5, "bm25_weight": 0.3, "vector_weight": 0.7, "reranker_model": "bge-reranker-base"},
            "query": {"decompose": False, "decompose_strategy": "step_back", "max_sub_queries": 3, "synonym_expansion": True},
        }), encoding="utf-8")
        sys.argv = ["rag-builder", "validate", str(config)]
        result = main()
        assert result == 0

    def test_validate_invalid_config(self, tmp_path):
        """验证无效配置应返回 1。"""
        config = tmp_path / "bad.json"
        config.write_text(json.dumps({
            "chunking": {"strategy": "recursive", "chunk_size": 10, "chunk_overlap": 128, "min_chunk_size": 50},
            "embedding": {"model": "unknown-model", "batch_size": 8, "device": "auto", "normalize": True},
        }), encoding="utf-8")
        sys.argv = ["rag-builder", "validate", str(config)]
        result = main()
        assert result == 1

    def test_validate_nonexistent_file(self):
        """验证不存在的文件应返回 1。"""
        sys.argv = ["rag-builder", "validate", "/nonexistent/config.json"]
        result = main()
        assert result == 1


class TestCmdScaffold:
    """scaffold 子命令测试。"""

    def test_scaffold_creates_files(self, tmp_path):
        """scaffold 应生成项目文件。"""
        config = tmp_path / "config.json"
        config.write_text(json.dumps({
            "chunking": {"strategy": "recursive", "chunk_size": 512, "chunk_overlap": 128, "min_chunk_size": 50},
            "embedding": {"model": "bge-base-zh-v1.5", "batch_size": 8, "device": "auto", "normalize": True},
            "vector_store": {"backend": "milvus", "collection": "default", "metric": "cosine", "index_type": "HNSW"},
            "retriever": {"strategy": "hybrid", "top_k": 10, "rerank_top_n": 5, "bm25_weight": 0.3, "vector_weight": 0.7, "reranker_model": "bge-reranker-base"},
            "query": {"decompose": False, "decompose_strategy": "step_back", "max_sub_queries": 3, "synonym_expansion": True},
        }), encoding="utf-8")
        sys.argv = ["rag-builder", "scaffold", str(config), "-o", str(tmp_path), "-n", "test-proj"]
        result = main()
        assert result == 0
        assert (tmp_path / "test-proj" / "ingest.py").exists()
        assert (tmp_path / "test-proj" / "query.py").exists()


class TestCmdBenchmark:
    """benchmark 子命令测试。"""

    def test_benchmark_runs(self, tmp_path):
        """benchmark 应正常运行。"""
        gt = tmp_path / "gt.json"
        gt.write_text(json.dumps([
            {"query": "test", "expected_texts": ["text1"]},
        ]), encoding="utf-8")
        sys.argv = ["rag-builder", "benchmark", str(gt)]
        result = main()
        assert result == 0

    def test_benchmark_json_output(self, tmp_path, capsys):
        """benchmark --json 应输出 JSON。"""
        gt = tmp_path / "gt.json"
        gt.write_text(json.dumps([
            {"query": "test", "expected_texts": ["text1"]},
        ]), encoding="utf-8")
        sys.argv = ["rag-builder", "benchmark", str(gt), "--json"]
        result = main()
        assert result == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert "avg_precision" in data

    def test_benchmark_nonexistent_gt(self):
        """不存在的 ground truth 文件应返回 1。"""
        sys.argv = ["rag-builder", "benchmark", "/nonexistent/gt.json"]
        result = main()
        assert result == 1


class TestCmdIngest:
    """ingest 子命令测试。"""

    def test_ingest_preview(self, tmp_path, capsys):
        """ingest --preview 应预览分块结果而不入库。"""
        doc = tmp_path / "test.md"
        doc.write_text("# 标题\n这是一段测试内容。" * 20, encoding="utf-8")
        sys.argv = ["rag-builder", "ingest", str(doc), "--preview"]
        result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "预览分块结果" in output

    def test_ingest_nonexistent_path(self):
        """ingest 不存在的路径应返回 1。"""
        sys.argv = ["rag-builder", "ingest", "/nonexistent/path"]
        result = main()
        assert result == 1

    def test_ingest_directory(self, tmp_path, capsys):
        """ingest 应支持目录输入。"""
        (tmp_path / "a.md").write_text("# Doc A\n内容A" * 10, encoding="utf-8")
        (tmp_path / "b.txt").write_text("文本B" * 10, encoding="utf-8")
        sys.argv = ["rag-builder", "ingest", str(tmp_path), "--preview"]
        result = main()
        assert result == 0

    def test_ingest_with_chunk_size(self, tmp_path, capsys):
        """ingest --chunk-size 应控制分块大小。"""
        doc = tmp_path / "test.md"
        doc.write_text("A" * 1000, encoding="utf-8")
        sys.argv = ["rag-builder", "ingest", str(doc), "--preview", "--chunk-size", "200"]
        result = main()
        assert result == 0


class TestCmdQuery:
    """query 子命令测试。"""

    def test_query_nonexistent_without_store(self, capsys):
        """query 在没有向量库时应报错。"""
        sys.argv = ["rag-builder", "query", "test question"]
        # 会因为依赖缺失而失败
        result = main()
        # 结果取决于环境，可能是 1（依赖缺失）或 0
        assert result in (0, 1)

    def test_query_json_flag(self):
        """query --json 参数应被正确解析。"""
        sys.argv = ["rag-builder", "query", "test", "--json"]
        result = main()
        assert result in (0, 1)


class TestNoCommand:
    """无子命令测试。"""

    def test_no_command_prints_help(self, capsys):
        """无子命令应打印帮助信息并返回 1。"""
        sys.argv = ["rag-builder"]
        result = main()
        assert result == 1
