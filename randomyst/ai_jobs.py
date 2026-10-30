"""Bounded, volatile reading jobs; SSE observers never own the paid worker."""
import asyncio
import json
from threading import Lock
import time


class ReadingJob:
    def __init__(self):
        self.lock = Lock()
        self.stage = "QUEUED"
        self.revision = 0
        self.finished_at = None
        self.result = None
        self.error = None
        self.deadline = time.monotonic() + 1500

    def progress(self, stage):
        with self.lock:
            self.stage = stage
            self.revision += 1

    def finish(self, *, result=None, error=None):
        with self.lock:
            self.result, self.error = result, error
            self.finished_at = time.monotonic()
            self.revision += 1

    def snapshot(self):
        with self.lock:
            return self.revision, self.stage, self.finished_at, self.result, self.error


def event(name, data):
    return "event: " + name + "\ndata: " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n\n"


async def reading_events(job, *, heartbeat=10, poll=0.2):
    if job is None:
        yield event("missing", {})
        return
    revision, sent_at = -1, 0
    while True:
        current, stage, finished, result, error = job.snapshot()
        if finished is not None:
            yield event("error", {"error": error}) if error else event("result", result)
            return
        if current != revision:
            revision, sent_at = current, time.monotonic()
            yield event("progress", {"stage": stage})
        elif time.monotonic() - sent_at >= heartbeat:
            sent_at = time.monotonic()
            yield ": keep-alive\n\n"
        # Cancellation/disconnection only stops this observer. The bounded
        # worker continues and later observers receive the same saved result.
        await asyncio.sleep(poll)
