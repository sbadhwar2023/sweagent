"""Command line interface for the Professional SWE Agent.

This script exposes a minimal CLI for running the agent from the
terminal. It parses common arguments such as working directory,
iteration limits, debug toggles and resume support before
instantiating the agent and delegating execution to it. Upon
completion, a summary of the run is printed to stdout.
"""

import argparse
import os

from .config import Config
from .agent import ProfessionalSWEAgent


def main() -> None:
    """Entry point for running the SWE agent from the command line.

    This CLI parses standard options such as the working directory,
    iteration limits, model selection and debug flags. It initialises a
    :class:`Config` object, instantiates the agent and runs the task,
    finally printing a concise summary of the run. API keys may be
    supplied via command line or environment variables.
    """
    parser = argparse.ArgumentParser(
        description="Professional SWE Agent - Complete AI Code Assistant with LiteLLM support"
    )
    parser.add_argument("task", nargs="*", help="Task description")
    parser.add_argument("--working-dir", default=".", help="Working directory")
    parser.add_argument("--max-iterations", type=int, default=50, help="Maximum iterations")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--resume", help="Resume task by ID")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress.md tracking")
    parser.add_argument("--no-web", action="store_true", help="Disable web tools")
    parser.add_argument("--no-notebooks", action="store_true", help="Disable notebook tools")
    parser.add_argument(
        "--model",
        default="claude-3-5-sonnet-20241022",
        help="Primary LLM model identifier (e.g. gpt-4-turbo, claude-3-5-sonnet-20241022)",
    )
    parser.add_argument(
        "--models",
        help="Comma-separated list of LLM models to try in order for fallback",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key_arg",
        help="API key for the chosen LLM provider (overrides environment variables)",
    )
    args = parser.parse_args()

    # Determine the API key: use the explicit argument if provided, otherwise
    # fall back to common environment variables. It is acceptable for this to
    # be ``None``; the agent will rely on provider-specific environment
    # variables (e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY) if available.
    api_key = (
        args.api_key_arg
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("MISTRAL_API_KEY")
    )

    # Parse multiple models if provided
    model_list = None
    if args.models:
        model_list = [m.strip() for m in args.models.split(",") if m.strip()]

    # Build configuration object
    config = Config(
        api_key=api_key,
        model=args.model,
        models=model_list,
        working_dir=args.working_dir,
        max_iterations=args.max_iterations,
        debug_mode=args.debug,
        progress_tracking=not args.no_progress,
        enable_web=not args.no_web,
        enable_notebooks=not args.no_notebooks,
    )

    try:
        agent = ProfessionalSWEAgent(config)
        if args.resume:
            result = agent.execute_task("", resume_task_id=args.resume)
        else:
            task = " ".join(args.task) if args.task else input("Enter comprehensive task: ").strip()
            if not task:
                print("❌ No task provided")
                return
            result = agent.execute_task(task)
        print(f"\n📊 Professional Agent Final Summary:")
        print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
        print(f"🔄 Iterations: {result['iterations']}")
        print(f"🆔 Task ID: {result['task_id']}")
        print(f"🔧 Tools Used: {result.get('tools_used', len(agent.tools))}")
        if result.get('files_created'):
            print(f"📁 Files Created/Modified: {result['files_created']}")
        if result.get('sub_agents_spawned'):
            print(f"🤖 Sub-Agents Spawned: {result['sub_agents_spawned']}")
        if config.progress_tracking:
            print(f"📋 Comprehensive progress report: {config.progress_file}")
        if not result["success"] and result.get("resume_possible"):
            print(f"💾 Task can be resumed with: --resume {result['task_id']}")
    except KeyboardInterrupt:
        print("\n👋 Interrupted - comprehensive state and progress saved")
    except Exception as e:
        print(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
