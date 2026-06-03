"""Tests for rag_builder.config_schema — 配置验证和 GPU 显存估算。"""


from rag_builder.config_schema import (
    ChunkingConfig,
    EmbeddingConfig,
    QueryConfig,
    RAGConfig,
    RetrieverConfig,
    VectorStoreConfig,
    estimate_gpu_vram,
)


class TestChunkingConfig:
    """分块配置验证测试。"""

    def test_default_config_valid(self):
        """默认配置应通过验证。"""
        cfg = ChunkingConfig()
        errors = cfg.validate()
        assert errors == [], f"默认配置不应有错误，实际: {errors}"

    def test_invalid_strategy(self):
        """未知策略应报错。"""
        cfg = ChunkingConfig(strategy="unknown")
        errors = cfg.validate()
        assert len(errors) == 1
        assert "未知分块策略" in errors[0]
        assert "unknown" in errors[0]

    def test_chunk_size_too_small(self):
        """chunk_size < 100 应报错。"""
        cfg = ChunkingConfig(chunk_size=50)
        errors = cfg.validate()
        assert any("chunk_size=50" in e and "太小" in e for e in errors)

    def test_chunk_size_too_large(self):
        """chunk_size > 4096 应报错。"""
        cfg = ChunkingConfig(chunk_size=8192)
        errors = cfg.validate()
        assert any("chunk_size=8192" in e and "太大" in e for e in errors)

    def test_overlap_gte_chunk_size(self):
        """overlap >= chunk_size 应报错。"""
        cfg = ChunkingConfig(chunk_size=512, chunk_overlap=512)
        errors = cfg.validate()
        assert any("chunk_overlap" in e for e in errors)

    def test_negative_overlap(self):
        """负 overlap 应报错。"""
        cfg = ChunkingConfig(chunk_overlap=-10)
        errors = cfg.validate()
        assert any("不能为负" in e for e in errors)

    def test_all_valid_strategies(self):
        """所有合法策略都应通过验证。"""
        for strategy in ["recursive", "semantic", "by_title", "fixed_size"]:
            cfg = ChunkingConfig(strategy=strategy)
            errors = cfg.validate()
            assert errors == [], f"策略 {strategy} 应通过验证，实际错误: {errors}"


class TestEmbeddingConfig:
    """嵌入模型配置验证测试。"""

    def test_default_config_valid(self):
        """默认配置应通过验证。"""
        cfg = EmbeddingConfig()
        errors = cfg.validate()
        assert errors == [], f"默认配置不应有错误，实际: {errors}"

    def test_unknown_model(self):
        """未知模型应报错。"""
        cfg = EmbeddingConfig(model="gpt-4")
        errors = cfg.validate()
        assert len(errors) == 1
        assert "未知嵌入模型" in errors[0]
        assert "gpt-4" in errors[0]

    def test_batch_size_zero(self):
        """batch_size=0 应报错。"""
        cfg = EmbeddingConfig(batch_size=0)
        errors = cfg.validate()
        assert any("batch_size" in e for e in errors)

    def test_batch_size_too_large(self):
        """batch_size > 256 应报错。"""
        cfg = EmbeddingConfig(batch_size=512)
        errors = cfg.validate()
        assert any("batch_size=512" in e for e in errors)

    def test_invalid_device(self):
        """非法 device 应报错。"""
        cfg = EmbeddingConfig(device="tpu")
        errors = cfg.validate()
        assert any("device" in e for e in errors)

    def test_preset_returns_dict(self):
        """preset 属性应返回模型信息字典。"""
        cfg = EmbeddingConfig(model="bge-base-zh-v1.5")
        preset = cfg.preset
        assert isinstance(preset, dict)
        assert preset["dimensions"] == 768
        assert preset["language"] == "zh"

    def test_preset_unknown_model(self):
        """未知模型的 preset 应返回空字典。"""
        cfg = EmbeddingConfig(model="nonexistent")
        assert cfg.preset == {}

    def test_all_valid_models(self):
        """所有预设模型都应通过验证。"""
        for model in ["bge-base-zh-v1.5", "bge-m3", "bge-large-zh-v1.5",
                       "text-embedding-3-small", "text-embedding-3-large"]:
            cfg = EmbeddingConfig(model=model)
            errors = cfg.validate()
            assert errors == [], f"模型 {model} 应通过验证，实际错误: {errors}"


