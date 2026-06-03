---
name: rag-builder
description: Build and optimize RAG systems — PDF parsing, chunking, hybrid retrieval, reranking, query decomposition, RAGAS evaluation. Includes config validation, project scaffolding, and benchmarking tools.
triggers:
  - RAG
  - retrieval augmented generation
  - PDF parsing
  - chunking
  - embedding
  - vector search
  - hybrid retrieval
  - BM25
  - reranker
  - query decomposition
  - RAGAS
  - Milvus
  - Chroma
  - FAISS
  - bge
  - knowledge base
---

# RAG Builder Skill

从零构建或优化 RAG（检索增强生成）系统。覆盖完整 pipeline：文档解析 → 分块 → 向量化 → 混合检索 → 精排 → 查询分解 → 评估。

## 快速决策树

```
你的场景是什么？
├── 从零搭建 RAG → 阅读「完整 Pipeline 指南」，用 rag-builder scaffold 生成骨架
├── 检索效果差 → 跳转「检索优化」章节
├── 需要评估 → 跳转「RAGAS 评估」章节
└── PDF 解析问题 → 跳转「文档解析」章节
```

---

## 1. 完整 Pipeline 指南

### 1.1 Pipeline 架构

```
文档 → 解析(PDF/MD/TXT) → 分块(Chunking) → 向量化(Embedding) → 存储(Milvus/Chroma)
                                                                              ↓
用户查询 → 查询理解 → 混合检索(BM25+Vector) → Reranker精排 → LLM生成 → 回答
```

### 1.2 配置验证

用 `rag-builder validate` 检查配置是否合理：

```bash
python -m rag_builder validate rag_config.json
```

配置文件示例（`rag_config.json`）：
```json
{
  "chunking": {
    "strategy": "recursive",
    "chunk_size": 512,
    "chunk_overlap": 128,
    "min_chunk_size": 50
  },
  "embedding": {
    "model": "bge-base-zh-v1.5",
    "batch_size": 8,
    "device": "auto",
    "normalize": true
  },
  "vector_store": {
    "backend": "milvus",
    "collection": "my_docs",
    "metric": "cosine",
    "index_type": "HNSW"
  },
  "retriever": {
    "strategy": "hybrid",
    "top_k": 10,
    "rerank_top_n": 5,
    "bm25_weight": 0.3,
    "vector_weight": 0.7,
    "reranker_model": "bge-reranker-base"
  },
  "query": {
    "decompose": false,
    "decompose_strategy": "step_back",
    "max_sub_queries": 3,
    "synonym_expansion": true
  }
}
```

### 1.3 生成项目骨架

```bash
# 生成示例配置
python -m rag_builder init -o rag_config.json

# 验证配置
python -m rag_builder validate rag_config.json

# 生成项目骨架
python -m rag_builder scaffold rag_config.json -o ./output -n my-rag
```

生成的项目包含 `ingest.py`（入库）、`query.py`（查询）、`config.py`（配置），直接可用。

---

## 2. 文档解析

### 2.1 PDF 解析方案对比

| 方案 | 适用场景 | 安装 | 输出格式 |
|------|---------|------|---------|
| **pymupdf** | 简单 PDF，纯文本提取 | `pip install pymupdf` | 按页文本 |
| **marker-pdf** | 复杂排版，OCR 需求 | `pip install marker-pdf` | Markdown |
| **MinerU** | 学术论文，表格/公式 | Docker: `opendatalab/mineru` | content_list.json |
| **unstructured** | 通用文档 | `pip install unstructured` | 元素列表 |

### 2.2 pymupdf 快速提取

```python
import fitz  # pymupdf

def extract_pdf(pdf_path: str) -> list[dict]:
    """提取 PDF 文本，按页分割。"""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append({"text": text, "page": i + 1, "source": pdf_path})
    return pages
```

### 2.3 MinerU Docker 解析（复杂 PDF）

```bash
# 解析 PDF
docker run --rm --gpus all \
  -v /path/to/pdfs:/data \
  opendatalab/mineru:latest \
  mineru -p /data/file.pdf -o /data/output -b pipeline

# 输出在 /data/output/file/auto/content_list.json
```

content_list.json 结构：
```json
[
  {
    "type": "text",
    "text": "正文内容...",
    "page_idx": 0
  },
  {
    "type": "table",
    "table_body": "<html>...</html>",
    "page_idx": 1
  }
]
```

### 2.4 Markdown/纯文本

