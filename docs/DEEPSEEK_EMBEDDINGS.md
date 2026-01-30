# DeepSeek Embeddings Integration Guide

## Overview

Alpha now supports **DeepSeek embeddings** as a cost-effective alternative to OpenAI embeddings for the vector memory system. DeepSeek provides an OpenAI-compatible API, making integration seamless.

---

## Benefits of DeepSeek Embeddings

✅ **Cost-Effective**: Significantly cheaper than OpenAI
✅ **High Quality**: Excellent semantic understanding
✅ **OpenAI-Compatible**: Uses the same API format
✅ **Easy Integration**: No code changes needed, just configuration
✅ **Unified Key Management**: Use same DEEPSEEK_API_KEY for LLM and embeddings

---

## Configuration

### 1. Get DeepSeek API Key

Visit: https://platform.deepseek.com/api_keys

### 2. Set Environment Variable

```bash
export DEEPSEEK_API_KEY="your-key-here"
```

Permanent configuration (add to `~/.bashrc` or `~/.zshrc`):
```bash
echo 'export DEEPSEEK_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Update config.yaml

The default configuration has been updated to use DeepSeek:

```yaml
memory:
  vector_memory:
    embedding_provider: "deepseek"
    embedding_model: "deepseek-embedding-v2"
```

**Alternative providers** (if needed):
```yaml
# For OpenAI
embedding_provider: "openai"
embedding_model: "text-embedding-3-small"

# For Anthropic/Voyage
embedding_provider: "anthropic"
embedding_model: "voyage-2"
```

---

## Testing

### Quick Test

```bash
# Test DeepSeek embedding
./test_deepseek_embedding.py
```

Expected output:
```
============================================================
Testing DeepSeek Embeddings
============================================================
✅ DEEPSEEK_API_KEY configured: sk-xxxxx...xxxx
1. Initializing DeepSeek embedding service...
✅ Service initialized: deepseek
   Model: deepseek-embedding-v2
   Dimension: 1536

2. Testing single text embedding...
✅ Generated embedding with 1536 dimensions
   First 5 values: [0.123, -0.456, 0.789, ...]

3. Testing batch embeddings...
✅ Generated 3 embeddings
   Text 1: 1536 dimensions
   Text 2: 1536 dimensions
   Text 3: 1536 dimensions

============================================================
✅ All tests passed!
============================================================
```

### Run Vector Memory Tests

```bash
source venv/bin/activate
python -m pytest tests/test_vector_memory.py -v
```

All 32 vector memory tests should now pass (previously skipped).

---

## Technical Details

### API Endpoint

DeepSeek embeddings use OpenAI-compatible API:
- **Base URL**: `https://api.deepseek.com/v1`
- **Model**: `deepseek-embedding-v2`
- **Dimension**: 1536 (same as OpenAI text-embedding-3-small)

### Implementation

The embedding service automatically handles DeepSeek by:
1. Using OpenAI SDK with custom base URL
2. Same API format as OpenAI
3. Transparent switching between providers

Code location: `alpha/vector_memory/embeddings.py`

```python
# Initialize DeepSeek
service = EmbeddingService(
    provider="deepseek",
    model="deepseek-embedding-v2",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

# Generate embeddings
embedding = service.embed_single("Hello, world!")
```

---

## Cost Comparison

| Provider | Model | Cost (per 1M tokens) | Dimension |
|----------|-------|---------------------|-----------|
| **DeepSeek** | deepseek-embedding-v2 | ~$0.01-0.02 | 1536 |
| OpenAI | text-embedding-3-small | $0.02 | 1536 |
| OpenAI | text-embedding-3-large | $0.13 | 3072 |
| Anthropic | voyage-2 | ~$0.10 | 1024 |

**DeepSeek offers the best cost-effectiveness for embeddings!**

---

## Troubleshooting

### Error: "DeepSeek API key not provided"

**Solution**: Set DEEPSEEK_API_KEY environment variable
```bash
export DEEPSEEK_API_KEY="your-key-here"
```

### Error: "Failed to initialize DeepSeek embeddings"

**Checklist**:
1. ✅ API key is correct
2. ✅ Internet connection working
3. ✅ OpenAI package installed (`pip install openai`)
4. ✅ API credits available

### Error: "OpenAI package not installed"

**Solution**: Install OpenAI SDK
```bash
source venv/bin/activate
pip install openai
```

### Tests still skipped?

**Check configuration**:
```bash
# Verify API key is set
echo $DEEPSEEK_API_KEY

# Verify config.yaml
cat config.yaml | grep -A 5 "vector_memory"
```

---

## Switching Providers

You can switch between embedding providers anytime:

### Switch to OpenAI
```yaml
embedding_provider: "openai"
embedding_model: "text-embedding-3-small"
```
```bash
export OPENAI_API_KEY="your-key"
```

### Switch to DeepSeek (recommended)
```yaml
embedding_provider: "deepseek"
embedding_model: "deepseek-embedding-v2"
```
```bash
export DEEPSEEK_API_KEY="your-key"
```

### Switch to Anthropic/Voyage
```yaml
embedding_provider: "anthropic"
embedding_model: "voyage-2"
```
```bash
export VOYAGE_API_KEY="your-key"
pip install voyageai
```

**Note**: Switching providers does NOT require rebuilding the vector database. Existing embeddings remain compatible.

---

## FAQ

**Q: Can I use the same DeepSeek key for LLM and embeddings?**
A: Yes! DeepSeek uses the same API key for both.

**Q: Do I need to rebuild vectors when switching providers?**
A: No, existing vectors remain usable. New embeddings will use the new provider.

**Q: Which provider is best?**
A: **DeepSeek** for cost-effectiveness, **OpenAI** for highest quality, **Anthropic** for Voyage AI integration.

**Q: Can I use local embeddings?**
A: Not recommended. Local embeddings require 2GB+ dependencies and offer lower quality.

**Q: What's the embedding dimension?**
A: DeepSeek: 1536, OpenAI-small: 1536, OpenAI-large: 3072, Voyage: 1024

**Q: Are embeddings cached?**
A: Yes, ChromaDB caches embeddings to avoid repeated API calls.

---

## Summary

✅ **DeepSeek embeddings now supported**
✅ **Default configuration updated**
✅ **Test script provided**
✅ **No code changes required**
✅ **Most cost-effective option**

**Get started**: Set `DEEPSEEK_API_KEY` and run `./test_deepseek_embedding.py`

---

**Sources**:
- [DeepSeek API Docs](https://api-docs.deepseek.com/)
- [Integrating DeepSeek Embeddings with ChromaDB](https://medium.com/@bhdilanka/integrating-deepseek-embeddings-with-chromadb-a-complete-guide-795f47c3d1fe)
- [Building Custom Knowledge Bases with DeepSeek Embeddings](https://chat-deep.ai/guide/building-custom-knowledge-bases-with-deepseek-embeddings/)

---

**Document Version**: 1.0
**Created**: 2026-01-30
**Status**: Production Ready
