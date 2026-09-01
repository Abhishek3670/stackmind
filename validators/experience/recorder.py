"""Experience recording logic that extracts structured execution evidence from harness runs.

Implements Phase 1 Experience Capture (§28 & §1–§2).
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validators.experience.models import (
    ExperienceAction,
    ExperienceCorrection,
    ExperienceFailure,
    ExperienceObservation,
    ExperienceRecord,
    ExperienceVerification,
)
from validators.harness.snapshot import TrustLevel, VerificationDimensions, WorkspaceDiff


class ExperienceRecorder:
    """Transforms harness execution contexts into canonical Experience Records."""

    @staticmethod
    def capture_from_stage_inputs(
        project_path: Path,
        agent: str,
        stage_inputs: dict[str, Any],
        *,
        diff: WorkspaceDiff | None = None,
        dimensions: VerificationDimensions | None = None,
        trust_level: TrustLevel | None = None,
        duration_ms: int = 0,
    ) -> ExperienceRecord:
        """Construct an ExperienceRecord from a completed harness task execution."""
        task = stage_inputs["task"]
        decision = stage_inputs["decision"]
        context = stage_inputs["context"]
        now: datetime = stage_inputs.get("run_at", datetime.now(timezone.utc))
        timestamp_str = now.isoformat()

        # Task signature fingerprint
        task_query = getattr(task, "query", "") or getattr(task, "title", "") or task.identifier
        task_signature = f"{task.kind}:{task_query}"
        experience_id = ExperienceRecord.mint_id(task_signature, timestamp_str)

        # Actions & Observations
        actions: list[ExperienceAction] = []
        observations: list[ExperienceObservation] = []

        if hasattr(decision, "commands") and decision.commands:
            for cmd in decision.commands:
                actions.append(
                    ExperienceAction(
                        tool="bash",
                        command_or_symbol=cmd,
                        input_summary=cmd[:200],
                        timestamp=timestamp_str,
                    )
                )
                observations.append(
                    ExperienceObservation(
                        output_summary="Executed command sequence",
                        exit_code=0,
                        is_error=False,
                    )
                )

        # Failures & Blockers
        failures: list[ExperienceFailure] = []
        if decision.blockers:
            for b in decision.blockers:
                failures.append(
                    ExperienceFailure(
                        phase="execution",
                        error_message=b,
                    )
                )

        corrections: list[ExperienceCorrection] = []

        # Effective verification dimensions and diff
        effective_diff = diff or stage_inputs.get("diff", WorkspaceDiff())
        effective_dim = dimensions or stage_inputs.get("dimensions", VerificationDimensions())
        effective_trust = trust_level or stage_inputs.get("trust_level", TrustLevel.OBSERVABLE)

        verification = ExperienceVerification(
            dimensions=effective_dim,
            observed_diff=effective_diff,
            contract_id=getattr(task, "work_order_id", None),
            declaration_matches=stage_inputs.get("declaration_matches", True),
            tests_passed=effective_dim.all_passed,
        )

        environment = {
            "git_commit": getattr(context, "git_commit", None),
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
            "runtime_version": "v3.1.0",
        }

        initial_state = {
            "context_revision": getattr(context, "revision", "REV-0000000000000000"),
            "work_order_id": getattr(task, "work_order_id", None),
        }

        final_state = {
            "all_changed_files": list(effective_diff.all_changed_files),
            "files_modified_count": len(effective_diff.all_changed_files),
            "status": decision.status,
            "summary": decision.summary,
        }

        return ExperienceRecord(
            experience_id=experience_id,
            work_order_id=getattr(task, "work_order_id", None),
            task_id=task.identifier,
            agent_id=agent,
            task_signature=task_signature,
            environment=environment,
            initial_state=initial_state,
            actions=tuple(actions),
            observations=tuple(observations),
            failures=tuple(failures),
            corrections=tuple(corrections),
            final_state=final_state,
            verification=verification,
            trust_level=effective_trust,
            learning_eligible=(effective_trust == TrustLevel.LEARNING_ELIGIBLE),
            outcome=decision.status,
            duration_ms=duration_ms,
            recorded_at=timestamp_str,
        )
