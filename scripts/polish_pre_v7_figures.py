#!/usr/bin/env python3
"""Deterministic presentation-only polish for generated pre-V7 SVG figures.

This script changes text placement only. It does not read or alter scientific
inputs and never touches V7 modules or outputs.
"""
from __future__ import annotations

import argparse
from pathlib import Path


FIG2_OLD = '<text x="180.0" y="700.0" font-family="Arial, Helvetica, sans-serif" font-size="17" font-weight="400" fill="#202124" text-anchor="start">targeted policies trade event recovery against hidden-error recovery and sampling distortion; fixed disagreement is not a free improvement.</text>'
FIG2_NEW = '\n'.join((
    '<text x="180.0" y="694.0" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="400" fill="#202124" text-anchor="start">targeted policies trade event recovery against hidden-error recovery and sampling distortion;</text>',
    '<text x="180.0" y="718.0" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="400" fill="#202124" text-anchor="start">fixed disagreement is not a free improvement.</text>',
))

FIG4_OLD_SWATCH = '<rect x="835.0" y="535.0" width="18.0" height="18.0" rx="2.0" fill="#00897b" stroke="#00897b" stroke-width="0"/>'
FIG4_NEW_SWATCH = '<rect x="805.0" y="535.0" width="18.0" height="18.0" rx="2.0" fill="#00897b" stroke="#00897b" stroke-width="0"/>'
FIG4_OLD_LABEL = '<text x="862.0" y="550.0" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="400" fill="#202124" text-anchor="start">observability risk</text>'
FIG4_NEW_LABEL = '<text x="832.0" y="550.0" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="400" fill="#202124" text-anchor="start">observability risk</text>'


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise ValueError(f"expected exactly one layout anchor in {path}, found {count}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def polish(output_dir: Path) -> None:
    fig2 = output_dir / "fig2_v3_equal_budget.svg"
    fig4 = output_dir / "fig4_v6_architecture.svg"
    replace_once(fig2, FIG2_OLD, FIG2_NEW)
    replace_once(fig4, FIG4_OLD_SWATCH, FIG4_NEW_SWATCH)
    replace_once(fig4, FIG4_OLD_LABEL, FIG4_NEW_LABEL)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="manuscript/figures/generated")
    args = parser.parse_args()
    polish(Path(args.output_dir))


if __name__ == "__main__":
    main()
