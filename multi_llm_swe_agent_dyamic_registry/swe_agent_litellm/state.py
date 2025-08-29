"""State management structures for the SWE Agent.

This module defines a handful of dataclasses used to record the
working state of the agent, individual progress entries, and
summaries of conversation context. Persisting these objects allows
the agent to be restarted mid-task and to generate comprehensive
progress reports.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple


@dataclass
class ProgressEntry:
    """Representation of a single progress event in the agent's timeline.

    Attributes
    ----------
    timestamp: str
        ISO formatted timestamp when the action occurred.
    action: str
        Short description of the action performed.
    details: str
        Additional details about what happened.
    files_affected: List[str]
        Paths to files that were created or modified by the action.
    status: str
        The outcome of the action. One of ``"completed"``, ``"failed"`` or
        ``"skipped"``.
    """

    timestamp: str
    action: str
    details: str
    files_affected: List[str] = field(default_factory=list)
    status: str = "completed"


@dataclass
class ConversationSummary:
    """A summary of conversation context for compressing long tasks.

    Attributes
    ----------
    summary_id: str
        Unique identifier for this summary.
    iterations_covered: Tuple[int, int]
        Inclusive range of iterations that this summary covers.
    key_accomplishments: List[str]
        Highlights of what was accomplished during the covered iterations.
    current_focus: str
        Brief description of what the agent was focusing on at the end of the
        covered iterations.
    next_steps: List[str]
        Suggested next actions to take following the end of the summary.
    files_created_modified: List[str]
        List of files that were created or modified during the covered
        iterations.
    errors_resolved: List[str]
        A list of error messages that were encountered and resolved.
    timestamp: str
        ISO formatted timestamp when the summary was created.
    """

    summary_id: str
    iterations_covered: Tuple[int, int]
    key_accomplishments: List[str]
    current_focus: str
    next_steps: List[str]
    files_created_modified: List[str]
    errors_resolved: List[str]
    timestamp: str


@dataclass
class AgentState:
    """Persistent state for the :class:`ProfessionalSWEAgent`.

    This structure contains the high level context required to resume a
    task mid-way through, including the task identifier, the original
    user request, lists of completed steps, progress entries, summaries
    and any files created or modified so far. It also records error
    information for later debugging and provides a place to attach
    sub-agent results.
    """

    task_id: str
    original_task: str
    completed_steps: List[str]
    current_step: str
    error_history: List[Dict]
    iteration_count: int
    last_successful_operation: str
    working_context: Dict[str, Any]
    progress_entries: List[ProgressEntry] = field(default_factory=list)
    conversation_summaries: List[ConversationSummary] = field(default_factory=list)
    files_tracking: Dict[str, Dict] = field(default_factory=dict)
    sub_agent_results: List[Dict] = field(default_factory=list)
