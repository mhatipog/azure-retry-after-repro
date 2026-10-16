#!/usr/bin/env python3
"""Read-only inspection of publicly exposed Azure SDK Azure DevOps CI logs."""
import json
import re
import urllib.error
import urllib.request

PROJECTS = (
    "https://dev.azure.com/azure-sdk/public",
    "https://dev.azure.com/azure-sdk/29ec6040-b234-4e31-b139-33dc4287b756",
)
BUILDS = (6966021, 6966022, 6966023)
DIAGNOSTIC = re.compile(r"##\[error\]|\berror\b|\bfail(?:ed|ure)?\b|Traceback|Exception|AssertionError|black|pylint|mypy|pyright|pytest", re.I)


def fetch(url, accept="application/json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "azure-sdk-public-ci-diagnostic"})
    try:
        with urllib.request.urlopen(req, timeout=18) as response:
            body = response.read(2_000_000)
            return response.status, body.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(300).decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def inspect(build):
    print(f"\\n### BUILD {build}", flush=True)
    project = None
    timeline = None
    for base in PROJECTS:
        status, body = fetch(f"{base}/_apis/build/builds/{build}/timeline?api-version=7.1")
        print(f"timeline {base}: HTTP {status}", flush=True)
        if status == 200:
            try:
                timeline = json.loads(body)
                project = base
                break
            except json.JSONDecodeError:
                print("Response was not JSON:", body[:200])
        else:
            print("Response excerpt:", body[:240])
    if not timeline:
        print("UNAVAILABLE: public timeline could not be retrieved", flush=True)
        return

    for path in (
        f"/_apis/test/runs?buildUri=vstfs%3A%2F%2F%2FBuild%2FBuild%2F{build}&api-version=7.1",
        f"/_apis/testresults/runs?buildId={build}&api-version=7.1-preview.1",
    ):
        status, body = fetch(project + path)
        print(f"Test runs query {path.split('?')[0]}: HTTP {status}")
        if status == 200:
            try:
                value = json.loads(body)
                runs = value.get("value", [])
                print(f"Test runs returned: {len(runs)}, reported total: {value.get('count')}")
                for run in runs[:25]:
                    if not isinstance(run, dict):
                        continue
                    print(f"  run id={run.get('id')} name={run.get('name')} failed={run.get('statistics', {}).get('failedTests')}")
                    rid = run.get("id")
                    if rid and (run.get('statistics', {}).get('failedTests') or run.get('uncompletedTests') or run.get('state') == "Completed"):
                        results_url = f"{project}/_apis/test/runs/{rid}/results?outcomes=Failed&api-version=7.1"
                        code, details = fetch(results_url)
                        print(f"    failed results HTTP {code}")
                        if code == 200:
                            try:
                                data = json.loads(details)
                                for result in data.get("value", [])[:7]:
                                    print("      test:", str(result.get("automatedTestName") or result.get("testCaseTitle"))[:180])
                                    print("      error:", str(result.get("errorMessage"))[:500])
                            except json.JSONDecodeError:
                                print("      not json")
            except json.JSONDecodeError:
                print("Invalid test runs JSON", body[:200])
        else:
            print("Test API response excerpt:", body[:120])

    records = timeline.get("records", [])
    failing = [x for x in records if x.get("result") == "failed" or any(i.get("type") == "error" for i in x.get("issues", []))]
    print(f"Timeline records: {len(records)}, failed/error records: {len(failing)}")
    for rec in failing[:35]:
        print(f"\\n- {rec.get('type')} / {rec.get('name')} => {rec.get('result')}")
        for issue in rec.get("issues", [])[:8]:
            if issue.get("type") == "error":
                print("  ISSUE:", str(issue.get("message", ""))[:800])
        log = rec.get("log") or {}
        logid = log.get("id")
        if logid is None:
            continue
        status, content = fetch(f"{project}/_apis/build/builds/{build}/logs/{logid}?api-version=7.1", accept="text/plain")
        print(f"  log {logid}: HTTP {status}, bytes received {len(content)}")
        if status != 200:
            print("  ", content[:180])
            continue
        lines = content.splitlines()
        chosen = [i for i, line in enumerate(lines) if DIAGNOSTIC.search(line)]
        print(f"  log lines: {len(lines)} matching diagnostics: {len(chosen)}")

        if build == 6966022 and logid == 11:
            print("  Full AutoRest environment failure log:")
            for index, line in enumerate(lines[-120:], max(0, len(lines) - 120)):
                print(f"    L{index+1}: {line[:400]}")

        displayed = set()
        for pos in chosen[-24:]:
            for index in range(max(0, pos - 1), min(len(lines), pos + 3)):
                if index not in displayed:
                    print(f"    L{index+1}: {lines[index][:360]}")
                    displayed.add(index)


if __name__ == "__main__":
    for build_id in BUILDS:
        inspect(build_id)
