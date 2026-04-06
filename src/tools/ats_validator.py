"""
ats_validator.py — Tool 5
Local, deterministic ATS scoring. Không dùng LLM.
Dùng session.jd_data (JDExtraction) để lấy required keywords.

Agent gọi: Action: validate_ats(<tailored cv text>)
is_ready=True → agent dừng loop → Final Answer.
"""
import re
from src.telemetry.logger import logger

_REQUIRED_SECTIONS = ["experience", "education", "skills"]
_FORMAT_ANTI_PATTERNS = [
    (r"\|.+\|.+\|", "Table detected — ATS may fail to parse columns"),
    (r"<[a-zA-Z]+>", "HTML tags detected — strip before submission"),
]


def validate_ats(args: str) -> str:
    from src.tools._session import session

    text = args.strip()
    if not text:
        # Fallback: assemble from tailored sections in session
        if session.tailored_sections:
            text = "\n\n".join(session.tailored_sections.values())
        else:
            return "ERROR: No CV text to validate. Provide text or call draft_section first."

    if not session.jd_data:
        return "ERROR: No JD loaded. Call extract_jd first."

    jd = session.jd_data
    cv_lower = text.lower()

    # All required keywords from JDExtraction
    all_kw = (
        [s.skill_name for s in jd.technical_skills if s.is_mandatory] +
        [s.skill_name for s in jd.soft_skills if s.is_mandatory]
    )
    nice_kw = (
        [s.skill_name for s in jd.technical_skills if not s.is_mandatory] +
        [s.skill_name for s in jd.soft_skills if not s.is_mandatory]
    )

    matched  = [kw for kw in all_kw if kw.lower() in cv_lower]
    missing  = [kw for kw in all_kw if kw.lower() not in cv_lower]
    kw_score = (len(matched) / len(all_kw) * 100) if all_kw else 100.0

    sections_found = sum(1 for s in _REQUIRED_SECTIONS if s in cv_lower)
    sec_score = (sections_found / len(_REQUIRED_SECTIONS)) * 100

    flags = [msg for pat, msg in _FORMAT_ANTI_PATTERNS if re.search(pat, text)]
    fmt_score = max(0.0, 100.0 - len(flags) * 25)

    overall  = (kw_score * 0.40) + (fmt_score * 0.40) + (sec_score * 0.20)
    is_ready = overall >= 80.0 and len(missing) == 0

    logger.log_event("TOOL_RESULT", {
        "tool": "validate_ats",
        "score": round(overall, 1),
        "missing": missing,
        "is_ready": is_ready,
    })

    lines = [
        f"ATS Score: {overall:.1f}/100",
        f"  Keyword match : {kw_score:.1f}%  ({len(matched)}/{len(all_kw)} mandatory keywords matched)",
        f"  Format        : {fmt_score:.1f}%",
        f"  Sections      : {sec_score:.1f}%",
    ]
    if missing:
        lines.append(f"Missing keywords : {', '.join(missing)}")
    if nice_kw:
        matched_nice = [k for k in nice_kw if k.lower() in cv_lower]
        lines.append(f"Nice-to-have hit : {len(matched_nice)}/{len(nice_kw)}")
    if flags:
        lines.append(f"Format issues    : {'; '.join(flags)}")
    lines.append(f"Ready to submit  : {'YES ✓' if is_ready else 'NO — improve missing keywords'}")

    return "\n".join(lines)


ats_validator_tool = {
    "name": "validate_ats",
    "description": (
        "Scores the tailored CV text against the job requirements using a local ATS algorithm. "
        "Requires extract_jd to be called first. "
        "Input: the tailored CV text (or empty string to use drafted sections from session). "
        "Output: ATS score, missing keywords, format issues, and ready-to-submit flag. "
        "When score >= 80 and no missing keywords, the CV is ready — output Final Answer."
    ),
    "function": validate_ats,
}
