# Verified SDK reproduction — 2026-10-16

**Status: reproduced in GitHub Actions using the official published, unmodified `azure-core==1.41.0` package.**

## Reproduction links

- [Successful GitHub Actions run #3](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616)
- [Python 3.11 raw JSON artifact](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616/artifacts/12027610082)
- [Python 3.13 raw JSON artifact](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616/artifacts/12027600121)
- Reproduction code: [azure_retry_after_repro.py](azure_retry_after_repro.py)
- PR head SHA: `601073c36df4644856bb55b5d67b3f52bf1e6d56` (merge-tested at `c8837ce033d8718e2d023d268b2dce04b0d39274`).

| Observation | Python 3.11.17 | Python 3.13.16 |
|---|---:|---:|
| Official SDK version | 1.41.0 | 1.41.0 |
| Configured operation timeout | 1 second | 1 second |
| First HTTP response (in-memory fake transport) | 429 + Retry-After: 120 | 429 + Retry-After: 120 |
| SDK requested transport sleep | 120 seconds | 120 seconds |
| Transport send calls | 1 | 1 |
| SDK exception after virtual sleep | ServiceResponseTimeoutError | ServiceResponseTimeoutError |
| CI job status | success | success |

The test uses a *virtual wall clock*. The sleep request is observed and the virtual clock advances 120 seconds instantly; it did **not** wait 120 seconds of real elapsed time. No cloud endpoint or credentials were used, and the test is not an Azure production incident.

## Implication and proposed expectation

`RetryPolicy(timeout=1)` does not currently prevent `Retry-After: 120` from requesting a sleep far beyond the configured retry timeout. If this timeout is meant to cover the entire operation, the client should fail promptly when the required server delay exceeds the remaining budget. It must **not** retry earlier than the server's requested delay.

The current result is an **observable SDK behavior**; whether it violates Microsoft's intended documented contract remains a maintainer decision. It does not demonstrate a security vulnerability, duplicated POST, Azure cost impact or a real blocked worker.

Related historically closed request: https://github.com/Azure/azure-sdk-for-python/issues/15952

## Artifact digests (GitHub Actions uploads)

- Python 3.11 ZIP SHA-256: `c82d1fef788ca7422afee5f391fac9a8d43e665134e49b77d43680853ccd0c56`
- Python 3.13 ZIP SHA-256: `d360e1d982373132edd702b0061b9f3e1b70c7de70579d444d52b90f44fa55d0`

These checksums identify the GitHub-hosted evidence archives; the committed source remains the reproducible primary artifact.
