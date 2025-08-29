"""
Web search tool.

Perform a DuckDuckGo search and return formatted results. This
tool relies on the optional ``duckduckgo_search`` dependency; if
the library is not installed it returns an appropriate error.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List

from swe_agent_litellm.base_tool import BaseTool

try:
    from duckduckgo_search import DDGS  # type: ignore[import-not-found]
except Exception:
    DDGS = None  # type: ignore


class WebSearchTool(BaseTool):
    """Search the web for solutions and information."""

    name = "web_search"
    description = "Search the web for solutions and information"
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "number", "description": "Number of results", "default": 5},
        },
        "required": ["query"],
    }

    def run(self, tool_input: Dict[str, Any], agent: Optional[Any] = None) -> Dict[str, Any]:
        # Fail fast if dependency missing
        if DDGS is None:
            return {
                "success": False,
                "error": "Web search is unavailable because duckduckgo_search is not installed.",
            }
        try:
            query = tool_input.get("query", "")
            num_results = int(tool_input.get("num_results", 5))
            results: List[Dict[str, Any]] = []
            with DDGS() as ddgs:
                for i, result in enumerate(ddgs.text(query, max_results=num_results)):
                    results.append(result)
                    if i + 1 >= num_results:
                        break
            if not results:
                return {"success": False, "error": "No results found or query failed."}
            formatted_results = "\n\n".join([
                f"{i+1}. [{res['title']}]({res['href']})\n{res['body']}"
                for i, res in enumerate(results)
            ])
            return {
                "success": True,
                "output": f"🔍 Web search results for '{query}':\n\n{formatted_results}",
                "query": query,
                "placeholder": False,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_tool() -> BaseTool:
    return WebSearchTool()