```python
from pathlib import Path

def load_text_files(directory: str) -> list[dict]:
    """加载目录下所有 .md 和 .txt 文件。"""
    docs = []
    for ext in ["*.md", "*.txt"]:
        for f in Path(directory).glob(f"**/{ext}"):
            text = f.read_text(encoding="utf-8", errors="ignore")
            docs.append({"text": text, "source": str(f)})
    return docs
```

---

## 3. 分块策略

### 3.1 策略对比

| 策略 | 原理 | 适用场景 | 推荐 |
|------|------|---------|------|
| **recursive** | 按段落→句子→字符递归切分 | 通用文本 | ⭐ 默认首选 |
| **semantic** | 语义相似度切分 | 主题跳跃多的文档 | 效果好但慢 |
| **by_title** | 按标题层级切分 | 结构化文档（Markdown） | 技术文档推荐 |
| **fixed_size** | 固定字符数切分 | 简单场景 | 不推荐 |

### 3.2 Recursive 分块实现

```python
def recursive_split(text: str, chunk_size: int = 512, overlap: int = 128) -> list[str]:
    """递归分块：段落 → 句子 → 字符。"""
    if len(text) <= chunk_size:
        return [text]

    separators = ["\n\n", "\n", "。", ".", " "]
    return _split_recursive(text, separators, chunk_size, overlap)


def _split_recursive(text, separators, chunk_size, overlap):
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    sep = separators[0]
    parts = text.split(sep)
    result, current = [], ""

    for part in parts:
        candidate = current + sep + part if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                result.append(current)
            if len(part) > chunk_size:
                result.extend(_split_recursive(part, separators[1:], chunk_size, overlap))
            else:
                current = part
    if current:
        result.append(current)

    # 添加 overlap
    if overlap > 0 and len(result) > 1:
        overlapped = [result[0]]
        for i in range(1, len(result)):
            overlapped.append(result[i-1][-overlap:] + result[i])
        result = overlapped

    return result
```

### 3.3 分块参数经验值

| 文档类型 | chunk_size | chunk_overlap | 说明 |
|---------|-----------|---------------|------|
| 通用文本 | 512 | 128 | 默认值，适合大多数场景 |
| 技术文档 | 1024 | 256 | 代码块较长，需要更大窗口 |
| 法律/合同 | 256 | 64 | 精确条款匹配 |
| 学术论文 | 512 | 128 | 与通用相同 |
| 对话记录 | 384 | 128 | 保留对话上下文 |

### 3.4 表格特殊处理

表格不适合常规分块，应保持完整：

```python
def chunk_with_tables(content_list: list[dict], chunk_size: int = 512) -> list[dict]:
    """带表格的分块：表格独立成 chunk，文本正常分块。"""
    chunks = []
    for item in content_list:
        if item.get("type") == "table":
            # 表格完整保留
            chunks.append({
                "text": item["table_body"],
                "type": "table",
                "page": item.get("page_idx"),
            })
        else:
            # 文本正常分块
            text = item.get("text", "")
            for chunk_text in recursive_split(text, chunk_size):
                chunks.append({"text": chunk_text, "type": "text"})
    return chunks
```

---

## 4. 嵌入模型选择

### 4.1 模型对比

| 模型 | 维度 | 最大长度 | 显存 | 语言 | 推荐场景 |
|------|------|---------|------|------|---------|
| **bge-base-zh-v1.5** | 768 | 512 | 1GB | 中文 | ⭐ 中文首选，8GB显存友好 |
| **bge-large-zh-v1.5** | 1024 | 512 | 1.5GB | 中文 | 更高精度，显存充足时 |
| **bge-m3** | 1024 | 8192 | 2GB | 多语言 | 长文档、多语言场景 |
| **text-embedding-3-small** | 1536 | 8191 | 0 | 多语言 | API 调用，无 GPU |
| **text-embedding-3-large** | 3072 | 8191 | 0 | 多语言 | API 调用，最高精度 |

### 4.2 本地嵌入（sentence-transformers）

```python
import torch
torch.cuda.is_available()  # Windows 必须先初始化 CUDA

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-zh-v1.5")
embeddings = model.encode(
    ["文本1", "文本2"],
    batch_size=8,
    normalize_embeddings=True,
    show_progress_bar=True,
)
# embeddings.shape = (2, 768)
```

### 4.3 API 嵌入（OpenAI 兼容）

