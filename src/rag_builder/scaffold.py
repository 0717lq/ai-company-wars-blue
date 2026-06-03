"""RAG project scaffolding — generate boilerplate project structure.

根据配置生成完整的 RAG 项目骨架代码，包括 ingest.py、query.py、config.py 等。
"""

import json
from pathlib import Path
from typing import Any

from .config_schema import RAGConfig


def _render(template: str, **kwargs: Any) -> str:
    """用 $VAR 占位符替换模板变量，避免与 Python f-string 的 {} 冲突。"""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"${key}", str(value))
    return result


# 每个 scaffold 文件的模板（用 $VAR 占位符）
INGEST_TEMPLATE = '''"""RAG Ingest pipeline — PDF/文本解析、分块、向量化、入库。

用法:
    python ingest.py <input_path> [--preview] [--collection NAME]
"""

import argparse
import json
import sys
from pathlib import Path


def load_documents(input_path: str) -> list[dict]:
    """加载文档。支持 PDF、Markdown、纯文本。"""
    path = Path(input_path)
    documents = []

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.glob("**/*.md")) + list(path.glob("**/*.txt"))
    else:
        print(f"Error: {input_path} not found")
        sys.exit(1)

    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        documents.append({"text": text, "source": str(f)})
    return documents


def chunk_documents(documents: list[dict], chunk_size: int = $chunk_size,
                    chunk_overlap: int = $chunk_overlap) -> list[dict]:
    """递归分块。按段落 -> 句子 -> 字符三级分割。"""
    chunks = []
    for doc in documents:
        text = doc["text"]
        # 简单的递归分块实现
        separators = ["\\n\\n", "\\n", "。", ".", " "]
        current_chunks = _split_text(text, separators, chunk_size, chunk_overlap)
        for i, chunk_text in enumerate(current_chunks):
            if len(chunk_text.strip()) < $min_chunk_size:
                continue
            chunks.append({
                "text": chunk_text.strip(),
                "source": doc["source"],
                "chunk_index": i,
            })
    return chunks


def _split_text(text: str, separators: list[str], chunk_size: int,
                overlap: int) -> list[str]:
    """递归文本分割。"""
    if len(text) <= chunk_size:
        return [text]

    # 选择第一个能分割的分隔符
    sep = separators[0] if separators else ""
    remaining_seps = separators[1:] if len(separators) > 1 else []

    if sep:
        parts = text.split(sep)
    else:
        # 按字符硬切
        parts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    result = []
    current = ""
    for part in parts:
        candidate = current + sep + part if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                result.append(current)
            # 如果单个 part 超长，递归用更小的分隔符
            if len(part) > chunk_size and remaining_seps:
                result.extend(_split_text(part, remaining_seps, chunk_size, overlap))
            else:
                current = part
    if current:
        result.append(current)

    # 添加 overlap
    if overlap > 0 and len(result) > 1:
        overlapped = [result[0]]
        for i in range(1, len(result)):
            prev_tail = result[i-1][-overlap:]
            overlapped.append(prev_tail + result[i])
        result = overlapped

    return result


def preview_chunks(chunks: list[dict], n: int = 5) -> None:
    """预览前 N 个 chunk。"""
    print(f"\\n=== 预览: 共 {{len(chunks)}} 个 chunks ===")
    for i, chunk in enumerate(chunks[:n]):
        print(f"\\n--- Chunk {{i+1}} ({{len(chunk[\'text\'])}} chars) ---")
        print(chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"])
    if len(chunks) > n:
        print(f"\\n... 还有 {{len(chunks) - n}} 个 chunks")


def main():
    parser = argparse.ArgumentParser(description="RAG Ingest Pipeline")
    parser.add_argument("input_path", help="输入文件或目录")
    parser.add_argument("--preview", action="store_true", help="预览分块结果，不入库")
    parser.add_argument("--collection", default="$collection", help="Milvus collection 名称")
    parser.add_argument("--chunk-size", type=int, default=$chunk_size)
    parser.add_argument("--chunk-overlap", type=int, default=$chunk_overlap)
    args = parser.parse_args()

    print(f"[1/3] 加载文档: {{args.input_path}}")
    docs = load_documents(args.input_path)
    print(f"  -> 加载了 {{len(docs)}} 个文档")

    print(f"[2/3] 分块 (chunk_size={{args.chunk_size}}, overlap={{args.chunk_overlap}})")
    chunks = chunk_documents(docs, args.chunk_size, args.chunk_overlap)
    print(f"  -> 生成 {{len(chunks)}} 个 chunks")

    if args.preview:
        preview_chunks(chunks)
        return

    print("[3/3] 向量化 + 入库...")
    # TODO: 接入 embedding model + Milvus
    # from sentence_transformers import SentenceTransformer
    # model = SentenceTransformer("$embedding_model")
    # embeddings = model.encode([c["text"] for c in chunks], batch_size=$batch_size)
    print("  -> TODO: 接入向量库（参考 SKILL.md 中的 Milvus 配置）")
    print("\\nDone!")


if __name__ == "__main__":
    main()
'''


