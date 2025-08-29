"""User display formatting for the SWE Agent.

The :class:`AgentDisplay` class centralizes all output formatting and
verbosity control for the agent. It provides helpers for showing
headers, task starts, tool invocation and results, status updates,
progress bars, errors and successes. Keeping these concerns separate
from the main agent logic simplifies unit testing and reuse.
"""

from typing import Dict, Any


class AgentDisplay:
    """Professional AI agent display formatting with clean UI."""

    def __init__(self, verbosity_level: str = "standard", indent_level: int = 0):
        """Initialize the display with verbosity control.

        Parameters
        ----------
        verbosity_level: str
            Desired verbosity (``"minimal"``, ``"standard"``, ``"verbose"`` or ``"debug"``).
        indent_level: int
            Indentation level applied to nested sub-agent output.
        """
        self.verbosity = verbosity_level
        self.show_debug = verbosity_level == "debug"
        self.indent_level = indent_level
        self.indent = "  " * indent_level

    def show_header(self, working_dir: str, tools_count: int) -> None:
        """Display a clean header at startup.

        Parameters
        ----------
        working_dir: str
            Directory the agent is operating within.
        tools_count: int
            Number of tools available to the agent.
        """
        print(f"\n🔧 SWE Agent Professional")
        print(f"📁 Working directory: {working_dir}")
        if self.verbosity in ["verbose", "debug"]:
            print(f"⚙️  Available tools: {tools_count}")
        print()

    def show_task_start(self, task: str) -> None:
        """Show the start of a new task."""
        print(f"🎯 Task: {task}\n")

    def show_tool_start(self, tool_name: str, params: str = "") -> None:
        """Display a tool invocation with professional formatting."""
        display_name = self._get_tool_display_name(tool_name, params)
        print(f"{self.indent}⏺ {display_name}")

    def show_tool_result(self, tool_name: str, params: str, result: Dict[str, Any]) -> None:
        """Display a tool result with clean formatting."""
        if result.get("success"):
            result_text = self._format_tool_result(tool_name, params, result)
            print(f"{self.indent}  ⎿ {result_text}")
        else:
            error_msg = self._format_error_message(result.get("error", "Operation failed"))
            print(f"{self.indent}  ⎿ {error_msg}")

    def show_status(self, status: str, details: str = "") -> None:
        """Display status updates based on verbosity."""
        if self.verbosity != "minimal":
            if details and self.verbosity in ["verbose", "debug"]:
                print(f"📊 {status}: {details}")
            else:
                print(f"📊 {status}")

    def show_progress(self, current: int, total: int, description: str = "") -> None:
        """Display a progress bar based on iterations."""
        if self.verbosity != "minimal":
            percentage = int((current / total) * 100) if total > 0 else 0
            bar = "█" * (percentage // 10) + "░" * (10 - percentage // 10)
            print(f"⏳ [{bar}] {percentage}% {description}")

    def show_error(self, error: str, suggestion: str = "") -> None:
        """Display a user-friendly error message with optional suggestion."""
        print(f"❌ {self._format_error_message(error)}")
        if suggestion:
            print(f"💡 Suggestion: {suggestion}")

    def show_success(self, message: str) -> None:
        """Display a success message."""
        print(f"✅ {message}")

    def debug_log(self, message: str) -> None:
        """Display debug information when verbosity is debug."""
        if self.show_debug:
            print(f"🐛 DEBUG: {message}")

    # Internal formatting helpers -------------------------------------------------

    def _get_tool_display_name(self, tool_name: str, params: str) -> str:
        """Map a tool name to a user-friendly display representation."""
        name_map = {
            "str_replace_editor": "Edit",
            "bash": "Bash",
            "grep_search": "Search",
            "glob_search": "Find",
            "list_directory": "List",
            "web_search": "WebSearch",
            "web_fetch": "WebFetch",
            "todo_write": "TodoWrite",
            "task_agent": "TaskAgent",
            "notebook_edit": "NotebookEdit",
            "update_progress_md": "UpdateProgress",
            "ask_user_step": "AskUser",
            "create_summary": "CreateSummary",
        }
        display_name = name_map.get(tool_name, tool_name.replace("_", " ").title())
        if params:
            if len(params) > 50:
                params = params[:47] + "..."
            return f"{display_name}({params})"
        return f"{display_name}()"

    def _format_tool_result(self, tool_name: str, params: str, result: Dict[str, Any]) -> str:
        """Format tool results in a user-friendly way."""
        if tool_name == "str_replace_editor":
            operation = result.get("operation", "edit")
            if operation == "create":
                return "Created file"
            elif operation == "str_replace":
                changes = result.get("changes", 1)
                return f"Made {changes} replacement{'s' if changes != 1 else ''}"
            elif operation in ["view", "view_range"]:
                lines = result.get("line_count", 0)
                if lines == 0:
                    return "File is empty"
                return f"Read {lines} line{'s' if lines != 1 else ''}"
            else:
                return "File modified"
        elif tool_name == "bash":
            if result.get("stdout"):
                output_lines = len(result["stdout"].split('\n'))
                return f"Command executed ({output_lines} lines output)"
            else:
                return "Command executed successfully"
        elif tool_name == "grep_search":
            matches = result.get("matches", 0)
            if matches == 0:
                return "No matches found"
            return f"Found {matches} match{'es' if matches != 1 else ''}"
        elif tool_name == "glob_search":
            files = result.get("files", [])
            return f"Found {len(files)} file{'s' if len(files) != 1 else ''}"
        elif tool_name == "list_directory":
            items = result.get("items", [])
            return f"Listed {len(items)} item{'s' if len(items) != 1 else ''}"
        elif tool_name == "web_search":
            results = result.get("results", [])
            return f"Found {len(results)} search result{'s' if len(results) != 1 else ''}"
        elif tool_name == "web_fetch":
            length = result.get("content_length", 0)
            return f"Fetched content ({length} characters)"
        elif tool_name == "todo_write":
            total = result.get("total_todos", 0)
            return f"Updated {total} todo{'s' if total != 1 else ''}"
        elif tool_name == "task_agent":
            return "Sub-agent completed task"
        else:
            return str(result.get("output", "Operation completed"))[:100]

    def _format_error_message(self, error: str) -> str:
        """Convert common error patterns into friendly messages."""
        error = str(error)
        if "No such file or directory" in error:
            return "File not found"
        elif "Permission denied" in error:
            return "Permission denied - check file permissions"
        elif "Command not found" in error:
            return "Command not available"
        elif "Connection refused" in error or "Network" in error:
            return "Network connection failed"
        elif "Timeout" in error.lower():
            return "Operation timed out"
        elif len(error) > 100:
            return error[:97] + "..."
        else:
            return error
