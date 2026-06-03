"""RAG Builder CLI — RAG pipeline 配置验证、脚手架生成、评估、入库、检索工具。

用法:
    rag-builder init                              # 生成示例配置
    rag-builder validate <config.json>            # 验证配置
    rag-builder scaffold <config.json> -o <dir>   # 生成项目骨架
    rag-builder benchmark <ground_truth.json>     # 运行评估
    rag-builder ingest <dir> --config <json>      # 文档入库
    rag-builder query "问题" --config <json>      # 混合检索
"""

import argparse
import json
import sys
from pathlib import Path

from .config_schema import (
    RAGConfig,
    estimate_gpu_vram,
)
from .scaffold import scaffold_project


def cmd_validate(args):
    """验证 RAG 配置。"""
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: {config_path} not found", file=sys.stderr)
        return 1

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    try:
        config = RAGConfig.from_dict(data)
    except Exception as e:
        print(f"Error: 配置解析失败: {e}", file=sys.stderr)
        return 1

    errors = config.validate()

    if errors:
        print(f"配置验证失败 ({len(errors)} 个问题):")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
        return 1
    else:
        print("配置验证通过 ✓")
        # 显示 GPU 显存估算
        vram = estimate_gpu_vram(config)
        print("\nGPU 显存估算:")
        print(f"  Embedding: {vram['embedding']:.1f} GB")
        print(f"  Reranker:  {vram['reranker']:.1f} GB")
        print(f"  总计:      {vram['total']:.1f} GB")
        print(f"  8GB 显存:  {'✓ 可用' if vram['fits_8gb'] else '✗ 超限'}")
        return 0


def cmd_scaffold(args):
    """生成 RAG 项目骨架。"""
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: {config_path} not found", file=sys.stderr)
        return 1

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    config = RAGConfig.from_dict(data)
    errors = config.validate()
    if errors:
        print("配置验证失败，无法生成骨架:")
        for err in errors:
            print(f"  - {err}")
        return 1

    files = scaffold_project(config, args.output, args.name)
    print(f"生成了 {len(files)} 个文件到 {args.output}/{args.name}/:")
    for name in files:
        print(f"  - {name}")
    return 0


def cmd_benchmark(args):
    """运行评估。"""
    from .benchmark import load_ground_truth, run_benchmark

    gt_path = Path(args.ground_truth)
    if not gt_path.exists():
        print(f"Error: {gt_path} not found", file=sys.stderr)
        return 1

    queries = load_ground_truth(str(gt_path))
    if not queries:
        print("Error: ground truth 为空", file=sys.stderr)
        return 1

    # 使用 dummy retrieve function（实际需要用户接入自己的检索函数）
    def dummy_retrieve(query: str) -> list[str]:
        print(f"  [dummy] 检索: {query[:50]}...", file=sys.stderr)
        return []

    report = run_benchmark(queries, dummy_retrieve, config_name=args.config)

    if args.json:
        print(report.to_json())
    else:
        print(report.summary())

    if args.output:
        Path(args.output).write_text(report.to_json(), encoding="utf-8")
        print(f"\n报告已保存到: {args.output}")

    return 0


