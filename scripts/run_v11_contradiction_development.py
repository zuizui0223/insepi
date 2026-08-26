#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from interaction_sensing.simulation.contradiction_development_v11 import write_v11


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--development-replicates", type=int, default=300)
    parser.add_argument("--heldout-replicates", type=int, default=300)
    args = parser.parse_args()
    path = write_v11(
        args.output,
        development_replicates=args.development_replicates,
        heldout_replicates=args.heldout_replicates,
    )
    result = json.loads(path.read_text())
    print("V11_RESULT_SHA256", sha256_file(path))
    print("V11_PROTOCOL_SHA256", result["protocol_sha256"])
    print("V11_CLAIM_LEVEL", result["claim"]["level"])
    print("V11_CLAIM_LABEL", result["claim"]["label"])
    for strategy, metrics in result["strategies"].items():
        print(
            "V11_STRATEGY",
            strategy,
            f"localisation={metrics['heldout_failure_localisation_accuracy']:.6f}",
            f"wrong_repair={metrics['wrong_module_intervention_rate']:.6f}",
            f"shared={metrics['shared_blindspot_discovery_rate']:.6f}",
            f"no_fault_false={metrics['no_fault_false_intervention_rate']:.6f}",
            f"experiments={metrics['experiments_to_stable_falsification']:.6f}",
            f"repair_positive={metrics['heldout_repair_positive_transfer_rate']:.6f}",
            f"repair_reduction={metrics['heldout_repair_relative_loss_reduction']:.6f}",
        )


if __name__ == "__main__":
    main()
