"""
paths.py — VERBATIM copy of `deerflow.config.paths`.

Used by:
    ThreadDataMiddleware — to compute per-thread workspace/uploads/outputs dirs
    UploadsMiddleware    — to read the historical uploads dir for a thread

The class encapsulates a directory layout convention; nothing here depends on
any other deerflow module. Only stdlib (`os`, `re`, `shutil`, `pathlib`).

Two environment variables affect path resolution:
    DEER_FLOW_HOME           — overrides the base data directory.
    DEER_FLOW_HOST_BASE_DIR  — host-side path for Docker bind mounts when
                               running inside a container with /var/run/docker.sock
                               passed through (DooD).
"""

import os
import re
import shutil
from pathlib import Path, PureWindowsPath

# Inside the sandbox container, agents see this prefix; host-side it maps to
# {base_dir}/threads/{thread_id}/user-data/ via Docker volume mounts.
VIRTUAL_PATH_PREFIX = "/mnt/user-data"

# Defensive: thread IDs are eventually used as path components. A malicious
# thread_id like "../../etc" would otherwise allow filesystem escape.
_SAFE_THREAD_ID_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


def _default_local_base_dir() -> Path:
    """Repo-local fallback: `<package-root>/.deer-flow/`.

    Computed from THIS module's __file__ so it stays correct regardless of
    where the process was launched from. In the standalone copy this resolves
    to <wherever-this-folder-lives>/.deer-flow/ — adjust if you want a fixed
    location.
    """
    backend_dir = Path(__file__).resolve().parents[4]
    return backend_dir / ".deer-flow"


def _validate_thread_id(thread_id: str) -> str:
    if not _SAFE_THREAD_ID_RE.match(thread_id):
        raise ValueError(
            f"Invalid thread_id {thread_id!r}: only alphanumeric characters, "
            "hyphens, and underscores are allowed."
        )
    return thread_id


def _join_host_path(base: str, *parts: str) -> str:
    """Join host filesystem path segments while preserving native style.

    Docker Desktop on Windows expects bind mount sources in Windows form
    (e.g. `C:\\repo\\backend\\.deer-flow`). Using `Path(base) / ...` on a POSIX
    host can mangle Windows paths into mixed-separator strings, so this helper
    detects Windows-style inputs and uses `PureWindowsPath` for them.
    """
    if not parts:
        return base
    if re.match(r"^[A-Za-z]:[\\/]", base) or base.startswith("\\\\") or "\\" in base:
        result = PureWindowsPath(base)
        for part in parts:
            result /= part
        return str(result)
    result = Path(base)
    for part in parts:
        result /= part
    return str(result)


def join_host_path(base: str, *parts: str) -> str:
    """Public alias for `_join_host_path` — exported for callers outside this module."""
    return _join_host_path(base, *parts)


