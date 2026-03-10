# Ollama Qwen 2.5 Integration Guide

## Overview

This guide explains how to use your **local Qwen 2.5** model running on Ollama instead of cloud-based LLMs (Gemini, OpenAI) to avoid rate limits and API costs.

## ✅ What's Been Set Up

1. **Ollama Service** (`app/services/ollama_service.py`)
   - Direct integration with Ollama API
   - Support for text generation, chat, and RAG queries
   - Automatic connection validation

2. **LLM Factory** (`app/services/llm_factory.py`)
   - Unified interface for switching between LLM providers
   - Easy toggle between Ollama (local) and Gemini (cloud)
   - Environment-based configuration

3. **Test Suite** (`test_ollama_qwen.py`)
   - Comprehensive tests for all Ollama features
   - Real estate domain examples
   - RAG-style query demonstrations

## 🚀 Quick Start

### Option 1: Direct Ollama Usage

```python
from app.services.ollama_service import get_ollama_service

# Get service instance
ollama = get_ollama_service()

# Simple generation
response = ollama.generate("What is absorption rate in real estate?")
print(response)

# Chat with history
messages = [
    {"role": "user", "content": "What is PSF?"},
]
response = ollama.chat(messages)
print(response)

# RAG query with context
context = "Project has 100 units, absorption rate 12% per year"
query = "What is the absorption rate?"
response = ollama.generate_with_context(query, context)
print(response)
```

### Option 2: Using LLM Factory (Recommended)

```python
from app.services.llm_factory import get_llm

# Use Ollama (local, no rate limits)
llm = get_llm(provider="ollama")
response = llm.generate("Your question here")

# Use Gemini (cloud, has rate limits)
llm = get_llm(provider="gemini", api_key="your-key")
response = llm.generate("Your question here")

# Use default (automatically chooses best available)
from app.services.llm_factory import get_default_llm
llm = get_default_llm()
response = llm.generate("Your question here")
```

## 🔧 Configuration

### Environment Variables (.env or .env.production)

```bash
# Choose provider: "ollama" or "gemini"
LLM_PROVIDER=ollama

# Ollama settings (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest

# Gemini settings (cloud)
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Switching Between Providers

**Method 1: Environment Variable**
```bash
# Use Ollama (no rate limits)
export LLM_PROVIDER=ollama

# Use Gemini (cloud)
export LLM_PROVIDER=gemini
```

**Method 2: Code**
```python
# Force Ollama
llm = get_llm(provider="ollama")

# Force Gemini
llm = get_llm(provider="gemini")
```

## 📊 Testing

### Run All Tests
```bash
python test_ollama_qwen.py
```

### Run Specific Test
```python
from test_ollama_qwen import test_basic_generation
test_basic_generation()
```

### Test LLM Factory
```bash
python app/services/llm_factory.py
```

## 🎯 Use Cases

### 1. Avoid Rate Limits During Testing

**Before (Gemini - rate limited):**
```python
# Hits rate limit after ~60 requests/min
for i in range(1000):
    response = gemini.generate(f"Query {i}")  # ❌ Rate limit!
```

**After (Ollama - unlimited):**
```python
# No rate limits!
ollama = get_llm(provider="ollama")
for i in range(1000):
    response = ollama.generate(f"Query {i}")  # ✅ Works!
```

### 2. Privacy-Sensitive Data

```python
# Keep sensitive data local
ollama = get_llm(provider="ollama")

sensitive_context = """
Project: Confidential Development
Investment: ₹500 Cr (internal only)
...
"""

# Data never leaves your machine
response = ollama.generate_with_context(query, sensitive_context)
```

### 3. Cost Optimization

```python
# Development/testing: Use Ollama (free)
if os.getenv("ENV") == "development":
    llm = get_llm(provider="ollama")
else:
    # Production: Use Gemini (paid but faster)
    llm = get_llm(provider="gemini")
```

### 4. Real Estate Analysis

```python
from app.services.llm_factory import get_llm

llm = get_llm(provider="ollama")

system_prompt = """You are a real estate financial analyst.
Provide concise insights based on metrics."""

analysis = llm.generate(
    prompt="""Analyze:
    - Total Investment: ₹50 Cr
    - Annual Revenue: ₹12 Cr
    - Absorption Rate: 15%/year (market avg: 12%)

    What are the key insights?""",
    system_prompt=system_prompt,
    temperature=0.5  # Lower = more factual
)

