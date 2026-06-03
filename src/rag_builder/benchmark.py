"""RAG pipeline benchmarking — 评估检索质量和配置效果。

提供轻量级的检索质量评估工具，不依赖 RAGAS 框架本身，但能生成 RAGAS 兼容的评估数据。
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class BenchmarkResult:
    """单条评估结果。"""
    query: str
    retrieved_texts: list[str]
    expected_texts: list[str]
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0

    def compute_metrics(self) -> None:
        """计算精确率、召回率、F1。"""
        if not self.expected_texts:
            self.precision = 1.0 if self.retrieved_texts else 0.0
            self.recall = 1.0
            self.f1 = self.precision
            return

        retrieved_set = set(self.retrieved_texts)
        expected_set = set(self.expected_texts)
        hits = retrieved_set & expected_set

        self.precision = len(hits) / len(retrieved_set) if retrieved_set else 0.0
        self.recall = len(hits) / len(expected_set) if expected_set else 0.0
        self.f1 = (
            2 * self.precision * self.recall / (self.precision + self.recall)
            if (self.precision + self.recall) > 0
            else 0.0
        )


@dataclass
class BenchmarkReport:
    """评估报告。"""
    results: list[BenchmarkResult] = field(default_factory=list)
    config_name: str = "default"
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def avg_precision(self) -> float:
        """平均精确率。"""
        if not self.results:
            return 0.0
        return sum(r.precision for r in self.results) / len(self.results)

    @property
    def avg_recall(self) -> float:
        """平均召回率。"""
        if not self.results:
            return 0.0
        return sum(r.recall for r in self.results) / len(self.results)

    @property
    def avg_f1(self) -> float:
        """平均 F1 分数。"""
        if not self.results:
            return 0.0
        return sum(r.f1 for r in self.results) / len(self.results)

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典。"""
        return {
            "config_name": self.config_name,
            "timestamp": self.timestamp,
            "num_queries": len(self.results),
            "avg_precision": round(self.avg_precision, 4),
            "avg_recall": round(self.avg_recall, 4),
            "avg_f1": round(self.avg_f1, 4),
            "per_query": [
                {
                    "query": r.query,
                    "precision": round(r.precision, 4),
                    "recall": round(r.recall, 4),
                    "f1": round(r.f1, 4),
                    "retrieved_count": len(r.retrieved_texts),
                    "expected_count": len(r.expected_texts),
                }
                for r in self.results
            ],
        }

    def to_json(self) -> str:
        """转为 JSON 字符串。"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def summary(self) -> str:
        """生成文本摘要。"""
        lines = [
            "=== RAG Benchmark Report ===",
            f"Config: {self.config_name}",
            f"Queries: {len(self.results)}",
            f"Avg Precision: {self.avg_precision:.4f}",
            f"Avg Recall: {self.avg_recall:.4f}",
            f"Avg F1: {self.avg_f1:.4f}",
            "",
            "--- Per Query ---",
        ]
        for i, r in enumerate(self.results):
            lines.append(
                f"  [{i+1}] P={r.precision:.3f} R={r.recall:.3f} F1={r.f1:.3f} | {r.query[:50]}"
            )
        return "\n".join(lines)


def load_ground_truth(path: str) -> list[dict[str, Any]]:
    """加载 ground truth 评估数据。

    格式:
    [
        {
            "query": "什么是 RAG？",
            "expected_texts": ["RAG 是检索增强生成...", "Retrieval-Augmented Generation..."]
        },
        ...
    ]
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(
    queries: list[dict[str, Any]],
    retrieve_fn: Any,
    config_name: str = "default",
) -> BenchmarkReport:
    """运行评估。

    Args:
        queries: 评估数据，每条含 query 和 expected_texts
        retrieve_fn: 检索函数，接收 query 字符串，返回 list[str]（检索到的文本列表）
        config_name: 配置名称

    Returns:
        BenchmarkReport 评估报告
    """
    report = BenchmarkReport(config_name=config_name)

    for item in queries:
        query = item["query"]
        expected = item.get("expected_texts", [])

        # 调用检索函数
        retrieved = retrieve_fn(query)
        if isinstance(retrieved, list) and retrieved and isinstance(retrieved[0], dict):
            retrieved_texts = [r.get("text", str(r)) for r in retrieved]
        else:
            retrieved_texts = [str(r) for r in retrieved]

        # 计算指标
        result = BenchmarkResult(
            query=query,
            retrieved_texts=retrieved_texts,
            expected_texts=expected,
        )
        result.compute_metrics()
        report.results.append(result)

    return report


def generate_ragas_dataset(
    queries: list[dict[str, Any]],
    retrieve_fn: Any,
    generate_fn: Any = None,
) -> list[dict[str, Any]]:
    """生成 RAGAS 兼容的评估数据集。

    输出格式符合 RAGAS evaluate() 的 requirements:
    - question: 用户问题
    - ground_truth: 标准答案
    - contexts: 检索到的上下文列表
    - answer: LLM 生成的回答

    Args:
        queries: 评估数据
        retrieve_fn: 检索函数
        generate_fn: 生成函数（可选）

    Returns:
        RAGAS 兼容的数据集
    """
    dataset = []

    for item in queries:
        query = item["query"]
        ground_truth = item.get("answer", "")

        # 检索
        retrieved = retrieve_fn(query)
        if isinstance(retrieved, list) and retrieved and isinstance(retrieved[0], dict):
            contexts = [r.get("text", str(r)) for r in retrieved]
        else:
            contexts = [str(r) for r in retrieved]

        # 生成回答
        answer = ""
        if generate_fn:
            answer = generate_fn(query, retrieved)
        elif ground_truth:
            answer = ground_truth  # 没有生成函数时用 ground_truth 占位

        dataset.append({
            "question": query,
            "ground_truth": ground_truth,
            "contexts": contexts,
            "answer": answer,
        })

    return dataset
