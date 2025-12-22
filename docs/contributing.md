# Contributing Guide

We welcome contributions to the Professional SWE Agent! This guide will help you get started.

## Getting Started

### Development Setup

1. **Fork and clone the repository**:
```bash
git clone https://github.com/yourusername/sweagent.git
cd sweagent
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists
```

4. **Set up pre-commit hooks** (if configured):
```bash
pre-commit install
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

Follow the project structure and coding conventions:

```
swe_agent_litellm/
├── main.py              # CLI entry point
├── config.py            # Configuration management
├── agent.py             # Core agent implementation
├── state.py             # State management
├── display.py           # Output formatting
├── tool_registry.py     # Dynamic tool discovery
├── base_tool.py         # Tool base class
└── tools/               # Tool implementations
    ├── core/            # Core tools (bash, file ops, etc.)
    └── domain/          # Domain-specific tools
```

### 3. Testing

Run the test suite:

```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Test with different models
python -m swe_agent_litellm.main --max-iterations 1 --model gpt-4o-mini "Say hello"
```

### 4. Code Quality

Ensure your code meets quality standards:

```bash
# Linting
flake8 swe_agent_litellm/
pylint swe_agent_litellm/

# Type checking
mypy swe_agent_litellm/

# Formatting
black swe_agent_litellm/
isort swe_agent_litellm/
```

## Contribution Types

### 1. Adding New Tools

Create tools in the appropriate directory:

- **Core tools** (`tools/core/`): Essential functionality used across domains
- **Domain tools** (`tools/domain/`): Specialized tools for specific use cases

#### Tool Development Template

```python
from ..base_tool import BaseTool
from typing import Dict, Any

