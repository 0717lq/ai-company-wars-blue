# 向量存储方案

## 方案对比

| 方案 | 分布式 | 持久化 | 适用规模 | 安装 |
|------|--------|--------|---------|------|
| **Milvus** | ✅ | ✅ | 百万级+ | Docker / pip |
| **Chroma** | ❌ | ✅ | 十万级 | `pip install chromadb` |
| **FAISS** | ❌ | 手动 | 百万级 | `pip install faiss-cpu` |
| **Qdrant** | ✅ | ✅ | 百万级+ | Docker / pip |

## Milvus 基础用法

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

connections.connect("default", host="localhost", port="19530")

fields = [
    FieldSchema("id", DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema("text", DataType.VARCHAR, max_length=65535),
    FieldSchema("source", DataType.VARCHAR, max_length=1024),
    FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=768),
]
schema = CollectionSchema(fields, description="RAG chunks")
collection = Collection("my_docs", schema)

collection.create_index(
    field_name="embedding",
    index_params={"index_type": "HNSW", "metric_type": "COSINE", "params": {"M": 16, "efConstruction": 256}}
)
collection.insert([texts, sources, embeddings])
collection.load()

results = collection.search(
    data=[query_embedding], anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=10, output_fields=["text", "source"],
)
```

## Chroma 快速上手

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("my_docs")

collection.add(documents=["文本1", "文本2"], ids=["doc1", "doc2"])
results = collection.query(query_texts=["查询文本"], n_results=10)
```

## FAISS 轻量方案

```python
import faiss, numpy as np

dim = 768
index = faiss.IndexFlatIP(dim)  # 内积（已归一化时等价于余弦相似度）
vectors = np.array(embeddings, dtype="float32")
faiss.normalize_L2(vectors)
index.add(vectors)

query_vec = np.array([query_embedding], dtype="float32")
faiss.normalize_L2(query_vec)
scores, indices = index.search(query_vec, k=10)
```

## Milvus 分页限制

offset+limit > 16384 会报错。用 id 范围分页：

```python
last_id = 0
while True:
    results = collection.query(expr=f"id > {last_id}", limit=2000, output_fields=["text"])
    if not results:
        break
    last_id = results[-1]["id"]
```