QUERY_TEMPLATE = '''"""RAG Query pipeline — 检索增强生成。

用法:
    python query.py "你的问题"
    python query.py "你的问题" --json
"""

import argparse
import json
import sys
from datetime import datetime


def decompose_query(question: str, strategy: str = "$decompose_strategy") -> list[str]:
    """查询分解。将复杂问题拆成子问题。"""
    # TODO: 接入 LLM 做查询分解
    # 策略: step_back (抽象化), multi_query (多角度), sub_questions (拆子问题)
    return [question]  # 默认不分解


def retrieve(question: str, top_k: int = $top_k) -> list[dict]:
    """检索相关文档。"""
    # TODO: 接入 Milvus + BM25 混合检索
    # 1. 向量检索: collection.search(embedding, limit=top_k)
    # 2. BM25 检索: bm25_index.get_top_n(question, corpus, n=top_k)
    # 3. RRF 融合: reciprocal_rank_fusion(vector_results, bm25_results)
    return [
        {"text": "示例检索结果", "score": 0.95, "source": "demo.pdf"}
    ]


def rerank(question: str, documents: list[dict], top_n: int = $rerank_top_n) -> list[dict]:
    """Reranker 精排。"""
    # TODO: 接入 bge-reranker
    # from sentence_transformers import CrossEncoder
    # model = CrossEncoder("BAAI/bge-reranker-base")
    # scores = model.predict([(question, doc["text"]) for doc in documents])
    # 按 score 排序取 top_n
    return documents[:top_n]


def generate(question: str, context: list[dict]) -> str:
    """生成回答。"""
    # TODO: 接入 LLM
    context_text = "\\n---\\n".join(d["text"] for d in context)
    prompt = f"""基于以下参考资料回答问题。

参考资料:
{context_text}

问题: {question}
请用中文回答，引用来源。"""
    return f"[TODO: 接入 LLM] 基于 {len(context)} 个文档生成回答"


def query_pipeline(question: str, json_output: bool = False) -> dict | str:
    """完整 RAG 查询流程。"""
    # 1. 查询分解
    sub_queries = decompose_query(question)

    # 2. 检索
    all_docs = []
    for sq in sub_queries:
        docs = retrieve(sq)
        all_docs.extend(docs)

    # 3. 去重 + Rerank
    seen = set()
    unique_docs = []
    for doc in all_docs:
        if doc["text"] not in seen:
            seen.add(doc["text"])
            unique_docs.append(doc)
    reranked = rerank(question, unique_docs)

    # 4. 生成
    answer = generate(question, reranked)

    result = {
        "tool": "rag-builder",
        "command": "query",
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "sub_queries": sub_queries,
        "retrieved_docs": len(all_docs),
        "reranked_docs": len(reranked),
        "answer": answer,
        "sources": [d.get("source", "") for d in reranked],
    }

    if json_output:
        return result
    else:
        print(f"\\n问题: {question}")
        if len(sub_queries) > 1:
            print(f"子问题: {sub_queries}")
        print(f"检索: {len(all_docs)} -> 精排: {len(reranked)} -> 生成回答")
        print(f"\\n回答:\\n{answer}")
        print(f"\\n来源: {{", ".join(d.get('source', '') for d in reranked)}}")
        return result


def main():
    parser = argparse.ArgumentParser(description="RAG Query Pipeline")
    parser.add_argument("question", help="用户问题")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    parser.add_argument("--top-k", type=int, default=$top_k)
    parser.add_argument("--rerank-top-n", type=int, default=$rerank_top_n)
    args = parser.parse_args()

    result = query_pipeline(args.question, args.json)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
'''


