"""Embedding 抽象层 — 统一本地和远程 Embedding 接口。

支持 sentence-transformers 本地模型和 OpenAI 兼容 API（如 MIMO、DashScope）。
通过工厂函数 get_provider() 按名称获取 provider 实例。

用法:
    provider = get_provider("st", model="bge-base-zh-v1.5")
    embeddings = provider.embed_texts(["你好世界", "测试文本"])

    provider = get_provider("openai", model="text-embedding-3-small",
                            api_key="sk-xxx", base_url="https://api.openai.com/v1")
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Embedding 提供者抽象基类。"""

    @abstractmethod
    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 8,
        normalize: bool = True,
    ) -> list[list[float]]:
        """将文本列表转换为向量列表。

        Args:
            texts: 待嵌入的文本列表
            batch_size: 批处理大小
            normalize: 是否 L2 归一化

        Returns:
            向量列表，与 texts 一一对应
        """

    @abstractmethod
    def dimension(self) -> int:
        """返回 embedding 向量维度。"""


class STProvider(EmbeddingProvider):
    """sentence-transformers 本地 Embedding Provider。

    使用 sentence-transformers 库加载本地模型，在 GPU/CPU 上推理。
    """

    def __init__(self, model: str = "BAAI/bge-base-zh-v1.5", device: str = "auto"):
        """初始化 ST Provider。

        Args:
            model: 模型名称或本地路径
            device: 设备 (auto/cpu/cuda)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as err:
            raise ImportError(
                "sentence-transformers 未安装。请执行: "
                "pip install rag-builder[st] 或 pip install sentence-transformers"
            ) from err

        self._model_name = model
        if device == "auto":
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self._model = SentenceTransformer(model, device=device)
        # 获取维度：用空文本测试
        self._dimension = self._model.encode(["test"]).shape[1]

    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 8,
        normalize: bool = True,
    ) -> list[list[float]]:
        """使用 sentence-transformers 编码文本。"""
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def dimension(self) -> int:
        """返回 embedding 维度。"""
        return self._dimension


class OpenAIProvider(EmbeddingProvider):
    """OpenAI 兼容 API Embedding Provider。

    支持 OpenAI、MIMO、DashScope 等 OpenAI 兼容接口。
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        dimensions: int | None = None,
    ):
        """初始化 OpenAI Provider。

        Args:
            model: 模型名称
            api_key: API 密钥
            base_url: API 基础 URL
            dimensions: 输出维度（部分模型支持）
        """
        try:
            from openai import OpenAI
        except ImportError as err:
            raise ImportError(
                "openai 未安装。请执行: pip install rag-builder[openai] 或 pip install openai"
            ) from err

        self._model = model
        self._dimensions = dimensions
        self._client = OpenAI(api_key=api_key, base_url=base_url)

        # 探测维度：用一条短文本测试
        if dimensions:
            self._dimension = dimensions
        else:
            try:
                resp = self._client.embeddings.create(model=model, input=["test"])
                self._dimension = len(resp.data[0].embedding)
            except Exception:
                self._dimension = 1536  # OpenAI 默认维度

    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 8,
        normalize: bool = True,
    ) -> list[list[float]]:
        """通过 OpenAI 兼容 API 获取 embeddings。"""
        all_embeddings: list[list[float]] = []

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            kwargs: dict = {"model": self._model, "input": batch}
            if self._dimensions:
                kwargs["dimensions"] = self._dimensions

            resp = self._client.embeddings.create(**kwargs)
            batch_embeddings = [item.embedding for item in resp.data]
            all_embeddings.extend(batch_embeddings)

        # 归一化（如果需要）
        if normalize:
            all_embeddings = self._normalize_batch(all_embeddings)

        return all_embeddings

    def dimension(self) -> int:
        """返回 embedding 维度。"""
        return self._dimension

    @staticmethod
    def _normalize_batch(vectors: list[list[float]]) -> list[list[float]]:
        """L2 归一化向量批次。"""
        import math

        normalized = []
        for vec in vectors:
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                normalized.append([x / norm for x in vec])
            else:
                normalized.append(vec)
        return normalized


def get_provider(
    name: str,
    model: str = "",
    api_key: str = "",
    base_url: str = "",
    device: str = "auto",
    dimensions: int | None = None,
) -> EmbeddingProvider:
    """工厂函数：按名称获取 Embedding Provider。

    Args:
        name: provider 名称 ("st" 或 "openai")
        model: 模型名称（留空使用默认）
        api_key: API 密钥（仅 openai provider 需要）
        base_url: API 基础 URL（仅 openai provider）
        device: 设备（仅 st provider）
        dimensions: 输出维度（仅 openai provider）

    Returns:
        EmbeddingProvider 实例

    Raises:
        ValueError: 未知 provider 名称
    """
    if name == "st":
        model = model or "BAAI/bge-base-zh-v1.5"
        return STProvider(model=model, device=device)
    elif name == "openai":
        model = model or "text-embedding-3-small"
        base_url = base_url or "https://api.openai.com/v1"
        return OpenAIProvider(
            model=model, api_key=api_key, base_url=base_url, dimensions=dimensions
        )
    else:
        raise ValueError(
            f"未知 embedding provider: {name!r}，可选: ['st', 'openai']"
        )
