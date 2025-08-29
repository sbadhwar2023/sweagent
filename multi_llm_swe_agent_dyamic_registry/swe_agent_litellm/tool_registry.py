"""
Dynamic tool registry for Professional SWE Agent.

This module provides a registry that discovers and loads tool
implementations from the ``tools`` package at runtime. Rather
than hardcoding a list of tools in the agent, the registry
introspects modules in the ``core`` and ``domain`` namespaces to
collect instances of :class:`BaseTool`. This allows you to
organise tools by domain, extend them without modifying the
agent core and enable or disable tools based on configuration.

Key responsibilities of the registry include:

* Discovering tool modules within configured directories.
* Instantiating tool classes and collecting their schemas.
* Providing a list of tool definitions in a format compatible
  with LLM function calling (name, description, parameters).
* Offering lookup of tool instances by name so that the agent
  can invoke them at runtime.

The registry is intentionally lightweight and does not depend
on any external frameworks. It uses ``importlib`` to dynamically
import modules. Tool definitions live in files that export either
``get_tool()`` returning a :class:`BaseTool` instance or define
classes inheriting from :class:`BaseTool`. When multiple tool
classes exist in a single module the first one discovered is
registered by default.
"""

from __future__ import annotations

import importlib
import inspect
import os
from types import ModuleType
from typing import Dict, List, Optional, Type

from .base_tool import BaseTool


class DynamicToolRegistry:
    """Manage dynamic discovery and registration of tools.

    The registry searches for Python modules in the provided
    ``search_paths``. Each module is expected to either provide a
    ``get_tool()`` function that returns a :class:`BaseTool`
    instance or define one or more subclasses of ``BaseTool``.
    Only one instance per module will be registered; if a module
    defines multiple subclasses of ``BaseTool`` you can expose a
    single entry point via ``get_tool()`` for clarity.

    Parameters
    ----------
    search_paths: List[str]
        A list of package path strings (e.g. ``swe_agent_litellm.tools.core``)
        to search for tool modules. Submodules under these
        packages will be discovered and loaded.
    config: Optional[Any]
        Optional configuration object. If provided, the registry
        may use it to filter out tools (for example disabling
        web or notebook related tools). The config is not used
        directly here but passed through to allow custom
        filtering logic when needed.
    """

    def __init__(self, search_paths: List[str], config: Optional[Any] = None) -> None:
        self.search_paths = search_paths
        self.config = config
        self._tools: Dict[str, BaseTool] = {}

    @property
    def tools(self) -> Dict[str, BaseTool]:
        """Return the registry of tool instances keyed by name."""
        return self._tools

    def load_tools(self) -> None:
        """Discover and load tool modules from the configured paths.

        This method iterates through all modules within the
        specified ``search_paths`` packages, imports them and
        attempts to extract a ``BaseTool`` instance. The lookup
        priority is:

        1. If the module defines a top‑level ``get_tool``
           function, call it and register the returned object.
        2. Otherwise, scan the module for classes that subclass
           ``BaseTool`` (excluding ``BaseTool`` itself) and
           instantiate the first one found with a no‑arg
           constructor.

        Modules that fail to import or do not expose a valid
        tool are silently skipped. If multiple tools share the
        same name, later registrations will overwrite earlier
        ones.
        """
        for pkg_path in self.search_paths:
            try:
                package = importlib.import_module(pkg_path)
            except Exception:
                continue
            # Walk the package directory to find modules
            pkg_dir = os.path.dirname(package.__file__)
            for filename in os.listdir(pkg_dir):
                if filename.startswith("_") or not filename.endswith(".py"):
                    continue
                module_name = filename[:-3]
                full_module_name = f"{pkg_path}.{module_name}"
                try:
                    module = importlib.import_module(full_module_name)
                except Exception:
                    # Skip modules that fail to import
                    continue
                tool = self._extract_tool_from_module(module)
                if tool:
                    # Optional filtering based on config
                    if self._should_register_tool(tool):
                        self._tools[tool.name] = tool

    def _extract_tool_from_module(self, module: ModuleType) -> Optional[BaseTool]:
        """Extract a tool instance from a loaded module.

        This helper attempts to call ``get_tool()`` if present.
        If not found, it scans for subclasses of ``BaseTool`` and
        instantiates the first one discovered. Returns ``None`` if
        no valid tool is found.
        """
        # First try get_tool
        if hasattr(module, "get_tool") and callable(getattr(module, "get_tool")):
            try:
                tool = module.get_tool()
                if isinstance(tool, BaseTool):
                    return tool
            except Exception:
                return None
        # Otherwise search for BaseTool subclasses
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseTool) and obj is not BaseTool:
                try:
                    return obj()  # type: ignore[call-arg]
                except Exception:
                    return None
        return None

    def _should_register_tool(self, tool: BaseTool) -> bool:
        """Determine whether a tool should be registered based on config.

        This method can be customised to filter tools at load time.
        For example, if the agent configuration has ``enable_web``
        set to ``False``, web-related tools can be skipped here.

        Currently the method performs simple checks on the tool name
        against known categories. If no configuration is provided
        all tools are registered.
        """
        if self.config is None:
            return True
        # Example filters: disable web or notebook tools
        name = tool.name.lower()
        try:
            if not getattr(self.config, "enable_web", True):
                if name in {"web_fetch", "web_search"}:
                    return False
            if not getattr(self.config, "enable_notebooks", True):
                if name == "notebook_edit":
                    return False
        except Exception:
            pass
        return True

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return the tool definitions formatted for LLM function calling.

        Each returned dictionary contains the name, description and
        parameters schema of the corresponding tool. These objects
        can be passed directly into ``litellm`` or similar LLM
        libraries that support function calling.
        """
        schemas = []
        for tool in self._tools.values():
            schemas.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
            )
        return schemas

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool instance by its name."""
        return self._tools.get(name)