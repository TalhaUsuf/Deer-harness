"""
memory_queue.py — Adapted copy of `deerflow.agents.memory.queue`.

Compared to the original: the only change is the lazy import of `MemoryUpdater`
inside `_process_queue` — instead of importing from
`deerflow.agents.memory.updater`, we use a local STUB updater defined at the
bottom of this file (`_StubMemoryUpdater`).

⚠ The stub does NOT actually persist any memory — it just logs that an update
would have happened. In the original codebase, `MemoryUpdater` runs an LLM
prompt to extract facts from the conversation and writes them atomically to
`memory.json`. To restore that behaviour, replace `_StubMemoryUpdater` with
your own implementation that exposes an
`update_memory(messages, thread_id, agent_name, correction_detected, reinforcement_detected) -> bool`
method.

Used by: MemoryMiddleware (calls `get_memory_queue().add(...)` after each turn).
External deps: stdlib only.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .memory_config import get_memory_config

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """One queued conversation awaiting memory extraction."""

    thread_id: str
    messages: list[Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    agent_name: str | None = None
    correction_detected: bool = False
    reinforcement_detected: bool = False


class MemoryUpdateQueue:
    """Debounced queue: many `add()` calls within `debounce_seconds` -> one flush.

    Per-thread deduplication: re-queueing for the same thread_id replaces the
    previous entry but ORs the correction/reinforcement flags so we never lose
    a positive signal that fired earlier in the debounce window.
    """

    def __init__(self):
        self._queue: list[ConversationContext] = []
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._processing = False

    def add(
        self,
        thread_id: str,
        messages: list[Any],
        agent_name: str | None = None,
        correction_detected: bool = False,
        reinforcement_detected: bool = False,
    ) -> None:
        """Queue a conversation; debounce timer is (re)set."""
        config = get_memory_config()
        if not config.enabled:
            return
        with self._lock:
            self._enqueue_locked(
                thread_id=thread_id,
                messages=messages,
                agent_name=agent_name,
                correction_detected=correction_detected,
                reinforcement_detected=reinforcement_detected,
            )
            self._reset_timer()
        logger.info(
            "Memory update queued for thread %s, queue size: %d",
            thread_id,
            len(self._queue),
        )

    def add_nowait(
        self,
        thread_id: str,
        messages: list[Any],
        agent_name: str | None = None,
        correction_detected: bool = False,
        reinforcement_detected: bool = False,
    ) -> None:
        """Like `add` but flushes immediately on a background thread."""
        config = get_memory_config()
        if not config.enabled:
            return
        with self._lock:
            self._enqueue_locked(
                thread_id=thread_id,
                messages=messages,
                agent_name=agent_name,
                correction_detected=correction_detected,
                reinforcement_detected=reinforcement_detected,
            )
            self._schedule_timer(0)
        logger.info(
            "Memory update queued for immediate processing on thread %s, queue size: %d",
            thread_id,
            len(self._queue),
        )

    def _enqueue_locked(
        self,
        *,
        thread_id: str,
        messages: list[Any],
        agent_name: str | None,
        correction_detected: bool,
        reinforcement_detected: bool,
    ) -> None:
        """Replace any existing context for this thread, OR-merging the flags.

        Caller must hold self._lock.
        """
        existing_context = next(
            (c for c in self._queue if c.thread_id == thread_id), None
        )
        merged_correction = correction_detected or (
            existing_context.correction_detected if existing_context is not None else False
        )
        merged_reinforcement = reinforcement_detected or (
            existing_context.reinforcement_detected if existing_context is not None else False
        )
        context = ConversationContext(
            thread_id=thread_id,
            messages=messages,
            agent_name=agent_name,
            correction_detected=merged_correction,
            reinforcement_detected=merged_reinforcement,
        )
        self._queue = [c for c in self._queue if c.thread_id != thread_id]
        self._queue.append(context)

    def _reset_timer(self) -> None:
        config = get_memory_config()
        self._schedule_timer(config.debounce_seconds)
        logger.debug("Memory update timer set for %ss", config.debounce_seconds)

    def _schedule_timer(self, delay_seconds: float) -> None:
        # Cancel any pending timer so the debounce window starts fresh.
        if self._timer is not None:
            self._timer.cancel()
        # Daemon=True so a hung memory update won't block process exit.
        self._timer = threading.Timer(delay_seconds, self._process_queue)
        self._timer.daemon = True
        self._timer.start()

    def _process_queue(self) -> None:
        """Drain the queue; called by the debounce timer."""
        # Lazy import (was: `from deerflow.agents.memory.updater import MemoryUpdater`).
        # In the standalone build this is a stub that logs without persisting.
        # Replace with your own implementation when wiring this folder into your app.
        with self._lock:
            if self._processing:
                # Another worker is mid-flight; reschedule to drain new entries.
                self._schedule_timer(0)
                return
            if not self._queue:
                return
            self._processing = True
            contexts_to_process = self._queue.copy()
            self._queue.clear()
            self._timer = None

        logger.info("Processing %d queued memory updates", len(contexts_to_process))
        try:
            updater = _StubMemoryUpdater()
            for context in contexts_to_process:
                try:
                    logger.info("Updating memory for thread %s", context.thread_id)
                    success = updater.update_memory(
                        messages=context.messages,
                        thread_id=context.thread_id,
                        agent_name=context.agent_name,
                        correction_detected=context.correction_detected,
                        reinforcement_detected=context.reinforcement_detected,
                    )
                    if success:
                        logger.info(
                            "Memory updated successfully for thread %s",
                            context.thread_id,
                        )
                    else:
                        logger.warning(
                            "Memory update skipped/failed for thread %s",
                            context.thread_id,
                        )
                except Exception as e:
                    logger.error(
                        "Error updating memory for thread %s: %s",
                        context.thread_id,
                        e,
                    )
                if len(contexts_to_process) > 1:
                    # Tiny gap so an LLM-backed updater does not get rate-limited.
                    time.sleep(0.5)
        finally:
            with self._lock:
                self._processing = False

    def flush(self) -> None:
        """Block-process the queue right now (for tests / graceful shutdown)."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
        self._process_queue()

    def flush_nowait(self) -> None:
        """Schedule an immediate process on a daemon thread."""
        with self._lock:
            self._schedule_timer(0)

    def clear(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._queue.clear()
            self._processing = False

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._queue)

    @property
    def is_processing(self) -> bool:
        with self._lock:
            return self._processing