class Paths:
    """Centralized path configuration for DeerFlow application data.

    Layout (host side):
        {base_dir}/
        ├── memory.json
        ├── USER.md
        ├── agents/{agent_name}/{config.yaml,SOUL.md,memory.json}
        └── threads/{thread_id}/
            └── user-data/      <- mounted as /mnt/user-data inside sandbox
                ├── workspace/
                ├── uploads/
                └── outputs/

    base_dir resolution priority:
        1. constructor `base_dir` arg
        2. DEER_FLOW_HOME environment variable
        3. `_default_local_base_dir()` (repo-local fallback)
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self._base_dir = Path(base_dir).resolve() if base_dir is not None else None

    @property
    def host_base_dir(self) -> Path:
        """Host-visible base dir for Docker bind mounts.

        When this process runs inside a container with the Docker socket
        mounted, the daemon resolves bind sources against the host filesystem.
        DEER_FLOW_HOST_BASE_DIR lets you point the daemon at the host path.
        """
        if env := os.getenv("DEER_FLOW_HOST_BASE_DIR"):
            return Path(env)
        return self.base_dir

    def _host_base_dir_str(self) -> str:
        if env := os.getenv("DEER_FLOW_HOST_BASE_DIR"):
            return env
        return str(self.base_dir)

    @property
    def base_dir(self) -> Path:
        if self._base_dir is not None:
            return self._base_dir
        if env_home := os.getenv("DEER_FLOW_HOME"):
            return Path(env_home).resolve()
        return _default_local_base_dir()

    @property
    def memory_file(self) -> Path:
        return self.base_dir / "memory.json"

    @property
    def user_md_file(self) -> Path:
        return self.base_dir / "USER.md"

    @property
    def agents_dir(self) -> Path:
        return self.base_dir / "agents"

    def agent_dir(self, name: str) -> Path:
        return self.agents_dir / name.lower()

    def agent_memory_file(self, name: str) -> Path:
        return self.agent_dir(name) / "memory.json"

    def thread_dir(self, thread_id: str) -> Path:
        return self.base_dir / "threads" / _validate_thread_id(thread_id)

    def sandbox_work_dir(self, thread_id: str) -> Path:
        return self.thread_dir(thread_id) / "user-data" / "workspace"

    def sandbox_uploads_dir(self, thread_id: str) -> Path:
        return self.thread_dir(thread_id) / "user-data" / "uploads"

    def sandbox_outputs_dir(self, thread_id: str) -> Path:
        return self.thread_dir(thread_id) / "user-data" / "outputs"

    def acp_workspace_dir(self, thread_id: str) -> Path:
        return self.thread_dir(thread_id) / "acp-workspace"

    def sandbox_user_data_dir(self, thread_id: str) -> Path:
        return self.thread_dir(thread_id) / "user-data"

    def host_thread_dir(self, thread_id: str) -> str:
        return _join_host_path(
            self._host_base_dir_str(), "threads", _validate_thread_id(thread_id)
        )

    def host_sandbox_user_data_dir(self, thread_id: str) -> str:
        return _join_host_path(self.host_thread_dir(thread_id), "user-data")

    def host_sandbox_work_dir(self, thread_id: str) -> str:
        return _join_host_path(self.host_sandbox_user_data_dir(thread_id), "workspace")

    def host_sandbox_uploads_dir(self, thread_id: str) -> str:
        return _join_host_path(self.host_sandbox_user_data_dir(thread_id), "uploads")

    def host_sandbox_outputs_dir(self, thread_id: str) -> str:
        return _join_host_path(self.host_sandbox_user_data_dir(thread_id), "outputs")

    def host_acp_workspace_dir(self, thread_id: str) -> str:
        return _join_host_path(self.host_thread_dir(thread_id), "acp-workspace")

    def ensure_thread_dirs(self, thread_id: str) -> None:
        """Create all standard sandbox dirs for a thread with mode 0o777.

        The explicit chmod() is required because `Path.mkdir(mode=...)` is
        masked by the process umask; sandbox containers may run as a different
        UID than the host process and need world-writable mount sources.
        """
        for d in [
            self.sandbox_work_dir(thread_id),
            self.sandbox_uploads_dir(thread_id),
            self.sandbox_outputs_dir(thread_id),
            self.acp_workspace_dir(thread_id),
        ]:
            d.mkdir(parents=True, exist_ok=True)
            d.chmod(0o777)

    def delete_thread_dir(self, thread_id: str) -> None:
        """Idempotent: missing thread directories are silently ignored."""
        thread_dir = self.thread_dir(thread_id)
        if thread_dir.exists():
            shutil.rmtree(thread_dir)

    def resolve_virtual_path(self, thread_id: str, virtual_path: str) -> Path:
        """Translate a sandbox virtual path to the host filesystem path.

        Defends against path traversal: requires segment-boundary match on the
        prefix and verifies the resolved path is contained within base.
        """
        stripped = virtual_path.lstrip("/")
        prefix = VIRTUAL_PATH_PREFIX.lstrip("/")
        if stripped != prefix and not stripped.startswith(prefix + "/"):
            raise ValueError(f"Path must start with /{prefix}")
        relative = stripped[len(prefix) :].lstrip("/")
        base = self.sandbox_user_data_dir(thread_id).resolve()
        actual = (base / relative).resolve()
        try:
            actual.relative_to(base)
        except ValueError:
            raise ValueError("Access denied: path traversal detected")
        return actual


# ── Singleton accessor ────────────────────────────────────────────────────

_paths: Paths | None = None


def get_paths() -> Paths:
    """Lazy singleton Paths() instance — most call sites use this."""
    global _paths
    if _paths is None:
        _paths = Paths()
    return _paths


def resolve_path(path: str) -> Path:
    """Resolve a path string; relative paths are anchored at base_dir."""
    p = Path(path)
    if not p.is_absolute():
        p = get_paths().base_dir / path
    return p.resolve()
