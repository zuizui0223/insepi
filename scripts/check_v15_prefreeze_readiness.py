#!/usr/bin/env python3
"""Report or enforce the V15-v2 held-out readiness gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from interaction_sensing.v15_prefreeze import (
    assert_ready_for_heldout,
    evaluate_prefreeze_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        default="benchmarks/v15_prefreeze_readiness_registry.json",
        help="machine-readable V15-v2 readiness registry",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="exit non-zero unless held-out execution is fully frozen and ready",
    )
    args = parser.parse_args()

    payload = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    readiness = evaluate_prefreeze_registry(payload)
    print(
        json.dumps(
            {
                "state": readiness.state.value,
                "absence_strategy": readiness.absence_strategy.value,
                "safe_target_presence_upper_bound": readiness.safe_target_presence_upper_bound,
                "blockers": list(readiness.blockers),
                "frozen_items": list(readiness.frozen_items),
                "development_defined_items": list(readiness.development_defined_items),
                "unset_items": list(readiness.unset_items),
            },
            indent=2,
            sort_keys=True,
        )
    )

    if args.require_ready:
        assert_ready_for_heldout(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
