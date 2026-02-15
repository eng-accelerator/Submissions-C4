# 🌐 Using OpenRouter with Vérité Financial

OpenRouter gives you access to multiple AI providers through a single API, including Claude, GPT-4, and many others. This guide shows you how to use OpenRouter with your financial advisor app.

## 🎯 Why Use OpenRouter?

- **Multiple Models**: Access Claude, GPT-4, Llama, and 100+ other models
- **Cost Optimization**: Choose cheaper models or compare prices
- **Redundancy**: Fallback to other models if one is down
- **Flexibility**: Switch models without changing code
- **Credits System**: Pay-as-you-go with credits

## 🚀 Quick Setup

### Step 1: Get OpenRouter API Key

1. Go to https://openrouter.ai/
2. Sign up for an account
3. Go to "Keys" section
4. Create a new API key
5. Add credits to your account

### Step 2: Set Environment Variables

**Linux/Mac:**
```bash
export USE_OPENROUTER=true
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
export OPENROUTER_MODEL='anthropic/claude-3.5-sonnet'
```

**Windows CMD:**
```cmd
set USE_OPENROUTER=true
set OPENROUTER_API_KEY=sk-or-v1-your-key-here
set OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

**Windows PowerShell:**
```powershell
$env:USE_OPENROUTER="true"
$env:OPENROUTER_API_KEY="sk-or-v1-your-key-here"
$env:OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
```

### Step 3: Run the App

```bash
python web_app.py
```

You should see:
```
🌐 API: OpenRouter
   Model: anthropic/claude-3.5-sonnet
   API Key: ✅ Set
```

## 🎨 Available Models

### Claude Models (Recommended)
```bash
# Claude 3.5 Sonnet - Best balance (recommended)
export OPENROUTER_MODEL='anthropic/claude-3.5-sonnet'

# Claude 3 Opus - Most capable
export OPENROUTER_MODEL='anthropic/claude-3-opus'

# Claude 3 Haiku - Fastest & cheapest
export OPENROUTER_MODEL='anthropic/claude-3-haiku'
```

### OpenAI Models
```bash
# GPT-4 Turbo
export OPENROUTER_MODEL='openai/gpt-4-turbo'

# GPT-4
export OPENROUTER_MODEL='openai/gpt-4'

# GPT-3.5 Turbo - Cheapest
export OPENROUTER_MODEL='openai/gpt-3.5-turbo'
```

### Other Models
```bash
# Google Gemini Pro
export OPENROUTER_MODEL='google/gemini-pro'

# Meta Llama 3 70B
export OPENROUTER_MODEL='meta-llama/llama-3-70b-instruct'

# Perplexity
export OPENROUTER_MODEL='perplexity/llama-3-sonar-large-32k-online'
```

Full model list: https://openrouter.ai/models

## 💰 Pricing Comparison

Approximate costs per 1M tokens (as of Feb 2024):

| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| Claude 3.5 Sonnet | $3 | $15 | Balanced (recommended) |
| Claude 3 Opus | $15 | $75 | Most capable |
| Claude 3 Haiku | $0.25 | $1.25 | Speed & cost |
| GPT-4 Turbo | $10 | $30 | Alternative to Claude |
| GPT-3.5 Turbo | $0.50 | $1.50 | Budget option |
| Llama 3 70B | Free | Free | Completely free! |

**Typical usage for this app:**
- Document parsing: ~500-1,000 tokens input, ~500 tokens output
- Each agent analysis: ~1,000-2,000 tokens input, ~1,000-2,000 tokens output
- Full comprehensive plan: ~10,000-15,000 tokens total

**Estimated cost per use:**
- With Claude 3.5 Sonnet: $0.05-0.15 per complete analysis
- With GPT-3.5 Turbo: $0.01-0.03 per complete analysis
- With Llama 3 70B: Free!

## 🔄 Switching Between Providers

### Use Anthropic Directly (Default)
```bash
unset USE_OPENROUTER
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
python web_app.py
```

### Use OpenRouter
```bash
export USE_OPENROUTER=true
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
python web_app.py
```

### Check Which is Active
The startup message shows which API is being used:
```
🤖 API: Anthropic (Direct)     OR     🌐 API: OpenRouter
```

## ⚙️ Advanced Configuration

### Create a Configuration File

Create `.env` file:
```bash
# Choose one:
USE_OPENROUTER=true
# USE_OPENROUTER=false

