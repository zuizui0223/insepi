#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from interaction_sensing.simulation.causal_intervention_v12 import write_v12


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = write_v12(args.output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    import json
    result = json.loads(output.read_text(encoding="utf-8"))
    print("V12_RESULT_SHA256", digest)
    print("V12_PROTOCOL_SHA256", result["protocol_sha256"])
    print("V12_CLAIM_LEVEL", result["claim"]["level"])
    print("V12_CLAIM_LABEL", result["claim"]["label"])
    for name, row in result["strategies"].items():
        print(
            "V12_STRATEGY",
            name,
            f"localisation={row['heldout_localisation_accuracy_budget2']:.6f}",
            f"full={row['heldout_full_battery_localisation_accuracy']:.6f}",
            f"shared={row['shared_representation_recall_budget2']:.6f}",
            f"wrong={row['wrong_module_intervention_rate_budget2']:.6f}",
            f"no_fault_false={row['no_fault_false_intervention_rate_budget2']:.6f}",
            f"one={row['accuracy_after_one_intervention']:.6f}",
            f"stable={row['mean_active_interventions_to_stable_correct_diagnosis']:.6f}",
            f"repair_positive={row['heldout_repair_positive_transfer_rate']:.6f}",
            f"repair_reduction={row['heldout_repair_relative_loss_reduction']:.6f}",
        )


if __name__ == "__main__":
    main()