```python
from openai import OpenAI

client = OpenAI(api_key="your-key", base_url="https://api.openai.com/v1")

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=["文本1", "文本2"],
)
embeddings = [item.embedding for item in response.data]
```

### 4.4 查询指令

部分模型需要为查询添加指令前缀：

```python
# bge-base-zh-v1.5 / bge-large-zh-v1.5
query = "为这个句子生成表示以用于检索相关文章：" + user_query

# bge-m3 / OpenAI — 不需要指令
query = user_query
```

---

## 5. 向量存储

### 5.1 方案对比

| 方案 | 分布式 | 持久化 | 适用规模 | 安装 |
|------|--------|--------|---------|------|
| **Milvus** | ✅ | ✅ | 百万级+ | Docker / pip |
| **Chroma** | ❌ | ✅ | 十万级 | `pip install chromadb` |
| **FAISS** | ❌ | 手动 | 百万级 | `pip install faiss-cpu` |
| **Qdrant** | ✅ | ✅ | 百万级+ | Docker / pip |

### 5.2 Milvus 基础用法

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# 连接
connections.connect("default", host="localhost", port="19530")

# 定义 schema
fields = [
    FieldSchema("id", DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema("text", DataType.VARCHAR, max_length=65535),
    FieldSchema("source", DataType.VARCHAR, max_length=1024),
    FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=768),
]
schema = CollectionSchema(fields, description="RAG chunks")
collection = Collection("my_docs", schema)

# 创建索引
collection.create_index(
    field_name="embedding",
    index_params={"index_type": "HNSW", "metric_type": "COSINE", "params": {"M": 16, "efConstruction": 256}}
)

# 插入
collection.insert([texts, sources, embeddings])
collection.load()

# 搜索
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=10,
    output_fields=["text", "source"],
)
```

### 5.3 Chroma 快速上手

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("my_docs")

# 插入
collection.add(
    documents=["文本1", "文本2"],
    ids=["doc1", "doc2"],
    metadatas=[{"source": "a.pdf"}, {"source": "b.pdf"}],
)

# 查询
results = collection.query(
    query_texts=["查询文本"],
    n_results=10,
)
```

### 5.4 FAISS 轻量方案

```python
import faiss
import numpy as np

dim = 768
index = faiss.IndexFlatIP(dim)  # 内积（已归一化时等价于余弦相似度）

# 添加向量
vectors = np.array(embeddings, dtype="float32")
faiss.normalize_L2(vectors)  # 归一化
index.add(vectors)

# 搜索
query_vec = np.array([query_embedding], dtype="float32")
faiss.normalize_L2(query_vec)
scores, indices = index.search(query_vec, k=10)
```

---

## 6. 混合检索

### 6.1 BM25 + 向量融合

```python
from rank_bm25 import BM25Okapi
import jieba

# BM25 索引
tokenized_corpus = [list(jieba.cut(doc)) for doc in corpus_texts]
bm25 = BM25Okapi(tokenized_corpus)

# BM25 检索
query_tokens = list(jieba.cut(query))
bm25_scores = bm25.get_scores(query_tokens)
bm25_top = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]

# 向量检索
vector_results = collection.search(query_embedding, limit=top_k)

# RRF (Reciprocal Rank Fusion) 融合
def rrf_fusion(ranked_lists: list[list[int]], k: int = 60) -> list[int]:
    """RRF 融合多个排序列表。"""
    scores = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)
```

### 6.2 混合检索策略选择

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| 精确术语查询 | BM25 权重高 (0.6) | 关键词匹配更准 |
| 语义模糊查询 | 向量权重高 (0.7) | 语义理解更好 |
| 混合场景 | RRF 融合 | 不需要调权重 |
| 有 reranker | 先粗排再精排 | reranker 弥补融合不足 |

---

## 7. Reranker 精排

### 7.1 为什么需要 Reranker

检索器（embedding）做的是"粗排"——快速从百万文档中找到 Top-K 候选。
Reranker 做的是"精排"——用交叉编码器精确计算 query-document 相关性。

**两阶段架构：粗排(10) → 精排(5) → 生成**

### 7.2 bge-reranker 用法

```python
import torch
torch.cuda.is_available()  # Windows CUDA 初始化

from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-base", device="cpu")  # CPU 节省显存

# 计算相关性分数
pairs = [(query, doc["text"]) for doc in candidates]
scores = reranker.predict(pairs)

# 按分数排序
scored_docs = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
top_docs = [doc for doc, score in scored_docs[:rerank_top_n]]
```

