# DRAFT ONLY — DO NOT SUBMIT UPSTREAM WITHOUT CI EVIDENCE

Proposed title: **[azure-core] Retry-After wait appears to exceed RetryPolicy operation timeout (sync + async)**

## Summary

The official `azure-core` retry policy appears to request an HTTP transport sleep of 120 seconds after `429 Retry-After: 120` even with `RetryPolicy(timeout=1)`. The configured timeout may be checked only on a subsequent retry attempt.

The intended semantics of the `timeout` option should be confirmed with maintainers before describing this as a definitive bug.

## Reproduction — pending verification

This repository contains `azure_retry_after_repro.py`, a **no-network** characterization using:

- Unmodified published `azure-core==1.41.0`.
- Real `Pipeline`, `AsyncPipeline`, `RetryPolicy`, and `AsyncRetryPolicy`.
- A local fake transport that returns HTTP 429 with `Retry-After: 120`.
- A virtual wall clock to observe whether `transport.sleep(120)` is requested despite a one-second operation timeout.
- Raw JSON evidence for both Python 3.11 and 3.13, uploaded by GitHub Actions.

**Fill in only after actual CI jobs complete:**

- Run: `[link]`
- Commit: `[SHA]`
- Python + azure-core version: `[from artifact]`
- Sync sleep/attempts/result: `[from artifact]`
- Async sleep/attempts/result: `[from artifact]`

## Expected

If the retry timeout represents a total operation budget inclusive of waiting, stop instead of sleeping beyond the remaining budget. **Never retry earlier than the server's Retry-After requirement.**

## Actual

**Not yet verified against official installed Microsoft SDK.** Consult the CI evidence JSON and runner logs.

## Prior report

Related closed issue: https://github.com/Azure/azure-sdk-for-python/issues/15952 (historical request to limit excessively long Retry-After waits; closed due to inactivity).

## Scope

Reliability/timeout semantics. This is NOT a confirmed security vulnerability, proof of duplicated write, or live Azure incident. Keep separate from potential monotonic-clock and retry-header parsing issues.
