"""V15 target-absence evidence contract.

Observation support answers whether the primary stream was measurable enough to
attempt interpretation. It does not certify biological target absence, and a low
score from a positive-only target observer cannot be inverted into absence.

A safe absence call therefore requires a separate evidence channel/criterion that
has been validated independently of the positive target path. This module only
specifies that interface. It does not claim that such a field-calibrated channel
already exists.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TargetAbsenceEvidence:
    """Independent evidence that may support target absence.

    ``supports_absence=True`` is intentionally fail-closed: the caller must name
    both the evidence source and an independent validation reference, and must
    explicitly attest that the evidence is not obtained by simply inverting the
    positive target observer.
    """

    supports_absence: bool = False
    source: str | None = None
    validation_ref: str | None = None
    independent_of_positive_target_path: bool = False

    def __post_init__(self) -> None:
        if self.supports_absence:
            if self.source is None or not self.source.strip():
                raise ValueError("certified absence evidence requires a named source")
            if self.validation_ref is None or not self.validation_ref.strip():
                raise ValueError("certified absence evidence requires an independent validation reference")
            if not self.independent_of_positive_target_path:
                raise ValueError("absence evidence cannot be obtained by inverting the positive target path")

    @classmethod
    def unavailable(cls) -> "TargetAbsenceEvidence":
        """Default V15 state before an independent absence channel is validated."""

        return cls()

    @classmethod
    def independently_validated(
        cls,
        *,
        source: str,
        validation_ref: str,
    ) -> "TargetAbsenceEvidence":
        """Construct a positive absence-evidence record with explicit provenance."""

        return cls(
            supports_absence=True,
            source=source,
            validation_ref=validation_ref,
            independent_of_positive_target_path=True,
        )
