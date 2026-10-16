# First independent Microsoft SDK verification — review checklist

This PR intentionally does **not** change the reproduction script or its expectations. It verifies that GitHub Actions runs against the *published, unmodified* Microsoft SDK and produces artifacts under two independent Python versions.

## Gate 1 — Execution

- [ ] Python 3.11 installs `azure-core==1.41.0`.
- [ ] Python 3.13 installs `azure-core==1.41.0`.
- [ ] Both jobs save `azure-retry-evidence.json`.
- [ ] Logs confirm no Azure credentials or network HTTP requests were used.

## Gate 2 — Outcome

Only if confirmed by the raw artifacts:

- [ ] Sync official pipeline requests `transport.sleep(120)` with a 1-second retry timeout.
- [ ] Async official pipeline requests `transport.sleep(120)` with a 1-second retry timeout.
- [ ] Each attempt count, exception class and virtual elapsed time is recorded.

**Red CI is useful evidence.** A mismatch may reveal a test harness issue or falsify the original hypothesis. Review logs before changing assertions; never force a green status.

## Gate 3 — Upstream readiness

- [ ] Recheck latest release/main branch.
- [ ] Check existing Azure SDK issues and expected `timeout` semantics.
- [ ] Create a small Microsoft regression test and surgical patch.
- [ ] Keep security/CVE claims out unless a genuinely exploitable trust boundary is proven.

Prior issue: https://github.com/Azure/azure-sdk-for-python/issues/15952
