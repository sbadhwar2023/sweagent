# Configuration Guide

## Command Line Options

The SWE Agent supports various configuration options through command line arguments:

| Option | Description | Default |
|--------|-------------|---------|
| `task` | Task description (or enter interactively) | - |
| `--working-dir` | Working directory | `.` |
| `--max-iterations` | Maximum iterations | `50` |
| `--model` | Primary LLM model | `claude-3-5-sonnet-20241022` |
| `--models` | Comma-separated fallback models | - |
| `--api-key` | API key (overrides env vars) | - |
| `--debug` | Enable debug mode | `False` |
| `--resume` | Resume task by ID | - |
| `--no-progress` | Disable progress.md tracking | `False` |
| `--no-web` | Disable web tools | `False` |
| `--no-notebooks` | Disable notebook tools | `False` |

## Model Configuration

### Primary Model Selection

```bash
# Use Claude Sonnet
python -m swe_agent_litellm.main --model claude-3-5-sonnet-20241022 "Your task"

# Use GPT-4
python -m swe_agent_litellm.main --model gpt-4o "Your task"

# Use Mistral
python -m swe_agent_litellm.main --model mistral/mistral-large-latest "Your task"
```

### Fallback Models

Configure multiple models for reliability:

```bash
python -m swe_agent_litellm.main \
  --model claude-3-5-sonnet-20241022 \
  --models gpt-4o-mini,mistral/mistral-large-latest \
  "Complex task with fallback support"
```

## Feature Toggles

### Disable Specific Features

```bash
# Disable web tools
python -m swe_agent_litellm.main --no-web "Code-only task"

# Disable notebook support
python -m swe_agent_litellm.main --no-notebooks "Task without Jupyter"

# Disable progress tracking
python -m swe_agent_litellm.main --no-progress "Quick task"
```

## Advanced Configuration

### Debug Mode

Enable verbose logging:

```bash
export LITELLM_LOG=DEBUG
python -m swe_agent_litellm.main --debug "Task to debug"
```

### Working Directory

Specify a different working directory:

```bash
python -m swe_agent_litellm.main --working-dir /path/to/project "Analyze this codebase"
```

### Iteration Limits

Control maximum iterations for long-running tasks:

```bash
# Short task
python -m swe_agent_litellm.main --max-iterations 10 "Simple refactor"

# Long task
python -m swe_agent_litellm.main --max-iterations 200 "Complete feature development"
```

## State Management

### Resume Tasks

Tasks can be paused and resumed:

```bash
# Start a task (automatically assigns ID)
python -m swe_agent_litellm.main "Long running task"

# Resume by ID
python -m swe_agent_litellm.main --resume task_123
```

State is persisted in `.swe_agent_professional_state.pkl` in the working directory.

### Progress Tracking

By default, the agent creates `progress.md` files to track:
- Task breakdown and status
- Files created/modified
- Tools used and outcomes
- Iteration summaries
- Error logs

Disable with `--no-progress` if not needed.

## Environment Variables

### API Configuration

```bash
# Primary providers
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export MISTRAL_API_KEY=sk-...

# Azure OpenAI
export AZURE_API_KEY=...
export AZURE_API_BASE="https://your-resource.openai.azure.com"

# Debug settings
export LITELLM_LOG=DEBUG
```

### Custom Configuration

You can also create a `.env` file in your working directory:

```env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
LITELLM_LOG=INFO
```

## Provider-Specific Settings

### OpenAI Configuration

```bash
# Use specific GPT model
python -m swe_agent_litellm.main --model gpt-4o-mini "Task"

# With custom API base (for proxies)
export OPENAI_API_BASE=https://your-proxy.com/v1
```

### Anthropic Configuration

```bash
# Use specific Claude model
python -m swe_agent_litellm.main --model claude-3-haiku-20240307 "Fast task"
```

### Azure OpenAI Configuration

```bash
# Use Azure deployment
python -m swe_agent_litellm.main --model azure/your-deployment-name "Task"
```

## Performance Tuning

### Memory Management

For large codebases, consider:
- Limiting iterations with `--max-iterations`
- Using specific working directories to focus scope
- Disabling unnecessary features with `--no-web` or `--no-notebooks`

### Model Selection Strategy

1. **Fast iterations**: Use `gpt-4o-mini` or `claude-3-haiku-20240307`
2. **Complex reasoning**: Use `claude-3-5-sonnet-20241022` or `gpt-4o`
3. **Reliability**: Configure fallback models with `--models`

## Troubleshooting Configuration

### Common Issues

**Model not available**
- Check provider API status
- Verify API key permissions
- Try fallback models

**Rate limiting**
- Configure fallback models
- Reduce iteration frequency
- Use different providers

**Authentication errors**
- Verify API key format
- Check environment variable names
- Test with simple requests

For more help, see our [troubleshooting guide](troubleshooting.md).