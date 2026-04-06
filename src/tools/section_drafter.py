"""
section_drafter.py — Tool 4
Rewrite một section của CV để nhắm vào JD keywords.
Dùng session.cv_data (CandidateMasterCV) + session.jd_data (JDExtraction).

Agent gọi: Action: draft_section(summary)
           Action: draft_section(experience)
           Action: draft_section(skills)
"""
from src.telemetry.logger import logger

_VALID = {"summary", "experience", "skills"}


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

    keywords = [s.skill_name for s in jd.technical_skills] + [s.skill_name for s in jd.soft_skills]
    keywords_str = ", ".join(keywords[:14])

    # ── Build source data from CandidateMasterCV ──────────────
    if section == "experience":
        entries = []
        for exp in cv.get("work_experience", []):
            bullets = "\n".join(f"- {b['text']}" for b in exp.get("bullets", []))
            entries.append(f"{exp['job_title']} @ {exp['company_name']} ({exp.get('start_date',{}).get('raw','?')} – {exp.get('end_date',{}).get('raw','Present')})\n{bullets}")
        source = "\n\n".join(entries) or "No work experience found."
        section_label = "Work Experience"

    elif section == "summary":
        name = cv.get("contact", {}).get("full_name", "Candidate")
        skills = [s["name"] for s in cv.get("skills", [])][:10]
        recent = cv.get("work_experience", [{}])[0]
        source = (
            f"Name: {name}\n"
            f"Skills: {', '.join(skills)}\n"
            f"Most recent: {recent.get('job_title','')} @ {recent.get('company_name','')}"
        )
        section_label = "Professional Summary"

    else:  # skills
        skills = [s["name"] for s in cv.get("skills", [])]
        source = "Verified skills: " + ", ".join(skills)
        section_label = "Core Competencies"

    logger.log_event("TOOL_CALL", {"tool": "draft_section", "section": section, "keywords": keywords[:8]})

    system = (
        f"You are a professional CV writer. Rewrite the '{section_label}' section "
        f"to naturally incorporate these JD keywords: {keywords_str}.\n"
        f"Rules:\n"
        f"- Use STAR method for experience bullets (Action + measurable Result).\n"
        f"- Do NOT invent experiences or metrics not in the source data.\n"
        f"- Tone: {jd.summary_requirements[:120]}\n"
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
