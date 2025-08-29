"""Implementation of the Professional SWE Agent.

This module contains the :class:`ProfessionalSWEAgent` class which
orchestrates configuration, tool definitions, state management, user
interaction and the core execution loop. The agent is capable of
performing software‑engineering tasks by delegating work to a suite
of tools and by leveraging large language models (LLMs) through the
`litellm` library. Compared to the original monolithic implementation
the design here is modular and provider‑agnostic: it supports
multiple LLM backends such as OpenAI, Anthropic, Azure, Mistral and
others via a unified interface and can fall back across models if
requests fail. The agent responds to user tasks, invokes tools when
function calls are returned by the LLM, handles errors gracefully,
generates summaries to manage long conversations, spawns sub‑agents
for complex subtasks and persists its internal state for recovery.
"""

from __future__ import annotations

import os
import json
import pickle
import glob
import re
import datetime
import requests
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

# Optional imports for third-party services. These libraries may not be
# present in all environments; therefore they are loaded lazily. If
# unavailable, the agent will raise an informative error when used.
try:
    # LiteLLM provides a unified interface for multiple LLM providers.
    import litellm  # type: ignore[import-not-found]
except Exception:
    litellm = None  # type: ignore[assignment]
try:
    from duckduckgo_search import DDGS  # type: ignore[import-not-found]
except Exception:
    DDGS = None  # type: ignore[assignment]

from .config import Config
from .state import AgentState, ProgressEntry, ConversationSummary
from .display import AgentDisplay
from .tool_registry import DynamicToolRegistry