class TestVectorStoreConfig:
    """向量存储配置验证测试。"""

    def test_default_config_valid(self):
        """默认配置应通过验证。"""
        cfg = VectorStoreConfig()
        errors = cfg.validate()
        assert errors == []

    def test_invalid_backend(self):
        """未知后端应报错。"""
        cfg = VectorStoreConfig(backend="pinecone")
        errors = cfg.validate()
        assert any("未知向量库" in e for e in errors)

    def test_invalid_metric(self):
        """未知度量应报错。"""
        cfg = VectorStoreConfig(metric="manhattan")
        errors = cfg.validate()
        assert any("未知度量" in e for e in errors)

    def test_invalid_index_type(self):
        """未知索引类型应报错。"""
        cfg = VectorStoreConfig(index_type="IVF_PQ")
        errors = cfg.validate()
        assert any("未知索引类型" in e for e in errors)

    def test_empty_collection(self):
        """空 collection 名称应报错。"""
        cfg = VectorStoreConfig(collection="")
        errors = cfg.validate()
        assert any("collection" in e and "空" in e for e in errors)


class TestRetrieverConfig:
    """检索策略配置验证测试。"""

    def test_default_config_valid(self):
        """默认配置应通过验证。"""
        cfg = RetrieverConfig()
        errors = cfg.validate()
        assert errors == []

    def test_invalid_strategy(self):
        """未知策略应报错。"""
        cfg = RetrieverConfig(strategy="dpr")
        errors = cfg.validate()
        assert any("未知检索策略" in e for e in errors)

    def test_rerank_top_n_exceeds_top_k(self):
        """rerank_top_n > top_k 应报错。"""
        cfg = RetrieverConfig(top_k=5, rerank_top_n=10)
        errors = cfg.validate()
        assert any("精排数量不能大于粗排数量" in e for e in errors)

    def test_bm25_weight_out_of_range(self):
        """bm25_weight 超出 [0,1] 应报错。"""
        cfg = RetrieverConfig(bm25_weight=1.5)
        errors = cfg.validate()
        assert any("bm25_weight" in e for e in errors)

    def test_vector_weight_negative(self):
        """负 vector_weight 应报错。"""
        cfg = RetrieverConfig(vector_weight=-0.1)
        errors = cfg.validate()
        assert any("vector_weight" in e for e in errors)

    def test_rerank_strategy_unknown_model(self):
        """rerank 策略使用未知模型应报错。"""
        cfg = RetrieverConfig(strategy="rerank", reranker_model="gpt-4")
        errors = cfg.validate()
        assert any("未知 reranker" in e for e in errors)


class TestQueryConfig:
    """查询配置验证测试。"""

    def test_default_config_valid(self):
        """默认配置应通过验证。"""
        cfg = QueryConfig()
        errors = cfg.validate()
        assert errors == []

    def test_invalid_decompose_strategy(self):
        """未知分解策略应报错。"""
        cfg = QueryConfig(decompose_strategy="tree_of_thought")
        errors = cfg.validate()
        assert any("未知查询分解策略" in e for e in errors)

    def test_max_sub_queries_zero(self):
        """max_sub_queries=0 应报错。"""
        cfg = QueryConfig(max_sub_queries=0)
        errors = cfg.validate()
        assert any("max_sub_queries" in e for e in errors)

    def test_max_sub_queries_too_large(self):
        """max_sub_queries > 10 应报错。"""
        cfg = QueryConfig(max_sub_queries=20)
        errors = cfg.validate()
        assert any("max_sub_queries" in e for e in errors)


