from __future__ import annotations

import inspect

import pytest

from interaction_sensing import physical_evaluation_v13 as v13e


def _development():
    responses = []
    labels = []
    templates = {
        "event_side": {
            "event_restore": (0.8, 0.05),
            "observability_restore": (0.05, 0.02),
            "shared_restore": (0.4, 0.10),
        },
        "nuisance_side": {
            "event_restore": (0.02, 0.05),
            "observability_restore": (0.05, 0.8),
            "shared_restore": (0.10, 0.4),
        },
        "shared_optical": {
            "event_restore": (0.35, 0.10),
            "observability_restore": (0.10, 0.35),
            "shared_restore": (0.65, 0.65),
        },
        "no_fault": {
            "event_restore": (-0.02, -0.01),
            "observability_restore": (-0.01, -0.02),
            "shared_restore": (-0.02, -0.02),
        },
    }
    for label in v13e.CLASSES:
        for rep in range(12):
            block = f"dev-{label}-{rep:02d}"
            jitter = (rep - 5.5) * 0.001
            response = {
                intervention: (pair[0] + jitter, pair[1] - jitter)
                for intervention, pair in templates[label].items()
            }
            responses.append(v13e.BlockResponse(block, "development", response))
            labels.append(v13e.DevelopmentLabel(block, label))
    return responses, labels, templates


def _heldout(templates):
    responses = []
    truth = []
    qc = []
    # 6 day x scene clusters, each with 4 classes x 3 replicate blocks = 72.
    for cluster in range(6):
        day = f"held_day_{1 + cluster // 3:02d}"
        scene = f"held_scene_{1 + cluster % 3:02d}"
        for label in v13e.CLASSES:
            for rep in range(3):
                block = f"held-c{cluster}-{label}-{rep}"
                jitter = (cluster - 2.5) * 0.002 + (rep - 1) * 0.001
                response = {
                    intervention: (pair[0] * 0.92 + jitter, pair[1] * 0.92 - jitter)
                    for intervention, pair in templates[label].items()
                }
                responses.append(v13e.BlockResponse(block, "heldout", response))
                truth.append(v13e.HeldoutTruth(block, label, day, scene))
                qc.append(v13e.QcAnnotation(block, protected_qc=(rep == 0), gross_protocol_violation=False))
    return responses, truth, qc


def test_v13_predictor_signature_cannot_receive_heldout_truth() -> None:
    names = set(inspect.signature(v13e.predict_heldout).parameters)
    assert names == {"models", "heldout_responses"}
    assert "heldout_truth" not in names
    assert "treatment_class" not in names


def test_v13_training_requires_development_labels_only_and_exact_block_alignment() -> None:
    responses, labels, _ = _development()
    models = v13e.fit_strategy_models(responses, labels)
    assert set(models) == set(v13e.STRATEGIES)
    with pytest.raises(ValueError):
        v13e.fit_strategy_models(responses, labels[:-1])
    bad = list(responses)
    bad[0] = v13e.BlockResponse(bad[0].block_id, "heldout", bad[0].responses)
    with pytest.raises(ValueError):
        v13e.fit_strategy_models(bad, labels)


def test_v13_blinded_prediction_emits_four_strategies_per_heldout_block() -> None:
    development, labels, templates = _development()
    heldout, _truth, _qc = _heldout(templates)
    models = v13e.fit_strategy_models(development, labels)
    predictions = v13e.predict_heldout(models, heldout)
    assert len(predictions) == 72 * 4
    assert {(row.block_id, row.strategy) for row in predictions} == {
        (row.block_id, strategy) for row in heldout for strategy in v13e.STRATEGIES
    }
    assert len(v13e.prediction_ledger_sha256(predictions)) == 64


def test_v13_primary_two_intervention_prediction_does_not_use_unselected_third_response() -> None:
    development, labels, templates = _development()
    heldout, _truth, _qc = _heldout(templates)
    models = v13e.fit_strategy_models(development, labels)
    target = heldout[0]
    base = [p for p in v13e.predict_heldout(models, [target]) if p.strategy == "dual_observer_vector"][0]
    third = base.intervention_order[2]
    altered = dict(target.responses)
    altered[third] = (999.0, -999.0)
    modified = v13e.BlockResponse(target.block_id, target.split, altered)
    changed = [p for p in v13e.predict_heldout(models, [modified]) if p.strategy == "dual_observer_vector"][0]
    assert changed.intervention_order[:2] == base.intervention_order[:2]
    assert changed.predicted_class_after_one == base.predicted_class_after_one
    assert changed.predicted_class_budget2 == base.predicted_class_budget2
    # Full-battery diagnosis is allowed to use the third response and may change.


def test_v13_truth_join_scores_blocks_and_exact_six_clusters() -> None:
    development, labels, templates = _development()
    heldout, truth, qc = _heldout(templates)
    models = v13e.fit_strategy_models(development, labels)
    predictions = v13e.predict_heldout(models, heldout)
    report = v13e.evaluate_predictions(predictions, truth, qc)
    assert report["heldout_block_count"] == 72
    assert report["gross_qc_violation"] is False
    assert report["prediction_ledger_sha256"] == v13e.prediction_ledger_sha256(predictions)
    assert set(report["strategies"]) == set(v13e.STRATEGIES)
    for strategy in v13e.STRATEGIES:
        assert len(report["per_cluster_accuracy"][strategy]) == 6
        row = report["strategies"][strategy]
        assert 0 <= row["heldout_min_cluster_localisation_accuracy_budget2"] <= 1
        assert 0 <= row["heldout_cluster_bootstrap_ci_low"] <= row["heldout_cluster_bootstrap_ci_high"] <= 1


def test_v13_evaluator_rejects_prediction_or_truth_cardinality_mismatch() -> None:
    development, labels, templates = _development()
    heldout, truth, qc = _heldout(templates)
    models = v13e.fit_strategy_models(development, labels)
    predictions = v13e.predict_heldout(models, heldout)
    with pytest.raises(ValueError, match="prediction ledger"):
        v13e.evaluate_predictions(predictions[:-1], truth, qc)
    with pytest.raises(ValueError):
        v13e.evaluate_predictions(predictions, truth[:-1], qc)


def test_v13_gross_protected_qc_violation_forces_claim_d() -> None:
    development, labels, templates = _development()
    heldout, truth, qc = _heldout(templates)
    models = v13e.fit_strategy_models(development, labels)
    predictions = v13e.predict_heldout(models, heldout)
    qc = list(qc)
    first = qc[0]
    qc[0] = v13e.QcAnnotation(first.block_id, protected_qc=True, gross_protocol_violation=True)
    report = v13e.evaluate_predictions(predictions, truth, qc)
    assert report["gross_qc_violation"] is True
    assert report["claim"]["level"] == "D"


def test_v13_prediction_ledger_hash_changes_if_prediction_is_tampered() -> None:
    development, labels, templates = _development()
    heldout, _truth, _qc = _heldout(templates)
    models = v13e.fit_strategy_models(development, labels)
    predictions = list(v13e.predict_heldout(models, heldout))
    original = v13e.prediction_ledger_sha256(predictions)
    row = predictions[0]
    predictions[0] = v13e.HeldoutPrediction(
        row.block_id,
        row.strategy,
        "shared_optical" if row.predicted_class_budget2 != "shared_optical" else "event_side",
        row.predicted_class_after_one,
        row.full_battery_prediction,
        row.intervention_order,
    )
    assert v13e.prediction_ledger_sha256(predictions) != original
