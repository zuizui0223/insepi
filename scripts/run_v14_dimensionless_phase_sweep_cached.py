#!/usr/bin/env python3
"""Performance wrapper for the canonical V14a phase sweep.

The scientific runner is unchanged. This wrapper memoises only the deterministic
closed-world prototype calculation keyed by `(DimensionlessPoint, regime,
samples)` before executing the same runner. Cached and uncached mini-runs are
required to be byte-identical in tests.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import runpy

import interaction_sensing.simulation.dimensionless_observability_v14 as v14


v14._prototype_vector = lru_cache(maxsize=None)(v14._prototype_vector)  # type: ignore[attr-defined]

runpy.run_path(str(Path(__file__).with_name("run_v14_dimensionless_phase_sweep.py")), run_name="__main__")
