#!/usr/bin/env python3
"""Fill the editor cover-letter V7 summary from the same verified ledger/report.

No scientific decision is made here. The script dynamically loads the preregistered
submission finalizer, reuses its report/ledger verification and claim-level wording,
and inserts a concise editor-facing summary into the cover-letter template.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
FINALIZER_PATH = HERE / "finalize_submission_from_v7.py"
SPEC = importlib.util.spec_from_file_location("v7_submission_finalizer_for_cover", FINALIZER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load locked V7 submission finalizer")
FINALIZER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FINALIZER
SPEC.loader.exec_module(FINALIZER)

MARKER = "[[V7_EDITOR_RESULT_SUMMARY]]"


def finalize_cover(template: str, v7) -> str:
    if template.count(MARKER) != 1:
        raise ValueError(f"expected exactly one cover-letter marker, found {template.count(MARKER)}")
    summary = FINALIZER.claim_texts(v7)["abstract"]
    text = template.replace(MARKER, summary, 1)
    if "[[V7_" in text:
        raise ValueError("final cover letter still contains a V7 placeholder")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--template", default="editor/EDITOR_COVER_LETTER_TEMPLATE.md", type=Path)
    parser.add_argument("--output", default="manuscript/generated/EDITOR_COVER_LETTER_FINAL.md", type=Path)
    args = parser.parse_args()

    v7 = FINALIZER.verify_v7(args.ledger, args.report)
    text = finalize_cover(args.template.read_text(encoding="utf-8"), v7)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print("MEE_EDITOR_COVER_CLAIM_LEVEL", v7.claim_level)
    print(args.output)


if __name__ == "__main__":
    main()
