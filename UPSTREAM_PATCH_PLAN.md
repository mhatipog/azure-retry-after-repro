# Minimal Azure SDK upstream PR plan — verified behavior, not yet patched

## Primary regression to add at Microsoft

Reproduce the official package behavior in the native upstream tests for both sync and async retry policies:

- `RetryPolicy(timeout=1, retry_total=1)` / `AsyncRetryPolicy(timeout=1, retry_total=1)`.
- In-memory transport, first HTTP 429 with `Retry-After: 120`.
- Observe `transport.sleep` requested with 120 seconds even though only 1 second remains.
- Desired new assertion (**if maintainers agree timeout covers retry waits**): client raises the appropriate timeout error **without sleeping 120 seconds or sending a second request**.
- Preserve control case: `Retry-After: 0.25`, `timeout=1`, then HTTP 200; exactly one 0.25-second sleep and one permitted retry.
- Preserve control case: HTTP 200 on first attempt; no sleep.
- Preserve explicit server-throttling semantics: never retry **earlier** than `Retry-After` in an attempt to fit the deadline.

## Scope: one issue, one semantic change

1. Decide whether `timeout` is an **operation-wide** budget including delays (docs call it 'Timeout setting for the operation') or a per-attempt timeout.
2. In sync `sdk/core/azure-core/azure/core/pipeline/policies/_retry.py` and async `_retry_async.py`, account for actual elapsed time before scheduling retry sleep, and compare the required wait to the remaining operation budget.
3. If the required wait cannot fit, fail promptly using the existing timeout exception classification. Do not clamp and retry earlier.
4. Keep `RetryPolicy.sleep()` compatibility and avoid global transport changes unless a reviewer prefers a shared helper.
5. Test small/zero retry intervals, exhausted counts, boundary equal to remaining deadline, and sync/async parity.

## Separate future tickets (not this first PR)

- Replacing `time.time()` with monotonic measurement for duration bookkeeping, plus wall-clock jump tests.
- Validating `Retry-After` header parsing for non-finite/invalid inputs.
- Discussing header override of method/status filters, which appears to be an explicit design rule.
- Sharing retry budgets across nested SDKs and pipelines.

## Existing proof

- [CI run #3: green on Python 3.11 and 3.13](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616)
- [Machine-readable evidence](EVIDENCE.md)
- [Upstream issue draft](ISSUE_DRAFT.md)
- [Previous Microsoft report #15952](https://github.com/Azure/azure-sdk-for-python/issues/15952)

## Current contribution blocker

The connected GitHub integration has write access to this user-owned reproduction repository but cannot open a new issue in `Azure/azure-sdk-for-python`: GitHub REST returns HTTP 403, `Resource not accessible by integration`. No upstream issue or PR has been created. To prepare a direct source PR, first fork `Azure/azure-sdk-for-python` to the user's GitHub account and ensure write access to the fork. Then add native upstream tests before a narrowly scoped implementation.
