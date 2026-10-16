"""Characterize Retry-After/timeout behavior in the *unmodified* azure-core SDK.

No Azure account, remote endpoint or real 120-second delay is involved.
Do not mistake virtual transport.sleep() observations for production timings.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import platform
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from azure.core.pipeline import AsyncPipeline, Pipeline
from azure.core.pipeline.policies import AsyncRetryPolicy, RetryPolicy
from azure.core.pipeline.transport import HttpRequest
import azure.core.pipeline.policies._retry as sync_retry_module
import azure.core.pipeline.policies._retry_async as async_retry_module

START = 1_700_000_000.0
SERVER_DELAY_SECONDS = 120.0
OPERATION_TIMEOUT_SECONDS = 1.0


class VirtualClock:
    def __init__(self):
        self.now = START
        self.sleeps = []

    def time(self):
        return self.now

    def sleep(self, delay):
        duration = float(delay)
        self.sleeps.append(duration)
        self.now += duration


class FakeTransport:
    """A deterministic transport. It NEVER opens a socket."""

    def __init__(self, clock):
        self.clock = clock
        self.calls = 0

    def open(self):
        pass

    def close(self):
        pass

    def send(self, request, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return SimpleNamespace(status_code=429, headers={"Retry-After": "120"})
        return SimpleNamespace(status_code=200, headers={})

    def sleep(self, duration):
        self.clock.sleep(duration)


class FakeAsyncTransport(FakeTransport):
    async def send(self, request, **kwargs):
        return super().send(request, **kwargs)

    async def sleep(self, duration):
        self.clock.sleep(duration)


def summarize(transport, clock, response=None, error=None):
    return {
        "transport_calls": transport.calls,
        "sleep_calls_seconds": clock.sleeps,
        "virtual_elapsed_seconds": clock.now - START,
        "outcome": "exception" if error is not None else "response",
        "exception_type": type(error).__name__ if error is not None else None,
        "response_status": (
            response.http_response.status_code if response is not None else None
        ),
    }


def run_sync():
    clock = VirtualClock()
    transport = FakeTransport(clock)
    response = error = None
    with patch.object(sync_retry_module, "time", SimpleNamespace(time=clock.time)):
        try:
            response = Pipeline(
                transport, [RetryPolicy(timeout=1, retry_total=1)]
            ).run(HttpRequest("GET", "https://example.invalid"))
        except Exception as exc:
            error = exc
    return summarize(transport, clock, response, error)


async def run_async():
    clock = VirtualClock()
    transport = FakeAsyncTransport(clock)
    response = error = None
    with patch.object(sync_retry_module, "time", SimpleNamespace(time=clock.time)), \
         patch.object(async_retry_module, "time", SimpleNamespace(time=clock.time)):
        try:
            response = await AsyncPipeline(
                transport, [AsyncRetryPolicy(timeout=1, retry_total=1)]
            ).run(HttpRequest("GET", "https://example.invalid"))
        except Exception as exc:
            error = exc
    return summarize(transport, clock, response, error)


def matches_source_prediction(observed):
    return all(
        result["sleep_calls_seconds"] == [SERVER_DELAY_SECONDS]
        and result["transport_calls"] == 1
        and result["outcome"] == "exception"
        and result["exception_type"] in {
            "ServiceResponseTimeoutError",
            "ServiceRequestTimeoutError",
        }
        for result in observed.values()
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="azure-retry-evidence.json")
    args = parser.parse_args()

    observed = {"sync": run_sync(), "async": asyncio.run(run_async())}
    agrees = matches_source_prediction(observed)
    evidence = {
        "test": "unmodified azure-core Pipeline retry after + timeout",
        "sdk": "azure-core",
        "sdk_version": importlib.metadata.version("azure-core"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "http_response": {"status": 429, "retry_after": "120"},
        "configured_operation_timeout_seconds": OPERATION_TIMEOUT_SECONDS,
        "configured_retry_total": 1,
        "real_network_requests": 0,
        "fake_transport": True,
        "virtual_wall_clock": True,
        "observed": observed,
        "source_prediction_confirmed": agrees,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))

    if not agrees:
        print("OBSERVATIONS DIFFER: preserve JSON and investigate; do not claim reproduction.")
        return 1
    print("SOURCE PREDICTION CONFIRMED in both official SDK pipelines (virtual time).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
