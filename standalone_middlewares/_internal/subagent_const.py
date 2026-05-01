"""
subagent_const.py — Single constant carried over from
`deerflow.subagents.executor`.

The original `executor.py` is ~600 lines of subagent-execution machinery
(thread pools, scheduler, SSE event emission). SubagentLimitMiddleware only
imports the constant `MAX_CONCURRENT_SUBAGENTS`, so that is all that lives
here.

If your environment runs more or fewer subagents in parallel, change this
value (the middleware also clamps user-supplied limits to [2, 4] regardless,
see `subagent_limit_middleware.py` for the clamping logic).
"""

# Hard cap on parallel `task` tool calls per LLM response.
MAX_CONCURRENT_SUBAGENTS = 3
