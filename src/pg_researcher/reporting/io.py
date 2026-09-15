from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from pg_researcher.models import ReportPlan, ResearchReport


class ReportIOError(ValueError):
    pass


def load_report_plan(path: Path) -> ReportPlan:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ReportPlan.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ReportIOError(f"invalid report plan {path}: {exc}") from exc


def load_research_report(path: Path) -> ResearchReport:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ResearchReport.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ReportIOError(f"invalid research report {path}: {exc}") from exc


def write_research_report(report: ResearchReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False)
    path.write_text(rendered + "\n", encoding="utf-8")
