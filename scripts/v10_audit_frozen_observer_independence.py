#!/usr/bin/env python3
"""Fail-closed static audit of exact frozen observer implementation independence.

The audit runs only after exact V5 checkouts are available and before V10 real
pixels are downloaded. It asks a deliberately narrow, auditable question:
PolliPi's frozen analysis implementation must not import InsePi's
``interaction_sensing`` package, and InsePi's frozen implementation must not
import PolliPi's ``pollipi_analysis`` package.

This does not claim statistical independence of observer errors. It verifies the
software-level non-import boundary used by the epistemic-separation claim.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess

POLLIPI_COMMIT = "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
INSEPI_COMMIT = "980813bab996909020140fad5bd83b055eb3db9c"


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _require_exact(root: Path, expected: str, label: str) -> None:
    actual = _git_head(root)
    if actual != expected:
        raise RuntimeError(f"{label} checkout mismatch: {actual} != {expected}")


def _module_names(tree: ast.AST) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.lineno, node.module))
        elif isinstance(node, ast.Call):
            # Catch common dynamic-import forms when the module name is a literal.
            name = None
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                name = "__import__"
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            ):
                name = "import_module"
            if name and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                found.append((node.lineno, node.args[0].value))
    return found


def audit_tree(root: Path, forbidden_prefix: str) -> list[str]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        # Generated/virtual environment directories are not frozen observer source.
        if any(part in {".git", ".venv", "venv", "site-packages", "__pycache__"} for part in path.parts):
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (UnicodeDecodeError, SyntaxError) as exc:
            raise RuntimeError(f"cannot statically audit {path}: {exc}") from exc
        for lineno, module in _module_names(tree):
            if module == forbidden_prefix or module.startswith(forbidden_prefix + "."):
                violations.append(f"{path}:{lineno}: imports {module}")
    return violations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pollipi-root", required=True, type=Path)
    parser.add_argument("--insepi-root", required=True, type=Path)
    args = parser.parse_args()

    _require_exact(args.pollipi_root, POLLIPI_COMMIT, "PolliPi")
    _require_exact(args.insepi_root, INSEPI_COMMIT, "InsePi")

    pollipi_source = args.pollipi_root / "packages" / "analysis" / "src"
    insepi_source = args.insepi_root / "src"
    violations = [
        *audit_tree(pollipi_source, "interaction_sensing"),
        *audit_tree(insepi_source, "pollipi_analysis"),
    ]
    if violations:
        detail = "\n".join(violations)
        raise RuntimeError(f"frozen observer cross-implementation import boundary failed:\n{detail}")

    print("V10_FROZEN_OBSERVER_IMPLEMENTATION_INDEPENDENCE PASS")
    print("V10_POLLIPI_FORBIDDEN_IMPORT interaction_sensing")
    print("V10_INSEPI_FORBIDDEN_IMPORT pollipi_analysis")
    print("V10_STATISTICAL_ERROR_INDEPENDENCE_CLAIM false")


if __name__ == "__main__":
    main()
