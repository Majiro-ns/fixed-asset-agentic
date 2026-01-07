import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = REPO_ROOT / "docs" / "specs"
DANGER_DOC = REPO_ROOT / "docs" / "03_rules.md"


def _read_issue_body(issue_number: int) -> str:
    body = os.environ.get("ISSUE_BODY")
    if body:
        return body
    api_url = f"https://api.github.com/repos/{os.environ.get('GITHUB_REPOSITORY')}/issues/{issue_number}"
    print(f"[agent_run] fetching issue body via curl: {api_url}")
    result = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: token {os.environ.get('GITHUB_TOKEN')}", api_url],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return data.get("body") or ""


def _parse_spec_files(body: str) -> List[Path]:
    specs: List[Path] = []
    for line in body.splitlines():
        if line.startswith("SPEC:"):
            rel = line.replace("SPEC:", "").strip()
            p = (SPEC_ROOT / rel).resolve()
            if p.exists():
                specs.append(p)
    return specs


def _read_specs(spec_paths: List[Path]) -> None:
    for p in spec_paths:
        try:
            print(f"[agent_run] SPEC {p.relative_to(REPO_ROOT)}")
            print(p.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[agent_run] failed to read spec {p}: {exc}")


def _check_danger_zone() -> None:
    if not DANGER_DOC.exists():
        return
    forbidden_keywords = [
        "Forbidden",
        "Danger zone",
    ]
    text = DANGER_DOC.read_text(encoding="utf-8")
    if any(k.lower() in text.lower() for k in forbidden_keywords):
        print("[agent_run] scanned rules for danger zone (informational only)")


def run_agent(issue_number: int) -> None:
    print(f"[agent_run] start for issue #{issue_number}")
    body = _read_issue_body(issue_number)
    spec_paths = _parse_spec_files(body)
    if spec_paths:
        _read_specs(spec_paths)
    _check_danger_zone()

    cmd = ["pwsh", "-File", str(REPO_ROOT / "scripts" / "dev_take_issue.ps1"), "-IssueNumber", str(issue_number)]
    print(f"[agent_run] running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("[agent_run] done")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent runner for labeled issues")
    parser.add_argument("--issue", type=int, required=True, help="Issue number")
    args = parser.parse_args()
    run_agent(args.issue)


if __name__ == "__main__":
    main()
