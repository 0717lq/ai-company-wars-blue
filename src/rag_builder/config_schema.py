"""RAG pipeline configuration schema and validation.

验证 RAG pipeline 配置是否合理，检查嵌入模型、向量库、检索策略等参数的兼容性。
"""

from dataclasses import dataclass, field
from typing import Any

# 嵌入模型预设配置
EMBEDDING_PRESETS: dict[str, dict[str, Any]] = {
    "bge-base-zh-v1.5": {
        "dimensions": 768,
        "max_seq_length": 512,
        "gpu_vram_gb": 1.0,
        "query_instruction": "为这个句子生成表示以用于检索相关文章：",
        "language": "zh",
    },
    "bge-m3": {
        "dimensions": 1024,
        "max_seq_length": 8192,
        "gpu_vram_gb": 2.0,
        "query_instruction": None,
        "language": "multilingual",
    },
    "bge-large-zh-v1.5": {
        "dimensions": 1024,
        "max_seq_length": 512,
        "gpu_vram_gb": 1.5,
        "query_instruction": "为这个句子生成表示以用于检索相关文章：",
        "language": "zh",
    },
    "text-embedding-3-small": {
        "dimensions": 1536,
        "max_seq_length": 8191,
        "gpu_vram_gb": 0,
        "query_instruction": None,
        "language": "multilingual",
    },
    "text-embedding-3-large": {
        "dimensions": 3072,
        "max_seq_length": 8191,
        "gpu_vram_gb": 0,
        "query_instruction": None,
        "language": "multilingual",
    },
}

# Reranker 预设配置
RERANKER_PRESETS: dict[str, dict[str, Any]] = {
    "bge-reranker-base": {
        "max_seq_length": 512,
        "gpu_vram_gb": 1.5,
        "language": "zh",
    },
    "bge-reranker-v2-m3": {
        "max_seq_length": 8192,
        "gpu_vram_gb": 2.0,
        "language": "multilingual",
    },
    "bge-reranker-large": {
        "max_seq_length": 512,
        "gpu_vram_gb": 2.0,
        "language": "zh",
    },
    "cohere": {
        "max_seq_length": 4096,
        "gpu_vram_gb": 0,
        "language": "multilingual",
    },
}


@dataclass
class ChunkingConfig:
    """分块策略配置。"""
    strategy: str = "recursive"  # recursive, semantic, by_title, fixed_size
    chunk_size: int = 512
    chunk_overlap: int = 128
    min_chunk_size: int = 50

    def validate(self) -> list[str]:
        """验证分块配置，返回错误列表。"""
        errors = []
        valid_strategies = {"recursive", "semantic", "by_title", "fixed_size"}
        if self.strategy not in valid_strategies:
            errors.append(f"未知分块策略: {self.strategy}，可选: {valid_strategies}")
        if self.chunk_size < 100:
            errors.append(f"chunk_size={self.chunk_size} 太小，建议 >= 100")
        if self.chunk_size > 4096:
            errors.append(f"chunk_size={self.chunk_size} 太大，建议 <= 4096")
        if self.chunk_overlap >= self.chunk_size:
            errors.append(f"chunk_overlap={self.chunk_overlap} >= chunk_size={self.chunk_size}")
        if self.chunk_overlap < 0:
            errors.append(f"chunk_overlap={self.chunk_overlap} 不能为负")
        if self.min_chunk_size < 10:
            errors.append(f"min_chunk_size={self.min_chunk_size} 太小，建议 >= 10")
        return errors


@dataclass
class EmbeddingConfig:
    """嵌入模型配置。"""
    model: str = "bge-base-zh-v1.5"
    batch_size: int = 8
    device: str = "auto"  # auto, cpu, cuda
    normalize: bool = True

    def validate(self) -> list[str]:
        """验证嵌入配置，返回错误列表。"""
        errors = []
        if self.model not in EMBEDDING_PRESETS:
            errors.append(
                f"未知嵌入模型: {self.model}，可选: {list(EMBEDDING_PRESETS.keys())}"
            )
        if self.batch_size < 1:
            errors.append(f"batch_size={self.batch_size} 必须 >= 1")
        if self.batch_size > 256:
            errors.append(f"batch_size={self.batch_size} 过大，建议 <= 256")
        if self.device not in {"auto", "cpu", "cuda"}:
            errors.append(f"device={self.device} 无效，可选: auto/cpu/cuda")
        return errors

    @property
    def preset(self) -> dict[str, Any]:
        """获取模型预设信息。"""
        return EMBEDDING_PRESETS.get(self.model, {})


@dataclass
class VectorStoreConfig:
    """向量存储配置。"""
    backend: str = "milvus"  # milvus, chroma, faiss, qdrant
    collection: str = "default"
    metric: str = "cosine"  # cosine, ip, l2
    index_type: str = "HNSW"  # HNSW, IVF_FLAT, FLAT

    def validate(self) -> list[str]:
        """验证向量存储配置。"""
        errors = []
        valid_backends = {"milvus", "chroma", "faiss", "qdrant"}
        if self.backend not in valid_backends:
            errors.append(f"未知向量库: {self.backend}，可选: {valid_backends}")
        valid_metrics = {"cosine", "ip", "l2"}
        if self.metric not in valid_metrics:
            errors.append(f"未知度量: {self.metric}，可选: {valid_metrics}")
        valid_indexes = {"HNSW", "IVF_FLAT", "FLAT"}
        if self.index_type not in valid_indexes:
            errors.append(f"未知索引类型: {self.index_type}，可选: {valid_indexes}")
        if not self.collection:
            errors.append("collection 名称不能为空")
        return errors


