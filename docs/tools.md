# Available Tools

The SWE Agent comes with a comprehensive set of tools for various software engineering tasks.

## Core Tools

### File Operations

#### String Replace Editor
- **Purpose**: Edit files with precise string replacements
- **Use cases**: Code modifications, refactoring, bug fixes
- **Features**: Multi-line support, exact matching, backup creation

#### Glob Search
- **Purpose**: Find files using glob patterns
- **Use cases**: Locate configuration files, source code, documentation
- **Patterns**: `*.py`, `**/*.js`, `src/**/*.ts`

#### Grep Search
- **Purpose**: Search for text patterns within files
- **Use cases**: Find function definitions, variable usage, error messages
- **Features**: Regular expressions, case-insensitive search, context lines

#### List Directory
- **Purpose**: Explore project structure
- **Use cases**: Understanding codebase layout, finding relevant files
- **Features**: Recursive listing, file type filtering, size information

### Execution Tools

#### Bash Execution
- **Purpose**: Run shell commands safely
- **Use cases**: Building projects, running tests, installing dependencies
- **Features**: Timeout protection, output capture, error handling

#### Notebook Editing
- **Purpose**: Manipulate Jupyter notebooks
- **Use cases**: Data analysis, documentation, interactive development
- **Features**: Cell-level editing, output preservation, metadata handling

### Web Integration

#### Web Search
- **Purpose**: Search the internet for information
- **Use cases**: Research, documentation lookup, troubleshooting
- **Provider**: DuckDuckGo integration

#### Web Fetch
- **Purpose**: Retrieve and analyze web content
- **Use cases**: Documentation analysis, API reference lookup
- **Features**: HTML parsing, content extraction, link following

### Task Management

#### Task Agent
- **Purpose**: Spawn specialized sub-agents
- **Use cases**: Complex multi-step tasks, parallel processing
- **Features**: Isolated execution, result aggregation, error isolation

#### Progress Tracking
- **Purpose**: Document task progress automatically
- **Use cases**: Project documentation, debugging, audit trails
- **Output**: Markdown reports, file change logs, execution summaries

#### Todo Management
- **Purpose**: Track and manage task lists
- **Use cases**: Breaking down complex tasks, progress monitoring
- **Features**: Priority levels, status tracking, dependency management

## Tool Usage Examples

### File Editing Example

```python
# Search for a function
grep_result = agent.use_tool("grep_search", {
    "pattern": "def calculate_total",
    "file_pattern": "*.py"
})

# Edit the function
agent.use_tool("str_replace_editor", {
    "command": "str_replace",
    "path": "utils.py",
    "old_str": "def calculate_total(items):\n    return sum(items)",
    "new_str": "def calculate_total(items):\n    return sum(item.price for item in items)"
})
```

### Project Analysis Example

```python
# List project structure
structure = agent.use_tool("list_directory", {
    "path": ".",
    "recursive": True
})

# Search for configuration files
configs = agent.use_tool("glob_search", {
    "pattern": "**/*config*"
})

# Find main entry points
entries = agent.use_tool("grep_search", {
    "pattern": "if __name__ == ['\"]__main__['\"]:",
    "file_pattern": "*.py"
})
```

### Web Research Example

```python
# Search for documentation
search_results = agent.use_tool("web_search", {
    "query": "Flask authentication JWT tutorial"
})

# Fetch specific documentation
docs = agent.use_tool("web_fetch", {
    "url": "https://flask-jwt-extended.readthedocs.io/",
    "extract_content": True
})
```

### Task Coordination Example

```python
# Create sub-agent for specific task
subtask_result = agent.use_tool("task_agent", {
    "task": "Analyze security vulnerabilities in authentication module",
    "working_dir": "./auth",
    "max_iterations": 20
})

# Track progress
agent.use_tool("update_progress", {
    "status": "Security analysis completed",
    "details": subtask_result
})
```

## Tool Configuration

### Global Settings

Tools can be configured globally through command line options:

```bash
# Disable web tools
python -m swe_agent_litellm.main --no-web "Code-only task"

# Disable notebook tools
python -m swe_agent_litellm.main --no-notebooks "Server-side task"
```

### Tool-Specific Parameters

Each tool accepts specific parameters for customization:

#### Grep Search Parameters
- `pattern`: Regular expression pattern
- `file_pattern`: File glob pattern (optional)
- `case_sensitive`: Boolean (default: True)
- `context_lines`: Number of surrounding lines
- `max_results`: Limit number of matches

#### Bash Execution Parameters
- `command`: Shell command to execute
- `timeout`: Maximum execution time
- `capture_output`: Whether to capture stdout/stderr
- `working_dir`: Directory to execute in

#### Web Search Parameters
- `query`: Search terms
- `num_results`: Maximum number of results
- `time_range`: Restrict to recent results
- `site_filter`: Limit to specific domains

## Custom Tool Development

### Creating New Tools

Tools are automatically discovered from the `tools/` directory. To add a new tool:

1. Create a new Python file in `tools/core/` or `tools/domain/`
2. Inherit from `BaseTool`
3. Implement required methods

```python
from ..base_tool import BaseTool

class CustomTool(BaseTool):
    def get_name(self) -> str:
        return "custom_tool"
    
    def get_description(self) -> str:
        return "Description of what this tool does"
    
    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            },
            "required": ["input"]
        }
    
    def execute(self, **kwargs) -> dict:
        # Tool implementation
        return {"success": True, "result": "Tool output"}
```

### Tool Categories

#### Core Tools (`tools/core/`)
- Essential functionality used across all domains
- File operations, execution, basic utilities
- Always available regardless of configuration

#### Domain Tools (`tools/domain/`)
- Specialized tools for specific domains
- Web development, data science, DevOps, etc.
- May require additional dependencies

## Best Practices

### Tool Selection
1. **Start simple**: Use basic tools before complex ones
2. **Combine tools**: Chain tools for complex workflows
3. **Error handling**: Always check tool results
4. **Resource management**: Be mindful of API limits and execution time

### Performance Optimization
1. **Parallel execution**: Use task agents for independent operations
2. **Caching**: Reuse search and fetch results when possible
3. **Scoped operations**: Limit file operations to relevant directories
4. **Batch operations**: Group similar operations together

### Security Considerations
1. **Input validation**: Always validate tool parameters
2. **Path safety**: Ensure file paths are within project bounds
3. **Command injection**: Sanitize bash command inputs
4. **API limits**: Respect rate limits and quotas

For more detailed examples, see our [examples guide](examples.md).