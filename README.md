# Azure Retry-After: reproducible timeout characterization

> **Verified 2026-10-16:** [Official SDK CI run #3](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616) passed on Python 3.11 and 3.13. Both real Microsoft SDK pipelines requested **120 seconds of virtual transport sleep** with `RetryPolicy(timeout=1)`. See [full evidence, logs and checksums](EVIDENCE.md). No real 120-second wait or Azure endpoint was involved. Upstream issue submission is not yet accepted by Microsoft.

Independent, **no-cloud, no-credentials** verification of the unmodified Microsoft `azure-core==1.41.0` retry policy.

A local fake transport responds to the first GET with HTTP `429` and `Retry-After: 120`, while `RetryPolicy(timeout=1, retry_total=1)` is configured. A virtual clock lets us observe whether the official sync and async pipelines request 120 seconds of sleeping **without waiting in real time**.

## Run

```bash
python -m pip install azure-core==1.41.0
python azure_retry_after_repro.py --output azure-retry-evidence.json
```

The script prints and saves machine-readable observations, including transport attempts, requested sleep duration, resulting exception and exact package/Python versions. It exits nonzero if source-predicted behavior is not observed.

GitHub Actions runs on Python 3.11 and 3.13. See **Actions → Characterize azure-core Retry-After behavior**, then open each run's uploaded `azure-retry-evidence-py*` artifact. A failed run can still contain useful evidence; **do not claim success based on the existence of an artifact alone**.

## Hypothesis and limits

The source appears to call `transport.sleep(120)` before enforcing the remaining operation timeout. Expected behavior for a deadline shorter than the server-requested delay should be to stop, **not** retry early and violate `Retry-After`.

- A successful characterization proves the official SDK code path under controlled in-memory transport and virtual-clock conditions.
- It does **not** prove an Azure production incident, 120 seconds of actual waiting, security exploitability or a bug accepted by Microsoft.
- This work is not a vulnerability disclosure. A prior related feature request is [Azure SDK #15952](https://github.com/Azure/azure-sdk-for-python/issues/15952), closed as stale in 2024.

Before proposing an upstream change: verify the original behavior, discuss the intended timeout semantics, and add narrowly scoped failing regression tests against the maintained Microsoft source tree. No real HTTP calls or Azure account are required.
