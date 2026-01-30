#!/usr/bin/env python3
"""
Test DeepSeek Embeddings

This script tests the DeepSeek embedding functionality.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alpha.vector_memory.embeddings import EmbeddingService


def test_deepseek_embeddings():
    """Test DeepSeek embedding service."""
    print("=" * 60)
    print("Testing DeepSeek Embeddings")
    print("=" * 60)

    # Check API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not set")
        print("\nTo configure:")
        print("  export DEEPSEEK_API_KEY='your-key-here'")
        print("\nGet your key at: https://platform.deepseek.com/api_keys")
        return False

    print(f"✅ DEEPSEEK_API_KEY configured: {api_key[:8]}...{api_key[-4:]}")

    try:
        # Initialize service
        print("\n1. Initializing DeepSeek embedding service...")
        service = EmbeddingService(
            provider="deepseek",
            model="deepseek-embedding-v2"
        )
        print(f"✅ Service initialized: {service.provider.value}")
        print(f"   Model: {service.model}")
        print(f"   Dimension: {service.get_embedding_dimension()}")

        # Test single embedding
        print("\n2. Testing single text embedding...")
        text = "Hello, this is a test of DeepSeek embeddings."
        embedding = service.embed_single(text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")

        # Test batch embeddings
        print("\n3. Testing batch embeddings...")
        texts = [
            "DeepSeek is a powerful AI model.",
            "Embeddings convert text to vectors.",
            "Vector search enables semantic similarity."
        ]
        embeddings = service.embed(texts)
        print(f"✅ Generated {len(embeddings)} embeddings")
        for i, emb in enumerate(embeddings):
            print(f"   Text {i+1}: {len(emb)} dimensions")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your API key is correct")
        print("2. Check your internet connection")
        print("3. Ensure you have API credits")
        print("4. Check DeepSeek API status: https://platform.deepseek.com")
        return False


if __name__ == "__main__":
    success = test_deepseek_embeddings()
    sys.exit(0 if success else 1)
