"""Embedding abstraction layer tests."""
from unittest.mock import MagicMock, patch

import pytest

from rag_builder.embeddings import (
    EmbeddingProvider,
    OpenAIProvider,
    STProvider,
    get_provider,
)


class TestEmbeddingProviderABC:
    """EmbeddingProvider ABC tests."""

    def test_cannot_instantiate_abc(self):
        """ABC cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EmbeddingProvider()


class TestSTProvider:
    """STProvider tests (mock sentence-transformers)."""

    def test_embed_texts_returns_correct_shape(self):
        """embed_texts should return vectors with correct shape."""
        mock_st = MagicMock()
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.tolist.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_result.shape = (2, 3)
        mock_model.encode.return_value = mock_result
        mock_st.SentenceTransformer.return_value = mock_model

        with patch.dict("sys.modules", {"sentence_transformers": mock_st, "torch": MagicMock()}):
            provider = STProvider(model="test-model", device="cpu")
            provider._dimension = 3
            result = provider.embed_texts(["hello", "world"])

        assert len(result) == 2
        assert len(result[0]) == 3

    def test_dimension_property(self):
        """dimension property should return correct value."""
        mock_st = MagicMock()
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.shape = (1, 768)
        mock_model.encode.return_value = mock_result
        mock_st.SentenceTransformer.return_value = mock_model

        with patch.dict("sys.modules", {"sentence_transformers": mock_st, "torch": MagicMock()}):
            provider = STProvider(model="test", device="cpu")
            assert provider.dimension() == 768

    def test_import_error_without_sentence_transformers(self):
        """Should raise ImportError when sentence-transformers not installed."""
        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with pytest.raises(ImportError, match="sentence-transformers"):
                STProvider(model="test")


class TestOpenAIProvider:
    """OpenAIProvider tests (mock openai)."""

    def test_embed_texts_calls_api(self):
        """embed_texts should call OpenAI API and return results."""
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client

        mock_resp = MagicMock()
        mock_resp.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6]),
        ]
        mock_client.embeddings.create.return_value = mock_resp

        with patch.dict("sys.modules", {"openai": mock_openai}):
            provider = OpenAIProvider(model="test-model", api_key="sk-test")
            provider._dimension = 3
            result = provider.embed_texts(["hello", "world"], normalize=False)

        assert len(result) == 2
        mock_client.embeddings.create.assert_called()

    def test_normalize_batch(self):
        """_normalize_batch should return L2 normalized vectors."""
        vectors = [[3.0, 4.0], [1.0, 0.0]]
        result = OpenAIProvider._normalize_batch(vectors)
        assert abs(result[0][0] - 0.6) < 1e-6
        assert abs(result[0][1] - 0.8) < 1e-6
        assert abs(result[1][0] - 1.0) < 1e-6

    def test_normalize_zero_vector(self):
        """Zero vector normalization should not error."""
        result = OpenAIProvider._normalize_batch([[0.0, 0.0]])
        assert result == [[0.0, 0.0]]

    def test_batch_processing(self):
        """Large batches should call API in chunks.

        验证: 10 条文本 / batch_size=5 → embed_texts 应调用 2 次 API。
        注意: __init__ 会调 1 次 API 探测维度，embed_texts 的调用单独计算。
        """
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client

        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=[0.1, 0.2]) for _ in range(5)]
        mock_client.embeddings.create.return_value = mock_resp

        with patch.dict("sys.modules", {"openai": mock_openai}):
            provider = OpenAIProvider(model="test", api_key="sk-test")
            provider._dimension = 2
            # __init__ 已调用 1 次 API（维度探测），重置计数后单独测试 embed_texts
            mock_client.embeddings.create.reset_mock()
            result = provider.embed_texts(["text"] * 10, batch_size=5, normalize=False)

        # embed_texts 应调用 2 次（batch 0-4, batch 5-9）
        assert mock_client.embeddings.create.call_count == 2
        assert len(result) == 10

    def test_import_error_without_openai(self):
        """Should raise ImportError when openai not installed."""
        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(ImportError, match="openai"):
                OpenAIProvider(model="test")


class TestGetProvider:
    """Factory function get_provider tests."""

    def test_st_provider(self):
        """get_provider('st') should return STProvider."""
        with patch("rag_builder.embeddings.STProvider") as mock_cls:
            mock_cls.return_value = MagicMock(spec=EmbeddingProvider)
            get_provider("st", model="test")
            mock_cls.assert_called_once_with(model="test", device="auto")

    def test_openai_provider(self):
        """get_provider('openai') should return OpenAIProvider."""
        with patch("rag_builder.embeddings.OpenAIProvider") as mock_cls:
            mock_cls.return_value = MagicMock(spec=EmbeddingProvider)
            get_provider("openai", model="test", api_key="sk-1", base_url="http://x")
            mock_cls.assert_called_once_with(
                model="test", api_key="sk-1", base_url="http://x", dimensions=None
            )

    def test_unknown_provider_raises(self):
        """Unknown provider should raise ValueError."""
        with pytest.raises(ValueError, match="unknown"):
            get_provider("unknown")

    def test_default_models(self):
        """Default model names should be set correctly."""
        with patch("rag_builder.embeddings.STProvider") as mock_st:
            mock_st.return_value = MagicMock()
            get_provider("st")
            mock_st.assert_called_with(model="BAAI/bge-base-zh-v1.5", device="auto")
