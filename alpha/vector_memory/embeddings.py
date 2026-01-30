"""
Alpha - Embedding Service

Provides embedding generation for text using various LLM providers.
"""

import logging
from typing import List, Optional
from enum import Enum
import os

logger = logging.getLogger(__name__)


class EmbeddingProvider(Enum):
    """Supported embedding providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    LOCAL = "local"


class EmbeddingService:
    """
    Generates embeddings for text using LLM providers.

    Supports:
    - OpenAI embeddings (text-embedding-3-small, text-embedding-3-large)
    - DeepSeek embeddings (deepseek-embedding-v2) - OpenAI-compatible API
    - Anthropic embeddings (via voyageai)
    - Local embeddings (sentence-transformers)
    """

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize embedding service.

        Args:
            provider: Embedding provider (openai, deepseek, anthropic, local)
            model: Model name (provider-specific)
            api_key: API key (if required)
        """
        self.provider = EmbeddingProvider(provider)
        self.model = model
        self.api_key = api_key
        self.client = None

        self._initialize_client()
        logger.info(f"Embedding service initialized: {self.provider.value}")

    def _initialize_client(self):
        """Initialize the embedding client based on provider."""
        if self.provider == EmbeddingProvider.OPENAI:
            self._initialize_openai()
        elif self.provider == EmbeddingProvider.DEEPSEEK:
            self._initialize_deepseek()
        elif self.provider == EmbeddingProvider.ANTHROPIC:
            self._initialize_anthropic()
        elif self.provider == EmbeddingProvider.LOCAL:
            self._initialize_local()

    def _initialize_openai(self):
        """Initialize OpenAI embeddings client."""
        try:
            from openai import OpenAI

            api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided")

            self.client = OpenAI(api_key=api_key)
            self.model = self.model or "text-embedding-3-small"

            logger.info(f"OpenAI embeddings initialized: {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {e}")
            raise

    def _initialize_deepseek(self):
        """Initialize DeepSeek embeddings client (OpenAI-compatible API)."""
        try:
            from openai import OpenAI

            api_key = self.api_key or os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DeepSeek API key not provided")

            # DeepSeek uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )
            self.model = self.model or "deepseek-embedding-v2"

            logger.info(f"DeepSeek embeddings initialized: {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed (required for DeepSeek)")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek embeddings: {e}")
            raise

    def _initialize_anthropic(self):
        """Initialize Anthropic/Voyage embeddings client."""
        try:
            # Anthropic recommends using Voyage AI for embeddings
            import voyageai

            api_key = self.api_key or os.getenv("VOYAGE_API_KEY")
            if not api_key:
                raise ValueError("Voyage API key not provided")

            self.client = voyageai.Client(api_key=api_key)
            self.model = self.model or "voyage-2"

            logger.info(f"Voyage embeddings initialized: {self.model}")
        except ImportError:
            logger.warning(
                "voyageai package not installed, falling back to OpenAI"
            )
            self.provider = EmbeddingProvider.OPENAI
            self._initialize_openai()
        except Exception as e:
            logger.error(f"Failed to initialize Voyage embeddings: {e}")
            raise

    def _initialize_local(self):
        """Initialize local embeddings using sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = self.model or "all-MiniLM-L6-v2"
            self.client = SentenceTransformer(self.model)

            logger.info(f"Local embeddings initialized: {self.model}")
        except ImportError:
            logger.error("sentence-transformers package not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize local embeddings: {e}")
            raise

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            if self.provider == EmbeddingProvider.OPENAI:
                return self._embed_openai(texts)
            elif self.provider == EmbeddingProvider.DEEPSEEK:
                return self._embed_deepseek(texts)
            elif self.provider == EmbeddingProvider.ANTHROPIC:
                return self._embed_anthropic(texts)
            elif self.provider == EmbeddingProvider.LOCAL:
                return self._embed_local(texts)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )

        embeddings = [item.embedding for item in response.data]
        logger.info(f"Generated {len(embeddings)} OpenAI embeddings")
        return embeddings

    def _embed_deepseek(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using DeepSeek (OpenAI-compatible API)."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )

        embeddings = [item.embedding for item in response.data]
        logger.info(f"Generated {len(embeddings)} DeepSeek embeddings")
        return embeddings

    def _embed_anthropic(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Voyage AI."""
        result = self.client.embed(
            texts=texts,
            model=self.model
        )

        embeddings = result.embeddings
        logger.info(f"Generated {len(embeddings)} Voyage embeddings")
        return embeddings

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        embeddings = self.client.encode(
            texts,
            convert_to_numpy=False,
            show_progress_bar=False
        )

        # Convert to list format
        embeddings = [emb.tolist() for emb in embeddings]
        logger.info(f"Generated {len(embeddings)} local embeddings")
        return embeddings

    def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        embeddings = self.embed([text])
        return embeddings[0] if embeddings else []

    def get_embedding_dimension(self) -> int:
        """
        Get embedding vector dimension.

        Returns:
            Embedding dimension size
        """
        if self.provider == EmbeddingProvider.OPENAI:
            if "text-embedding-3-small" in self.model:
                return 1536
            elif "text-embedding-3-large" in self.model:
                return 3072
            elif "text-embedding-ada-002" in self.model:
                return 1536
            else:
                return 1536  # default

        elif self.provider == EmbeddingProvider.DEEPSEEK:
            # DeepSeek embedding dimension
            if "deepseek-embedding-v2" in self.model:
                return 1536
            else:
                return 1536  # default

        elif self.provider == EmbeddingProvider.ANTHROPIC:
            if "voyage-2" in self.model:
                return 1024
            else:
                return 1024  # default

        elif self.provider == EmbeddingProvider.LOCAL:
            # Get dimension from model
            if hasattr(self.client, 'get_sentence_embedding_dimension'):
                return self.client.get_sentence_embedding_dimension()
            else:
                # Default for all-MiniLM-L6-v2
                return 384

        return 1536  # fallback default


class ChromaEmbeddingFunction:
    """
    Wrapper to make EmbeddingService compatible with ChromaDB.

    ChromaDB expects an embedding function with __call__ method.
    """

    def __init__(self, embedding_service: EmbeddingService):
        """
        Initialize ChromaDB-compatible embedding function.

        Args:
            embedding_service: EmbeddingService instance
        """
        self.embedding_service = embedding_service

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate embeddings (ChromaDB interface).

        Args:
            input: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.embedding_service.embed(input)
