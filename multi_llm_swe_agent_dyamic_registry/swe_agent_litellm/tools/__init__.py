"""
Tool collection package.

This namespace package exposes two subpackages: ``core`` and
``domain``. Core tools provide general purpose capabilities such
as file editing, bash execution and search. Domain tools can be
added independently for specialised tasks (e.g. finance or
healthcare operations). New modules placed under these
directories will be automatically loaded by the
:class:`~swe_agent_litellm.tool_registry.DynamicToolRegistry`.

When creating a new tool, define a subclass of
:class:`~swe_agent_litellm.base_tool.BaseTool` or provide a
``get_tool()`` function returning an instance. Make sure to
populate the ``name``, ``description`` and ``input_schema``
attributes so that the agent can advertise and call your tool
properly.
"""

from . import core  # noqa: F401
from . import domain  # noqa: F401

from ..tool_registry import DynamicToolRegistry

def create_professional_tool_schema(config=None):
    """Return the full professional tool schema using the dynamic registry.

    This helper maintains backwards compatibility with earlier
    versions of the package that exposed a fixed list of tool
    definitions. It instantiates a :class:`DynamicToolRegistry`,
    loads all available tools and returns their schemas. An
    optional configuration may be supplied to filter out
    web or notebook tools.

    Parameters
    ----------
    config: Optional[Any]
        Agent configuration used to determine which tools to
        register. If not provided, all tools are included.

    Returns
    -------
    List[Dict[str, Any]]
        A list of tool definitions with ``name``, ``description``
        and ``input_schema`` keys.
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