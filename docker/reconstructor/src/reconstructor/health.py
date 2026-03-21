import threading
import time
from dataclasses import dataclass, field

import uvicorn
from litestar import Litestar, get
from typing import Any

from litestar.response import Response

# How long the worker can go without polling before we report unhealthy.
# During a reconstruction, the loop blocks — so this must be generous.
_MAX_IDLE_SECONDS = 3600  # 1 hour (reconstructions can be long)


@dataclass
class WorkerHealth:
    """Thread-safe health state shared between the worker loop and the HTTP probe."""

    last_poll: float = field(default_factory=time.monotonic)
    last_token_ok: float = 0.0
    consecutive_auth_failures: int = 0
    started: bool = False

    def record_poll(self) -> None:
        self.last_poll = time.monotonic()

    def record_token_ok(self) -> None:
        self.last_token_ok = time.monotonic()
        self.consecutive_auth_failures = 0

    def record_auth_failure(self) -> None:
        self.consecutive_auth_failures += 1


_state = WorkerHealth()


def get_health_state() -> WorkerHealth:
    return _state


@get("/health")
async def health_check() -> Response[dict[str, Any]]:
    if not _state.started:
        return Response({"status": "starting"}, status_code=503)

    if _state.consecutive_auth_failures >= 5:
        return Response(
            {"status": "unhealthy", "reason": "auth_failing", "consecutive_failures": _state.consecutive_auth_failures},
            status_code=503,
        )

    idle = time.monotonic() - _state.last_poll
    if idle > _MAX_IDLE_SECONDS:
        return Response(
            {"status": "unhealthy", "reason": "idle_too_long", "idle_seconds": int(idle)},
            status_code=503,
        )

    return Response({"status": "ok"}, status_code=200)


def start_health_server(port: int = 8001) -> None:
    """Run a minimal Litestar health server on a daemon thread."""
    app = Litestar([health_check])

    def _run() -> None:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

    thread = threading.Thread(target=_run, daemon=True, name="health-server")
    thread.start()
