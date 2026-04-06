"""
Shared session state cho CV tailoring agent.
Dùng CandidateMasterCV (từ cv_extractor) và JDExtraction (từ jd_extractor).
"""
from typing import Any, Dict, Optional


class CVSession:
    llm: Any = None                          # LLMProvider instance
    cv_data: Optional[Dict] = None           # CandidateMasterCV dict từ extract_cv
    jd_data: Any = None                      # JDExtraction object từ extract_jd_requirements
    tailored_sections: Dict[str, str] = {}   # section → drafted text


session = CVSession()