class NewTool(BaseTool):
    """Brief description of what this tool does."""
    
    def get_name(self) -> str:
        """Return the tool name for registration."""
        return "new_tool"
    
    def get_description(self) -> str:
        """Return human-readable description."""
        return "Performs specific operations with clear purpose"
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input parameter description"
                },
                "option": {
                    "type": "boolean",
                    "description": "Optional parameter",
                    "default": False
                }
            },
            "required": ["input"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        try:
            # Implement tool logic here
            result = self._perform_operation(kwargs)
            
            return {
                "success": True,
                "result": result,
                "message": "Operation completed successfully"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Tool execution failed: {e}"
            }
    
    def _perform_operation(self, params: Dict[str, Any]) -> Any:
        """Private method for core tool logic."""
        # Implement the actual functionality
        pass
```

#### Tool Guidelines

1. **Single Responsibility**: Each tool should have one clear purpose
2. **Error Handling**: Always handle errors gracefully
3. **Parameter Validation**: Validate inputs before processing
4. **Documentation**: Include clear docstrings and parameter descriptions
5. **Security**: Sanitize inputs, especially for file operations and command execution

### 2. Improving Existing Tools

When enhancing existing tools:

1. **Maintain backward compatibility**
2. **Add comprehensive tests**
3. **Update documentation**
4. **Consider performance implications**

### 3. Bug Fixes

For bug fixes:

1. **Write a test that reproduces the bug**
2. **Fix the issue**
3. **Ensure the test passes**
4. **Add regression tests if appropriate**

### 4. Documentation

Documentation contributions are highly valued:

- **API documentation**: Update docstrings and API references
- **User guides**: Improve tutorials and examples
- **Configuration guides**: Document new options and features
- **Troubleshooting**: Add solutions for common issues

## Code Standards

### Python Code Style

Follow PEP 8 and these additional guidelines:

```python
# Use type hints
def process_data(input_data: Dict[str, Any]) -> List[str]:
    """Process input data and return results."""
    pass

# Use meaningful variable names
user_authentication_token = get_auth_token()  # Good
token = get_auth_token()  # Less clear

# Document complex logic
def complex_algorithm(data: List[int]) -> int:
    """
    Implement complex sorting algorithm.
    
    Args:
        data: List of integers to sort
        
    Returns:
        Index of the optimal element
        
    Raises:
        ValueError: If data is empty
    """
    # Step 1: Validate input
    if not data:
        raise ValueError("Data cannot be empty")
    
    # Step 2: Apply algorithm logic
    # (explain non-obvious steps)
    pass
```

### Tool Development Standards

1. **Consistent Return Format**:
```python
# Success case
return {
    "success": True,
    "result": actual_result,
    "message": "Description of what happened"
}

# Error case  
return {
    "success": False,
    "error": error_details,
    "message": "User-friendly error description"
}
```

2. **Parameter Schema Standards**:
```python
{
    "type": "object",
    "properties": {
        "required_param": {
            "type": "string",
            "description": "Clear description of what this parameter does"
        },
        "optional_param": {
            "type": "boolean",
            "description": "Optional parameter with default",
            "default": False
        }
    },
    "required": ["required_param"],
    "additionalProperties": False
}
```

### Security Guidelines

1. **Input Validation**: Always validate and sanitize user inputs
2. **Path Safety**: Ensure file operations stay within bounds
3. **Command Injection**: Use subprocess safely for shell commands
4. **API Keys**: Never log or expose API keys
5. **Error Messages**: Don't leak sensitive information in error messages

## Testing

### Writing Tests

1. **Unit Tests**: Test individual tool functionality
```python
import pytest
from swe_agent_litellm.tools.core.new_tool import NewTool

def test_new_tool_basic_functionality():
    """Test basic tool operation."""
    tool = NewTool()
    result = tool.execute(input="test data")
    
    assert result["success"] is True
    assert "result" in result
    assert result["message"] is not None

def test_new_tool_error_handling():
    """Test tool error handling."""
    tool = NewTool()
    result = tool.execute(input="")  # Invalid input
    
    assert result["success"] is False
    assert "error" in result
```

2. **Integration Tests**: Test tools with the agent
```python
def test_tool_with_agent():
    """Test tool integration with agent."""
    config = Config(model="gpt-4o-mini", max_iterations=1)
    agent = Agent(config)
    
    result = agent.run("Use new_tool to process test data")
    assert result["success"] is True
```

### Test Coverage

Aim for high test coverage:

```bash
# Run tests with coverage
pytest --cov=swe_agent_litellm tests/

# Generate coverage report
coverage html
```

## Documentation

### Docstring Standards

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int = 0) -> Dict[str, Any]:
    """
    Brief description of the function.
    
    Longer description with more details about what the function does,
    how it works, and any important considerations.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter with default value
        
    Returns:
        Dictionary containing the results with keys:
        - success (bool): Whether operation succeeded
        - result (Any): The actual result data
        - message (str): Human-readable status message
        
    Raises:
        ValueError: When param1 is empty
        RuntimeError: When operation fails due to external factors
        
    Example:
        >>> result = example_function("test", 5)
        >>> print(result["success"])
        True
    """
    pass
```

### README Updates

When adding significant features, update relevant documentation:

- Main README.md
- Tool-specific documentation
- Configuration examples
- Usage examples

## Submitting Changes

### 1. Prepare Your Pull Request

Before submitting:

1. **Run all tests**: Ensure nothing is broken
2. **Update documentation**: Include relevant doc changes
3. **Add changelog entry**: Describe your changes
4. **Rebase on main**: Ensure clean git history

```bash
git rebase origin/main
```

### 2. Pull Request Description

Use this template for your PR description:

```markdown
## Description
Brief description of the changes and their purpose.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Changes Made
- Specific change 1
- Specific change 2
- Specific change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published
```

### 3. Review Process

1. **Automated checks**: Ensure CI passes
2. **Code review**: Address reviewer feedback
3. **Testing**: Verify functionality across different models
4. **Documentation review**: Ensure docs are clear and accurate

## Release Process

### Version Management

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Changelog

Maintain CHANGELOG.md with:

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerability fixes

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Code Review**: Pull request comments

### Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [LiteLLM Documentation](https://docs.litellm.ai/)

## Recognition

Contributors will be recognized in:
- README acknowledgments
- Release notes
- Contributor list

Thank you for contributing to the Professional SWE Agent! 🚀