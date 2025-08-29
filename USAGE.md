# Professional SWE Agent - Detailed Usage Guide

This guide provides comprehensive examples and advanced usage patterns for the Professional SWE Agent.

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Basic Usage Patterns](#basic-usage-patterns)
- [Advanced Configuration](#advanced-configuration)
- [Multi-Model Strategies](#multi-model-strategies)
- [Tool-Specific Usage](#tool-specific-usage)
- [Real-World Examples](#real-world-examples)
- [Debugging & Troubleshooting](#debugging--troubleshooting)
- [Performance Optimization](#performance-optimization)

## Installation & Setup

### Prerequisites

- Python 3.8+
- Git
- Internet connection (for web tools and LLM APIs)

### Step-by-Step Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd sweagent-v10/multi_llm_swe_agent_dyamic_registry
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up API keys:**

Choose your preferred LLM provider(s) and set the corresponding environment variables:

```bash
# For OpenAI models
export OPENAI_API_KEY="sk-..."

# For Anthropic Claude models  
export ANTHROPIC_API_KEY="sk-ant-..."

# For Mistral models
export MISTRAL_API_KEY="sk-..."

# For Azure OpenAI (also need endpoint)
export AZURE_API_KEY="..."
export AZURE_API_BASE="https://your-resource.openai.azure.com"
```

4. **Verify installation:**
```bash
python -m swe_agent_litellm.main --max-iterations 1 "Say hello and confirm you're working"
```

## Basic Usage Patterns

### Interactive Mode

Start the agent without specifying a task to enter interactive mode:

```bash
python -m swe_agent_litellm.main
# You'll be prompted: "Enter comprehensive task:"
```

### Command Line Tasks

Provide tasks directly via command line:

```bash
python -m swe_agent_litellm.main "Create a Python script that calculates fibonacci numbers"
```

### Working Directory Control

Specify where the agent should operate:

```bash
python -m swe_agent_litellm.main \
  --working-dir /path/to/my/project \
  "Add unit tests for all Python modules"
```

### Iteration Limits

Control how long the agent runs:

```bash
# Quick tasks
python -m swe_agent_litellm.main --max-iterations 10 "Fix syntax errors in main.py"

# Complex projects  
python -m swe_agent_litellm.main --max-iterations 200 "Refactor entire codebase for Python 3.11"
```

## Advanced Configuration

### Model Selection

#### Single Model Usage
```bash
# Use GPT-4
python -m swe_agent_litellm.main --model gpt-4o "Analyze code performance"

# Use Claude
python -m swe_agent_litellm.main --model claude-3-5-sonnet-20241022 "Write documentation"

# Use Mistral
python -m swe_agent_litellm.main --model mistral/mistral-large-latest "Debug application"
```

#### Model Fallback Chains
```bash
# Primary: Claude, Fallback: GPT-4, Then: Mistral
python -m swe_agent_litellm.main \
  --model claude-3-5-sonnet-20241022 \
  --models gpt-4o,mistral/mistral-large-latest \
  "Complex refactoring task"
```

### Feature Toggles

#### Disable Web Access
```bash
python -m swe_agent_litellm.main --no-web "Work only with local files"
```

#### Disable Notebook Support
```bash
python -m swe_agent_litellm.main --no-notebooks "Focus on Python scripts only"
```

#### Disable Progress Tracking
```bash
python -m swe_agent_litellm.main --no-progress "Don't create progress.md file"
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
python -m swe_agent_litellm.main --debug "Investigate why tests are failing"
```

Enable LiteLLM debug logging:
```bash
export LITELLM_LOG=DEBUG
python -m swe_agent_litellm.main "Your task"
```

## Multi-Model Strategies

### Cost Optimization Strategy
```bash
# Start with cheaper model, fallback to premium if needed
python -m swe_agent_litellm.main \
  --model gpt-4o-mini \
  --models claude-3-5-sonnet-20241022,gpt-4o \
  "Complex architectural refactoring"
```

### Speed vs Quality Strategy
```bash
# Fast model for simple tasks, high-quality for complex reasoning
python -m swe_agent_litellm.main \
  --model gpt-3.5-turbo \
  --models gpt-4o,claude-3-5-sonnet-20241022 \
  "Quick bug fixes with fallback to advanced reasoning"
```

### Provider Diversification
```bash
# Mix different providers for reliability
python -m swe_agent_litellm.main \
  --model claude-3-5-sonnet-20241022 \
  --models gpt-4o,mistral/mistral-large-latest \
  "Mission-critical deployment script"
```

## Tool-Specific Usage

### File Operations
The agent automatically uses appropriate tools based on task context:

```bash
# Triggers str_replace_editor, glob_search, grep_search
python -m swe_agent_litellm.main "Find all TODO comments and convert them to GitHub issues"

# Uses bash tool for system operations
python -m swe_agent_litellm.main "Set up a Python virtual environment and install dependencies"
```

### Web Research
```bash
# Enables web_search and web_fetch tools
python -m swe_agent_litellm.main \
  "Research best practices for FastAPI authentication and implement them"

# Disable web access if not needed (faster execution)
python -m swe_agent_litellm.main --no-web \
  "Refactor existing authentication code"
```

### Notebook Workflows
```bash
# Uses notebook_edit tool
python -m swe_agent_litellm.main \
  "Analyze the Jupyter notebook and create a clean Python script version"

# Skip notebook tools if not needed
python -m swe_agent_litellm.main --no-notebooks \
  "Work only with .py files"
```

## Real-World Examples

### 1. Code Review and Improvement

```bash
python -m swe_agent_litellm.main \
  --working-dir ./my-project \
  --max-iterations 75 \
  --model claude-3-5-sonnet-20241022 \
  "Perform a comprehensive code review of this Python project. Check for:
   - Security vulnerabilities
   - Performance bottlenecks  
   - Code style violations
   - Missing error handling
   - Opportunities for refactoring
   Create a detailed report and fix critical issues."
```

### 2. Feature Development

```bash
python -m swe_agent_litellm.main \
  --working-dir ./web-app \
  --max-iterations 150 \
  --model gpt-4o \
  --models claude-3-5-sonnet-20241022 \
  "Add a complete user authentication system to this Flask app:
   - User registration and login
   - Password hashing with bcrypt
   - JWT token-based sessions
   - Password reset functionality
   - Email verification
   - Admin user management
   Include comprehensive tests and documentation."
```

### 3. Bug Investigation and Fixing

```bash
python -m swe_agent_litellm.main \
  --working-dir ./buggy-app \
  --debug \
  --model claude-3-5-sonnet-20241022 \
  "The application crashes intermittently with 'ConnectionError'. 
   Investigate the root cause by:
   - Analyzing logs and stack traces
   - Reviewing database connection handling
   - Checking for race conditions
   - Testing with different loads
   - Implementing proper error handling and retry logic"
```

### 4. Documentation Generation

```bash
python -m swe_agent_litellm.main \
  --working-dir ./api-project \
  --no-web \
  --model gpt-4o-mini \
  --models claude-3-5-sonnet-20241022 \
  "Generate comprehensive documentation for this API project:
   - README with setup instructions
   - API endpoint documentation with examples
   - Code comments and docstrings
   - Developer guide for contributions
   - Deployment instructions
   Make sure everything is properly formatted in Markdown."
```

### 5. Test Suite Creation

```bash
python -m swe_agent_litellm.main \
  --working-dir ./my-library \
  --max-iterations 100 \
  --model claude-3-5-sonnet-20241022 \
  "Create a comprehensive test suite for this Python library:
   - Unit tests for all functions and classes
   - Integration tests for main workflows
   - Mock external dependencies
   - Test edge cases and error conditions
   - Set up pytest configuration
   - Achieve >90% code coverage
   - Add GitHub Actions CI pipeline"
```

### 6. Database Migration

```bash
python -m swe_agent_litellm.main \
  --working-dir ./django-project \
  --model gpt-4o \
  "Migrate this Django project from SQLite to PostgreSQL:
   - Update database settings
   - Create migration scripts
   - Handle data type differences
   - Update deployment configurations
   - Create backup and restore procedures
   - Test the migration process thoroughly"
```

## Resume Functionality

### Saving Progress
The agent automatically saves progress every few iterations. State is stored in `.swe_agent_professional_state.pkl`.

### Resuming Tasks
If a task is interrupted or you want to continue later:

```bash
# The agent will show the task ID when it completes or is interrupted
python -m swe_agent_litellm.main --resume task_abc123
```

### Managing State Files
```bash
# Clean slate - remove old state
rm .swe_agent_professional_state.pkl

# Work in different directory to avoid conflicts
python -m swe_agent_litellm.main --working-dir ./fresh-project "New task"
```

## Progress Tracking

### Understanding progress.md
The agent creates detailed progress reports:

- **Task Overview**: Original request and current status
- **Iteration Log**: What happened in each step  
- **Files Modified**: Complete change tracking
- **Tools Used**: Which capabilities were leveraged
- **Errors and Resolutions**: How problems were solved

### Customizing Progress Reports
```bash
# Disable progress tracking for simple tasks
python -m swe_agent_litellm.main --no-progress "Quick file edit"

# Progress files are created in the working directory
python -m swe_agent_litellm.main --working-dir ./reports "Generate analysis"
# Creates: ./reports/progress.md
```

## Debugging & Troubleshooting

### Common Issues and Solutions

#### API Key Problems
```bash
# Test API key explicitly
python -m swe_agent_litellm.main --api-key sk-your-key --model gpt-4o-mini "test"

# Check environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

#### Model Access Issues
```bash
# Try a different model
python -m swe_agent_litellm.main --model gpt-3.5-turbo "test"

# Use fallback chain for reliability
python -m swe_agent_litellm.main \
  --model claude-3-5-sonnet-20241022 \
  --models gpt-4o-mini,gpt-3.5-turbo \
  "test task"
```

#### Performance Issues
```bash
# Reduce iteration limit
python -m swe_agent_litellm.main --max-iterations 25 "focused task"

# Disable unnecessary features
python -m swe_agent_litellm.main --no-web --no-notebooks "local task only"
```

#### Tool Execution Problems
```bash
# Enable debug mode to see detailed tool output
python -m swe_agent_litellm.main --debug "problematic task"

# Check working directory permissions
ls -la ./
```

### Advanced Debugging

#### LiteLLM Debug Logging
```bash
export LITELLM_LOG=DEBUG
python -m swe_agent_litellm.main "task"
```

#### Inspect Tool Registry
```python
from swe_agent_litellm.tool_registry import DynamicToolRegistry
registry = DynamicToolRegistry()
registry.discover_tools()
print([tool.get_name() for tool in registry.tools.values()])
```

#### Manual State Inspection
```python
import pickle
with open('.swe_agent_professional_state.pkl', 'rb') as f:
    state = pickle.load(f)
    print(f"Task ID: {state.task_id}")
    print(f"Iterations: {state.iteration}")
    print(f"Current step: {state.current_step}")
```

## Performance Optimization

### Model Selection for Performance

**Fast Response (Simple Tasks):**
- `gpt-3.5-turbo`
- `gpt-4o-mini`
- `claude-3-haiku-20240307`

**Balanced (Most Tasks):**
- `gpt-4o`
- `claude-3-5-sonnet-20241022`

**Maximum Capability (Complex Tasks):**
- `gpt-4o`
- `claude-3-opus-20240229`
- `mistral/mistral-large-latest`

### Resource Management

```bash
# Limit iterations to prevent runaway tasks
python -m swe_agent_litellm.main --max-iterations 50 "bounded task"

# Disable features you don't need
python -m swe_agent_litellm.main --no-web --no-notebooks "local development"

# Use appropriate working directory
python -m swe_agent_litellm.main --working-dir ./specific-project "focused work"
```

### Batch Operations

For multiple similar tasks, consider running them sequentially:

```bash
# Script for batch processing
for project in project1 project2 project3; do
  echo "Processing $project..."
  python -m swe_agent_litellm.main \
    --working-dir "./$project" \
    --max-iterations 30 \
    "Add logging to all Python files"
done
```

## Best Practices

### Task Description Guidelines

**Good Task Descriptions:**
- Specific and actionable
- Include context and constraints
- Mention expected outputs
- Specify quality requirements

```bash
python -m swe_agent_litellm.main "
Create a REST API endpoint for user registration that:
- Accepts JSON with username, email, password
- Validates email format and password strength
- Stores user in database with hashed password
- Returns JSON response with user ID or error
- Includes comprehensive error handling
- Follows our existing code style in auth.py
"
```

**Avoid Vague Descriptions:**
- "Make the code better"
- "Fix bugs"
- "Add features"

### Model Selection Strategy

1. **Start Conservative**: Use cost-effective models for initial attempts
2. **Fallback to Premium**: Include high-capability models for complex reasoning
3. **Provider Diversity**: Mix different providers for reliability
4. **Context Awareness**: Choose models based on task type

### Monitoring and Maintenance

- Check `progress.md` files regularly
- Monitor API usage and costs
- Clean up state files periodically
- Update models as new versions become available

---

For additional help or to report issues, please refer to the project documentation or create an issue in the repository.