### 7.3 Reranker 显存管理

| 模型 | 显存 | 速度 | 推荐 |
|------|------|------|------|
| bge-reranker-base | 1.5GB | 快 | ⭐ 8GB显存首选 |
| bge-reranker-large | 2GB | 中 | 更高精度 |
| bge-reranker-v2-m3 | 2GB | 中 | 多语言/长文本 |
| Cohere API | 0 | 快 | 无 GPU 时 |

**关键：reranker 放 CPU 运行**，把 GPU 留给 embedding 模型。reranker 处理量小（Top-K=10-20），CPU 足够快。

---

## 8. 查询分解

### 8.1 三种策略

| 策略 | 原理 | 示例 |
|------|------|------|
| **step_back** | 抽象化查询 | "兴图新科2023年营收" → "兴图新科财务数据" |
| **multi_query** | 多角度改写 | "RAG 优缺点" → ["RAG 优势", "RAG 局限", "RAG 替代方案"] |
| **sub_questions** | 拆子问题 | "对比A和B公司" → ["A公司概况", "B公司概况", "A vs B"] |

### 8.2 实现模板

```python
def decompose_query(question: str, strategy: str = "multi_query", llm=None) -> list[str]:
    """查询分解。需要接入 LLM。"""
    if strategy == "step_back":
        prompt = f"将以下问题抽象化，生成一个更宽泛的检索查询：\n{question}"
    elif strategy == "multi_query":
        prompt = f"从3个不同角度改写以下问题，每行一个：\n{question}"
    elif strategy == "sub_questions":
        prompt = f"将以下问题拆解为2-3个子问题，每行一个：\n{question}"
    else:
        return [question]

    # 调用 LLM
    response = llm.generate(prompt)
    sub_queries = [q.strip() for q in response.split("\n") if q.strip()]
    return sub_queries[:max_sub_queries]
```

### 8.3 何时启用查询分解

- **简单事实查询**（"什么是XXX"）→ 不需要分解
- **复杂对比查询**（"对比A和B"）→ sub_questions
- **模糊查询**（"XXX怎么样"）→ multi_query
- **专业术语查询**（"兴图新科营收"）→ step_back

---

## 9. RAGAS 评估

### 9.1 核心指标

| 指标 | 衡量什么 | 范围 | 说明 |
|------|---------|------|------|
| **Faithfulness** | 回答是否忠于检索结果 | 0-1 | 低分=幻觉 |
| **Answer Relevancy** | 回答是否切题 | 0-1 | 低分=答非所问 |
| **Context Precision** | 检索结果是否精确 | 0-1 | 低分=噪音多 |
| **Context Recall** | 检索是否全面 | 0-1 | 低分=遗漏关键信息 |

### 9.2 RAGAS v0.2+ API

```python
from ragas import evaluate
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    LLMContextPrecisionWithoutReference,
    LLMContextRecall,
)
from datasets import Dataset

# 准备数据
data = {
    "question": ["什么是RAG？"],
    "answer": ["RAG是检索增强生成..."],       # LLM 生成的回答
    "contexts": [["RAG全称Retrieval-Augmented..."]],  # 检索到的上下文
    "ground_truth": ["RAG是一种结合检索和生成的AI技术..."],  # 标准答案
}
dataset = Dataset.from_dict(data)

# 评估
result = evaluate(
    dataset,
    metrics=[
        Faithfulness(),
        AnswerRelevancy(),
        LLMContextPrecisionWithoutReference(),
        LLMContextRecall(),
    ],
)
print(result)
```

### 9.3 用 rag-builder 生成评估数据

```bash
# 从 ground_truth.json 生成 RAGAS 兼容数据集
python -m rag_builder benchmark ground_truth.json --config my_config -o report.json
```

ground_truth.json 格式：
```json
[
  {
    "query": "什么是 RAG？",
    "expected_texts": ["RAG 是检索增强生成..."],
    "answer": "RAG 是一种结合检索和生成的 AI 技术..."
  }
]
```

---

## 10. 常见问题与陷阱

### 10.1 Windows CUDA 初始化

```python
# 必须在 import sentence_transformers 之前
import torch
torch.cuda.is_available()  # 触发 CUDA runtime 初始化

# 然后才能安全导入
from sentence_transformers import SentenceTransformer
```

不初始化 CUDA 直接 import → 静默崩溃（无 traceback）。

### 10.2 Milvus 分页限制

