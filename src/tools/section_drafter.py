"""Draft core CV sections using the canonical CV and JD schemas."""

from src.schemas import JobDescription, RequirementPriority
from src.telemetry.logger import logger

_VALID = {"summary", "experience", "skills"}


def _target_keywords(jd: JobDescription) -> list[str]:
    keywords: list[str] = []

    for requirement in jd.requirements:
        value = (requirement.normalized_value or requirement.text).strip()
        if not value:
            continue
        if requirement.priority == RequirementPriority.MUST or requirement.required:
            keywords.append(value)

    keywords.extend(jd.target_keywords)

    deduped: list[str] = []
    seen = set()
    for keyword in keywords:
        normalized = keyword.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(keyword)

    return deduped


def _jd_tone(jd: JobDescription) -> str:
    if jd.summary:
        return jd.summary[:160]
    if jd.company_industry:
        return f"Target role in {jd.company_industry} with title {jd.title}."
    return f"Target role: {jd.title}."


def draft_section(args: str) -> str:
    from src.tools._session import session

    section = args.strip().lower()
    if section not in _VALID:
        return f"ERROR: Unknown section '{section}'. Choose: {', '.join(_VALID)}."
    if not session.jd_data:
        return "ERROR: No JD loaded. Call extract_jd first."
    if not session.cv_data:
        return "ERROR: No CV loaded. Call extract_cv first."
    if not session.llm:
        return "ERROR: No LLM in session."

    jd = session.jd_data
    cv = session.cv_data

    keywords = _target_keywords(jd)
    keywords_str = ", ".join(keywords[:14])

    if section == "experience":
        entries = []
        for exp in cv.work_experience:
            start = exp.start_date.raw if exp.start_date else "?"
            end = exp.end_date.raw if exp.end_date else ("Present" if exp.is_current else "Present")
            bullets = "\n".join(f"- {bullet.text}" for bullet in exp.bullets)
            entries.append(f"{exp.job_title} @ {exp.company_name} ({start} – {end})\n{bullets}")
        source = "\n\n".join(entries) or "No work experience found."
        section_label = "Work Experience"

    elif section == "summary":
        name = cv.contact.full_name
        skills = [skill.name for skill in cv.skills][:10]
        recent = cv.work_experience[0] if cv.work_experience else None
        source = (
            f"Name: {name}\n"
            f"Skills: {', '.join(skills)}\n"
            f"Most recent: {(recent.job_title + ' @ ' + recent.company_name) if recent else ''}"
        )
        section_label = "Professional Summary"

    else:  # skills
        skills = [skill.name for skill in cv.skills]
        source = "Verified skills: " + ", ".join(skills)
        section_label = "Core Competencies"

    logger.log_event("TOOL_CALL", {"tool": "draft_section", "section": section, "keywords": keywords[:8]})

    system = (
        f"You are a professional CV writer. Rewrite the '{section_label}' section "
        f"to naturally incorporate these JD keywords: {keywords_str}.\n"
        f"Rules:\n"
        f"- Use STAR method for experience bullets (Action + measurable Result).\n"
        f"- Do NOT invent experiences or metrics not in the source data.\n"
        f"- Tone: {_jd_tone(jd)}\n"
        f"- Return only the rewritten section text, no explanation."
    )

    result = session.llm.generate(source, system_prompt=system)
    drafted = result["content"].strip()

    session.tailored_sections[section] = drafted

    logger.log_event("TOOL_RESULT", {"tool": "draft_section", "section": section, "chars": len(drafted)})
    return drafted


section_drafter_tool = {
    "name": "draft_section",
    "description": (
        "Rewrites a CV section to target the job's required keywords. "
        "Requires extract_cv and extract_jd to be called first. "
        "Input: section name — one of: summary, experience, skills. "
        "Output: rewritten section text optimized for the target job."
    ),
    "function": draft_section,
}