# If using OpenRouter:
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# If using Anthropic directly:
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Then load it:
```bash
# Linux/Mac
source .env

# Or use python-dotenv
pip install python-dotenv
```

### Model-Specific Settings

Some models work better with different parameters. Edit `config.py`:

```python
# For Claude models
API_CONFIG = {
    'model': 'claude-sonnet-4-20250514',
    'max_tokens': 4096,
    'temperature': 0.3,
}

# For GPT models (might want higher temperature)
API_CONFIG = {
    'model': 'gpt-4-turbo',
    'max_tokens': 4096,
    'temperature': 0.5,
}
```

## 🧪 Testing Different Models

Want to test which model works best? Run this script:

```bash
# Test with different models
for model in "anthropic/claude-3.5-sonnet" "openai/gpt-4-turbo" "openai/gpt-3.5-turbo"
do
    echo "Testing $model..."
    export OPENROUTER_MODEL=$model
    python financial_advisor_app.py
    echo "---"
done
```

## 🔍 Monitoring Usage

### Check OpenRouter Dashboard
1. Go to https://openrouter.ai/activity
2. See your API usage and costs
3. Monitor credit balance

### Add Usage Logging

Edit `financial_advisor_app.py` to log costs:

```python
def _analyze_openrouter(self, data: str, system_prompt: str):
    result = # ... existing code ...
    
    # Log usage
    if 'usage' in result_data:
        tokens = result_data['usage']
        print(f"Tokens used: {tokens.get('total_tokens', 0)}")
    
    return result
```

## ❓ Troubleshooting

### "OpenRouter API key required"
```bash
# Make sure it's set:
echo $OPENROUTER_API_KEY

# Set it:
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
```

### "Insufficient credits"
- Go to https://openrouter.ai/credits
- Add credits to your account
- Minimum is usually $5

### "Model not found"
- Check model name at https://openrouter.ai/models
- Make sure it's spelled exactly right
- Use format: `provider/model-name`

### Rate Limits
OpenRouter has rate limits per model:
- Free models: May be slower or rate-limited
- Paid models: Higher limits

### Poor Results with Some Models
Not all models are equal for financial advice:
- **Best**: Claude 3.5 Sonnet, Claude 3 Opus, GPT-4
- **Good**: GPT-4 Turbo, Gemini Pro
- **OK**: GPT-3.5 Turbo, Llama 3 70B
- **Not Recommended**: Smaller models (<13B parameters)

## 🎯 Best Practices

1. **Start with Claude 3.5 Sonnet** - Best quality-to-cost ratio
2. **Use GPT-3.5 for testing** - Cheapest way to test the app
3. **Try Llama 3 70B if budget-conscious** - Free and decent quality
4. **Monitor your costs** - Check dashboard regularly
5. **Set spending limits** - In OpenRouter settings
6. **Use caching** - OpenRouter caches recent requests

## 📊 Model Recommendations by Use Case

**Best Quality (Don't care about cost):**
- `anthropic/claude-3-opus`

**Best Balance (Recommended):**
- `anthropic/claude-3.5-sonnet`

**Budget-Friendly:**
- `openai/gpt-3.5-turbo`
- `anthropic/claude-3-haiku`

**Completely Free:**
- `meta-llama/llama-3-70b-instruct`

**Testing/Development:**
- `openai/gpt-3.5-turbo` (cheap)
- `meta-llama/llama-3-70b-instruct` (free)

## 🆚 OpenRouter vs Direct API

| Feature | OpenRouter | Anthropic Direct |
|---------|-----------|------------------|
| Multiple models | ✅ | ❌ |
| One API key | ✅ | ❌ |
| Credits system | ✅ | ❌ |
| Slightly higher cost | ⚠️ | ✅ |
| Extra latency | ⚠️ (~50-100ms) | ✅ |
| Dashboard/analytics | ✅ | ✅ |
| Rate limits | Model-dependent | Standard |

**Use OpenRouter if:**
- You want to try multiple models
- You prefer credits system
- You want unified billing

**Use Anthropic directly if:**
- You only need Claude
- You want lowest latency
- You have Anthropic credits

## 🔐 Security Notes

- Never commit API keys to git
- Use environment variables
- Consider `.env` files (add to `.gitignore`)
- Rotate keys periodically
- Monitor usage for unexpected charges

---

**Need Help?**
- OpenRouter Discord: https://discord.gg/openrouter
- Documentation: https://openrouter.ai/docs
- Status: https://status.openrouter.ai/
