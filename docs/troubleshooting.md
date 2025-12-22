# Troubleshooting Guide

Common issues and their solutions for the Professional SWE Agent.

## Installation Issues

### ImportError: No module named 'litellm'

**Cause**: Missing or outdated LiteLLM installation

**Solution**:
```bash
pip install --upgrade litellm
# or
pip install -r requirements.txt
```

### Permission Denied Errors

**Cause**: Insufficient file system permissions

**Solutions**:
1. Check working directory permissions:
```bash
ls -la
chmod 755 .
```

2. Run with appropriate user permissions:
```bash
sudo chown -R $USER:$USER .
```

### Python Version Compatibility

**Cause**: Unsupported Python version

**Solution**:
Ensure Python 3.8 or higher:
```bash
python --version
# If needed, install Python 3.8+
```

## Authentication Issues

### API Key Not Found

**Error**: `No API key found for provider`

**Solutions**:

1. **Check environment variables**:
```bash
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
echo $MISTRAL_API_KEY
```

2. **Set variables correctly**:
```bash
export OPENAI_API_KEY=sk-your-key-here
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

3. **Use command line override**:
```bash
python -m swe_agent_litellm.main --api-key sk-your-key "Task"
```

4. **Create .env file**:
```env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Invalid API Key Format

**Error**: `Invalid API key format`

**Solutions**:
1. **OpenAI keys** start with `sk-`
2. **Anthropic keys** start with `sk-ant-`
3. **Mistral keys** start with `sk-`
4. **Check for extra spaces or characters**

### Authentication Failed

**Error**: `401 Unauthorized`

**Causes and Solutions**:

1. **Expired key**: Generate new API key from provider
2. **Wrong provider**: Check model name matches API key provider
3. **Quota exceeded**: Check usage limits in provider dashboard
4. **Invalid permissions**: Ensure key has required model access

## Model Issues

### Model Not Found

**Error**: `Model not found` or `Invalid model`

**Solutions**:

1. **Check model name spelling**:
```bash
# Correct
--model claude-3-5-sonnet-20241022
--model gpt-4o
--model mistral/mistral-large-latest

# Incorrect
--model claude-sonnet  # Missing version
--model gpt4          # Missing hyphen
```

2. **Verify model availability**:
- Check provider documentation
- Ensure you have access to the model
- Try alternative models

3. **Use fallback models**:
```bash
python -m swe_agent_litellm.main \
  --model claude-3-5-sonnet-20241022 \
  --models gpt-4o-mini,mistral/mistral-large-latest \
  "Task with fallback"
```

### Rate Limiting

**Error**: `Rate limit exceeded`

**Solutions**:

1. **Wait and retry**: Most rate limits are temporary
2. **Use different model**:
```bash
--model gpt-4o-mini  # Usually has higher limits
```

3. **Configure fallback models**:
```bash
--models gpt-4o-mini,claude-3-haiku-20240307
```

4. **Reduce iteration frequency**:
```bash
--max-iterations 10  # Fewer API calls
```

## Runtime Issues

### Task Won't Resume

**Error**: `Cannot resume task` or `Task ID not found`

**Causes and Solutions**:

1. **Missing state file**:
```bash
ls -la .swe_agent_professional_state.pkl
# If missing, task cannot be resumed
```

2. **Corrupted state file**:
```bash
rm .swe_agent_professional_state.pkl
# Start fresh (loses resume capability)
```

3. **Wrong working directory**:
```bash
# Ensure you're in the same directory where task was started
cd /original/working/directory
```

4. **Invalid task ID**:
```bash
# Check available task IDs in progress.md or state file
```

### Tools Not Working

#### Web Tools Disabled

**Error**: Web search or fetch not working

**Solutions**:
1. **Check if disabled**:
```bash
# Remove --no-web flag if present
python -m swe_agent_litellm.main "Task"  # Enable web tools
```

2. **Network connectivity**:
```bash
curl -I https://google.com  # Test internet access
```

#### File Permission Issues

**Error**: Cannot read/write files

**Solutions**:
1. **Check file permissions**:
```bash
ls -la filename
chmod 644 filename  # Make readable/writable
```

2. **Directory permissions**:
```bash
chmod 755 directory_name
```

#### Bash Execution Issues

**Error**: Command execution failures

**Solutions**:
1. **Check command syntax**:
```bash
# Test command manually first
ls -la
```

2. **Path issues**:
```bash
which python  # Check if tools are in PATH
```

### Memory and Performance

#### Out of Memory

**Error**: Memory allocation errors

**Solutions**:
1. **Limit iterations**:
```bash
--max-iterations 20
```

2. **Disable heavy features**:
```bash
--no-web --no-notebooks
```

3. **Use lighter models**:
```bash
--model gpt-4o-mini
```

#### Slow Performance

**Solutions**:
1. **Use faster models**:
```bash
--model claude-3-haiku-20240307  # Fastest
--model gpt-4o-mini              # Fast and cheap
```

2. **Reduce scope**:
```bash
--working-dir ./specific/subdirectory
```

3. **Disable progress tracking**:
```bash
--no-progress
```

## Network Issues

### Connection Timeouts

**Error**: Request timeouts or connection errors

**Solutions**:

1. **Check internet connection**:
```bash
ping api.openai.com
ping api.anthropic.com
```

2. **Proxy configuration**:
```bash
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

3. **Firewall issues**: Ensure ports 80/443 are open

### DNS Resolution

**Error**: Cannot resolve hostnames

**Solutions**:
1. **Check DNS settings**:
```bash
nslookup api.openai.com
```

2. **Use alternative DNS**:
```bash
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
```

## Debugging Techniques

### Enable Debug Logging

```bash
export LITELLM_LOG=DEBUG
python -m swe_agent_litellm.main --debug "Task"
```

### Check Progress Files

```bash
cat progress.md           # Current progress
ls -la progress_*.md     # Historical progress files
```

### Validate Configuration

```bash
# Test with minimal task
python -m swe_agent_litellm.main --max-iterations 1 "Say hello"
```

### Test API Connectivity

```bash
# Test OpenAI
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Test Anthropic
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/messages
```

## Common Error Messages

### "No module named 'swe_agent_litellm'"

**Solution**:
```bash
cd multi_llm_swe_agent_dyamic_registry
python -m swe_agent_litellm.main "Task"
```

### "Task description is required"

**Solution**: Provide task as argument or run interactively:
```bash
python -m swe_agent_litellm.main "Your task description"
# or
python -m swe_agent_litellm.main  # Interactive mode
```

### "Working directory does not exist"

**Solution**:
```bash
mkdir -p /path/to/directory
# or use existing directory
--working-dir ./existing/path
```

## Getting Help

### Log Analysis

1. **Save debug output**:
```bash
python -m swe_agent_litellm.main --debug "Task" 2>&1 | tee debug.log
```

2. **Check specific errors**:
```bash
grep -i error debug.log
grep -i traceback debug.log
```

### Community Support

- Check existing issues on GitHub
- Search documentation for similar problems
- Provide full error messages when reporting issues

### Diagnostic Information

When reporting issues, include:

```bash
# System info
python --version
pip list | grep litellm

# Environment
env | grep -E "(OPENAI|ANTHROPIC|MISTRAL|AZURE)"

# Error output
python -m swe_agent_litellm.main --debug "test" 2>&1
```

## Prevention Tips

1. **Always test with simple tasks first**
2. **Keep API keys secure and up to date**
3. **Monitor usage quotas and limits**
4. **Use version control for important state files**
5. **Regular backup of progress files**
6. **Test network connectivity before long tasks**

For more help, see our [configuration guide](configuration.md) or [examples](examples.md).