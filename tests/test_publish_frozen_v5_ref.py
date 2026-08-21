from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "publish_frozen_v5_ref.py"
SPEC = importlib.util.spec_from_file_location("publish_frozen_v5_ref_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_frozen_sha_registry_is_exact() -> None:
    assert MODULE.CONFIG["pollipi"]["sha"] == "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
    assert MODULE.CONFIG["insepi"]["sha"] == "980813bab996909020140fad5bd83b055eb3db9c"
    assert MODULE.FROZEN_BRANCH == "frozen/v5-method"


def test_remote_normalisation_accepts_https_and_ssh_forms() -> None:
    expected = "https://github.com/zuizui0223/insepi.git"
    assert MODULE.normalise_remote(expected) == expected
    assert MODULE.normalise_remote("git@github.com:zuizui0223/insepi.git") == expected
    assert MODULE.normalise_remote("ssh://git@github.com/zuizui0223/insepi.git") == expected


def test_missing_local_frozen_object_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/zuizui0223/insepi.git"], check=True)
    with pytest.raises(MODULE.RecoveryError, match="required frozen commit is not present locally"):
        MODULE.verify_repo(repo, "insepi")