@dataclass
class RetrieverConfig:
    """检索策略配置。"""
    strategy: str = "hybrid"  # vector, bm25, hybrid, rerank
    top_k: int = 10
    rerank_top_n: int = 5
    bm25_weight: float = 0.3
    vector_weight: float = 0.7
    reranker_model: str = "bge-reranker-base"

    def validate(self) -> list[str]:
        """验证检索配置。"""
        errors = []
        valid_strategies = {"vector", "bm25", "hybrid", "rerank"}
        if self.strategy not in valid_strategies:
            errors.append(f"未知检索策略: {self.strategy}，可选: {valid_strategies}")
        if self.top_k < 1:
            errors.append(f"top_k={self.top_k} 必须 >= 1")
        if self.top_k > 100:
            errors.append(f"top_k={self.top_k} 过大，建议 <= 100")
        if self.rerank_top_n > self.top_k:
            errors.append(
                f"rerank_top_n={self.rerank_top_n} > top_k={self.top_k}，"
                "精排数量不能大于粗排数量"
            )
        if not (0 <= self.bm25_weight <= 1):
            errors.append(f"bm25_weight={self.bm25_weight} 必须在 [0, 1] 范围")
        if not (0 <= self.vector_weight <= 1):
            errors.append(f"vector_weight={self.vector_weight} 必须在 [0, 1] 范围")
        if self.strategy == "rerank" and self.reranker_model not in RERANKER_PRESETS:
            errors.append(
                f"未知 reranker: {self.reranker_model}，可选: {list(RERANKER_PRESETS.keys())}"
            )
        return errors


@dataclass
class QueryConfig:
    """查询处理配置。"""
    decompose: bool = False
    decompose_strategy: str = "step_back"  # step_back, multi_query, sub_questions
    max_sub_queries: int = 3
    synonym_expansion: bool = True

    def validate(self) -> list[str]:
        """验证查询配置。"""
        errors = []
        valid_strategies = {"step_back", "multi_query", "sub_questions"}
        if self.decompose_strategy not in valid_strategies:
            errors.append(
                f"未知查询分解策略: {self.decompose_strategy}，可选: {valid_strategies}"
            )
        if self.max_sub_queries < 1:
            errors.append(f"max_sub_queries={self.max_sub_queries} 必须 >= 1")
        if self.max_sub_queries > 10:
            errors.append(f"max_sub_queries={self.max_sub_queries} 过大，建议 <= 10")
        return errors


@dataclass
class RAGConfig:
    """完整 RAG pipeline 配置。"""
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    retriever: RetrieverConfig = field(default_factory=RetrieverConfig)
    query: QueryConfig = field(default_factory=QueryConfig)

    def validate(self) -> list[str]:
        """验证整个 pipeline 配置，返回所有错误。"""
        errors = []
        errors.extend(self.chunking.validate())
        errors.extend(self.embedding.validate())
        errors.extend(self.vector_store.validate())
        errors.extend(self.retriever.validate())
        errors.extend(self.query.validate())

        # 交叉验证
        preset = self.embedding.preset
        if preset and self.chunking.chunk_size > preset.get("max_seq_length", 512):
            errors.append(
                f"chunk_size={self.chunking.chunk_size} > "
                f"模型最大序列长度 {preset['max_seq_length']}（{self.embedding.model}）"
            )
        return errors

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典。"""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RAGConfig":
        """从字典反序列化。"""
        return cls(
            chunking=ChunkingConfig(**data.get("chunking", {})),
            embedding=EmbeddingConfig(**data.get("embedding", {})),
            vector_store=VectorStoreConfig(**data.get("vector_store", {})),
            retriever=RetrieverConfig(**data.get("retriever", {})),
            query=QueryConfig(**data.get("query", {})),
        )


def estimate_gpu_vram(config: RAGConfig) -> dict[str, float]:
    """估算 GPU 显存需求（GB）。"""
    embed_preset = EMBEDDING_PRESETS.get(config.embedding.model, {})
    embed_vram = embed_preset.get("gpu_vram_gb", 0)

    rerank_vram = 0.0
    if config.retriever.strategy == "rerank":
        rerank_preset = RERANKER_PRESETS.get(config.retriever.reranker_model, {})
        rerank_vram = rerank_preset.get("gpu_vram_gb", 0)

    # batch_size 对显存有乘数效应
    batch_factor = max(1.0, config.embedding.batch_size / 8)
    total = (embed_vram + rerank_vram) * batch_factor

    return {
        "embedding": embed_vram * batch_factor,
        "reranker": rerank_vram * batch_factor,
        "total": total,
        "fits_8gb": total <= 7.5,  # 留 0.5GB 余量
    }
