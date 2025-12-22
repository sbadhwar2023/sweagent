# API Reference

This page documents the core APIs and interfaces of the Professional SWE Agent.

## Agent Class

### Constructor

```python
from swe_agent_litellm.agent import Agent
from swe_agent_litellm.config import Config

config = Config(
    working_dir="./project",
    model="claude-3-5-sonnet-20241022",
    max_iterations=50
)

agent = Agent(config)
```

### Main Methods

#### `run(task: str) -> dict`

Execute a task and return results.

**Parameters:**
- `task` (str): Description of the task to perform

**Returns:**
- `dict`: Result containing success status, output, and metadata

**Example:**
```python
result = agent.run("Create a Python function to parse CSV files")
print(result['success'])  # True/False
print(result['output'])   # Generated code or error message
```

#### `resume(task_id: str) -> dict`

Resume a previously started task.

**Parameters:**
- `task_id` (str): Unique identifier of the task to resume

**Returns:**
- `dict`: Current task state and continuation result

**Example:**
```python
result = agent.resume("task_12345")
```

## Configuration Class

### Config Parameters

```python
@dataclass
class Config:
    # Core settings
    working_dir: str = "."
    model: str = "claude-3-5-sonnet-20241022"
    fallback_models: List[str] = field(default_factory=list)
    max_iterations: int = 50
    
    # API settings
    api_key: Optional[str] = None
    
    # Feature flags
    enable_web_tools: bool = True
    enable_notebook_tools: bool = True
    enable_progress_tracking: bool = True
    
    # Debug settings
    debug: bool = False
    verbose: bool = False
```

### Configuration Methods

#### `from_env() -> Config`

Create configuration from environment variables.

```python
config = Config.from_env()
```

#### `from_dict(data: dict) -> Config`

Create configuration from dictionary.

```python
config = Config.from_dict({
    "model": "gpt-4o",
    "max_iterations": 100
})
```

## Tool Registry

### BaseTool Interface

All tools inherit from the `BaseTool` class:

```python
from swe_agent_litellm.base_tool import BaseTool

class CustomTool(BaseTool):
    def get_name(self) -> str:
        """Return tool name for registration"""
        return "custom_tool"
    
    def get_description(self) -> str:
        """Return human-readable description"""
        return "Performs custom operations"
    
    def get_parameters(self) -> dict:
        """Return JSON schema for parameters"""
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool with given parameters"""
        return {"success": True, "result": "Output"}
```

### Tool Registration

#### `ToolRegistry.register(tool: BaseTool) -> None`

Manually register a tool:

```python
from swe_agent_litellm.tool_registry import ToolRegistry

registry = ToolRegistry()
registry.register(CustomTool())
```

#### `ToolRegistry.discover() -> List[BaseTool]`

Auto-discover tools from the tools directory:

```python
tools = registry.discover()
```

## Core Tools API

### String Replace Editor

```python
{
    "name": "str_replace_editor",
    "parameters": {
        "command": "str_replace",  # or "view", "create"
        "path": "file/path.py",
        "old_str": "old code",
        "new_str": "new code"
    }
}
```

### Bash Execution

```python
{
    "name": "bash",
    "parameters": {
        "command": "ls -la",
        "timeout": 30
    }
}
```

### Grep Search

```python
{
    "name": "grep_search", 
    "parameters": {
        "pattern": "def.*function",
        "file_pattern": "*.py",
        "context_lines": 3
    }
}
```

### Glob Search

```python
{
    "name": "glob_search",
    "parameters": {
        "pattern": "**/*.js",
        "exclude_patterns": ["node_modules/**"]
    }
}
```

### Web Search

```python
{
    "name": "web_search",
    "parameters": {
        "query": "FastAPI authentication tutorial",
        "num_results": 5
    }
}
```

### Web Fetch

```python
{
    "name": "web_fetch",
    "parameters": {
        "url": "https://docs.python.org",
        "extract_content": True
    }
}
```

## State Management

### State Class

```python
@dataclass
class AgentState:
    task_id: str
    current_iteration: int
    max_iterations: int
    task_description: str
    working_dir: str
    progress: List[dict]
    files_modified: List[str]
    tool_results: List[dict]
    model: str
    created_at: datetime
    updated_at: datetime
```

### State Methods

#### `save_state(state: AgentState) -> None`

Persist state to disk:

```python
from swe_agent_litellm.state import save_state

save_state(current_state)
```

#### `load_state(task_id: str) -> AgentState`

Load state from disk:

```python
from swe_agent_litellm.state import load_state

state = load_state("task_12345")
```

## Progress Tracking

