# Examples and Use Cases

This page provides practical examples of using the Professional SWE Agent for various software engineering tasks.

## Basic Examples

### Simple Code Generation

```bash
python -m swe_agent_litellm.main "Create a Python function to calculate fibonacci numbers"
```

### File Analysis

```bash
python -m swe_agent_litellm.main --working-dir ./my-project "Analyze this codebase and identify potential bugs"
```

### Quick Refactoring

```bash
python -m swe_agent_litellm.main "Refactor the user authentication module to use modern security practices"
```

## Advanced Examples

### Feature Development with Multiple Models

```bash
python -m swe_agent_litellm.main \
  --model claude-3-5-sonnet-20241022 \
  --models gpt-4o,mistral/mistral-large-latest \
  --max-iterations 100 \
  "Add JWT-based authentication to this Flask application with refresh token support"
```

### Large Codebase Analysis

```bash
python -m swe_agent_litellm.main \
  --working-dir /path/to/large/project \
  --max-iterations 50 \
  --no-web \
  "Generate comprehensive documentation for all API endpoints"
```

### Database Migration

```bash
python -m swe_agent_litellm.main \
  --model gpt-4o \
  "Create database migration scripts to add user profiles with proper relationships"
```

## Domain-Specific Examples

### Web Development

#### React Component Creation
```bash
python -m swe_agent_litellm.main \
  "Create a reusable React component for a product card with TypeScript support"
```

#### API Development
```bash
python -m swe_agent_litellm.main \
  "Build a RESTful API for user management with proper error handling and validation"
```

#### Frontend Testing
```bash
python -m swe_agent_litellm.main \
  --working-dir ./frontend \
  "Add comprehensive Jest tests for all React components"
```

### Data Science

#### Data Analysis Script
```bash
python -m swe_agent_litellm.main \
  --no-web \
  "Create a Python script to analyze sales data and generate monthly reports"
```

#### Machine Learning Pipeline
```bash
python -m swe_agent_litellm.main \
  --max-iterations 80 \
  "Build a complete ML pipeline for customer churn prediction with model validation"
```

### DevOps and Infrastructure

#### Docker Configuration
```bash
python -m swe_agent_litellm.main \
  "Create Docker configuration for this Node.js application with multi-stage builds"
```

#### CI/CD Pipeline
```bash
python -m swe_agent_litellm.main \
  "Set up GitHub Actions workflow for automated testing and deployment"
```

#### Monitoring Setup
```bash
python -m swe_agent_litellm.main \
  "Add application monitoring with proper logging and health checks"
```

## Workflow Examples

### Bug Investigation and Fix

```bash
# Start investigation
python -m swe_agent_litellm.main \
  --working-dir ./buggy-app \
  "Investigate why users are getting 500 errors on login"

# Continue with specific fix
python -m swe_agent_litellm.main \
  --resume task_123 \
  "Implement the authentication bug fix and add regression tests"
```

### Code Review and Improvement

```bash
python -m swe_agent_litellm.main \
  --model claude-3-5-sonnet-20241022 \
  "Review this pull request and suggest improvements for performance and security"
```

### Legacy Code Modernization

```bash
python -m swe_agent_litellm.main \
  --max-iterations 150 \
  "Modernize this Python 2.7 codebase to Python 3.11 with type hints"
```

## Interactive Mode Examples

### Guided Development

```bash
# Start without a task for interactive mode
python -m swe_agent_litellm.main

# Agent will prompt for tasks interactively:
# > What would you like me to help you with?
# User: Help me implement user authentication
# > I'll help you implement user authentication. What framework are you using?
# User: FastAPI with SQLAlchemy
# > Great! I'll create a complete authentication system...
```

### Iterative Debugging

```bash
python -m swe_agent_litellm.main \
  --debug \
  "Debug why my tests are failing and fix the issues one by one"
```

## Multi-Step Project Examples

### E-commerce Platform

```bash
# Step 1: Architecture
python -m swe_agent_litellm.main \
  "Design the architecture for a multi-vendor e-commerce platform"

# Step 2: Core Models
python -m swe_agent_litellm.main \
  --resume task_456 \
  "Implement the core database models and relationships"

# Step 3: API Layer
python -m swe_agent_litellm.main \
  --resume task_456 \
  "Build the REST API with proper validation and documentation"

# Step 4: Frontend Integration
python -m swe_agent_litellm.main \
  --resume task_456 \
  "Create React components for the vendor dashboard"
```

### Microservices Migration

```bash
# Analysis phase
python -m swe_agent_litellm.main \
  --working-dir ./monolith \
  "Analyze this monolithic application and propose microservices architecture"

# Service extraction
python -m swe_agent_litellm.main \
  "Extract the user service from the monolith with proper API boundaries"

# Inter-service communication
python -m swe_agent_litellm.main \
  "Implement messaging between microservices using RabbitMQ"
```

## Performance and Optimization

### Model Selection by Task Type

| Task Type | Recommended Model | Reason |
|-----------|-------------------|--------|
| Quick fixes | `gpt-4o-mini` | Fast and cost-effective |
| Complex architecture | `claude-3-5-sonnet-20241022` | Superior reasoning |
| Code generation | `gpt-4o` | Excellent code quality |
| Documentation | `claude-3-haiku-20240307` | Good at explanations |
| Debugging | `claude-3-5-sonnet-20241022` | Strong analytical skills |

### Iteration Management

```bash
# Quick tasks
python -m swe_agent_litellm.main --max-iterations 5 "Fix this typo in the README"

# Medium complexity
python -m swe_agent_litellm.main --max-iterations 25 "Add input validation to the API"

# Complex projects
python -m swe_agent_litellm.main --max-iterations 200 "Build complete user management system"
```

## Error Handling Examples

### Graceful Fallback

```bash
# Primary model with fallbacks
python -m swe_agent_litellm.main \
  --model claude-3-5-sonnet-20241022 \
  --models gpt-4o-mini,mistral/mistral-large-latest \
  "Complex task with fallback support"
```

### Recovery from Interruptions

```bash
# If a task is interrupted, resume it
python -m swe_agent_litellm.main --resume task_789

# Check progress file
cat progress.md
```

## Tips for Success

### 1. Be Specific
```bash
# Vague
python -m swe_agent_litellm.main "Fix the app"

# Specific  
python -m swe_agent_litellm.main "Fix the authentication timeout issue in login.py by extending session duration"
```

### 2. Provide Context
```bash
# Include relevant context
python -m swe_agent_litellm.main \
  --working-dir ./backend \
  "Add rate limiting to the API using Flask-Limiter with Redis backend"
```

### 3. Use Appropriate Models
```bash
# For complex reasoning
--model claude-3-5-sonnet-20241022

# For speed and cost efficiency  
--model gpt-4o-mini

# For reliability
--models gpt-4o,claude-3-5-sonnet-20241022,mistral/mistral-large-latest
```

### 4. Monitor Progress
- Check `progress.md` files regularly
- Use `--debug` for detailed logging
- Resume long-running tasks when needed

For more specific guidance, see our [configuration guide](configuration.md) and [troubleshooting documentation](troubleshooting.md).