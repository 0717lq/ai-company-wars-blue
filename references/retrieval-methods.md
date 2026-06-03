# 检索方法

## BM25 + 向量 RRF 融合

```python
from rank_bm25 import BM25Okapi
import jieba

tokenized_corpus = [list(jieba.cut(doc)) for doc in corpus_texts]
bm25 = BM25Okapi(tokenized_corpus)

query_tokens = list(jieba.cut(query))
bm25_scores = bm25.get_scores(query_tokens)
bm25_top = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]

# RRF (Reciprocal Rank Fusion)
def rrf_fusion(ranked_lists: list[list[int]], k: int = 60) -> list[int]:
    scores = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)
```

## 混合检索策略选择

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| 精确术语查询 | BM25 权重高 (0.6) | 关键词匹配更准 |
| 语义模糊查询 | 向量权重高 (0.7) | 语义理解更好 |
| 混合场景 | RRF 融合 | 不需要调权重 |
| 有 reranker | 先粗排再精排 | reranker 弥补融合不足 |

## Reranker 精排

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-base", device="cpu")  # CPU 节省显存
pairs = [(query, doc["text"]) for doc in candidates]
scores = reranker.predict(pairs)
scored_docs = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
top_docs = [doc for doc, score in scored_docs[:rerank_top_n]]
```

### Reranker 显存管理

| 模型 | 显存 | 速度 | 推荐 |
|------|------|------|------|
| bge-reranker-base | 1.5GB | 快 | ⭐ 8GB显存首选 |
| bge-reranker-large | 2GB | 中 | 更高精度 |
| Cohere API | 0 | 快 | 无 GPU 时 |

关键：reranker 放 CPU 运行，把 GPU 留给 embedding 模型。Top-K=10-20，CPU 足够快。

## 查询分解

| 策略 | 原理 | 示例 |
|------|------|------|
| **step_back** | 抽象化查询 | "兴图新科2023年营收" → "兴图新科财务数据" |
| **multi_query** | 多角度改写 | "RAG 优缺点" → ["RAG 优势", "RAG 局限", "RAG 替代方案"] |
| **sub_questions** | 拆子问题 | "对比A和B公司" → ["A公司概况", "B公司概况", "A vs B"] |

### 何时启用

- 简单事实查询 → 不需要分解
- 复杂对比查询 → sub_questions
- 模糊查询 → multi_query
- 专业术语查询 → step_back