class TestRAGConfig:
    """完整 RAG 配置验证测试。"""

    def test_default_config_valid(self):
        """默认配置应通过验证。"""
        cfg = RAGConfig()
        errors = cfg.validate()
        assert errors == [], f"默认配置不应有错误，实际: {errors}"

    def test_chunk_size_exceeds_model_max_length(self):
        """chunk_size > 模型最大序列长度应报错。"""
        cfg = RAGConfig(
            chunking=ChunkingConfig(chunk_size=1024),
            embedding=EmbeddingConfig(model="bge-base-zh-v1.5"),  # max_seq_length=512
        )
        errors = cfg.validate()
        assert any("chunk_size" in e and "最大序列长度" in e for e in errors)

    def test_to_dict_and_from_dict_roundtrip(self):
        """序列化/反序列化往返应保持一致。"""
        cfg = RAGConfig(
            chunking=ChunkingConfig(chunk_size=256, chunk_overlap=64),
            embedding=EmbeddingConfig(model="bge-m3", batch_size=16),
            vector_store=VectorStoreConfig(backend="chroma", collection="test"),
        )
        d = cfg.to_dict()
        cfg2 = RAGConfig.from_dict(d)
        assert cfg2.chunking.chunk_size == 256
        assert cfg2.embedding.model == "bge-m3"
        assert cfg2.vector_store.backend == "chroma"

    def test_multiple_errors_collected(self):
        """多个错误应全部收集，不只报第一个。"""
        cfg = RAGConfig(
            chunking=ChunkingConfig(strategy="invalid"),
            embedding=EmbeddingConfig(model="invalid"),
            retriever=RetrieverConfig(strategy="invalid"),
        )
        errors = cfg.validate()
        assert len(errors) >= 3, f"应至少 3 个错误，实际 {len(errors)}: {errors}"


class TestEstimateGpuVram:
    """GPU 显存估算测试。"""

    def test_default_config_8gb_safe(self):
        """默认配置应在 8GB 显存内。"""
        cfg = RAGConfig()
        vram = estimate_gpu_vram(cfg)
        assert vram["fits_8gb"] is True, f"默认配置应适配8GB，实际: {vram}"

    def test_rerank_increases_vram(self):
        """启用 reranker 应增加显存需求。"""
        cfg_no_rerank = RAGConfig(
            retriever=RetrieverConfig(strategy="vector")
        )
        cfg_rerank = RAGConfig(
            retriever=RetrieverConfig(strategy="rerank", reranker_model="bge-reranker-base")
        )
        vram_no = estimate_gpu_vram(cfg_no_rerank)
        vram_yes = estimate_gpu_vram(cfg_rerank)
        assert vram_yes["total"] > vram_no["total"], (
            f"reranker 应增加显存: {vram_yes['total']} <= {vram_no['total']}"
        )

    def test_larger_batch_increases_vram(self):
        """更大的 batch_size 应增加显存需求。"""
        cfg_small = RAGConfig(embedding=EmbeddingConfig(batch_size=4))
        cfg_large = RAGConfig(embedding=EmbeddingConfig(batch_size=32))
        vram_small = estimate_gpu_vram(cfg_small)
        vram_large = estimate_gpu_vram(cfg_large)
        assert vram_large["total"] > vram_small["total"], (
            f"batch_size=32 应比 batch_size=4 显存更大: "
            f"{vram_large['total']} <= {vram_small['total']}"
        )

    def test_api_model_zero_vram(self):
        """API 模型不占本地显存。"""
        cfg = RAGConfig(embedding=EmbeddingConfig(model="text-embedding-3-small"))
        vram = estimate_gpu_vram(cfg)
        assert vram["embedding"] == 0.0
        assert vram["fits_8gb"] is True
