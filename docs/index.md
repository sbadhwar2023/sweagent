# Professional SWE Agent with Multi-LLM Support

A comprehensive AI-powered software engineering agent that can perform complex coding tasks using multiple LLM providers through LiteLLM integration.

## Overview

This agent supports OpenAI, Anthropic, Mistral, Azure OpenAI, and many other providers with intelligent fallback capabilities, making it a robust solution for automated software engineering tasks.

## Key Features

- 🤖 **Multi-LLM Support**: Works with 100+ models via LiteLLM
- 🔧 **Comprehensive Toolset**: File operations, web search, bash execution, notebook editing
- 📊 **Progress Tracking**: Automatic progress reporting with markdown summaries
- 🔄 **Resume Capability**: Pause and resume long-running tasks
- 🌐 **Web Integration**: Search capabilities and web content fetching
- 📋 **Sub-Agent Spawning**: Create specialized sub-agents for complex subtasks
- 🛡️ **Error Recovery**: Intelligent error handling with model fallback
- 💾 **State Persistence**: Maintains state between sessions

## Quick Start

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd sweagent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API keys:
```bash
# Choose one or more providers
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export MISTRAL_API_KEY=sk-...
```

### Basic Usage

```bash
cd multi_llm_swe_agent_dyamic_registry
python -m swe_agent_litellm.main "Create a simple Python calculator script"
```

## Documentation

- [Installation Guide](installation.md)
- [Configuration](configuration.md)
- [Available Tools](tools.md)
- [Examples](examples.md)
- [API Reference](api.md)
- [Troubleshooting](troubleshooting.md)

## Supported Models

### OpenAI
- GPT-4o, GPT-4o-mini
- GPT-4-turbo, GPT-4
- GPT-3.5-turbo

### Anthropic
- Claude-3.5-sonnet-20241022
- Claude-3-haiku-20240307
- Claude-3-opus-20240229

### Mistral
- mistral-large-latest
- mistral-medium-latest
- mistral-small-latest

### Azure OpenAI
- azure/&lt;deployment_name&gt;

## Contributing

We welcome contributions! Please see our [contributing guidelines](contributing.md) for details.

## License

MIT License - see [LICENSE](../LICENSE) for details.