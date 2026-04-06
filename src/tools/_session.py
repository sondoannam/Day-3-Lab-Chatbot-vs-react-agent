"""
Shared session state cho CV tailoring agent.
Dùng CandidateMasterCV (từ cv_extractor) và JDExtraction (từ jd_extractor).
"""
from typing import Any, Dict, Optional

from src.schemas.cv_tailoring import (
    CandidateMasterCV,
    JobDescription,
    MatchReport,
    TailoredSection,
)


class CVSession:
    llm: Any = None                                    # LLMProvider instance
    cv_data: Optional[CandidateMasterCV] = None        # Canonical CandidateMasterCV object
    jd_data: Optional[JobDescription] = None           # JobDescription object từ extract_jd_requirements
    match_report: Optional[MatchReport] = None         # MatchReport từ matcher tool
    tailored_sections: Dict[str, TailoredSection] = {} # section_id → TailoredSection
    tailored_cv: Any = None                            # TailoredCV khi assembled


session = CVSession()
