Professional SWE Agent
This project provides a modular, production–ready AI code assistant. It is designed to execute software-engineering tasks by orchestrating a suite of tools such as file editors, pattern searchers, task managers, Jupyter notebook operations and even the ability to spawn sub‑agents for specialised work. The original monolithic script has been refactored into a clean package structure to improve maintainability and ease of use.

Features
Rich tool suite: file creation, editing and search, directory listings, regex search, task management with to‑dos, intelligent summarisation, progress tracking, web search/fetch, Jupyter notebook editing and more.

Persistent state: tasks can be paused and resumed; the agent tracks progress across sessions via a pickle state file and a markdown progress log.

Sub‑agents: complex subtasks can be delegated to child agents that use a restricted subset of tools.

Customisable capabilities: web access and notebook support can be toggled at run time; the CLI exposes flags to disable them.

Verbose logging: configurable verbosity (standard, verbose, debug) and indentation for nested agents via the AgentDisplay class.

Directory structure
go
Copy
Edit
.
├── README.md               – This file.
└── swe_agent_litellm/      – Python package containing the agent implementation with LiteLLM support.
    ├── __init__.py         – Exposes top‑level classes for easy import.
    ├── agent.py            – Implements `ProfessionalSWEAgent` backed by LiteLLM.
    ├── config.py           – Defines the `Config` dataclass including model configuration.
    ├── state.py            – Contains `AgentState`, `ProgressEntry` and `ConversationSummary` dataclasses.
    ├── display.py          – Encapsulates all terminal UI and logging behaviour.
    ├── tools.py            – Defines the tool schema used by the agent.
    └── main.py             – Command‑line interface entry point.
Installation
Clone the repository or extract the provided swe_agent.zip archive.

Create a virtual environment (optional but recommended):

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install the required Python packages:

```bash
pip install litellm duckduckgo-search requests
```

The [litellm](https://github.com/berriai/litellm) library provides a unified
interface for calling multiple large language model providers (OpenAI,
Anthropic, Azure, Mistral, etc.). The optional `duckduckgo-search` package is
used for web search functionality; if you do not need web search you can
omit it and run the agent with the `--no-web` flag.

### Set API keys

The agent relies on environment variables for authentication with the LLM
providers. Depending on which model you intend to use you should set one or
more of the following variables before running the CLI:

- `OPENAI_API_KEY` – used for OpenAI or Azure OpenAI models (e.g. `gpt-4-turbo`).
- `ANTHROPIC_API_KEY` – used for Anthropic models (e.g. `claude-3-5-sonnet-20241022`).
- `MISTRAL_API_KEY` – used for Mistral AI models.

If you provide the `--api-key` argument on the command line, the agent will
assign that value to the appropriate provider environment variable based on
the model name. For example, if you run with `--model gpt-4-turbo` and
provide `--api-key=sk-...`, the agent will set `OPENAI_API_KEY` internally
unless it is already defined.

Usage
You can run the agent through the command‑line interface by using the swe_agent.main module. For example:

bash
Copy
Edit
python -m swe_agent.main "create a README file and initialise a git repository"
The agent will prompt you for guidance when it encounters ambiguous steps or failures. Progress will be written to a file named progress.md in the current working directory. To see all options, run:

bash
Copy
Edit
python -m swe_agent.main --help
Important flags:

--working-dir: Sets the directory the agent operates in (default is the current directory).

--max-iterations: Limits how many loops the agent will perform before stopping.

--debug: Enables verbose debug output.

--no-progress: Disables writing to progress.md.

--no-web: Disables web search and fetch tools (avoids requiring duckduckgo-search).

--no-notebooks: Disables Jupyter notebook editing tools.

To resume a previously interrupted task, pass the task ID returned by the agent:

bash
Copy
Edit
python -m swe_agent.main --resume <task_id>
Extending and testing
The modular architecture makes it straightforward to add new tools or customise behaviour:

To add a new tool, define its JSON schema in ``swe_agent_litellm/tools.py`` and implement a corresponding ``_execute_<toolname>`` method in ``swe_agent_litellm/agent.py``.

The ``swe_agent_litellm/display.py`` class centralises output; adjust it to change how progress and errors are presented.

Unit tests can import individual modules (e.g. from swe_agent import Config, ProfessionalSWEAgent) without executing the entire CLI.

Limitations
The agent depends on external services – namely the language model APIs and optional web search – and therefore requires network connectivity and valid API credentials for the LLM provider(s) of your choice (e.g. OpenAI, Anthropic, Mistral) as well as DuckDuckGo for web search.

The built‑in web search uses DuckDuckGo; you may need to adjust headers or timeouts if search fails.

Large tasks may still hit the maximum iteration limit; use the resume feature to continue work.

License
This project is provided as‑is for demonstration purposes. See LICENSE (if provided) for details.
