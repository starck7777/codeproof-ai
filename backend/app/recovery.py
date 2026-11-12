"""Explicit stale-worker recovery; never reruns an agent after hidden evaluation."""

import os
import time

from redis import Redis

from . import store
from .worker import TERMINAL


def recover():
    connection = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    recovered = []
    for run in store.listing("run", limit=10000):
        for identity in run["attempt_ids"]:
            attempt = store.get(identity)
            if attempt["status"] in TERMINAL:
                continue
            heartbeat = attempt.get("heartbeat", run["created"])
            stale_after = (
                attempt["budget"]["seconds"] + 180 if attempt["status"] != "Queued" else 1800
            )
            if time.time() - heartbeat > stale_after and not connection.exists(
                "attempt:" + identity
            ):
                attempt["status"] = "Failed"
                attempt["failure_category"] = "infrastructure"
                attempt["stop_reason"] = (
                    "Worker interrupted; no automatic repair retry after evaluation"
                )
                attempt["recovery_record"] = {"time": time.time(), "previous_heartbeat": heartbeat}
                store.save(identity, "attempt", attempt)
                recovered.append(identity)
    return recovered


if __name__ == "__main__":
    print(recover())
