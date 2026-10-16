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
DIAGNOSTIC = re.compile(r"##\\[error\\]|\\berror\\b|\\bfail(?:ed|ure)?\\b|Traceback|Exception|AssertionError|black|pylint|mypy|pyright|pytest", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "azure-sdk-public-ci-diagnostic"})
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
        status, content = fetch(f"{project}/_apis/build/builds/{build}/logs/{logid}?api-version=7.1")
        print(f"  log {logid}: HTTP {status}, bytes received {len(content)}")
        if status != 200:
            print("  ", content[:180])
            continue
        lines = content.splitlines()
        chosen = [i for i, line in enumerate(lines) if DIAGNOSTIC.search(line)]
        print(f"  log lines: {len(lines)} matching diagnostics: {len(chosen)}")
        displayed = set()
        for pos in chosen[-24:]:
            for index in range(max(0, pos - 1), min(len(lines), pos + 3)):
                if index not in displayed:
                    print(f"    L{index+1}: {lines[index][:360]}")
                    displayed.add(index)


if __name__ == "__main__":
    for build_id in BUILDS:
        inspect(build_id)
