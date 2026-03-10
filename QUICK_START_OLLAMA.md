# Quick Start: Using Qwen 2.5 (Ollama) for Testing

## 🎯 Problem Solved

**Before:** Using Gemini API → Hit rate limits (60 requests/min) → Tests fail
**After:** Using local Qwen 2.5 via Ollama → No rate limits → Tests run freely

## ✅ What's Ready

All integration code is complete and tested:

1. ✅ **Ollama Service** - Direct integration with Qwen 2.5
2. ✅ **LLM Factory** - Easy switching between providers
3. ✅ **Tests Passing** - All 5 test scenarios work
4. ✅ **Documentation** - Complete integration guide
5. ✅ **Examples** - 6 real-world usage examples

## 🚀 3-Second Quick Start

```python
from app.services.llm_factory import get_llm

# Use Qwen 2.5 (local, no rate limits)
llm = get_llm(provider="ollama")

# Ask anything - no rate limits!
response = llm.generate("What is absorption rate in real estate?")
print(response)
```

## 📝 Run Tests

```bash
# Test Ollama integration (5 comprehensive tests)
python test_ollama_qwen.py

# Test with examples (6 real-world scenarios)
python example_use_qwen_for_testing.py
```

## 🔄 Replace Gemini with Qwen in Your Tests

### Before (Gemini - rate limited)
```python
import google.generativeai as genai

genai.configure(api_key="your-key")
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Will hit rate limit after ~60 requests/min
for i in range(1000):
    response = model.generate_content(f"Query {i}")  # ❌ Rate limit!
```

### After (Qwen - unlimited)
```python
from app.services.llm_factory import get_llm

llm = get_llm(provider="ollama")

# No rate limits!
for i in range(1000):
    response = llm.generate(f"Query {i}")  # ✅ Works!
```

## 🔧 Configuration

### Option 1: Environment Variable (Recommended)

Add to your `.env` file:
```bash
LLM_PROVIDER=ollama
```

Then in your code:
```python
from app.services.llm_factory import get_default_llm

# Automatically uses Ollama based on .env
llm = get_default_llm()
```

### Option 2: Direct in Code

```python
from app.services.llm_factory import get_llm

# Force Ollama
llm = get_llm(provider="ollama")

# Or force Gemini when needed
llm = get_llm(provider="gemini", api_key="your-key")
```

## 💡 Common Use Cases

### 1. Avoid Rate Limits in Tests

```python
from app.services.llm_factory import get_llm

llm = get_llm(provider="ollama")

# Run unlimited queries
for query in your_test_queries:
    response = llm.generate(query)
    assert response is not None  # No rate limit errors!
```

### 2. RAG with Project Data

```python
llm = get_llm(provider="ollama")

context = """
Project: Pristine Heights
Total Units: 150
Absorption Rate: 10% per year
"""

query = "What is the absorption rate?"

prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
response = llm.generate(prompt, temperature=0.3)
```

### 3. Batch Analysis

```python
llm = get_llm(provider="ollama")

projects = [...]  # Your project data

for project in projects:
    analysis = llm.generate(
        f"Analyze this project: {project}",
        temperature=0.5
    )
    print(f"{project['name']}: {analysis}")
```

## 🆚 When to Use What

| Scenario | Use Ollama | Use Gemini |
|----------|------------|------------|
| **Development/Testing** | ✅ Yes (no limits) | ❌ No (rate limits) |
| **CI/CD Pipelines** | ✅ Yes (free) | ❌ No (costs money) |
| **Privacy-sensitive data** | ✅ Yes (local) | ❌ No (cloud) |
| **Production (speed critical)** | ⚠️ Maybe | ✅ Yes (faster) |
| **Offline work** | ✅ Yes | ❌ No |

## 🐛 Troubleshooting

### "Could not connect to Ollama"
```bash
# Start Ollama server
ollama serve
```

### "Model not found"
```bash
# Pull Qwen 2.5
ollama pull qwen2.5
```

### Slow inference
```bash
# Use smaller model
ollama pull qwen2.5:7b

# Or switch to Gemini for speed
llm = get_llm(provider="gemini")
```

## 📚 Files Created

1. `app/services/ollama_service.py` - Core Ollama integration
2. `app/services/llm_factory.py` - Provider switching logic
3. `test_ollama_qwen.py` - Comprehensive test suite
4. `example_use_qwen_for_testing.py` - Real-world examples
5. `OLLAMA_QWEN_INTEGRATION.md` - Complete documentation
6. `QUICK_START_OLLAMA.md` - This file

## ⚠️ Important Note About HuggingFace Token

You shared: `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`

**You don't need this for Ollama!** Ollama runs locally without any tokens.

**Security Alert:**
1. Go to https://huggingface.co/settings/tokens
2. **REVOKE this token immediately** (it's now public)
3. Generate a new one if you need HuggingFace access

Ollama ≠ HuggingFace:
- **Ollama**: Local model runtime (no auth needed)
- **HuggingFace**: Cloud model repository (needs token to download)

## ✅ Next Steps

1. ✅ Integration complete
2. ✅ Tests passing
3. ✅ Documentation ready
4. 📝 **Your turn**: Use in your tests!

```python
# In any test file:
from app.services.llm_factory import get_llm

def test_your_feature():
    llm = get_llm(provider="ollama")  # No rate limits!
    result = llm.generate("Your test query")
    assert result is not None
```

## 🎉 Benefits Summary

✅ **No rate limits** - Run unlimited queries
✅ **No API costs** - Completely free
✅ **Privacy** - Data stays on your machine
✅ **Speed** - No network latency (after first load)
✅ **Offline** - Works without internet
✅ **Easy switching** - One line to change providers

## 📞 Need Help?

Check the test outputs:
```bash
python test_ollama_qwen.py          # See 5 test scenarios
python example_use_qwen_for_testing.py  # See 6 examples
python app/services/llm_factory.py  # Test factory directly
```

Read the full guide:
- `OLLAMA_QWEN_INTEGRATION.md` - Complete integration guide

---

**Happy testing without rate limits! 🚀**
