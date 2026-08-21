#!/usr/bin/env python3
"""Publish an existing frozen V5 git object without rewriting its history.

This helper is intentionally conservative. It never cherry-picks, rebases, amends,
commits, resets the worktree, or checks out the frozen commit. It only verifies an
existing local commit object, creates/updates the local ref `frozen/v5-method`, and
optionally pushes that exact ref after checking repository identity.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


FROZEN_BRANCH = "frozen/v5-method"
CONFIG = {
    "pollipi": {
        "sha": "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9",
        "remote_suffix": "zuizui0223/pollipi.git",
    },
    "insepi": {
        "sha": "980813bab996909020140fad5bd83b055eb3db9c",
        "remote_suffix": "zuizui0223/insepi.git",
    },
}


class RecoveryError(RuntimeError):
    pass


def git(repo: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and completed.returncode != 0:
        raise RecoveryError(
            f"git {' '.join(args)} failed ({completed.returncode}): {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def normalise_remote(url: str) -> str:
    value = url.strip().replace("\\", "/")
    if value.startswith("git@github.com:"):
        value = "https://github.com/" + value.split(":", 1)[1]
    if value.startswith("ssh://git@github.com/"):
        value = "https://github.com/" + value.split("ssh://git@github.com/", 1)[1]
    return value.rstrip("/")


def verify_repo(repo: Path, kind: str) -> tuple[str, str]:
    if kind not in CONFIG:
        raise RecoveryError(f"unknown repository kind: {kind}")
    if not repo.is_dir():
        raise RecoveryError(f"repository path does not exist: {repo}")
    inside = git(repo, "rev-parse", "--is-inside-work-tree")
    if inside != "true":
        raise RecoveryError(f"not a git worktree: {repo}")

    expected_sha = str(CONFIG[kind]["sha"])
    object_type = git(repo, "cat-file", "-t", expected_sha, check=False)
    if object_type != "commit":
        raise RecoveryError(
            f"required frozen commit is not present locally: {expected_sha}; "
            "do not reconstruct it under the same V7 generation"
        )

    resolved = git(repo, "rev-parse", f"{expected_sha}^{{commit}}")
    if resolved != expected_sha:
        raise RecoveryError(f"frozen commit resolved unexpectedly: {resolved}")

    origin = normalise_remote(git(repo, "remote", "get-url", "origin"))
    suffix = str(CONFIG[kind]["remote_suffix"])
    if not origin.lower().endswith(suffix.lower()):
        raise RecoveryError(
            f"origin does not match expected repository {suffix}: {origin}"
        )
    return expected_sha, origin


def publish(repo: Path, kind: str, *, push: bool) -> dict[str, str]:
    expected_sha, origin = verify_repo(repo, kind)
    subject = git(repo, "show", "--no-patch", "--format=%s", expected_sha)

    if not push:
        return {
            "kind": kind,
            "sha": expected_sha,
            "origin": origin,
            "subject": subject,
            "status": "verified-local-only",
        }

    # Updating a branch ref does not alter the commit object or current worktree.
    git(repo, "branch", "-f", FROZEN_BRANCH, expected_sha)
    local_tip = git(repo, "rev-parse", FROZEN_BRANCH)
    if local_tip != expected_sha:
        raise RecoveryError(f"local frozen branch tip mismatch: {local_tip}")

    git(
        repo,
        "push",
        "origin",
        f"refs/heads/{FROZEN_BRANCH}:refs/heads/{FROZEN_BRANCH}",
    )
    remote_line = git(repo, "ls-remote", origin, f"refs/heads/{FROZEN_BRANCH}")
    if not remote_line:
        raise RecoveryError("remote frozen branch was not advertised after push")
    remote_tip = remote_line.split()[0]
    if remote_tip != expected_sha:
        raise RecoveryError(
            f"remote frozen branch mismatch: expected={expected_sha} actual={remote_tip}"
        )
    return {
        "kind": kind,
        "sha": expected_sha,
        "origin": origin,
        "subject": subject,
        "status": "published-exact-ref",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=sorted(CONFIG))
    parser.add_argument("repo", type=Path, help="path to the local clone that contains the frozen commit")
    parser.add_argument(
        "--push",
        action="store_true",
        help="after local verification, create/update frozen/v5-method and push the exact ref",
    )
    args = parser.parse_args()

    try:
        result = publish(args.repo.resolve(), args.kind, push=args.push)
    except RecoveryError as exc:
        print(f"FROZEN_V5_RECOVERY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print("FROZEN_V5_RECOVERY_STATUS", result["status"])
    print("FROZEN_V5_REPO", result["kind"])
    print("FROZEN_V5_SHA", result["sha"])
    print("FROZEN_V5_ORIGIN", result["origin"])
    print("FROZEN_V5_SUBJECT", result["subject"])


if __name__ == "__main__":
    main()
