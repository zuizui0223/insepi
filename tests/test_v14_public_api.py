import interaction_sensing as sensing


def test_v14_public_api_exposes_triad_and_visit_semantics() -> None:
    for name in (
        "TargetEvidence",
        "TargetRouteEvidence",
        "TargetEvidenceRoute",
        "NuisanceEvidence",
        "ObservationSupport",
        "ObservationTriadPolicy",
        "VisitObservationRecord",
        "VisitObservationStatus",
        "DiagnosticAction",
        "visit_record_from_interpretation",
        "summarise_visit_observations",
    ):
        assert hasattr(sensing, name), name
