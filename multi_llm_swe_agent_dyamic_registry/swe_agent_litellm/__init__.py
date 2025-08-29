"""Top-level package for the SWE Agent.

This package exposes the main classes and functions needed to use the
software engineering agent. Importing from this module will bring
into scope the configuration, state, display helpers, tool schema,
and the primary agent class used to execute tasks.
"""

from .config import Config
from .state import AgentState, ProgressEntry, ConversationSummary
from .display import AgentDisplay
from .tools import create_professional_tool_schema
from .agent import ProfessionalSWEAgent

__all__ = [
    "Config",
    "AgentState",
    "ProgressEntry",
    "ConversationSummary",
    "AgentDisplay",
    "create_professional_tool_schema",
    "ProfessionalSWEAgent",
]