```python
# 错误：offset+limit > 16384 会报错
collection.query(offset=16000, limit=1000)  # ERROR

# 正确：用 id 范围分页
last_id = 0
while True:
    results = collection.query(
        expr=f"id > {last_id}",
        limit=2000,
        output_fields=["text"],
    )
    if not results:
        break
    last_id = results[-1]["id"]
```

### 10.3 Reranker OOM

CrossEncoder 处理每个 (query, doc) 对，>20 个候选在 8GB 显存上容易 OOM。

解决方案：
- `reranker = CrossEncoder(model, device="cpu")` — 放 CPU
- 控制候选数量：`top_k=10, rerank_top_n=5`

### 10.4 嵌入模型选择误区

- **bge-base-zh** ≠ **bge-base-en**：中文场景用 zh 版本
- **bge-m3 训练需要 24GB+**：8GB 显存只能推理，不能微调
- **API 模型没有 query instruction**：text-embedding-3-small 等 API 模型不需要加指令前缀

### 10.5 分块 overlap 过大

overlap 过大 → chunk 之间高度重复 → 检索结果冗余 → 浪费 reranker 算力。

经验值：overlap = chunk_size 的 20-25%。

### 10.6 BM25 中文分词

```python
import jieba

# 不要用默认分词，加自定义词典
jieba.load_userdict("domain_terms.txt")  # 加载领域术语

# 示例：金融领域
# "营业收入" 不应被切成 "营业" + "收入"
```

### 10.7 API base_url 拼接

```python
# 错误：base_url 已含 /v1，再拼一次变 /v1/v1/chat/completions
base_url = "https://api.example.com/v1"
url = f"{base_url}/v1/chat/completions"  # 404!

# 正确：检查并清理
base_url = base_url.rstrip("/")
if not base_url.endswith("/v1"):
    base_url += "/v1"
```

### 10.8 LightRAG 集成坑

- **embedding 函数必须是 async + 返回 numpy.ndarray**（不是 list）
- **llm_model_func 必须过滤 kwargs**（LightRAG 会传入内部参数如 `hashing_kv`）
- **不要用 openai_complete_if_cache**（它忽略 api_key 参数，直接读环境变量）
- **没有断点续传**：中断 `ainsert()` 会从头重跑（但 LLM cache 保留）

---

## 11. 工具使用

### 11.1 CLI 命令

```bash
# 生成示例配置
python -m rag_builder init -o my_config.json

# 验证配置（检查参数兼容性 + GPU 显存估算）
python -m rag_builder validate my_config.json

# 生成项目骨架
python -m rag_builder scaffold my_config.json -o ./output -n my-rag

# 运行评估
python -m rag_builder benchmark ground_truth.json --config v1 -o report.json --json
```

### 11.2 Python API

```python
from rag_builder.config_schema import RAGConfig, estimate_gpu_vram
from rag_builder.scaffold import scaffold_project
from rag_builder.benchmark import run_benchmark, generate_ragas_dataset

# 创建配置
config = RAGConfig.from_dict({"chunking": {"chunk_size": 512}, ...})

# 验证
errors = config.validate()
vram = estimate_gpu_vram(config)

# 生成骨架
files = scaffold_project(config, "./output", "my-rag")

# 评估
report = run_benchmark(queries, my_retrieve_fn, config_name="v1")
print(report.summary())
```

---

## 12. 嵌入模型微调（高级）

当通用模型在领域文档上效果不好时，可以微调 embedding 模型。

### 12.1 训练数据格式

```json
{"query": "兴图新科2023年营收是多少？", "pos": ["兴图新科2023年度营业收入为..."], "neg": ["力源信息2023年营收..."]}
```

### 12.2 bge-base-zh-v1.5 微调（8GB 显存）

```bash
python -m FlagEmbedding.finetune.embedder.encoder_only.base \
  --model_name_or_path BAAI/bge-base-zh-v1.5 \
  --train_data data/finetune_data.jsonl \
  --output_dir output/bge-finetuned \
  --train_group_size 8 \
  --query_max_len 256 --passage_max_len 256 \
  --learning_rate 2e-5 --num_train_epochs 3 \
  --per_device_train_batch_size 16 \
  --fp16 --warmup_ratio 0.1
```

### 12.3 训练数据生成

```
已有文档 chunks → LLM 生成问题(concurrent) → BM25 挖掘 hard negatives → jsonl
```

关键：hard negatives 必须是语义相近但不正确的文档（不是随机文档）。
