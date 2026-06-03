# 常见问题与陷阱

## 1. Windows CUDA 初始化

```python
# 必须在 import sentence_transformers 之前
import torch
torch.cuda.is_available()  # 触发 CUDA runtime 初始化
from sentence_transformers import SentenceTransformer
```

不初始化 CUDA 直接 import → 静默崩溃（无 traceback）。

## 2. Milvus 分页限制

offset+limit > 16384 会报错。用 id 范围分页（见 vector-stores.md）。

## 3. Reranker OOM

CrossEncoder 处理每个 (query, doc) 对，>20 个候选在 8GB 显存上容易 OOM。
解决方案：`CrossEncoder(model, device="cpu")` + 控制候选数量 `top_k=10, rerank_top_n=5`。

## 4. 嵌入模型选择误区

- **bge-base-zh** ≠ **bge-base-en**：中文场景用 zh 版本
- **bge-m3 训练需要 24GB+**：8GB 显存只能推理，不能微调
- **API 模型没有 query instruction**：text-embedding-3-small 等不需要加指令前缀

## 5. 分块 overlap 过大

overlap 过大 → chunk 高度重复 → 检索冗余 → 浪费 reranker 算力。
经验值：overlap = chunk_size 的 20-25%。

## 6. BM25 中文分词

```python
import jieba
jieba.load_userdict("domain_terms.txt")  # 加载领域术语
# "营业收入" 不应被切成 "营业" + "收入"
```

## 7. API base_url 拼接

```python
# 错误：base_url 已含 /v1，再拼一次变 /v1/v1/chat/completions
base_url = "https://api.example.com/v1"
url = f"{base_url}/v1/chat/completions"  # 404!

# 正确：
base_url = base_url.rstrip("/")
if not base_url.endswith("/v1"):
    base_url += "/v1"
```

## 8. LightRAG 集成坑

- embedding 函数必须是 async + 返回 numpy.ndarray（不是 list）
- llm_model_func 必须过滤 kwargs
- 不要用 openai_complete_if_cache（忽略 api_key 参数）
- 没有断点续传：中断 ainsert() 会从头重跑（但 LLM cache 保留）

## 9. 嵌入模型微调

### 训练数据格式
```json
{"query": "兴图新科2023年营收是多少？", "pos": ["兴图新科2023年度营业收入为..."], "neg": ["力源信息2023年营收..."]}
```

### bge-base-zh-v1.5 微调（8GB 显存）
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

关键：hard negatives 必须是语义相近但不正确的文档（不是随机文档）。

## 10. RAGAS 评估

```python
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy, LLMContextPrecisionWithoutReference, LLMContextRecall
from datasets import Dataset

data = {
    "question": ["什么是RAG？"],
    "answer": ["RAG是检索增强生成..."],
    "contexts": [["RAG全称Retrieval-Augmented..."]],
    "ground_truth": ["RAG是一种结合检索和生成的AI技术..."],
}
dataset = Dataset.from_dict(data)
result = evaluate(dataset, metrics=[Faithfulness(), AnswerRelevancy(), LLMContextPrecisionWithoutReference(), LLMContextRecall()])
```
