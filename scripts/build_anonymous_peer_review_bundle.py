#!/usr/bin/env python3
"""Build a deterministic double-anonymous peer-review source bundle.

The bundle is a review artefact, not the archival release. It strips repository
identity while preserving scientific files and 64-character evidence hashes.
Forty-character Git commit identifiers are replaced consistently by deterministic
anonymous identifiers so the bundle cannot be trivially traced back by a commit
search while internal cross-file references remain coherent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile


INCLUDE_DIRS = ("src", "tests", "benchmarks", "scripts", "docs", "manuscript")
INCLUDE_FILES = ("pyproject.toml", "README.md")
EXCLUDE_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".git"}
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".tsv", ".csv", ".txt", ".yml", ".yaml", ".svg"}
GIT_SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def pseudo_sha(original: str) -> str:
    return hashlib.sha256(("anonymous-review|" + original.lower()).encode("utf-8")).hexdigest()[:40]


def sanitise_text(text: str) -> str:
    text = text.replace("zuizui0223", "anonymous-review")
    text = text.replace("ZHANG Ruiqi", "Anonymous Author")
    text = text.replace("張瑞琪", "Anonymous Author")
    text = EMAIL_RE.sub("anonymous@example.invalid", text)
    text = GIT_SHA_RE.sub(lambda match: pseudo_sha(match.group(0)), text)
    return text


def should_copy(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in EXCLUDE_PARTS for part in rel.parts):
        return False
    if path.suffix.lower() in {".zip", ".png", ".jpg", ".jpeg", ".pyc"}:
        return False
    return True


def copy_sanitised(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in TEXT_SUFFIXES or source.name in {"README.md", "pyproject.toml"}:
        destination.write_text(sanitise_text(source.read_text(encoding="utf-8")), encoding="utf-8")
    else:
        shutil.copy2(source, destination)


def find_license(root: Path) -> Path | None:
    for name in ("LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"):
        candidate = root / name
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def build(root: Path, staging: Path, zip_path: Path) -> dict[str, object]:
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    copied: list[str] = []
    for directory in INCLUDE_DIRS:
        base = root / directory
        if not base.exists():
            continue
        for source in sorted(path for path in base.rglob("*") if path.is_file()):
            if not should_copy(source, root):
                continue
            rel = source.relative_to(root)
            copy_sanitised(source, staging / rel)
            copied.append(rel.as_posix())
    for filename in INCLUDE_FILES:
        source = root / filename
        if source.exists():
            copy_sanitised(source, staging / filename)
            copied.append(filename)

    license_path = find_license(root)
    license_ready = license_path is not None
    if license_path is not None:
        copy_sanitised(license_path, staging / license_path.name)
        copied.append(license_path.name)

    readme = """# Anonymous peer-review code bundle\n\nThis bundle accompanies a double-anonymous methods-paper submission. Repository ownership, email addresses and Git commit identifiers have been anonymised for review. Scientific 64-character SHA-256 evidence fingerprints are retained.\n\nThe final public archive will restore canonical repository provenance after peer review.\n"""
    if not license_ready:
        readme += "\n**Packaging blocker:** no open-source software licence has yet been selected. This bundle is suitable for internal anonymous QA but must not be submitted until an explicit licence is chosen by the copyright holder.\n"
    (staging / "ANONYMOUS_REVIEW_README.md").write_text(readme, encoding="utf-8")

    identity_tokens = ("zuizui0223", "github.com/zuizui0223")
    leaks: list[str] = []
    for path in sorted(p for p in staging.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in identity_tokens):
            leaks.append(path.relative_to(staging).as_posix())
    if leaks:
        raise ValueError(f"identity tokens remain in anonymous bundle: {leaks}")

    manifest: dict[str, object] = {
        "schema": "mee-anonymous-peer-review-bundle-v1",
        "double_anonymous": True,
        "license_ready": license_ready,
        "v7_materialised": False,
        "files": sorted(set(copied + ["ANONYMOUS_REVIEW_README.md"])),
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    (staging / "ANONYMOUS_BUNDLE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in staging.rglob("*") if p.is_file()):
            rel = path.relative_to(staging).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--staging", default=".peer-review/anonymous")
    parser.add_argument("--zip", dest="zip_path", default=".peer-review/mee-anonymous-peer-review.zip")
    args = parser.parse_args()
    manifest = build(Path(args.root).resolve(), Path(args.staging), Path(args.zip_path))
    print("MEE_ANONYMOUS_BUNDLE", Path(args.zip_path))
    print("MEE_LICENSE_READY", str(manifest["license_ready"]).lower())
    print("MEE_BUNDLE_MANIFEST", manifest["manifest_sha256"])


if __name__ == "__main__":
    main()
