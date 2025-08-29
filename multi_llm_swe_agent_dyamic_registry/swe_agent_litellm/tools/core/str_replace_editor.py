"""
File editor tool.

This tool allows creation, viewing and basic string replacement of
files. It mirrors the behaviour of the original
``str_replace_editor`` tool defined in the monolithic agent but
encapsulates it in a reusable class. When invoked from an agent
it updates the agent's file tracking metadata and records
language information for new or modified files.
"""

from __future__ import annotations

import os
import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from swe_agent_litellm.base_tool import BaseTool


class StrReplaceEditorTool(BaseTool):
    """Create, view and edit files with advanced options and tracking."""

    name = "str_replace_editor"
    description = "Create, read, and edit files with advanced options and tracking"
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["create", "str_replace", "view", "view_range"],
                "description": "The command to execute",
            },
            "path": {"type": "string", "description": "Path to the file"},
            "file_text": {"type": "string", "description": "Content for create command"},
            "old_str": {"type": "string", "description": "String to replace"},
            "new_str": {"type": "string", "description": "Replacement string"},
            "view_range": {
                "type": "array",
                "items": {"type": "number"},
                "description": "[start_line, end_line]",
            },
        },
        "required": ["command", "path"],
    }

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
            ".txt": "text",
        }
        return language_map.get(ext, "unknown")

    def run(self, tool_input: Dict[str, Any], agent: Optional[Any] = None) -> Dict[str, Any]:
        command = tool_input.get("command")
        path = tool_input.get("path")
        try:
            if command == "create":
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                content = tool_input.get("file_text", "")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                # Track file creation
                if agent is not None:
                    try:
                        agent.state.files_tracking[path] = {
                            "created": datetime.datetime.now().isoformat(),
                            "size": len(content),
                            "lines": content.count("\n") + 1,
                            "action": "created",
                            "language": self._detect_language(path),
                        }
                        agent.state.last_successful_operation = f"Created: {path}"
                    except Exception:
                        pass
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
                        "lines": content.count("\n") + 1,
                        "language": self._detect_language(path),
                    },
                }
            elif command == "view_range":
                view_range: List[int] = tool_input.get("view_range", [1, 1])
                start_line, end_line = view_range
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                content = "".join(lines[start_line - 1 : end_line])
                return {"success": True, "output": content}
            elif command == "str_replace":
                with open(path, "r", encoding="utf-8") as f:
                    original_content = f.read()
                old_str = tool_input.get("old_str", "")
                new_str = tool_input.get("new_str", "")
                if old_str not in original_content:
                    return {
                        "success": False,
                        "error": f"Text not found in {path}: {old_str[:50]}...",
                    }
                new_content = original_content.replace(old_str, new_str)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                # Track modification
                if agent is not None:
                    try:
                        agent.state.files_tracking[path] = {
                            "modified": datetime.datetime.now().isoformat(),
                            "size": len(new_content),
                            "lines": new_content.count("\n") + 1,
                            "action": "modified",
                            "language": self._detect_language(path),
                            "changes": {
                                "old_size": len(original_content),
                                "new_size": len(new_content),
                                "diff": len(new_content) - len(original_content),
                            },
                        }
                        agent.state.last_successful_operation = f"Modified: {path}"
                    except Exception:
                        pass
                return {
                    "success": True,
                    "output": f"Updated {path} (size changed by {len(new_content) - len(original_content)} chars)",
                }
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_tool() -> BaseTool:
    """Return an instance of :class:`StrReplaceEditorTool`."""
    return StrReplaceEditorTool()