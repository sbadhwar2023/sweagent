"""
Core tools for the Professional SWE Agent.

This subpackage contains implementations of general purpose
capabilities such as executing shell commands, manipulating
files, searching directories, managing tasks and progress,
fetching web content, and editing Jupyter notebooks. These
tools are loaded by default and are suitable for most
software–engineering workflows.

To extend the agent with additional core tools, create a new
module in this directory and define a subclass of
:class:`~swe_agent_litellm.base_tool.BaseTool` or expose a
``get_tool()`` function returning an instance.
"""