from __future__ import annotations

import importlib
import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from queue import Empty, Queue
from typing import Any

from flarchitect.logging import logger


@dataclass
class _Subscription:
    topic: str
    queue: Queue


class _EventBus:
    """Very small in-memory pub/sub used for WebSocket broadcasting.

    - Topics are free-form strings (e.g. "all", "author", "book").
    - Subscribers receive JSON-serialisable dict messages.
    - This is process-local and non-durable; intended for development and
      single-process deployments. For production, prefer a real broker
      (Redis, NATS, etc.) and swap out publish/subscribe implementations.
    """

    def __init__(self) -> None:
        self._subs: defaultdict[str, set[Queue]] = defaultdict(set)
        self._lock = threading.Lock()

    def subscribe(self, topic: str) -> _Subscription:
        q: Queue = Queue()
        with self._lock:
            self._subs[topic].add(q)
        logger.debug(5, f"Subscribed queue to topic '{topic}'")
        return _Subscription(topic=topic, queue=q)

    def unsubscribe(self, sub: _Subscription) -> None:
        with self._lock:
            queues = self._subs.get(sub.topic)
            if queues and sub.queue in queues:
                queues.remove(sub.queue)
                if not queues:
                    self._subs.pop(sub.topic, None)
        logger.debug(5, f"Unsubscribed queue from topic '{sub.topic}'")

    def publish(self, topic: str, message: dict[str, Any]) -> None:
        with self._lock:
            # deliver to explicit topic and to 'all'
            targets = set(self._subs.get(topic, set())) | set(self._subs.get("all", set()))
        import contextlib
        for q in targets:
            with contextlib.suppress(Exception):  # pragma: no cover - defensive
                q.put_nowait(message)


_BUS = _EventBus()


def broadcast_change(*, model: Any | None, method: str, payload: Any, id: Any | None = None, many: bool = False) -> None:
    """Publish a change event to WebSocket subscribers.

    Args:
        model: SQLAlchemy model class the change applies to.
        method: The HTTP method that triggered the change (GET/POST/PATCH/DELETE).
        payload: Marshmallow-serialised output returned to the client.
        id: Optional primary key for single-object operations.
        many: Whether the payload contains multiple items.
    """
    try:
        model_name = model.__name__.lower() if model is not None else "unknown"
        message = {
            "ts": int(time.time() * 1000),
            "model": model_name,
            "method": method.upper(),
            "id": id,
            "many": bool(many),
            "payload": payload,
        }
        _BUS.publish(model_name, message)
        _BUS.publish("all", message)
        logger.debug(5, f"Broadcasted WS message for '{model_name}' {method}")
    except Exception as exc:  # pragma: no cover - best effort only
        logger.debug(4, f"WebSocket broadcast skipped: {exc}")


def init_websockets(architect: Any, path: str = "/ws") -> None:  # pragma: no cover - requires optional flask_sock runtime
    """Attach a minimal WebSocket endpoint if Flask-Sock is available.

    The endpoint accepts optional query parameters:
      - topic: subscribe to a specific model topic (defaults to 'all')

    Message format is JSON lines, one per event as emitted by ``broadcast_change``.

    This function is a no-op if the optional dependency ``flask_sock`` is not
    installed.
    """
    try:
        spec = importlib.util.find_spec("flask_sock")
        if spec is None:
            logger.debug(3, "flask_sock not installed; WebSocket endpoint not registered")
            return

        from flask import request
        from flask_sock import Sock  # type: ignore

        sock = Sock(architect.app)

        @sock.route(path)
        def ws(sock):  # type: ignore
            topic = (request.args.get("topic") or "all").lower()
            sub = _BUS.subscribe(topic)
            try:
                while True:
                    try:
                        msg = sub.queue.get(timeout=1.0)
                    except Empty:
                        # keep connection alive; allow client pings to be handled
                        continue
                    try:
                        sock.send(json.dumps(msg))
                    except Exception:
                        break
            finally:
                _BUS.unsubscribe(sub)

        logger.log(2, f"Registered WebSocket route at '{path}' using flask_sock")
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(3, f"Failed to initialise WebSocket endpoint: {exc}")
