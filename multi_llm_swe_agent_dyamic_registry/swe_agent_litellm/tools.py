"""Tool schema definitions for the SWE Agent (legacy entry point).

This module originally contained a static list of tool definitions. In order
to support a dynamic and extensible tool registry, the implementation
has been simplified to defer discovery to the new
``DynamicToolRegistry`` class. Calling ``create_professional_tool_schema``
will instantiate a registry, scan the ``swe_agent_litellm.tools.core``
and ``swe_agent_litellm.tools.domain`` packages, and return the
schemas of all loaded tools. This preserves backwards compatibility
with older code that imported from ``tools.py`` while encouraging
newer designs to depend directly on the dynamic registry.

Note
----
You should prefer importing :class:`DynamicToolRegistry` from
``swe_agent_litellm.tool_registry`` and using it directly when adding
new tool categories or custom filtering logic. This module remains
only as a convenience wrapper.
"""

from typing import List, Dict, Any, Optional

from .tool_registry import DynamicToolRegistry


def create_professional_tool_schema(config: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Return the full professional tool schema using the dynamic registry.

    This function instantiates a :class:`DynamicToolRegistry`, loads all
    available tools from the configured search paths and returns their
    schemas. An optional configuration object may be provided to
    filter tools (e.g. disabling web or notebook functionality).

    Parameters
    ----------
    config: Optional[Any]
        Agent configuration used to determine which tools to register.
        If not provided, all discovered tools are included.

    Returns
    -------
    List[Dict[str, Any]]
        A list of tool definitions with ``name``, ``description`` and
        ``input_schema`` keys, suitable for use with LLM function
        calling APIs.
    """
    registry = DynamicToolRegistry(
        [
            "swe_agent_litellm.tools.core",
            "swe_agent_litellm.tools.domain",
        ],
        config=config,
    )
    registry.load_tools()
    return registry.get_tool_schemas()
