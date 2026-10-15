"""
Evaluation export pipeline: harvest logs → rubric §3 → ``FINAL_RESULTS_TABLE`` →
``failure_log.md`` → ``FINAL_EVALUATION_REPORT.md`` (fully generated report).

Run the full chain::

    python scripts/export_evaluation.py
    python -m scripts.export_evaluation

Or individual steps, e.g.::

    python scripts/export_evaluation/harvest_evidence.py
"""

from __future__ import annotations

from scripts.export_evaluation.pipeline import main as run_export_pipeline

__all__ = ["run_export_pipeline"]
