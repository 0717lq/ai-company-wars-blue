# Embedding 模型选型

## 模型对比

| 模型 | 维度 | 最大长度 | 显存 | 语言 | 推荐场景 |
|------|------|---------|------|------|---------|
| **bge-base-zh-v1.5** | 768 | 512 | 1GB | 中文 | ⭐ 中文首选，8GB显存友好 |
| **bge-large-zh-v1.5** | 1024 | 512 | 1.5GB | 中文 | 更高精度，显存充足时 |
| **bge-m3** | 1024 | 8192 | 2GB | 多语言 | 长文档、多语言场景 |
| **text-embedding-3-small** | 1536 | 8191 | 0 | 多语言 | API 调用，无 GPU |
| **text-embedding-3-large** | 3072 | 8191 | 0 | 多语言 | API 调用，最高精度 |

## 本地嵌入（sentence-transformers）

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
```

## API 嵌入（OpenAI 兼容）

```python
from openai import OpenAI

client = OpenAI(api_key="your-key", base_url="https://api.openai.com/v1")
response = client.embeddings.create(model="text-embedding-3-small", input=["文本1", "文本2"])
embeddings = [item.embedding for item in response.data]
```

## 查询指令

```python
# bge-base-zh-v1.5 / bge-large-zh-v1.5
query = "为这个句子生成表示以用于检索相关文章：" + user_query

# bge-m3 / OpenAI — 不需要指令
query = user_query
```

## GPU 显存估算

| 模型 | 推理显存 | 微调显存 |
|------|---------|---------|
| bge-base-zh-v1.5 | 1GB | 4GB |
| bge-large-zh-v1.5 | 1.5GB | 6GB |
| bge-m3 | 2GB | 24GB+ |

8GB 显存推荐 bge-base-zh-v1.5，留 7GB 给系统和其他模型。