# ── Singleton accessor ─────────────────────────────────────────────────────

_memory_queue: MemoryUpdateQueue | None = None
_queue_lock = threading.Lock()


def get_memory_queue() -> MemoryUpdateQueue:
    global _memory_queue
    with _queue_lock:
        if _memory_queue is None:
            _memory_queue = MemoryUpdateQueue()
        return _memory_queue


def reset_memory_queue() -> None:
    global _memory_queue
    with _queue_lock:
        if _memory_queue is not None:
            _memory_queue.clear()
        _memory_queue = None


# ── Stub updater ───────────────────────────────────────────────────────────


class _StubMemoryUpdater:
    """Drop-in replacement for `deerflow.agents.memory.updater.MemoryUpdater`.

    Real implementation: prompts an LLM to extract facts from the conversation
    and atomically rewrites memory.json. Because that pulls in the model
    factory, prompt templates, and a JSON storage layer, the standalone copy
    just no-ops with an informational log line.

    Replace this class with your own when you wire memory persistence into
    your app — keep the same `update_memory(...)` signature.
    """

    def update_memory(
        self,
        *,
        messages: list[Any],
        thread_id: str,
        agent_name: str | None,
        correction_detected: bool,
        reinforcement_detected: bool,
    ) -> bool:
        logger.info(
            "[stub] Would persist memory: thread=%s agent=%s msgs=%d "
            "correction=%s reinforcement=%s",
            thread_id,
            agent_name,
            len(messages),
            correction_detected,
            reinforcement_detected,
        )
        return False
