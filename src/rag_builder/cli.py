"""RAG Builder CLI — RAG pipeline 配置验证、脚手架生成、评估工具。

用法:
    python -m rag_builder validate <config.json>
    python -m rag_builder scaffold <config.json> -o <output_dir> -n <project_name>
    python -m rag_builder benchmark <ground_truth.json> --config <config_name>
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


def main():
    parser = argparse.ArgumentParser(
        prog="rag-builder",
        description="RAG pipeline 配置验证、脚手架生成、评估工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

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

    # init
    p_init = subparsers.add_parser("init", help="生成示例配置文件")
    p_init.add_argument("-o", "--output", help="输出路径")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "validate": cmd_validate,
        "scaffold": cmd_scaffold,
        "benchmark": cmd_benchmark,
        "init": cmd_init,
    }
    return cmd_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
