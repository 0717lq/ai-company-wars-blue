"""Tests for rag_builder.benchmark — 评估工具测试。"""

import json

from rag_builder.benchmark import (
    BenchmarkReport,
    BenchmarkResult,
    generate_ragas_dataset,
    load_ground_truth,
    run_benchmark,
)


class TestBenchmarkResult:
    """单条评估结果测试。"""

    def test_perfect_match(self):
        """完全匹配时 P=R=F1=1.0。"""
        result = BenchmarkResult(
            query="test",
            retrieved_texts=["a", "b"],
            expected_texts=["a", "b"],
        )
        result.compute_metrics()
        assert result.precision == 1.0
        assert result.recall == 1.0
        assert result.f1 == 1.0

    def test_no_overlap(self):
        """完全不匹配时 P=R=F1=0.0。"""
        result = BenchmarkResult(
            query="test",
            retrieved_texts=["a", "b"],
            expected_texts=["c", "d"],
        )
        result.compute_metrics()
        assert result.precision == 0.0
        assert result.recall == 0.0
        assert result.f1 == 0.0

    def test_partial_match(self):
        """部分匹配时指标应介于 0 和 1 之间。"""
        result = BenchmarkResult(
            query="test",
            retrieved_texts=["a", "b", "c"],
            expected_texts=["a", "d"],
        )
        result.compute_metrics()
        # retrieved: {a,b,c}, expected: {a,d}, hits: {a}
        # P = 1/3, R = 1/2
        assert abs(result.precision - 1 / 3) < 0.001
        assert abs(result.recall - 0.5) < 0.001
        assert 0 < result.f1 < 1

    def test_empty_expected(self):
        """expected_texts 为空时特殊处理。"""
        result = BenchmarkResult(
            query="test",
            retrieved_texts=["a"],
            expected_texts=[],
        )
        result.compute_metrics()
        assert result.recall == 1.0

    def test_empty_retrieved(self):
        """retrieved_texts 为空时 P=0。"""
        result = BenchmarkResult(
            query="test",
            retrieved_texts=[],
            expected_texts=["a"],
        )
        result.compute_metrics()
        assert result.precision == 0.0
        assert result.recall == 0.0


class TestBenchmarkReport:
    """评估报告测试。"""

    def test_avg_metrics_empty(self):
        """空报告的平均指标应为 0。"""
        report = BenchmarkReport()
        assert report.avg_precision == 0.0
        assert report.avg_recall == 0.0
        assert report.avg_f1 == 0.0

    def test_avg_metrics_computed(self):
        """平均指标应正确计算。"""
        report = BenchmarkReport(results=[
            BenchmarkResult(query="q1", retrieved_texts=["a"], expected_texts=["a"],
                            precision=1.0, recall=1.0, f1=1.0),
            BenchmarkResult(query="q2", retrieved_texts=["b"], expected_texts=["c"],
                            precision=0.0, recall=0.0, f1=0.0),
        ])
        assert abs(report.avg_precision - 0.5) < 0.001
        assert abs(report.avg_recall - 0.5) < 0.001

    def test_to_json_valid(self):
        """to_json 应输出合法 JSON。"""
        report = BenchmarkReport(
            config_name="test",
            results=[
                BenchmarkResult(query="q1", retrieved_texts=["a"], expected_texts=["a"],
                                precision=1.0, recall=1.0, f1=1.0),
            ],
        )
        data = json.loads(report.to_json())
        assert data["config_name"] == "test"
        assert data["num_queries"] == 1
        assert data["avg_precision"] == 1.0

    def test_summary_contains_config_name(self):
        """summary 应包含配置名称。"""
        report = BenchmarkReport(config_name="my_config")
        text = report.summary()
        assert "my_config" in text

    def test_summary_contains_all_queries(self):
        """summary 应包含所有查询。"""
        report = BenchmarkReport(results=[
            BenchmarkResult(query="问题一", retrieved_texts=[], expected_texts=[],
                            precision=0, recall=0, f1=0),
            BenchmarkResult(query="问题二", retrieved_texts=[], expected_texts=[],
                            precision=0, recall=0, f1=0),
        ])
        text = report.summary()
        assert "问题一" in text
        assert "问题二" in text


class TestRunBenchmark:
    """运行评估测试。"""

    def test_basic_benchmark(self):
        """基本评估流程测试。"""
        queries = [
            {"query": "什么是RAG", "expected_texts": ["RAG是检索增强生成"]},
            {"query": "Python优势", "expected_texts": ["简洁", "生态丰富"]},
        ]

        def mock_retrieve(query: str) -> list[str]:
            if "RAG" in query:
                return ["RAG是检索增强生成", "无关内容"]
            return ["简洁", "其他"]

        report = run_benchmark(queries, mock_retrieve, config_name="test")
        assert len(report.results) == 2
        assert report.results[0].precision > 0

    def test_benchmark_with_dict_results(self):
        """retrieve 返回 dict 列表时应提取 text 字段。"""
        queries = [{"query": "test", "expected_texts": ["答案"]}]

        def mock_retrieve(query: str) -> list[dict]:
            return [{"text": "答案", "score": 0.95}, {"text": "噪音", "score": 0.3}]

        report = run_benchmark(queries, mock_retrieve)
        assert report.results[0].precision > 0


class TestLoadGroundTruth:
    """加载 ground truth 测试。"""

    def test_load_valid_json(self, tmp_path):
        """加载合法 JSON 文件。"""
        data = [{"query": "q1", "expected_texts": ["a"]}]
        path = tmp_path / "gt.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        result = load_ground_truth(str(path))
        assert len(result) == 1
        assert result[0]["query"] == "q1"


class TestGenerateRagasDataset:
    """RAGAS 数据集生成测试。"""

    def test_generates_correct_format(self):
        """生成的数据应符合 RAGAS 格式。"""
        queries = [
            {"query": "问题", "answer": "答案", "expected_texts": ["上下文"]},
        ]

        def mock_retrieve(query):
            return ["检索结果1", "检索结果2"]

        dataset = generate_ragas_dataset(queries, mock_retrieve)
        assert len(dataset) == 1
        item = dataset[0]
        assert "question" in item
        assert "ground_truth" in item
        assert "contexts" in item
        assert "answer" in item
        assert item["question"] == "问题"
        assert len(item["contexts"]) == 2

    def test_with_generate_function(self):
        """提供 generate_fn 时应使用它生成 answer。"""
        queries = [{"query": "q", "answer": ""}]

        def mock_retrieve(query):
            return ["ctx"]

        def mock_generate(query, docs):
            return "生成的回答"

        dataset = generate_ragas_dataset(queries, mock_retrieve, mock_generate)
        assert dataset[0]["answer"] == "生成的回答"