print(analysis)
```

## 🔍 Available Models

Check what models you have:
```python
from app.services.ollama_service import get_ollama_service

service = get_ollama_service()
models = service.get_available_models()
print(models)
# Output: ['qwen2.5:latest', 'mistral:latest', 'nomic-embed-text:latest']
```

Pull a new model:
```bash
ollama pull qwen2.5
ollama pull mistral
ollama pull llama3
```

## 🆚 Ollama vs Gemini Comparison

| Feature | Ollama (Qwen 2.5) | Gemini |
|---------|-------------------|--------|
| **Cost** | Free | Paid (after free tier) |
| **Rate Limits** | None | 60 requests/min |
| **Privacy** | Data stays local | Data sent to Google |
| **Speed** | Depends on your GPU/CPU | Fast (cloud) |
| **Setup** | Requires Ollama running | Just API key |
| **Offline** | ✅ Works offline | ❌ Needs internet |
| **Best For** | Testing, privacy, no limits | Production, speed |

## 🚨 Important Notes

### About Your HuggingFace Token

⚠️ **SECURITY ALERT**: You shared your HuggingFace token publicly: `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`

**Action Required:**
1. Go to https://huggingface.co/settings/tokens
2. **Revoke this token immediately**
3. Generate a new one
4. Never share tokens in chat/code

### Ollama vs HuggingFace

- **Ollama**: Runs models locally, no authentication needed
- **HuggingFace**: Cloud platform for downloading models
- **Your token**: Not needed for Ollama (only for HF Hub downloads)

### When Ollama Is Not Running

If you see: `ConnectionError: Could not connect to Ollama`

**Solution:**
```bash
# Start Ollama server
ollama serve

# In another terminal, verify it's running
ollama list
```

## 📝 Example: Modify Existing Code to Use Ollama

### Before (Hardcoded Gemini)
```python
import google.generativeai as genai

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content("Your query")
```

### After (Flexible with LLM Factory)
```python
from app.services.llm_factory import get_llm

# Automatically uses Ollama if LLM_PROVIDER=ollama
llm = get_llm()
response = llm.generate("Your query")
```

## 🔗 Integration with Your Codebase

Your current services that use LLM can be modified:

**Example: `app/services/qa_service.py`**
```python
# Add at the top
from app.services.llm_factory import get_default_llm

class QAService:
    def __init__(self):
        # Use factory instead of hardcoded Gemini
        self.llm = get_default_llm()  # Auto-selects Ollama or Gemini

    def answer_question(self, question: str, context: str) -> str:
        return self.llm.generate_with_context(question, context)
```

## 🎓 Learning Resources

- **Ollama Docs**: https://ollama.ai/
- **Qwen 2.5 Model**: https://ollama.ai/library/qwen2.5
- **Your Test Suite**: `test_ollama_qwen.py` (comprehensive examples)

## 💡 Tips

1. **Use Ollama for development/testing** (no rate limits)
2. **Use Gemini for production** (if you need faster cloud inference)
3. **Set `LLM_PROVIDER=ollama`** in your `.env` for testing
4. **Lower temperature (0.3-0.5)** for factual real estate analysis
5. **Higher temperature (0.7-0.9)** for creative descriptions

## 🐛 Troubleshooting

### Issue: "Could not connect to Ollama"
**Solution**: Run `ollama serve` in a terminal

### Issue: "Model 'qwen2.5:latest' not found"
**Solution**: Run `ollama pull qwen2.5`

### Issue: Slow inference
**Solution**:
- Qwen 2.5 is running on your CPU/GPU
- Consider using smaller model: `ollama pull qwen2.5:7b`
- Or use Gemini for faster cloud inference

### Issue: "API key required"
**Solution**: Either:
- Set `LLM_PROVIDER=ollama` (no key needed)
- Or set `GEMINI_API_KEY` for cloud usage

## ✅ Next Steps

1. ✅ Ollama service created
2. ✅ LLM factory created
3. ✅ Test suite created
4. ✅ Environment config updated
5. 🔄 Run tests: `python test_ollama_qwen.py`
6. 📝 Update your existing services to use `llm_factory.py`
7. 🚀 Enjoy unlimited, local LLM inference!

---

**Need Help?**
- Check test suite: `python test_ollama_qwen.py`
- Verify Ollama: `ollama list`
- Test factory: `python app/services/llm_factory.py`
