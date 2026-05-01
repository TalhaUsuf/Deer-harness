"""
_internal — inlined helpers from the deerflow codebase.

Every symbol here was originally imported from `deerflow.*` somewhere in the
17 middleware files. To make the `standalone_middlewares/` folder copy-pasteable
into another project (which won't have the deerflow package), those helpers
have been carried into this private `_internal/` subpackage and the middlewares
rewritten to import from here instead.

Layout:
    thread_state.py         <- deerflow.agents.thread_state
    paths.py                <- deerflow.config.paths
    memory_config.py        <- deerflow.config.memory_config
    title_config.py         <- deerflow.config.title_config
    app_config.py           <- deerflow.config.app_config (MINIMAL STUB)
    memory_message_processing.py  <- deerflow.agents.memory.message_processing
    memory_queue.py         <- deerflow.agents.memory.queue (with stub updater)
    file_conversion.py      <- deerflow.utils.file_conversion (extract_outline only)
    tool_search_registry.py <- deerflow.tools.builtins.tool_search (registry only)
    models_factory.py       <- deerflow.models.factory (STUB; raises if invoked)
    subagent_const.py       <- deerflow.subagents.executor (only MAX_CONCURRENT_SUBAGENTS)

Modules marked STUB do NOT carry over the original implementation — the original
pulls in too much of deerflow's plumbing (config orchestration, model factory,
LLM-driven memory updater). Each stub raises a clear NotImplementedError or
returns a sensible default so the corresponding middleware still imports
cleanly. Wire the stub up to your environment's equivalent before relying on
the affected middleware in production.
"""
