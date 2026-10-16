# Proposed Microsoft fix — independent CI verification

The Microsoft SDK fix is on `mhatipog/azure-sdk-for-python` branch `fix/retry-after-operation-timeout`, pinned at commit `1bbd45772515939a3147422b05db17ac8a0ccdbd`.

This PR executes a sparse checkout of that exact source commit (not the PyPI release) and runs the native pytest regression suite on Python 3.11 and 3.13. It uses no Azure endpoints or credentials.

Test outcomes must be inspected in the raw job logs. If failing, fix test assumptions or the source patch before considering upstream submission.

The original defect was previously reproduced using the unchanged published SDK in [Actions run #3](https://github.com/mhatipog/azure-retry-after-repro/actions/runs/38855964616).

The focused matrix uses `pytest --noconftest` because these in-memory tests do not need Azure SDK's unrelated OpenTelemetry/service fixture dependencies.

The updated matrix also runs an explicit **red baseline**: the same 16 tests must fail in precisely 12 cases against the original official wheel, then pass in all cases against the pinned patch source.
