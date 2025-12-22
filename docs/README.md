# Professional SWE Agent Documentation

Welcome to the documentation for the Professional SWE Agent - a comprehensive AI-powered software engineering assistant with multi-LLM support.

## Quick Navigation

- **[Getting Started](index.md)** - Overview and introduction
- **[Installation](installation.md)** - Setup instructions
- **[Configuration](configuration.md)** - Configuration options and settings
- **[Available Tools](tools.md)** - Complete tool reference
- **[Examples](examples.md)** - Practical usage examples
- **[API Reference](api.md)** - Developer API documentation
- **[Contributing](contributing.md)** - How to contribute to the project
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## What is Professional SWE Agent?

The Professional SWE Agent is an AI-powered assistant that can perform complex software engineering tasks using multiple LLM providers. It features:

- 🤖 **Multi-LLM Support** - Works with OpenAI, Anthropic, Mistral, Azure OpenAI, and 100+ other models
- 🔧 **Comprehensive Toolset** - File operations, web search, bash execution, notebook editing, and more
- 📊 **Progress Tracking** - Automatic progress reporting and task management
- 🔄 **Resume Capability** - Pause and resume long-running tasks
- 🛡️ **Error Recovery** - Intelligent error handling with model fallback

## Quick Start

1. **Install the agent**:
   ```bash
   git clone <repository-url>
   cd sweagent
   pip install -r requirements.txt
   ```

2. **Set up API keys**:
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   # or
   export ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

3. **Run your first task**:
   ```bash
   cd multi_llm_swe_agent_dyamic_registry
   python -m swe_agent_litellm.main "Create a simple Python calculator script"
   ```

## Documentation Structure

This documentation covers:

### For Users
- **Installation and setup** - Get up and running quickly
- **Configuration options** - Customize the agent for your needs
- **Usage examples** - Learn through practical examples
- **Troubleshooting** - Solve common issues

### For Developers
- **API reference** - Integrate with the agent programmatically
- **Tool development** - Create custom tools
- **Contributing guidelines** - Help improve the project

## Getting Help

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: Browse these docs for detailed information
- **Examples**: See practical usage patterns in the examples section

## Contributing

We welcome contributions! See our [contributing guide](contributing.md) for:
- Development setup instructions
- Code style guidelines
- How to add new tools
- Testing requirements
- Pull request process

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.