CONFIG_TEMPLATE = '''"""RAG pipeline configuration.

修改此文件来配置你的 RAG pipeline。
"""

# === 分块配置 ===
CHUNKING = {
    "strategy": "$chunk_strategy",       # recursive, semantic, by_title, fixed_size
    "chunk_size": $chunk_size,            # 每个 chunk 的最大字符数
    "chunk_overlap": $chunk_overlap,      # chunk 之间的重叠字符数
    "min_chunk_size": $min_chunk_size,    # 小于此长度的 chunk 会被丢弃
}

# === 嵌入模型配置 ===
EMBEDDING = {
    "model": "$embedding_model",          # 嵌入模型名称
    "batch_size": $batch_size,            # 批处理大小（8GB 显存建议 8-16）
    "device": "auto",                      # auto, cpu, cuda
    "normalize": True,                     # 是否归一化向量
}

# === 向量存储配置 ===
VECTOR_STORE = {
    "backend": "$vector_backend",         # milvus, chroma, faiss, qdrant
    "collection": "$collection",          # collection 名称
    "metric": "$metric",                  # cosine, ip (内积), l2 (欧氏距离)
    "index_type": "$index_type",          # HNSW, IVF_FLAT, FLAT
}

# === 检索配置 ===
RETRIEVER = {
    "strategy": "$retriever_strategy",    # vector, bm25, hybrid, rerank
    "top_k": $top_k,                      # 粗排返回文档数
    "rerank_top_n": $rerank_top_n,        # 精排返回文档数
    "bm25_weight": $bm25_weight,          # BM25 权重（混合检索时）
    "vector_weight": $vector_weight,      # 向量检索权重
}

# === 查询处理配置 ===
QUERY = {
    "decompose": $decompose,              # 是否启用查询分解
    "decompose_strategy": "$decompose_strategy",  # step_back, multi_query, sub_questions
    "max_sub_queries": $max_sub_queries,  # 最大子查询数
    "synonym_expansion": True,             # 是否启用同义词扩展
}
'''


README_TEMPLATE = '''# $project_name

基于 RAG（检索增强生成）的问答系统。

## 项目结构

```
$project_name/
├── config.py          # 配置文件
├── ingest.py          # 文档入库脚本
├── query.py           # 查询脚本
├── requirements.txt   # 依赖
└── README.md          # 说明文档
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 预览分块效果
python ingest.py ./documents --preview

# 3. 入库
python ingest.py ./documents

# 4. 查询
python query.py "你的问题"
python query.py "你的问题" --json  # JSON 输出（供 Agent 解析）
```

## 配置说明

编辑 `config.py` 调整 pipeline 参数。

## 技术栈

- **嵌入模型**: $embedding_model
- **向量库**: $vector_backend
- **检索策略**: $retriever_strategy
- **分块策略**: $chunk_strategy
'''


REQUIREMENTS_TEMPLATE = '''# RAG pipeline 依赖
sentence-transformers>=2.2
pymilvus>=2.4
jieba>=0.42
rank-bm25>=0.2
openai>=1.0
numpy>=1.24
'''


def scaffold_project(config: RAGConfig, output_dir: str, project_name: str = "rag-project") -> dict:
    """根据配置生成 RAG 项目骨架。

    Args:
        config: RAG pipeline 配置
        output_dir: 输出目录
        project_name: 项目名称

    Returns:
        生成的文件列表
    """
    out = Path(output_dir) / project_name
    out.mkdir(parents=True, exist_ok=True)

    # 填充模板变量（用 $VAR 占位符替换）
    template_vars = {
        "chunk_size": config.chunking.chunk_size,
        "chunk_overlap": config.chunking.chunk_overlap,
        "min_chunk_size": config.chunking.min_chunk_size,
        "chunk_strategy": config.chunking.strategy,
        "embedding_model": config.embedding.model,
        "batch_size": config.embedding.batch_size,
        "vector_backend": config.vector_store.backend,
        "collection": config.vector_store.collection,
        "metric": config.vector_store.metric,
        "index_type": config.vector_store.index_type,
        "retriever_strategy": config.retriever.strategy,
        "top_k": config.retriever.top_k,
        "rerank_top_n": config.retriever.rerank_top_n,
        "bm25_weight": config.retriever.bm25_weight,
        "vector_weight": config.retriever.vector_weight,
        "decompose": "True" if config.query.decompose else "False",
        "decompose_strategy": config.query.decompose_strategy,
        "max_sub_queries": config.query.max_sub_queries,
        "project_name": project_name,
    }

    files = {}

    # 生成 ingest.py
    ingest_content = _render(INGEST_TEMPLATE, **template_vars)
    (out / "ingest.py").write_text(ingest_content, encoding="utf-8")
    files["ingest.py"] = ingest_content

    # 生成 query.py
    query_content = _render(QUERY_TEMPLATE, **template_vars)
    (out / "query.py").write_text(query_content, encoding="utf-8")
    files["query.py"] = query_content

    # 生成 config.py
    config_content = _render(CONFIG_TEMPLATE, **template_vars)
    (out / "config.py").write_text(config_content, encoding="utf-8")
    files["config.py"] = config_content

    # 生成 README.md
    readme_content = _render(README_TEMPLATE, **template_vars)
    (out / "README.md").write_text(readme_content, encoding="utf-8")
    files["README.md"] = readme_content

    # 生成 requirements.txt
    req_content = REQUIREMENTS_TEMPLATE
    (out / "requirements.txt").write_text(req_content, encoding="utf-8")
    files["requirements.txt"] = req_content

    # 保存配置为 JSON
    config_json = json.dumps(config.to_dict(), indent=2, ensure_ascii=False)
    (out / "rag_config.json").write_text(config_json, encoding="utf-8")
    files["rag_config.json"] = config_json

    return files