class ProfessionalSWEAgent:
    """Professional SWE Agent - Complete AI code assistant with all capabilities.

    The agent orchestrates the use of a suite of tools to perform
    software engineering tasks such as file editing, searching,
    executing commands, spawning sub-agents, fetching web content,
    managing notebooks and tracking progress. It can persist and
    resume tasks, create intelligent summaries to manage long
    conversations and handle errors with user guidance.
    """

    def __init__(self, config: Config, progress_callback=None, indent_level: int = 0):
        self.config = config
        # Ensure litellm is available
        if litellm is None:
            raise ImportError(
                "The litellm library is required but not installed. Please install it to use the agent."
            )
        # Assign configuration and prepare the unified LLM interface.
        # Configure environment variables for API keys based on the chosen model(s).
        self._configure_api_keys()
        # Instantiate dynamic tool registry. It will discover tools from the
        # swe_agent_litellm.tools.core and swe_agent_litellm.tools.domain packages.
        self.registry = DynamicToolRegistry(
            [
                "swe_agent_litellm.tools.core",
                "swe_agent_litellm.tools.domain",
            ],
            config=self.config,
        )
        self.registry.load_tools()
        # Tool handlers mapping: name -> BaseTool instance
        self.tool_handlers = self.registry.tools
        # Convert tools into schema definitions for LLM function calling
        self.tools = self.registry.get_tool_schemas()
        self.llm_tools: List[Dict[str, Any]] = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in self.tools
        ]
        self.state: Optional[AgentState] = None
        self.active_sub_agents = 0
        self.progress_callback = progress_callback
        self.indent_level = indent_level

        # Initialize display system with verbosity control
        verbosity = "debug" if config.debug_mode else config.verbosity
        self.display = AgentDisplay(verbosity_level=verbosity, indent_level=indent_level)

        # Filter tools based on configuration. The registry may already
        # perform filtering, but we ensure the list of tools and
        # handlers reflect the agent's config. When a tool is
        # removed from the list we also remove it from
        # ``self.tool_handlers`` so that it cannot be invoked.
        if not config.enable_web:
            disabled = {"web_fetch", "web_search"}
            self.tools = [t for t in self.tools if t["name"] not in disabled]
            for name in disabled:
                self.tool_handlers.pop(name, None)
        if not config.enable_notebooks:
            self.tools = [t for t in self.tools if t["name"] != "notebook_edit"]
            self.tool_handlers.pop("notebook_edit", None)

        # Rebuild llm_tools after filtering to ensure only enabled tools are exposed to the LLM
        self.llm_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in self.tools
        ]

        # Change to working directory
        if config.working_dir != ".":
            os.chdir(config.working_dir)

        # State and progress file paths
        self.state_path = Path(config.working_dir) / config.state_file
        self.progress_path = Path(config.working_dir) / config.progress_file

        # Determine list of models to try. If multiple models are provided
        # they will be attempted in order until one succeeds.
        if self.config.models:
            self.models = self.config.models
        else:
            self.models = [self.config.model]
        # Configure tool support for models without native function calling.
        self._prepare_function_calling_support()

        # Show header
        self.display.show_header(os.getcwd(), len(self.tools))
        # Show tool categories in verbose/debug modes
        if self.display.verbosity in ["verbose", "debug"]:
            print(f"🔧 Tool Categories:")
            print(f"   📄 Files: Edit, Find, List")
            print(f"   🔍 Search: Search")
            print(f"   ⚡ Execute: Bash")
            print(f"   📝 Management: TodoWrite, CreateSummary, UpdateProgress")
            print(f"   🤖 Advanced: TaskAgent, AskUser")
            if config.enable_web:
                print(f"   🌐 Web: WebFetch, WebSearch")
            if config.enable_notebooks:
                print(f"   📓 Notebooks: NotebookEdit")
        # Debug logs
        self.display.debug_log(f"Progress file: {self.progress_path}")
        self.display.debug_log(f"Auto-summarization: Every {config.summarization_threshold} iterations")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def execute_task(self, task: str, resume_task_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a user‑defined task using the configured language model(s).

        This method forms the main control loop of the agent. It optionally
        resumes a previous task, constructs the initial conversation
        context and iterates until either the task is completed or the
        maximum iteration count is reached. At each iteration the agent
        calls the underlying large language model via :func:`_call_llm` with
        tool definitions, parses any tool calls from the response and
        executes them, then feeds the results back into the model. The
        conversation history is periodically summarised to manage context
        length. Progress is persisted between iterations and errors are
        handled with user guidance when necessary.

        Parameters
        ----------
        task: str
            Description of the task to perform. Ignored when resuming
            from a previous state.
        resume_task_id: Optional[str]
            Identifier of a previously saved task state to load.

        Returns
        -------
        Dict[str, Any]
            Structured result describing success, iteration count,
            final response, tools used, and metadata about files and
            sub‑agents.
        """
        # Try to resume if a task ID is provided
        if resume_task_id:
            if self._load_state(resume_task_id):
                self.display.show_status("Resuming task", self.state.original_task)
                self.display.debug_log(f"Completed steps: {len(self.state.completed_steps)}")
                self.display.debug_log(f"Current step: {self.state.current_step}")
                task = self.state.original_task
            else:
                self.display.show_error(f"Could not resume task {resume_task_id}", "Starting new task instead")

        # Initialize state if not already loaded
        if not self.state:
            import hashlib
            task_id = hashlib.md5(task.encode()).hexdigest()[:8]
            self.state = AgentState(
                task_id=task_id,
                original_task=task,
                completed_steps=[],
                current_step="Starting comprehensive task analysis",
                error_history=[],
                iteration_count=0,
                last_successful_operation="",
                working_context={},
            )
            # Initialize progress file
            if self.config.progress_tracking:
                self._initialize_progress_md()

        self.display.debug_log(f"Task ID: {self.state.task_id}")
        self.display.show_task_start(task)

        # Build system prompt
        system_prompt = self._build_professional_system_prompt()
        # Initialize conversation with optional summary context
        messages = self._initialize_conversation(system_prompt, task)

        max_iterations = self.config.max_iterations

        while self.state.iteration_count < max_iterations:
            try:
                self.display.debug_log(f"Iteration {self.state.iteration_count + 1}")
                self.display.debug_log(f"Current step: {self.state.current_step}")

                # Summarize periodically
                if (
                    self.state.iteration_count > 0
                    and self.state.iteration_count % self.config.summarization_threshold == 0
                ):
                    self.display.show_status("Creating intelligent summary", f"after {self.state.iteration_count} iterations")
                    self._create_intelligent_summary(messages)
                    messages = self._compress_conversation_with_summary(messages)

                # Call the LLM and receive a response. This may include tool calls.
                response = self._call_llm(messages, tools=self.llm_tools, max_tokens=4000)
                # Extract the assistant's message. LiteLLM normalises the structure to align
                # with the OpenAI chat format. The first choice is used.
                assistant = response.choices[0].message  # type: ignore[index]
                # Append the assistant message to the conversation for context. Some
                # providers return ``None`` for the content when a tool call is
                # requested; normalise this to an empty string. Preserve the
                # ``tool_calls`` property when present so that subsequent messages
                # with role ``tool`` are correctly recognised by the API.
                assistant_dict: Dict[str, Any] = {
                    "role": assistant.role,
                    "content": assistant.content or "",
                }
                tool_calls = getattr(assistant, "tool_calls", None)
                if tool_calls:
                    assistant_dict["tool_calls"] = tool_calls
                messages.append(assistant_dict)

                # Determine if any tools were requested via function calls. The field
                # ``tool_calls`` is present on the message when function calling is
                # supported; each entry contains the function name, arguments and an ID.
                tool_calls = getattr(assistant, "tool_calls", None)
                if tool_calls:
                    # For each requested tool, execute it and append the result as a
                    # dedicated tool message. After executing all tools the agent
                    # continues to the next iteration to send the results back to the model.
                    for call in tool_calls:
                        try:
                            tool_name: str = call["function"]["name"]
                            tool_args_str: str = call["function"].get("arguments", "{}")
                            # Parse arguments JSON string; fall back to empty dict on error
                            try:
                                tool_input: Dict[str, Any] = json.loads(tool_args_str) or {}
                            except Exception:
                                tool_input = {}
                            # Use Optional[str] instead of PEP 604 union for Python < 3.10
                            tool_id: Optional[str] = call.get("id")
                        except Exception:
                            # If the call structure is unexpected, skip this call
                            continue
                        # Display tool invocation
                        params_str = self._format_tool_params(tool_input)
                        self.display.show_tool_start(tool_name, params_str)
                        # Execute the tool and capture the result
                        result = self._execute_professional_tool(tool_name, tool_input)
                        # If the tool is interactive, request guidance from user when
                        # appropriate
                        if (
                            tool_name == "ask_user_step"
                            and result.get("success")
                            and tool_input.get("status") in ["failed", "needs_guidance"]
                        ):
                            user_guidance = self._get_user_guidance(tool_input, result)
                            result["output"] = user_guidance
                            self._process_user_guidance(user_guidance, tool_input)
                        # Display tool result
                        self.display.show_tool_result(tool_name, params_str, result)
                        # Stream progress to callback if provided
                        if self.progress_callback:
                            self.progress_callback(tool_name, params_str, result)
                        # Track progress for successful operations
                        if result.get("success"):
                            self._track_comprehensive_progress(tool_name, tool_input, result)
                        # Append the tool result back into conversation as a tool message
                        messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": result.get("output", "") if result.get("success") else f"Error: {result.get('error', 'Unknown error')}",
                            "tool_call_id": tool_id,
                        })
                    # Increment iteration and persist state after executing tools. The loop
                    # continues which will call the model again with the tool results.
                    self.state.iteration_count += 1
                    self._save_state()
                    continue

                # No tools were requested; this is likely the final response. Present
                # the assistant's content to the user, summarise progress and ask
                # whether the task is complete.
                final_response = assistant.content or "Task completed"
                print(f"💭 {final_response}")
                # Create a completion summary
                self._create_completion_summary()
                # Prompt the user to confirm completion
                print("\n❓ Is the overall task complete? (y/n/continue)")
                user_input = input("Response: ").strip().lower()
                if user_input == "y":
                    self._finalize_progress_md()
                    self._cleanup_state()
                    return {
                        "success": True,
                        "iterations": self.state.iteration_count + 1,
                        "final_response": final_response,
                        "task_id": self.state.task_id,
                        "tools_used": len(self.tools),
                        "files_created": len(self.state.files_tracking),
                        "sub_agents_spawned": len(self.state.sub_agent_results),
                    }
                elif user_input == "n":
                    feedback = input("What still needs to be done? ")
                    messages.append({"role": "user", "content": f"Task not complete. User feedback: {feedback}"})
                else:
                    messages.append({"role": "user", "content": "Please continue working on the task with your full capabilities."})

                # Increment iteration and save state at the end of the iteration
                self.state.iteration_count += 1
                self._save_state()

            except Exception as e:
                print(f"❌ Error in iteration {self.state.iteration_count + 1}: {e}")
                # Record error context
                error_record = {
                    "iteration": self.state.iteration_count + 1,
                    "error": str(e),
                    "step": self.state.current_step,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "context": self._get_comprehensive_context_summary(),
                    "tools_available": [t["name"] for t in self.tools],
                }
                self.state.error_history.append(error_record)
                # Handle error with recovery options
                recovery_action = self._handle_error_with_full_context(e, messages)
                if recovery_action == "abort":
                    self._save_state()
                    return {
                        "success": False,
                        "iterations": self.state.iteration_count + 1,
                        "error": str(e),
                        "task_id": self.state.task_id,
                        "resume_possible": True,
                        "tools_used": len(self.tools),
                        "comprehensive_state_saved": True,
                    }
                elif recovery_action == "retry":
                    messages.append({
                        "role": "user",
                        "content": f"Error occurred: {e}. Please retry using your full tool suite and intelligence based on comprehensive progress so far.",
                    })
                # Update iteration and save state after error
                self.state.iteration_count += 1
                self._save_state()

        # Reached max iterations
        self.display.show_status("Max iterations reached, creating final summary")
        self._create_completion_summary()
        self._save_state()
        return {
            "success": False,
            "iterations": max_iterations,
            "error": "Max iterations reached",
            "task_id": self.state.task_id,
            "resume_possible": True,
            "comprehensive_capabilities": True,
            "tools_available": len(self.tools),
        }

    # -------------------------------------------------------------------------
    # Private helper methods
    # -------------------------------------------------------------------------
    def _build_professional_system_prompt(self) -> str:
        """Build the system prompt describing all capabilities and context."""
        # Precompute capability descriptions that depend on configuration to avoid
        # f-string expressions containing newline characters. f-strings cannot
        # include unescaped newlines inside their expression braces.
        if self.config.enable_web:
            web_capabilities = (
                "\n- web_fetch: Fetch documentation, examples, tutorials\n"
                "- web_search: Search for solutions and libraries"
            )
        else:
            web_capabilities = "Disabled"
        if self.config.enable_notebooks:
            notebook_capabilities = "\n- notebook_edit: Full Jupyter notebook support"
        else:
            notebook_capabilities = "Disabled"
        base_prompt = (
            "You are a Professional Software Engineering Assistant with comprehensive capabilities.\n\n"
            "PROFESSIONAL CAPABILITIES:\n"
            "You have access to the complete professional tool suite for software engineering:\n\n"
            "📄 FILE OPERATIONS:\n"
            "- str_replace_editor: Create, read, edit files with range viewing\n"
            "- glob_search: Find files using patterns (**/*.py, src/**/*.js)\n"
            "- list_directory: Rich directory exploration with metadata\n\n"
            "🔍 SEARCH & ANALYSIS:\n"
            "- grep_search: Regex search across files with context\n"
            "- task_agent: Spawn specialized sub-agents for complex analysis\n\n"
            "⚡ EXECUTION & AUTOMATION:\n"
            "- bash: Execute commands with intelligent timeout handling\n\n"
            "📝 PROJECT MANAGEMENT:\n"
            "- todo_write: Create interactive task lists with progress tracking\n"
            "- create_summary: Intelligent context summarization\n"
            "- update_progress_md: Comprehensive progress documentation\n\n"
            "💬 USER INTERACTION:\n"
            "- ask_user_step: Get user guidance on failures and decisions\n\n"
            f"🌐 WEB & RESEARCH: {web_capabilities}\n\n"
            f"📓 DEVELOPMENT ENVIRONMENTS: {notebook_capabilities}\n\n"
            "INTELLIGENT BEHAVIOR:\n"
            "1. **Comprehensive Task Analysis** - Use full tool suite to understand requirements\n"
            "2. **Systematic Execution** - Break down complex tasks with todo_write\n"
            "3. **Intelligent Search** - Use glob_search and grep_search to understand codebases\n"
            "4. **Research Integration** - Leverage web tools for solutions and documentation\n"
            "5. **Sub-agent Delegation** - Use task_agent for specialized complex analysis\n"
            "6. **Progress Transparency** - Update progress.md and create summaries\n"
            "7. **Error Recovery** - Handle failures gracefully with user guidance\n"
            "8. **Context Management** - Use summarization to maintain long-term context\n\n"
            "PERSISTENCE & RECOVERY:\n"
            "- State is automatically saved after each major step\n"
            "- You can resume from any interruption point\n"
            "- Build on previous work instead of restarting\n"
            "- Maintain comprehensive context across sessions"
        )
        # Append previous summary context if available
        if self.state and self.state.conversation_summaries:
            latest_summary = self.state.conversation_summaries[-1]
            context = (
                "\n\nPREVIOUS COMPREHENSIVE PROGRESS:\n"
                f"📝 Key accomplishments: {latest_summary.key_accomplishments}\n"
                f"🎯 Current focus: {latest_summary.current_focus}\n"
                f"📁 Files created/modified: {latest_summary.files_created_modified}\n"
                f"🛠️ Errors resolved: {latest_summary.errors_resolved}\n"
                f"➡️ Next steps: {latest_summary.next_steps}\n"
                f"🤖 Sub-agent results: {len(self.state.sub_agent_results)} completed\n\n"
                "Continue building on this comprehensive progress."
            )
            base_prompt += context
        return base_prompt + f"\n\nWorking directory: {os.getcwd()}\nTools available: {len(self.tools)}"

    # -------------------------------------------------------------------------
    # Unified LLM helper methods
    # -------------------------------------------------------------------------
    def _configure_api_keys(self) -> None:
        """Set environment variables for API keys based on the chosen model(s).

        The agent accepts a single ``api_key`` for backwards compatibility
        but may need to set provider‑specific environment variables (e.g.
        ``OPENAI_API_KEY`` or ``ANTHROPIC_API_KEY``). If the relevant
        environment variable is already defined, the value from the
        configuration is not used to override it. This heuristic is
        intentionally simple; additional providers can be added here as
        needed.
        """
        # Nothing to configure if no api_key provided
        if not self.config.api_key:
            return
        # Determine all models to inspect
        candidate_models: List[str] = []
        if self.config.models:
            candidate_models = self.config.models
        elif self.config.model:
            candidate_models = [self.config.model]
        # For each model guess the provider and set env var if missing
        for model in candidate_models:
            lower_model = model.lower()
            # OpenAI or Azure OpenAI models often contain "gpt" or "openai" or "azure"
            if any(term in lower_model for term in ["gpt", "openai", "azure"]):
                if not os.getenv("OPENAI_API_KEY"):
                    os.environ["OPENAI_API_KEY"] = self.config.api_key  # pragma: no cover - environment side effect
            # Anthropic models usually contain "claude" or "anthropic"
            if any(term in lower_model for term in ["claude", "anthropic"]):
                if not os.getenv("ANTHROPIC_API_KEY"):
                    os.environ["ANTHROPIC_API_KEY"] = self.config.api_key  # pragma: no cover
            # Additional providers (e.g. "mistral", "llama") could be added here

    def _prepare_function_calling_support(self) -> None:
        """Enable function calling for models lacking native support.

        LiteLLM exposes a global flag ``add_function_to_prompt`` that
        instructs the library to embed tool definitions directly in the
        prompt for providers which do not support the OpenAI function
        calling API. This helper checks each configured model and
        activates the flag if any model does not support function
        calling.
        """
        try:
            # Guard against missing litellm import
            if litellm is None:
                return
            # Reset to False by default; will enable if any model lacks support
            setattr(litellm, "add_function_to_prompt", False)
            # Iterate over all configured models
            models_to_check = self.config.models or [self.config.model]
            for model in models_to_check:
                try:
                    supports = litellm.supports_function_calling(model=model)
                except Exception:
                    supports = False
                if not supports:
                    setattr(litellm, "add_function_to_prompt", True)
                    break
        except Exception:
            # Silently ignore errors; default behaviour will be used
            pass

    def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        **extra_params: Any,
    ) -> Any:
        """Invoke the LLM using the configured models with optional fallback.

        Parameters
        ----------
        messages: List[Dict[str, Any]]
            Conversation history in the OpenAI chat format.
        tools: Optional[List[Dict[str, Any]]]
            Tool definitions formatted for the LLM. When provided the LLM
            will be asked to call tools when appropriate.
        max_tokens: Optional[int]
            Maximum number of tokens in the response. If ``None`` the
            provider default is used.
        extra_params: dict
            Additional keyword arguments passed through to ``litellm.completion``.

        Returns
        -------
        Any
            The response object returned by ``litellm.completion``.

        Raises
        ------
        RuntimeError
            If all configured models fail to return a response.
        """
        last_exception: Optional[Exception] = None
        # Iterate over each configured model to attempt completion
        for model in self.models:
            try:
                params: Dict[str, Any] = {"model": model, "messages": messages}
                if tools:
                    params["tools"] = tools
                    # Ask the model to decide when to call tools automatically
                    params["tool_choice"] = "auto"
                if max_tokens is not None:
                    params["max_tokens"] = max_tokens
                # Merge any caller‑supplied parameters
                params.update(extra_params)
                # Make the request
                response = litellm.completion(**params)  # type: ignore[misc]
                return response
            except Exception as e:
                last_exception = e
                # Log the failure and try the next model
                self.display.debug_log(f"LLM call failed for model {model}: {e}")
                continue
        # All models failed; propagate the last exception
        raise RuntimeError(f"All configured LLM models failed: {last_exception}")

    def _execute_professional_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Route execution to the appropriate tool implementation.

        When using the dynamic registry, look up the tool by name
        and call its ``run`` method. If the tool is not known,
        return an error. Any exceptions raised by the tool
        execution will be caught and returned as errors.
        """
        try:
            handler = self.tool_handlers.get(tool_name)
            if handler:
                return handler.run(tool_input, agent=self)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Individual tool implementations
    # -------------------------------------------------------------------------
    def _execute_enhanced_bash(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a bash command with intelligent timeout handling."""
        # Adjust timeout based on type of command
        if any(cmd in command.lower() for cmd in ["install", "pip", "npm", "apt", "yum", "brew"]):
            timeout = min(300, timeout * 10)
        elif any(cmd in command.lower() for cmd in ["git clone", "wget", "curl", "download"]):
            timeout = min(180, timeout * 6)
        elif any(cmd in command.lower() for cmd in ["test", "pytest", "npm test", "make test"]):
            timeout = min(120, timeout * 4)
        try:
            print(f"  🔧 Running: {command}")
            if timeout > 60:
                print(f"  ⏱️ Extended timeout: {timeout}s for {command.split()[0]} operations")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd(),
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            success = result.returncode == 0
            if success:
                self.state.last_successful_operation = f"bash: {command[:50]}..."
                self._scan_for_new_files(command)
            return {
                "success": success,
                "output": output or "(No output)",
                "returncode": result.returncode,
                "command_type": self._classify_command(command),
                "timeout_used": timeout,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_enhanced_str_replace_editor(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Perform file operations including create, view and replace."""
        command = tool_input["command"]
        path = tool_input["path"]
        try:
            if command == "create":
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                content = tool_input.get("file_text", "")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                # Track file creation
                self.state.files_tracking[path] = {
                    "created": datetime.datetime.now().isoformat(),
                    "size": len(content),
                    "lines": content.count('\n') + 1,
                    "action": "created",
                    "language": self._detect_language(path),
                }
                self.state.last_successful_operation = f"Created: {path}"
                return {
                    "success": True,
                    "output": f"Created file: {path} ({len(content)} chars, {content.count(chr(10)) + 1} lines)",
                }
            elif command == "view":
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {
                    "success": True,
                    "output": content,
                    "file_info": {
                        "size": len(content),
                        "lines": content.count('\n') + 1,
                        "language": self._detect_language(path),
                    },
                }
            elif command == "view_range":
                start_line, end_line = tool_input["view_range"]
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                content = "".join(lines[start_line - 1 : end_line])
                return {"success": True, "output": content}
            elif command == "str_replace":
                with open(path, "r", encoding="utf-8") as f:
                    original_content = f.read()
                old_str = tool_input["old_str"]
                new_str = tool_input["new_str"]
                if old_str not in original_content:
                    return {
                        "success": False,
                        "error": f"Text not found in {path}: {old_str[:50]}...",
                    }
                new_content = original_content.replace(old_str, new_str)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                # Track modification
                self.state.files_tracking[path] = {
                    "modified": datetime.datetime.now().isoformat(),
                    "size": len(new_content),
                    "lines": new_content.count('\n') + 1,
                    "action": "modified",
                    "language": self._detect_language(path),
                    "changes": {
                        "old_size": len(original_content),
                        "new_size": len(new_content),
                        "diff": len(new_content) - len(original_content),
                    },
                }
                self.state.last_successful_operation = f"Modified: {path}"
                return {
                    "success": True,
                    "output": f"Updated {path} (size changed by {len(new_content) - len(original_content)} chars)",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_glob_search(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files matching a glob pattern."""
        try:
            pattern = tool_input["pattern"]
            base_path = tool_input.get("path", ".")
            recursive = tool_input.get("recursive", True)
            if recursive and "**" not in pattern:
                pattern = f"**/{pattern}"
            search_pattern = os.path.join(base_path, pattern)
            files = glob.glob(search_pattern, recursive=recursive)
            files = [f for f in files if os.path.isfile(f)]
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            categorized: Dict[str, List[str]] = {}
            for file_path in files:
                ext = Path(file_path).suffix.lower()
                categorized.setdefault(ext, []).append(file_path)
            return {
                "success": True,
                "output": (
                    f"Found {len(files)} files matching '{pattern}':\n"
                    + "\n".join(files[:20])
                    + (f"\n... and {len(files) - 20} more files" if len(files) > 20 else "")
                ),
                "file_count": len(files),
                "categories": categorized,
                "search_pattern": search_pattern,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_list_directory(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """List contents of a directory with metadata."""
        try:
            path = tool_input.get("path", ".")
            show_hidden = tool_input.get("show_hidden", False)
            recursive = tool_input.get("recursive", False)
            items = []
            total_size = 0
            if recursive:
                for root, dirs, files in os.walk(path):
                    if not show_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                        files = [f for f in files if not f.startswith(".")]
                    for name in dirs + files:
                        full_path = os.path.join(root, name)
                        rel_path = os.path.relpath(full_path, path)
                        is_dir = os.path.isdir(full_path)
                        size = 0 if is_dir else os.path.getsize(full_path)
                        total_size += size
                        items.append(
                            {
                                "name": rel_path,
                                "type": "directory" if is_dir else "file",
                                "size": size,
                                "language": None if is_dir else self._detect_language(full_path),
                            }
                        )
            else:
                for item in os.listdir(path):
                    if not show_hidden and item.startswith("."):
                        continue
                    full_path = os.path.join(path, item)
                    is_dir = os.path.isdir(full_path)
                    size = 0 if is_dir else os.path.getsize(full_path)
                    total_size += size
                    items.append(
                        {
                            "name": item,
                            "type": "directory" if is_dir else "file",
                            "size": size,
                            "language": None if is_dir else self._detect_language(full_path),
                        }
                    )
            items.sort(key=lambda x: (x["type"], x["name"]))
            output = f"📁 Directory: {path}\n"
            output += f"Total items: {len(items)}, Total size: {total_size} bytes\n\n"
            for item in items:
                icon = "📁" if item["type"] == "directory" else "📄"
                size_str = "" if item["type"] == "directory" else f" ({item['size']} bytes)"
                lang_str = "" if not item["language"] else f" [{item['language']}]"
                output += f"{icon} {item['name']}{size_str}{lang_str}\n"
            return {
                "success": True,
                "output": output,
                "items": items,
                "total_size": total_size,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_grep_search(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Search for a regex pattern within files with optional context."""
        try:
            pattern = tool_input["pattern"]
            search_path = tool_input.get("path", ".")
            file_pattern = tool_input.get("file_pattern", "*")
            case_sensitive = tool_input.get("case_sensitive", True)
            context_lines = tool_input.get("context_lines", 0)
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
            matches: List[Dict[str, Any]] = []
            files_searched = 0
            # Determine files to search
            if os.path.isfile(search_path):
                files_to_search = [search_path]
            else:
                files_to_search = glob.glob(os.path.join(search_path, "**", file_pattern), recursive=True)
                files_to_search = [f for f in files_to_search if os.path.isfile(f)]
            for file_path in files_to_search:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    files_searched += 1
                    for i, line in enumerate(lines):
                        if regex.search(line):
                            match_info: Dict[str, Any] = {
                                "file": file_path,
                                "line_number": i + 1,
                                "line": line.strip(),
                                "language": self._detect_language(file_path),
                            }
                            if context_lines > 0:
                                context: List[str] = []
                                start = max(0, i - context_lines)
                                end = min(len(lines), i + context_lines + 1)
                                for j in range(start, end):
                                    if j != i:
                                        context.append(f"{j+1}: {lines[j].strip()}")
                                match_info["context"] = context
                            matches.append(match_info)
                except Exception:
                    continue
            output = f"🔍 Pattern: '{pattern}' (case {'sensitive' if case_sensitive else 'insensitive'})\n"
            output += f"Files searched: {files_searched}, Matches found: {len(matches)}\n\n"
            for i, match in enumerate(matches[:15]):
                output += f"📄 {match['file']}:{match['line_number']}: {match['line']}\n"
                if match.get("context"):
                    for ctx in match["context"]:
                        output += f"     {ctx}\n"
                    output += "\n"
            if len(matches) > 15:
                output += f"... and {len(matches) - 15} more matches"
            return {
                "success": True,
                "output": output,
                "matches": matches,
                "files_searched": files_searched,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_todo_write(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Manage a list of todo items with status and priority."""
        try:
            todos_data = tool_input["todos"]
            current_todos: Dict[str, Any] = {todo["id"]: todo for todo in todos_data}
            output = f"{self.display.indent}⏺ Update Todos\n"
            status_counts = {"pending": 0, "in_progress": 0, "completed": 0}
            for todo in todos_data:
                status_symbol = {"pending": "☐", "in_progress": "🔄", "completed": "☒"}
                symbol = status_symbol.get(todo["status"], "☐")
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                priority = priority_emoji.get(todo["priority"], "")
                output += f"{self.display.indent}  ⎿  {symbol} {todo['content']} {priority}\n"
                status_counts[todo["status"]] = status_counts.get(todo["status"], 0) + 1
            output += f"\n{self.display.indent}Summary: {status_counts['completed']} completed, {status_counts['in_progress']} in progress, {status_counts['pending']} pending\n"
            print(output)
            return {
                "success": True,
                "output": output,
                "status_counts": status_counts,
                "total_todos": len(todos_data),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_task_agent(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Spawn a sub-agent to handle a specialized task."""
        try:
            description = tool_input["description"]
            prompt = tool_input["prompt"]
            agent_type = tool_input.get("agent_type", "general")
            if self.active_sub_agents >= self.config.max_sub_agents:
                return {
                    "success": False,
                    "error": f"Maximum sub-agents ({self.config.max_sub_agents}) already active",
                }
            self.display.show_status(f"Spawning {agent_type} sub-agent", description)
            self.active_sub_agents += 1
            try:
                sub_config = Config(
                    api_key=self.config.api_key,
                    working_dir=self.config.working_dir,
                    max_iterations=8,
                    debug_mode=False,
                    enable_web=agent_type in ["research", "general"],
                    enable_notebooks=agent_type in ["analysis", "general"],
                )
                sub_agent = ProfessionalSWEAgent(
                    config=sub_config,
                    progress_callback=self._handle_sub_agent_progress,
                    indent_level=self.indent_level + 1,
                )
                # Filter tools based on type
                if agent_type == "search":
                    sub_agent.tools = [t for t in self.tools if t["name"] in ["glob_search", "grep_search", "list_directory", "str_replace_editor"]]
                elif agent_type == "analysis":
                    sub_agent.tools = [t for t in self.tools if t["name"] in ["str_replace_editor", "grep_search", "bash", "create_summary"]]
                elif agent_type == "coding":
                    sub_agent.tools = [t for t in self.tools if t["name"] in ["str_replace_editor", "bash", "glob_search", "grep_search"]]
                elif agent_type == "debugging":
                    sub_agent.tools = [t for t in self.tools if t["name"] in ["str_replace_editor", "bash", "grep_search", "list_directory"]]
                else:
                    sub_agent.tools = self.tools[:6]
                sub_agent.state = None
                print(f"{self.display.indent}📊 Spawning {agent_type} sub-agent")
                print(f"{self.display.indent}🔧 Sub-agent tools: {len(sub_agent.tools)}")
                print(f"{self.display.indent}⚡ Task: {description}")
                import time
                start_time = time.time()
                try:
                    result = sub_agent.execute_task(prompt)
                    elapsed = time.time() - start_time
                    print(f"{self.display.indent}✅ Sub-agent completed in {elapsed:.1f}s")
                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"{self.display.indent}❌ Sub-agent failed after {elapsed:.1f}s: {str(e)}")
                    raise
                sub_result = {
                    "agent_type": agent_type,
                    "description": description,
                    "success": result["success"],
                    "iterations": result["iterations"],
                    "response": result.get("final_response", ""),
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                self.state.sub_agent_results.append(sub_result)
                return {
                    "success": result["success"],
                    "output": (
                        f"Sub-agent ({agent_type}) completed in {result['iterations']} iterations:\n"
                        + result.get("final_response", "No response")[:500]
                        + ("..." if len(str(result.get("final_response", ""))) > 500 else "")
                    ),
                    "sub_agent_result": sub_result,
                }
            finally:
                self.active_sub_agents -= 1
        except Exception as e:
            self.active_sub_agents -= 1
            return {"success": False, "error": str(e)}

    def _execute_web_fetch(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch content from a web URL with a prompt for analysis."""
        try:
            url = tool_input["url"]
            prompt = tool_input["prompt"]
            self.display.debug_log(f"Fetching URL: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            }
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            content = response.text[:8000]
            return {
                "success": True,
                "output": (
                    f"📄 Fetched from {url} ({len(content)} chars)\n\n"
                    f"Content preview:\n{content[:1000]}"
                    + ("..." if len(content) > 1000 else "")
                    + f"\n\nAnalysis prompt: {prompt}"
                ),
                "url": url,
                "content_length": len(content),
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch {url}: {str(e)}"}

    def _execute_web_search(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a web search and return formatted results."""
        # Fail fast if the duckduckgo_search dependency is missing
        if DDGS is None:
            return {
                "success": False,
                "error": "Web search is unavailable because duckduckgo_search is not installed.",
            }
        try:
            query = tool_input["query"]
            num_results = tool_input.get("num_results", 5)
            self.display.debug_log(f"Searching web: {query}")
            results: List[Dict[str, Any]] = []
            with DDGS() as ddgs:
                for i, result in enumerate(ddgs.text(query, max_results=num_results)):
                    results.append(result)
                    if i + 1 >= num_results:
                        break
            if not results:
                return {"success": False, "error": "No results found or query failed."}
            formatted_results = "\n\n".join(
                [
                    f"{i+1}. [{res['title']}]({res['href']})\n{res['body']}"
                    for i, res in enumerate(results)
                ]
            )
            return {
                "success": True,
                "output": f"🔍 Web search results for '{query}':\n\n{formatted_results}",
                "query": query,
                "placeholder": False,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_notebook_edit(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Perform notebook operations such as create and read."""
        try:
            command = tool_input["command"]
            path = tool_input["path"]
            if command == "create":
                notebook = {
                    "cells": [],
                    "metadata": {
                        "kernelspec": {
                            "display_name": "Python 3",
                            "language": "python",
                            "name": "python3",
                        },
                        "language_info": {
                            "name": "python",
                            "version": "3.8.0",
                        },
                    },
                    "nbformat": 4,
                    "nbformat_minor": 4,
                }
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w") as f:
                    json.dump(notebook, f, indent=2)
                self.state.files_tracking[path] = {
                    "created": datetime.datetime.now().isoformat(),
                    "size": len(json.dumps(notebook)),
                    "action": "created",
                    "type": "jupyter_notebook",
                }
                return {"success": True, "output": f"Created Jupyter notebook: {path}"}
            elif command == "read":
                with open(path, "r") as f:
                    notebook = json.load(f)
                cell_count = len(notebook.get("cells", []))
                cell_types: Dict[str, int] = {}
                for cell in notebook.get("cells", []):
                    cell_type = cell.get("cell_type", "unknown")
                    cell_types[cell_type] = cell_types.get(cell_type, 0) + 1
                return {
                    "success": True,
                    "output": f"📓 Notebook: {path}\nCells: {cell_count} total ({dict(cell_types)})",
                    "cell_count": cell_count,
                    "cell_types": cell_types,
                }
            elif command == "add_cell":
                cell_content = tool_input.get("cell_content", "")
                cell_type = tool_input.get("cell_type", "code")
                with open(path, "r") as f:
                    notebook = json.load(f)
                new_cell: Dict[str, Any] = {
                    "cell_type": cell_type,
                    "source": cell_content.split('\n'),
                    "metadata": {},
                }
                if cell_type == "code":
                    new_cell["execution_count"] = None
                    new_cell["outputs"] = []
                notebook["cells"].append(new_cell)
                with open(path, "w") as f:
                    json.dump(notebook, f, indent=2)
                return {
                    "success": True,
                    "output": f"Added {cell_type} cell to {path} (now {len(notebook['cells'])} cells)",
                }
            else:
                return {"success": False, "error": f"Notebook command '{command}' not implemented"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_create_summary(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Create an intelligent summary of recent progress."""
        try:
            reason = tool_input["reason"]
            key_accomplishments = tool_input["key_accomplishments"]
            current_focus = tool_input["current_focus"]
            next_steps = tool_input.get("next_steps", [])
            summary_id = f"professional_{len(self.state.conversation_summaries) + 1}"
            conversation_summary = ConversationSummary(
                summary_id=summary_id,
                iterations_covered=(
                    max(0, self.state.iteration_count - 8),
                    self.state.iteration_count,
                ),
                key_accomplishments=key_accomplishments,
                current_focus=current_focus,
                next_steps=next_steps,
                files_created_modified=list(self.state.files_tracking.keys()),
                errors_resolved=[err.get("error", "")[:50] for err in self.state.error_history[-3:]],
                timestamp=datetime.datetime.now().isoformat(),
            )
            self.state.conversation_summaries.append(conversation_summary)
            return {
                "success": True,
                "output": (
                    f"📋 Comprehensive Summary Created\nReason: {reason}\n"
                    f"Accomplishments: {len(key_accomplishments)}\n"
                    f"Files tracked: {len(self.state.files_tracking)}\n"
                    f"Sub-agents used: {len(self.state.sub_agent_results)}"
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_update_progress_md(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Update the markdown progress report with recent changes."""
        try:
            action = tool_input["action"]
            files_modified = tool_input.get("files_modified", [])
            for file_path in files_modified:
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    self.state.files_tracking[file_path] = {
                        "last_modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "size": stat.st_size,
                        "action": action,
                        "language": self._detect_language(file_path),
                    }
            progress_entry = ProgressEntry(
                timestamp=datetime.datetime.now().isoformat(),
                action=action,
                details=f"Modified {len(files_modified)} files" if files_modified else "Action completed with full tool suite",
                files_affected=files_modified,
                status="completed",
            )
            self.state.progress_entries.append(progress_entry)
            self._update_progress_md_file()
            return {
                "success": True,
                "output": (
                    f"📊 Progress Updated: {action}\n"
                    f"Files tracked: {len(files_modified)}\n"
                    f"Total files: {len(self.state.files_tracking)}\n"
                    f"Sub-agents: {len(self.state.sub_agent_results)}"
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Utility methods and helpers
    # -------------------------------------------------------------------------
    def _detect_language(self, file_path: str) -> str:
        """Infer the programming language from the file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".sql": "sql",
            ".sh": "shell",
            ".bat": "batch",
        }
        return language_map.get(ext, "unknown")

    def _classify_command(self, command: str) -> str:
        """Classify a shell command by its purpose."""
        command_lower = command.lower().strip()
        if any(cmd in command_lower for cmd in ["install", "pip", "npm", "apt", "brew"]):
            return "package_management"
        elif any(cmd in command_lower for cmd in ["git", "clone", "commit", "push", "pull"]):
            return "version_control"
        elif any(cmd in command_lower for cmd in ["test", "pytest", "npm test", "make test"]):
            return "testing"
        elif any(cmd in command_lower for cmd in ["build", "compile", "make", "webpack"]):
            return "build"
        elif any(cmd in command_lower for cmd in ["ls", "dir", "pwd", "whoami", "date"]):
            return "system_info"
        else:
            return "general"

    def _scan_for_new_files(self, command: str) -> None:
        """Look for files created by recent shell commands."""
        if any(pattern in command.lower() for pattern in ["touch", "echo >", "cat >", "mkdir", "cp", "mv"]):
            try:
                for path in Path(".").rglob("*"):
                    if path.is_file():
                        stat = path.stat()
                        age = datetime.datetime.now().timestamp() - stat.st_mtime
                        if age < 10:
                            file_str = str(path)
                            if file_str not in self.state.files_tracking:
                                self.state.files_tracking[file_str] = {
                                    "created": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                    "size": stat.st_size,
                                    "action": "created_by_command",
                                    "language": self._detect_language(file_str),
                                }
            except Exception:
                pass

    def _initialize_progress_md(self) -> None:
        """Write the initial markdown progress file."""
        content = (
            f"# Professional SWE Agent Progress Report\n\n"
            f"**Task ID:** {self.state.task_id}  \n"
            f"**Started:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
            f"**Agent Version:** Professional (Complete AI Code Assistant)  \n"
            f"**Tools Available:** {len(self.tools)} professional tools  \n"
            f"**Status:** In Progress\n\n"
            "## Task Description\n"
            f"{self.state.original_task}\n\n"
            "## Agent Capabilities\n"
            "✅ **File Operations:** str_replace_editor, glob_search, list_directory  \n"
            "✅ **Search & Analysis:** grep_search, task_agent spawning  \n"
            "✅ **Execution:** bash with intelligent timeouts  \n"
            "✅ **Project Management:** todo_write, create_summary, update_progress_md  \n"
            "✅ **User Interaction:** ask_user_step for guidance  \n"
            + (
                "✅ **Web Research:** web_fetch, web_search\n"
                if self.config.enable_web
                else "❌ **Web Research:** Disabled\n"
            )
            + (
                "✅ **Jupyter Notebooks:** notebook_edit\n"
                if self.config.enable_notebooks
                else "❌ **Jupyter Notebooks:** Disabled\n"
            )
            + "\n## Progress Timeline\n\n"
        )
        with open(self.progress_path, "w") as f:
            f.write(content)

    def _update_progress_md_file(self) -> None:
        """Rewrite the progress markdown file with latest information."""
        if not self.config.progress_tracking:
            return
        try:
            content = (
                f"# Professional SWE Agent Progress Report\n\n"
                f"**Task ID:** {self.state.task_id}  \n"
                f"**Started:** {self.state.progress_entries[0].timestamp if self.state.progress_entries else 'Unknown'}  \n"
                f"**Last Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
                f"**Agent Version:** Professional (Complete AI Code Assistant)  \n"
                f"**Tools Available:** {len(self.tools)} professional tools  \n"
                f"**Status:** {'Completed' if len(self.state.completed_steps) > 10 else 'In Progress'}  \n"
                f"**Iterations:** {self.state.iteration_count}\n\n"
                "## Task Description\n"
                f"{self.state.original_task}\n\n"
                "## Professional Agent Capabilities\n"
                "✅ **File Operations:** str_replace_editor (create/edit/view), glob_search, list_directory  \n"
                "✅ **Search & Analysis:** grep_search with regex, task_agent spawning  \n"
                "✅ **Execution:** bash with intelligent timeouts and classification  \n"
                "✅ **Project Management:** todo_write, create_summary, update_progress_md  \n"
                "✅ **User Interaction:** ask_user_step for error recovery guidance  \n"
                + (
                    "✅ **Web Research:** web_fetch, web_search for documentation\n"
                    if self.config.enable_web
                    else "❌ **Web Research:** Disabled\n"
                )
                + (
                    "✅ **Jupyter Notebooks:** notebook_edit for data science\n"
                    if self.config.enable_notebooks
                    else "❌ **Jupyter Notebooks:** Disabled\n"
                )
                + "\n## Comprehensive Summaries\n"
            )
            for summary in self.state.conversation_summaries:
                content += f"\n### {summary.summary_id} ({summary.timestamp[:19]})\n"
                content += f"**Iterations:** {summary.iterations_covered[0]}-{summary.iterations_covered[1]}\n\n"
                content += "**Key Accomplishments:**\n"
                for acc in summary.key_accomplishments:
                    content += f"- {acc}\n"
                content += f"\n**Current Focus:** {summary.current_focus}\n"
                if summary.next_steps:
                    content += "**Next Steps:**\n"
                    for step in summary.next_steps:
                        content += f"- {step}\n"
                content += "\n"
            content += "\n## Files Created/Modified (Enhanced Tracking)\n\n"
            for file_path, info in self.state.files_tracking.items():
                action = info.get("action", "unknown")
                timestamp = info.get("created") or info.get("modified", "unknown")
                size = info.get("size", 0)
                language = info.get("language", "unknown")
                lines = info.get("lines", "N/A")
                content += f"- **{file_path}** - {action} ({timestamp[:19]}, {size} bytes, {lines} lines, {language})\n"
            content += f"\n## Sub-Agent Results ({len(self.state.sub_agent_results)})\n\n"
            for i, result in enumerate(self.state.sub_agent_results, 1):
                status = "✅" if result["success"] else "❌"
                content += f"{i}. {status} **{result['agent_type']}** - {result['description']} ({result['iterations']} iterations)\n"
                content += f"   Response: {result['response'][:100]}{'...' if len(result['response']) > 100 else ''}\n\n"
            content += "\n## Detailed Timeline\n\n"
            for entry in self.state.progress_entries:
                status_emoji = {"completed": "✅", "failed": "❌", "skipped": "⏭️"}.get(entry.status, "🔄")
                content += f"### {entry.timestamp[:19]} {status_emoji}\n"
                content += f"**Action:** {entry.action}\n"
                content += f"**Details:** {entry.details}\n"
                if entry.files_affected:
                    content += f"**Files:** {', '.join(entry.files_affected)}\n"
                content += "\n"
            if self.state.error_history:
                content += "## Error History & Recovery\n\n"
                for error in self.state.error_history:
                    content += f"- **{error['timestamp'][:19]}** - Iteration {error['iteration']}\n"
                    content += f"  - **Step:** {error['step']}\n"
                    content += f"  - **Error:** {error['error'][:100]}{'...' if len(error['error']) > 100 else ''}\n"
                    content += f"  - **Context:** {error.get('context', 'No context')}\n\n"
            content += "## Tool Usage Statistics\n\n"
            content += f"- **Total Tools Available:** {len(self.tools)}\n"
            content += f"- **Files Tracked:** {len(self.state.files_tracking)}\n"
            content += f"- **Sub-Agents Spawned:** {len(self.state.sub_agent_results)}\n"
            content += f"- **Summaries Created:** {len(self.state.conversation_summaries)}\n"
            content += f"- **Errors Encountered:** {len(self.state.error_history)}\n"
            content += f"- **Progress Entries:** {len(self.state.progress_entries)}\n"
            with open(self.progress_path, "w") as f:
                f.write(content)
        except Exception as e:
            self.display.debug_log(f"Could not update progress.md: {e}")

    def _initialize_conversation(self, system_prompt: str, task: str) -> List[Dict[str, Any]]:
        """Initialize the conversation history with system and user messages."""
        if self.state.conversation_summaries:
            summary_context = self._build_comprehensive_summary_context()
            messages = [
                {
                    "role": "user",
                    "content": f"{system_prompt}\n\n{summary_context}\n\nContinue task with full capabilities: {task}",
                }
            ]
        else:
            messages = [
                {
                    "role": "user",
                    "content": f"{system_prompt}\n\nTask: {task}",
                }
            ]
        return messages

    def _build_comprehensive_summary_context(self) -> str:
        """Build a textual summary of previous progress for context."""
        if not self.state.conversation_summaries:
            return ""
        latest = self.state.conversation_summaries[-1]
        return (
            "COMPREHENSIVE PREVIOUS PROGRESS:\n"
            f"📝 Accomplishments: {', '.join(latest.key_accomplishments)}\n"
            f"🎯 Current Focus: {latest.current_focus}\n"
            f"📁 Files: {', '.join(latest.files_created_modified)}\n"
            f"🤖 Sub-agents: {len(self.state.sub_agent_results)} completed\n"
            f"🛠️ Errors resolved: {', '.join(latest.errors_resolved)}\n"
            f"➡️ Next: {', '.join(latest.next_steps)}"
        )

    def _create_intelligent_summary(self, messages: List[Dict[str, Any]]) -> None:
        """Leverage the LLM to create a structured summary of recent conversation."""
        try:
            recent_messages = messages[-10:]
            summary_prompt = (
                "Analyze this Professional SWE Agent conversation and create a comprehensive summary:\n"
                "1. Key accomplishments with technical details\n"
                "2. Current focus and technical context\n"
                "3. Files created/modified and their purposes\n"
                "4. Any errors resolved and solutions found\n"
                "5. Next logical steps with specific actions\n"
                "6. Tool usage patterns and effectiveness\n\n"
                "Be comprehensive but concise - this summary will guide future work."
            )
            # Use the unified LLM interface to generate a summary. We do not
            # provide tool definitions for summarisation. A small max_tokens is
            # specified to keep the summary concise.
            summary_messages = [
                {"role": "user", "content": summary_prompt},
                {"role": "assistant", "content": str(recent_messages)},
            ]
            summary_response = self._call_llm(summary_messages, max_tokens=1500)
            # Extract the summary text. Different providers return the text in
            # different structures but litellm normalises the response. The
            # assistant message content contains the summary.
            summary_text = ""
            try:
                summary_text = summary_response.choices[0].message.content or ""
            except Exception:
                pass
            summary_id = f"professional_summary_{len(self.state.conversation_summaries) + 1}"
            conversation_summary = ConversationSummary(
                summary_id=summary_id,
                iterations_covered=(
                    max(0, self.state.iteration_count - 10),
                    self.state.iteration_count,
                ),
                key_accomplishments=self._extract_accomplishments(summary_text),
                current_focus=self._extract_current_focus(summary_text),
                next_steps=self._extract_next_steps(summary_text),
                files_created_modified=list(self.state.files_tracking.keys()),
                errors_resolved=[err.get("error", "")[:50] for err in self.state.error_history[-5:]],
                timestamp=datetime.datetime.now().isoformat(),
            )
            self.state.conversation_summaries.append(conversation_summary)
            self.display.debug_log(
                f"Summary created: {len(conversation_summary.key_accomplishments)} accomplishments, {len(self.state.files_tracking)} files, {len(self.state.sub_agent_results)} sub-agents",
            )
        except Exception as e:
            self.display.debug_log(f"Could not create summary: {e}")

    def _compress_conversation_with_summary(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compress conversation using the latest summary to save tokens."""
        if not self.state.conversation_summaries:
            return messages
        latest_summary = self.state.conversation_summaries[-1]
        summary_text = (
            "PROFESSIONAL AGENT COMPREHENSIVE SUMMARY:\n"
            f"Key accomplishments: {', '.join(latest_summary.key_accomplishments)}\n"
            f"Current focus: {latest_summary.current_focus}\n"
            f"Files tracked: {len(latest_summary.files_created_modified)} ("
            + ", ".join(latest_summary.files_created_modified[:5])
            + (" ..." if len(latest_summary.files_created_modified) > 5 else "")
            + ")\n"
            f"Sub-agents used: {len(self.state.sub_agent_results)}\n"
            f"Errors resolved: {', '.join(latest_summary.errors_resolved)}\n"
            f"Next steps: {', '.join(latest_summary.next_steps)}\n"
            f"Tools available: {len(self.tools)} professional tools"
        )
        compressed = [messages[0], {"role": "user", "content": f"COMPREHENSIVE CONTEXT: {summary_text}"}] + messages[-self.config.context_retention :]
        return compressed

    def _get_comprehensive_context_summary(self) -> str:
        """Return a short summary of the current context for error reporting."""
        return (
            f"Step: {self.state.current_step}\n"
            f"Files: {len(self.state.files_tracking)}\n"
            f"Completed: {len(self.state.completed_steps)}\n"
            f"Sub-agents: {len(self.state.sub_agent_results)}\n"
            f"Tools: {len(self.tools)}\n"
            f"Summaries: {len(self.state.conversation_summaries)}"
        )

    def _handle_error_with_full_context(self, error: Exception, messages: List[Dict[str, Any]]) -> str:
        """Prompt the user for a recovery option after an error."""
        print(f"🆘 Error during: {self.state.current_step}")
        print(f"Comprehensive context: {self._get_comprehensive_context_summary()}")
        print(f"Available tools: {[t['name'] for t in self.tools]}")
        print(f"Sub-agents available: {self.config.max_sub_agents - self.active_sub_agents}")
        print("\nRecovery options:")
        print("1. retry - Try again with full tool suite")
        print("2. delegate - Spawn sub-agent to handle this issue")
        print("3. skip - Skip this step and continue")
        print("4. abort - Save comprehensive state and exit")
        choice = input("Recovery choice (1-4): ").strip().lower()
        if choice in ["2", "delegate"]:
            print("Would spawn debugging sub-agent to analyze and resolve the error...")
        return {"1": "retry", "2": "retry", "3": "skip", "4": "abort"}.get(choice, "retry")

    def _track_comprehensive_progress(self, tool_name: str, tool_input: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Update the completed steps list based on tool usage."""
        if tool_name == "bash":
            operation = f"Executed {self._classify_command(tool_input['command'])}: {tool_input['command'][:50]}..."
        elif tool_name == "str_replace_editor":
            operation = f"File {tool_input['command']}: {tool_input['path']}"
        elif tool_name == "task_agent":
            operation = f"Spawned {tool_input.get('agent_type', 'general')} sub-agent: {tool_input['description'][:50]}..."
        elif tool_name in ["glob_search", "grep_search"]:
            operation = f"Search with {tool_name}: {tool_input.get('pattern', 'N/A')}"
        else:
            operation = f"Used {tool_name}: {list(tool_input.keys())}"
        if operation not in self.state.completed_steps:
            self.state.completed_steps.append(operation)

    def _get_user_guidance(self, tool_input: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Interactively ask the user how to proceed after a failure."""
        step_description = tool_input["step_description"]
        status = tool_input["status"]
        error_details = tool_input.get("error_details", "")
        suggested_action = tool_input.get("suggested_next_action", "")
        print(f"\n📋 Step: {step_description}")
        print(f"📊 Status: {status.upper()}")
        print(f"🔧 Tools available: {len(self.tools)}")
        print(f"🤖 Sub-agents available: {self.config.max_sub_agents - self.active_sub_agents}")
        if error_details:
            print(f"❌ Error: {error_details}")
        if suggested_action:
            print(f"💡 Suggested: {suggested_action}")
        if status == "failed":
            print("\n❓ How should the Professional Agent handle this failure?")
            print("1. retry - Use full tool suite to try again")
            print("2. delegate - Spawn specialized sub-agent")
            print("3. research - Use web tools to find solution")
            print("4. skip - Mark as skipped and continue")
            print("5. manual - I'll handle this manually")
        else:
            print("\n❓ How should the Professional Agent proceed?")
            print("1. continue - Proceed with full capabilities")
            print("2. focus - Focus on specific aspect")
            print("3. delegate - Spawn sub-agent for next steps")
        choice = input("Your guidance: ").strip()
        additional_info = ""
        if choice in ["2", "delegate", "focus"]:
            additional_info = input("What should be the focus/delegation? ")
        elif choice in ["5", "manual"]:
            additional_info = input("What did you do manually? ")
        return f"User chose '{choice}' with Professional Agent context. Additional info: {additional_info}"

    def _process_user_guidance(self, guidance: str, tool_input: Dict[str, Any]) -> None:
        """Record the outcome of user guidance for tracking purposes."""
        if "skip" in guidance.lower():
            self.state.completed_steps.append(f"SKIPPED: {tool_input['step_description']}")
        elif "manual" in guidance.lower():
            self.state.completed_steps.append(f"MANUAL: {tool_input['step_description']}")
        elif "delegate" in guidance.lower():
            self.state.completed_steps.append(f"DELEGATED: {tool_input['step_description']}")

    def _format_tool_params(self, tool_input: Dict[str, Any]) -> str:
        """Create a concise string representation of tool parameters."""
        if not tool_input:
            return ""
        if "path" in tool_input:
            path = tool_input["path"]
            return path if len(path) <= 30 else "..." + path[-27:]
        elif "command" in tool_input:
            cmd = tool_input["command"]
            return cmd if len(cmd) <= 40 else cmd[:37] + "..."
        elif "pattern" in tool_input:
            pattern = tool_input["pattern"]
            return pattern if len(pattern) <= 30 else pattern[:27] + "..."
        elif "query" in tool_input:
            query = tool_input["query"]
            return query if len(query) <= 30 else query[:27] + "..."
        elif "url" in tool_input:
            url = tool_input["url"]
            return url if len(url) <= 40 else url[:37] + "..."
        else:
            key_params: List[str] = []
            for key, value in tool_input.items():
                if key in ["description", "content", "todos"]:
                    continue
                if isinstance(value, str) and len(value) < 20:
                    key_params.append(f"{key}={value}")
                elif isinstance(value, (int, bool)):
                    key_params.append(f"{key}={value}")
            params_str = ", ".join(key_params[:2])
            return params_str if len(params_str) <= 30 else params_str[:27] + "..."

    def _create_completion_summary(self) -> None:
        """Display a summary upon task completion."""
        if self.config.progress_tracking:
            self._update_progress_md_file()
        self.display.show_success("Task completed successfully!")
        if self.display.verbosity in ["verbose", "debug"]:
            print(f"\n📊 Task Summary:")
            print(f"✅ Files created/modified: {len(self.state.files_tracking)}")
            print(f"🤖 Sub-agents spawned: {len(self.state.sub_agent_results)}")
            print(f"📝 Progress entries: {len(self.state.progress_entries)}")
            print(f"🧠 Summaries created: {len(self.state.conversation_summaries)}")
        elif self.display.verbosity == "standard":
            print(f"📁 Files modified: {len(self.state.files_tracking)}")
            print(f"📊 Progress entries: {len(self.state.progress_entries)}")

    def _finalize_progress_md(self) -> None:
        """Mark the progress markdown as complete and append final statistics."""
        try:
            with open(self.progress_path, "r") as f:
                content = f.read()
            content = content.replace("**Status:** In Progress", "**Status:** Completed ✅")
            content += "\n\n## Task Completed Successfully\n"
            content += f"**Completion Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += "**Professional Agent Performance:**\n"
            content += f"- **Total Files Created/Modified:** {len(self.state.files_tracking)}\n"
            content += f"- **Total Steps Completed:** {len(self.state.completed_steps)}\n"
            content += f"- **Sub-Agents Utilized:** {len(self.state.sub_agent_results)}\n"
            content += f"- **Intelligent Summaries:** {len(self.state.conversation_summaries)}\n"
            content += f"- **Tools Available:** {len(self.tools)} professional tools\n"
            content += f"- **Error Recovery Events:** {len(self.state.error_history)}\n"
            content += "\n**Agent Capabilities Utilized:**\n"
            content += "✅ Complete AI code assistant functionality achieved\n"
            with open(self.progress_path, "w") as f:
                f.write(content)
        except Exception as e:
            self.display.debug_log(f"Could not finalize progress.md: {e}")

    def _extract_accomplishments(self, summary_text: str) -> List[str]:
        """Parse key accomplishments from summary text."""
        lines = summary_text.split('\n')
        accomplishments: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('-', '*', '•')) or any(stripped.startswith(f"{i}.") for i in range(1, 10)):
                accomplishments.append(stripped.lstrip('-*•0123456789. '))
        return accomplishments[:5]

    def _extract_current_focus(self, summary_text: str) -> str:
        """Parse the current focus from summary text."""
        lines = summary_text.lower().split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['current', 'focus', 'working on', 'now']):
                return line.strip()[:100]
        return "Continuing comprehensive task execution"

    def _extract_next_steps(self, summary_text: str) -> List[str]:
        """Parse suggested next steps from summary text."""
        lines = summary_text.split('\n')
        next_steps: List[str] = []
        in_next_section = False
        for line in lines:
            lower = line.lower()
            if any(keyword in lower for keyword in ['next', 'upcoming', 'plan', 'todo']):
                in_next_section = True
                continue
            if in_next_section and (
                line.strip().startswith(('-', '*', '•')) or any(line.strip().startswith(f"{i}.") for i in range(1, 10))
            ):
                next_steps.append(line.strip().lstrip('-*•0123456789. '))
        return next_steps[:3]

    def _save_state(self) -> None:
        """Persist the agent's internal state to disk."""
        try:
            with open(self.state_path, 'wb') as f:
                pickle.dump(self.state, f)
            if self.config.debug_mode:
                self.display.debug_log(f"State saved: {len(self.state.files_tracking)} files, {len(self.state.sub_agent_results)} sub-agents")
        except Exception as e:
            self.display.debug_log(f"Could not save state: {e}")

    def _load_state(self, task_id: str) -> bool:
        """Load a previously saved state from disk."""
        try:
            if not self.state_path.exists():
                return False
            with open(self.state_path, 'rb') as f:
                loaded_state: AgentState = pickle.load(f)
            if loaded_state.task_id == task_id:
                self.state = loaded_state
                return True
            return False
        except Exception as e:
            self.display.debug_log(f"Could not load state: {e}")
            return False

    def _handle_sub_agent_progress(self, tool_name: str, params: str, result: Dict[str, Any]) -> None:
        """Stream progress updates from sub-agents back to the parent."""
        # At present, progress from sub-agents is printed directly by their own displays
        pass

    def _cleanup_state(self) -> None:
        """Delete the persisted state after successful completion."""
        try:
            if self.state_path.exists():
                self.state_path.unlink()
                self.display.debug_log("State cleaned up")
        except Exception:
            pass
