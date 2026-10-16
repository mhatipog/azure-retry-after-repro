# UPSTREAM ISSUE DRAFT — OFFICIAL SDK BEHAVIOR REPRODUCED

Proposed title: **[azure-core] Retry-After wait appears to exceed RetryPolicy operation timeout (sync + async)**

## Summary

The official `azure-core` retry policy appears to request an HTTP transport sleep of 120 seconds after `429 Retry-After: 120` even with `RetryPolicy(timeout=1)`. The configured timeout may be checked only on a subsequent retry attempt.

The intended semantics of the `timeout` option should be confirmed with maintainers before describing this as a definitive bug.

## Reproduction — verified on GitHub Actions

This repository contains `azure_retry_after_repro.py`, a **no-network** characterization using:

- Unmodified published `azure-core==1.41.0`.
- Real `Pipeline`, `AsyncPipeline`, `RetryPolicy`, and `AsyncRetryPolicy`.
- A local fake transport that returns HTTP 429 with `Retry-After: 120`.
- A virtual wall clock to observe whether `transport.sleep(120)` is requested despite a one-second operation timeout.
- Raw JSON evidence for both Python 3.11 and 3.13, uploaded by GitHub Actions.

**Verified results:**

- [GitHub Actions run #3](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616) — two successful jobs, official `azure-core==1.41.0`.
- [Python 3.11 artifact](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616/artifacts/12027610082) / [Python 3.13 artifact](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616/artifacts/12027600121).
- Source commit (PR head): `601073c36df4644856bb55b5d67b3f52bf1e6d56`.
- **Sync:** requested sleep `[120.0]` seconds; one transport request; `ServiceResponseTimeoutError` after advancing virtual wall clock.
- **Async:** identical to sync on both Python versions.
- This is an observed virtual-clock sleep **request**, not an actual 120-second wall-clock delay.

## Expected

If the retry timeout represents a total operation budget inclusive of waiting, stop instead of sleeping beyond the remaining budget. **Never retry earlier than the server's Retry-After requirement.**

## Actual

**Verified in official unmodified published `azure-core==1.41.0`** under an in-memory transport and virtual clock, on Python 3.11.17 and 3.13.16. Both sync and async pipelines invoked `transport.sleep(120)` despite `timeout=1`, then raised `ServiceResponseTimeoutError` without a second HTTP send. See [EVIDENCE.md](EVIDENCE.md) and raw artifacts. This does not establish Microsoft's intended timeout semantics or live service impact.

## Prior report

Related closed issue: https://github.com/Azure/azure-sdk-for-python/issues/15952 (historical request to limit excessively long Retry-After waits; closed due to inactivity).

## Scope

Reliability/timeout semantics. This is NOT a confirmed security vulnerability, proof of duplicated write, or live Azure incident. Keep separate from potential monotonic-clock and retry-header parsing issues.