### Progress Entry

```python
@dataclass
class ProgressEntry:
    iteration: int
    action: str
    tool_name: str
    parameters: dict
    result: dict
    timestamp: datetime
    duration: float
```

### Progress Methods

#### `add_progress_entry(entry: ProgressEntry) -> None`

Add a new progress entry:

```python
from swe_agent_litellm.progress import add_progress_entry

entry = ProgressEntry(
    iteration=1,
    action="File created",
    tool_name="str_replace_editor",
    parameters={"command": "create", "path": "new_file.py"},
    result={"success": True},
    timestamp=datetime.now(),
    duration=1.5
)

add_progress_entry(entry)
```

#### `generate_progress_report() -> str`

Generate markdown progress report:

```python
from swe_agent_litellm.progress import generate_progress_report

report = generate_progress_report()
```

## Error Handling

### Custom Exceptions

```python
class SWEAgentError(Exception):
    """Base exception for SWE Agent"""
    pass

class ModelError(SWEAgentError):
    """Model-related errors"""
    pass

class ToolError(SWEAgentError):
    """Tool execution errors"""
    pass

class ConfigError(SWEAgentError):
    """Configuration errors"""
    pass
```

### Error Handling Examples

```python
try:
    result = agent.run("Complex task")
except ModelError as e:
    print(f"Model error: {e}")
    # Try fallback model
except ToolError as e:
    print(f"Tool error: {e}")
    # Retry with different parameters
except SWEAgentError as e:
    print(f"Agent error: {e}")
    # Handle general errors
```

## CLI Integration

### Main Entry Point

```python
from swe_agent_litellm.main import main

# Programmatic usage
if __name__ == "__main__":
    main([
        "Create a Flask app with authentication",
        "--model", "gpt-4o",
        "--max-iterations", "50"
    ])
```

### Command Line Arguments

The CLI supports these arguments through `argparse`:

```python
parser.add_argument("task", nargs="?", help="Task description")
parser.add_argument("--working-dir", default=".", help="Working directory")
parser.add_argument("--model", default="claude-3-5-sonnet-20241022")
parser.add_argument("--models", help="Comma-separated fallback models")
parser.add_argument("--max-iterations", type=int, default=50)
parser.add_argument("--api-key", help="API key override")
parser.add_argument("--debug", action="store_true")
parser.add_argument("--resume", help="Resume task by ID")
parser.add_argument("--no-progress", action="store_true")
parser.add_argument("--no-web", action="store_true")
parser.add_argument("--no-notebooks", action="store_true")
```

## LiteLLM Integration

### Model Configuration

```python
from litellm import completion

# Configure custom models
completion(
    model="azure/gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    api_key="your-key",
    api_base="https://your-endpoint.openai.azure.com"
)
```

### Provider Settings

```python
# Environment variables for different providers
os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
os.environ["AZURE_API_KEY"] = "..."
os.environ["AZURE_API_BASE"] = "https://..."
```

## Utilities

### File Utilities

```python
from swe_agent_litellm.utils import (
    read_file_safe,
    write_file_safe,
    backup_file,
    find_project_root
)

# Safe file operations with error handling
content = read_file_safe("path/to/file.py")
write_file_safe("output.py", modified_content)
```

### String Utilities

```python
from swe_agent_litellm.utils import (
    extract_code_blocks,
    format_diff,
    sanitize_filename
)

# Extract code from markdown
code_blocks = extract_code_blocks(markdown_text)
```

## Examples

### Basic Agent Usage

```python
from swe_agent_litellm.agent import Agent
from swe_agent_litellm.config import Config

# Create configuration
config = Config(
    model="claude-3-5-sonnet-20241022",
    max_iterations=25,
    enable_web_tools=True
)

# Initialize agent
agent = Agent(config)

# Run task
result = agent.run(
    "Create a REST API for user management with FastAPI"
)

if result['success']:
    print("Task completed successfully!")
    print(f"Files created: {result['files_created']}")
else:
    print(f"Task failed: {result['error']}")
```

### Custom Tool Development

```python
from swe_agent_litellm.base_tool import BaseTool

class DatabaseTool(BaseTool):
    def get_name(self):
        return "database_query"
    
    def get_description(self):
        return "Execute database queries safely"
    
    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "database": {"type": "string", "default": "main"}
            },
            "required": ["query"]
        }
    
    def execute(self, query: str, database: str = "main"):
        # Implement database connection and query execution
        # with proper error handling and security measures
        return {"success": True, "rows": [], "count": 0}

# Register with agent
agent.register_tool(DatabaseTool())
```

For more examples, see our [examples guide](examples.md).