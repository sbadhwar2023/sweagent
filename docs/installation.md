# Installation Guide

## Prerequisites

- Python 3.8 or higher
- Git
- API keys for at least one LLM provider

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd sweagent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys

Choose one or more providers and set the corresponding environment variables:

#### OpenAI
```bash
export OPENAI_API_KEY=sk-your-openai-key-here
```

#### Anthropic
```bash
export ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

#### Mistral
```bash
export MISTRAL_API_KEY=sk-your-mistral-key-here
```

#### Azure OpenAI
```bash
export AZURE_API_KEY=your-azure-key-here
export AZURE_API_BASE="https://your-resource.openai.azure.com"
```

### 4. Verify Installation

Run a simple test:

```bash
cd multi_llm_swe_agent_dyamic_registry
python -m swe_agent_litellm.main --max-iterations 1 "Say hello"
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Optional | OpenAI API key for GPT models |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API key for Claude models |
| `MISTRAL_API_KEY` | Optional | Mistral API key |
| `AZURE_API_KEY` | Optional | Azure OpenAI API key |
| `AZURE_API_BASE` | Optional | Azure OpenAI endpoint |
| `LITELLM_LOG` | Optional | Set to `DEBUG` for verbose logging |

## Docker Installation (Optional)

```bash
# Build the Docker image
docker build -t swe-agent .

# Run with environment variables
docker run -e OPENAI_API_KEY=sk-... swe-agent "Your task here"
```

## Troubleshooting

### Common Issues

**ImportError: No module named 'litellm'**
```bash
pip install --upgrade litellm
```

**API Key not found**
- Ensure environment variables are set correctly
- Check that variable names match exactly
- Try using the `--api-key` flag as an alternative

**Permission denied**
- Ensure Python has write permissions in the working directory
- Check that all required dependencies are installed

For more troubleshooting help, see our [troubleshooting guide](troubleshooting.md).