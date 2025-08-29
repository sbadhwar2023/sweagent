"""
Base classes and interfaces for defining agent tools.

This module defines a small abstraction for tools that may be
registered with an AI agent. Each tool implementation should
subclass :class:`BaseTool` and override the ``run`` method. A
standardised interface makes it easy for the agent to reason
about available capabilities regardless of the underlying
implementation. The registry will introspect tool instances to
discover names, descriptions and input schemas for large
language model function calling.

Following the recommendations from the broader agent community,
each tool exposes:

* ``name`` – a concise identifier used when invoking the tool.
* ``description`` – a short human friendly description that
  explains what the tool does and when to use it.
* ``input_schema`` – a JSON schema describing the expected
  parameters. This schema is used to inform LLM providers about
  the shape of inputs.
* ``run`` – the method that performs the actual work. It
  accepts a dictionary of parameters and optionally a reference
  to the parent agent for stateful operations. It returns a
  dictionary with at least a ``success`` flag and either
  ``output`` or ``error`` keys.

By decoupling tool logic from the agent implementation you can
add, modify or remove tools without modifying the agent core.
Domain specific tools can live in their own modules and are
dynamically loaded by the tool registry at runtime.
"""

from __future__ import annotations

from typing import Dict, Any, Optional


class BaseTool:
    """Abstract base class for all agent tools.

    Tools should inherit from this class and override the
    :meth:`run` method. Tool authors should also set the
    ``name``, ``description`` and ``input_schema`` class
    attributes so that agents can correctly advertise and
    register the tool with large language models.
    """

    #: Unique tool name. Overridden by subclasses.
    name: str = ""
    #: Short, human-readable description of the tool.
    description: str = ""
    #: JSON schema describing the tool's expected inputs.
    input_schema: Dict[str, Any] = {}

    def run(self, tool_input: Dict[str, Any], agent: Optional[Any] = None) -> Dict[str, Any]:
        """Execute the tool with the provided arguments.

        Parameters
        ----------
        tool_input: Dict[str, Any]
            A dictionary of parameters parsed from the LLM function
            call. Keys and value types should conform to
            ``self.input_schema``.
        agent: Optional[Any]
            A reference back to the invoking agent. Tools that
            require access to agent state (for example to track
            progress, update file metadata or spawn sub‑agents)
            should accept this parameter and use it appropriately.

        Returns
        -------
        Dict[str, Any]
            A result object. On success it should include
            ``{"success": True, "output": ...}`` and on failure
            ``{"success": False, "error": ...}``. Additional
            metadata may be returned depending on the tool.
        """
        raise NotImplementedError("Tools must implement the run method")