"""Shared session state for the active CV tailoring pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.schemas import CandidateMasterCV, JobDescription, MatchReport, TailoredCV, TailoredSection


@dataclass
class CVSession:
    llm: Any = None
    cv_data: Optional[CandidateMasterCV] = None
    jd_data: Optional[JobDescription] = None
    match_report: Optional[MatchReport] = None
    tailored_sections: dict[str, TailoredSection] = field(default_factory=dict)
    tailored_cv: Optional[TailoredCV] = None

    def set_cv_data(self, payload: CandidateMasterCV | dict | None) -> Optional[CandidateMasterCV]:
        if payload is None:
            self.cv_data = None
            return None
        if isinstance(payload, CandidateMasterCV):
            self.cv_data = payload
        else:
            self.cv_data = CandidateMasterCV.model_validate(payload)
        return self.cv_data

    def set_jd_data(self, payload: JobDescription | dict | None) -> Optional[JobDescription]:
        if payload is None:
            self.jd_data = None
            return None
        if isinstance(payload, JobDescription):
            self.jd_data = payload
        else:
            self.jd_data = JobDescription.model_validate(payload)
        return self.jd_data

    def clear_generated_state(self) -> None:
        self.match_report = None
        self.tailored_sections.clear()
        self.tailored_cv = None

    def reset(self) -> None:
        self.cv_data = None
        self.jd_data = None
        self.match_report = None
        self.tailored_sections.clear()
        self.tailored_cv = None


session = CVSession()