def cmd_init(args):
    """生成示例配置文件。"""
    RAGConfig()
    config_data = {
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

    output_path = Path(args.output or "rag_config.json")
    output_path.write_text(
        json.dumps(config_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"示例配置已生成: {output_path}")
    return 0


def cmd_ingest(args):
    """文档入库 — 解析、分块、向量化、存入向量库。"""
    from .parsers import chunk_documents, parse_directory, parse_markdown, parse_pdf, parse_text

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        return 1

    # 加载配置
    config = _load_config(args.config) if args.config else None

    chunk_size = args.chunk_size or (config.chunking.chunk_size if config else 512)
    chunk_overlap = args.chunk_overlap or (config.chunking.chunk_overlap if config else 128)
    strategy = args.strategy or (config.chunking.strategy if config else "recursive")

    # 1. 解析文档
    print(f"[1/4] 解析文档: {input_path}")
    if input_path.is_file():
        suffix = input_path.suffix.lower()
        if suffix == ".pdf":
            docs = parse_pdf(input_path)
        elif suffix in (".md", ".markdown"):
            docs = parse_markdown(input_path)
        else:
            docs = parse_text(input_path)
    else:
        docs = parse_directory(input_path)
    print(f"  -> 解析了 {len(docs)} 个文档段落")

    if not docs:
        print("Warning: 没有找到可解析的文档", file=sys.stderr)
        return 1

    # 2. 分块
    print(f"[2/4] 分块 (strategy={strategy}, chunk_size={chunk_size}, overlap={chunk_overlap})")
    chunks = chunk_documents(
        docs, strategy=strategy, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
    )
    print(f"  -> 生成 {len(chunks)} 个 chunks")

    if args.preview:
        # 预览模式：只展示分块结果
        print("\n=== 预览分块结果 ===")
        for i, chunk in enumerate(chunks[:10]):
            text_preview = chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"]
            print(f"\n[{i+1}] ({len(chunk['text'])} chars) source={chunk.get('source', '')}")
            print(f"    {text_preview}")
        if len(chunks) > 10:
            print(f"\n... 还有 {len(chunks) - 10} 个 chunks")
        return 0

    # 3. 向量化
    print("[3/4] 向量化...")
    try:
        from .embeddings import get_provider

        provider_name = args.embedding_provider or "st"
        model_name = args.embedding_model or ""
        provider = get_provider(
            provider_name,
            model=model_name,
            api_key=args.api_key or "",
            base_url=args.base_url or "",
        )
        texts = [c["text"] for c in chunks]
        embeddings = provider.embed_texts(texts, batch_size=args.batch_size or 8)
        print(f"  -> 生成 {len(embeddings)} 个向量 (dim={len(embeddings[0])})")
    except ImportError as e:
        print(f"Error: Embedding 依赖缺失: {e}", file=sys.stderr)
        return 1

    # 4. 存入向量库
    print("[4/4] 存入向量库...")
    try:
        from .vector_store import get_store

        backend = args.store or (config.vector_store.backend if config else "milvus")
        collection = args.collection or (config.vector_store.collection if config else "default")
        store = get_store(backend, collection=collection, dimension=len(embeddings[0]))

        ids = [f"chunk_{i:06d}" for i in range(len(chunks))]
        store.add_texts(
            texts=[c["text"] for c in chunks],
            embeddings=embeddings,
            ids=ids,
            metadata=[{"source": c.get("source", ""), **c.get("metadata", {})} for c in chunks],
        )
        print(f"  -> 存入 {len(chunks)} 个文档到 {backend}/{collection}")
    except ImportError as e:
        print(f"Error: 向量库依赖缺失: {e}", file=sys.stderr)
        return 1

    print(f"\nDone! 共入库 {len(chunks)} 个 chunks")
    return 0


def cmd_query(args):
    """混合检索 — BM25 + 向量 RRF 融合。"""
    # 加载配置
    config = _load_config(args.config) if args.config else None

    # 初始化 embedding provider
    try:
        from .embeddings import get_provider
        provider_name = args.embedding_provider or "st"
        model_name = args.embedding_model or ""
        provider = get_provider(
            provider_name,
            model=model_name,
            api_key=args.api_key or "",
            base_url=args.base_url or "",
        )
    except ImportError as e:
        print(f"Error: Embedding 依赖缺失: {e}", file=sys.stderr)
        return 1

    # 初始化向量库
    try:
        from .vector_store import get_store
        backend = args.store or (config.vector_store.backend if config else "milvus")
        collection = args.collection or (config.vector_store.collection if config else "default")
        store = get_store(backend, collection=collection)
    except ImportError as e:
        print(f"Error: 向量库依赖缺失: {e}", file=sys.stderr)
        return 1

    # 初始化检索器
    from .retriever import HybridRetriever

    retriever = HybridRetriever(
        vector_store=store,
        embedding_provider=provider,
        bm25_weight=args.bm25_weight or (config.retriever.bm25_weight if config else 0.3),
        vector_weight=args.vector_weight or (config.retriever.vector_weight if config else 0.7),
    )

    # 检索
    query_text = args.query
    top_k = args.top_k or (config.retriever.top_k if config else 10)

    print(f"查询: {query_text}")
    print(f"检索参数: top_k={top_k}, strategy=hybrid\n")

    results = retriever.search(query_text, top_k=top_k)

    if args.json:
        output = {
            "tool": "rag-builder",
            "command": "query",
            "query": query_text,
            "results": [
                {
                    "id": r.id,
                    "text": r.text[:500],
                    "score": round(r.score, 6),
                    "source": r.source,
                }
                for r in results
            ],
            "total": len(results),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"检索到 {len(results)} 条结果:\n")
        for i, r in enumerate(results):
            source = f" [{r.source}]" if r.source else ""
            text_preview = r.text[:200] + "..." if len(r.text) > 200 else r.text
            print(f"[{i+1}] score={r.score:.4f}{source}")
            print(f"    {text_preview}\n")

    return 0


def cmd_diagnose(args):
    """健康检查 — 配置 + 依赖 + GPU + 网络。"""
    from .diagnose import format_report, run_diagnosis

    report = run_diagnosis(
        config_path=args.config,
        skip_network=args.skip_network,
    )

    print(format_report(report, json_output=args.json))
    return 1 if report.summary["fail"] > 0 else 0


def _load_config(config_path: str | None) -> RAGConfig | None:
    """加载配置文件。"""
    if not config_path:
        return None
    path = Path(config_path)
    if not path.exists():
        print(f"Warning: 配置文件 {path} 不存在", file=sys.stderr)
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return RAGConfig.from_dict(data)


def main():
    parser = argparse.ArgumentParser(
        prog="rag-builder",
        description="RAG pipeline 配置验证、脚手架生成、评估、入库、检索工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init
    p_init = subparsers.add_parser("init", help="生成示例配置文件")
    p_init.add_argument("-o", "--output", help="输出路径")

    # validate
    p_validate = subparsers.add_parser("validate", help="验证 RAG 配置")
    p_validate.add_argument("config", help="配置文件路径 (JSON)")

    # scaffold
    p_scaffold = subparsers.add_parser("scaffold", help="生成 RAG 项目骨架")
    p_scaffold.add_argument("config", help="配置文件路径 (JSON)")
    p_scaffold.add_argument("-o", "--output", default=".", help="输出目录")
    p_scaffold.add_argument("-n", "--name", default="rag-project", help="项目名称")

    # benchmark
    p_benchmark = subparsers.add_parser("benchmark", help="运行评估")
    p_benchmark.add_argument("ground_truth", help="ground truth 文件路径 (JSON)")
    p_benchmark.add_argument("--config", default="default", help="配置名称")
    p_benchmark.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    p_benchmark.add_argument("-o", "--output", help="报告输出路径")

    # ingest — 文档入库
    p_ingest = subparsers.add_parser("ingest", help="文档入库（解析→分块→向量化→入库）")
    p_ingest.add_argument("input", help="输入文件或目录")
    p_ingest.add_argument("--config", help="配置文件路径 (JSON)")
    p_ingest.add_argument("--preview", action="store_true", help="预览分块结果，不入库")
    p_ingest.add_argument("--chunk-size", type=int, help="分块大小")
    p_ingest.add_argument("--chunk-overlap", type=int, help="分块重叠")
    p_ingest.add_argument("--strategy", help="分块策略 (recursive/fixed_size/by_sentence)")
    p_ingest.add_argument("--store", help="向量库后端 (milvus/chroma)")
    p_ingest.add_argument("--collection", help="collection 名称")
    p_ingest.add_argument("--embedding-provider", help="embedding 提供者 (st/openai)")
    p_ingest.add_argument("--embedding-model", help="embedding 模型名")
    p_ingest.add_argument("--api-key", help="API 密钥 (openai provider)")
    p_ingest.add_argument("--base-url", help="API 基础 URL (openai provider)")
    p_ingest.add_argument("--batch-size", type=int, default=8, help="批处理大小")

    # diagnose — 健康检查
    p_diagnose = subparsers.add_parser("diagnose", help="RAG 系统健康检查（配置+依赖+GPU+网络）")
    p_diagnose.add_argument("config", nargs="?", default=None, help="配置文件路径 (JSON)")
    p_diagnose.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    p_diagnose.add_argument("--skip-network", action="store_true", help="跳过网络连通性检测")

    # query — 混合检索
    p_query = subparsers.add_parser("query", help="混合检索（BM25 + 向量 RRF）")
    p_query.add_argument("query", help="查询文本")
    p_query.add_argument("--config", help="配置文件路径 (JSON)")
    p_query.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    p_query.add_argument("--top-k", type=int, help="返回数量")
    p_query.add_argument("--store", help="向量库后端 (milvus/chroma)")
    p_query.add_argument("--collection", help="collection 名称")
    p_query.add_argument("--embedding-provider", help="embedding 提供者 (st/openai)")
    p_query.add_argument("--embedding-model", help="embedding 模型名")
    p_query.add_argument("--api-key", help="API 密钥")
    p_query.add_argument("--base-url", help="API 基础 URL")
    p_query.add_argument("--bm25-weight", type=float, help="BM25 权重")
    p_query.add_argument("--vector-weight", type=float, help="向量权重")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "validate": cmd_validate,
        "scaffold": cmd_scaffold,
        "benchmark": cmd_benchmark,
        "init": cmd_init,
        "ingest": cmd_ingest,
        "query": cmd_query,
        "diagnose": cmd_diagnose,
    }
    return cmd_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
