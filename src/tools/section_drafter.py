"""
section_drafter.py — Tool 4
Drafts tailored CV sections using canonical CandidateMasterCV + MatchReport.
Returns structured TailoredSection / TailoredTextBlock with source evidence and
targeted requirement IDs. Assembles a TailoredCV and exports markdown.

Agent calls:
    Action: draft_section(summary)
    Action: draft_section(experience)
    Action: draft_section(skills)
    Action: assemble_cv()
    Action: export_cv_markdown()
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from src.schemas.cv_tailoring import (
    CandidateMasterCV,
    EvidenceQuote,
    ExtractionMetadata,
    JobDescription,
    MatchReport,
    MatchType,
    RequirementMatch,
    SourceType,
    TailoredCV,
    TailoredSection,
    TailoredTextBlock,
)
from src.telemetry.logger import logger

_VALID = {"summary", "experience", "skills"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _priority_req_ids(jd: JobDescription, match_report: MatchReport | None, section: str) -> List[str]:
    """Return requirement IDs most relevant to the section."""
    if section == "skills":
        cats = {"hard_skill", "tool"}
    elif section == "experience":
        cats = {"experience", "responsibility", "domain"}
    else:  # summary
        cats = {"hard_skill", "tool", "experience", "soft_skill"}

    # Prefer unmatched (gaps) first so we actively address them
    gap_ids: List[str] = []
    matched_ids: List[str] = []
    if match_report:
        for rm in match_report.matched_requirements:
            if rm.requirement_id in [r.requirement_id for r in jd.requirements if r.category.value in cats]:
                if not rm.matched:
                    gap_ids.append(rm.requirement_id)
                else:
                    matched_ids.append(rm.requirement_id)

    # Fall back to all reqs in category if match_report not available
    all_ids = [r.requirement_id for r in jd.requirements if r.category.value in cats]
    ordered = gap_ids + matched_ids + [i for i in all_ids if i not in gap_ids and i not in matched_ids]
    return ordered[:10]


def _keywords_for_section(jd: JobDescription, section: str) -> str:
    if section == "skills":
        cats = {"hard_skill", "tool"}
    elif section == "experience":
        cats = {"hard_skill", "tool", "experience", "responsibility"}
    else:
        cats = {"hard_skill", "tool", "experience", "soft_skill", "domain"}

    kws = [r.text for r in jd.requirements if r.category.value in cats]
    kws += jd.target_keywords or []
    return ", ".join(dict.fromkeys(kws[:16]))


# ── Section drafters ──────────────────────────────────────────────────────────

def _draft_summary(cv: CandidateMasterCV, jd: JobDescription, llm) -> tuple[str, List[EvidenceQuote]]:
    name = cv.contact.full_name
    skills = [s.name for s in cv.skills[:10]]
    recent = cv.work_experience[0] if cv.work_experience else None
    recent_line = f"{recent.job_title} @ {recent.company_name}" if recent else "N/A"
    existing_summary = cv.professional_summary or ""

    source = (
        f"Candidate: {name}\n"
        f"Existing summary: {existing_summary}\n"
        f"Skills: {', '.join(skills)}\n"
        f"Most recent role: {recent_line}"
    )
    evidence = []
    if existing_summary:
        evidence.append(EvidenceQuote(quote=existing_summary[:200], section_id="professional_summary", confidence=1.0))

    keywords_str = _keywords_for_section(jd, "summary")
    system = (
        f"You are a professional CV writer. Write a 3-5 sentence Professional Summary for '{name}' "
        f"targeting the role: {jd.title} at {jd.company_name or 'the company'}.\n"
        f"Naturally weave in these keywords: {keywords_str}.\n"
        f"Rules:\n"
        f"- Ground every claim in the source data below.\n"
        f"- Do NOT invent experiences or metrics not present.\n"
        f"- Tone: confident, results-oriented.\n"
        f"- Return only the summary paragraph, no heading or explanation."
    )
    result = llm.generate(source, system_prompt=system)
    return result["content"].strip(), evidence


def _draft_skills(cv: CandidateMasterCV, jd: JobDescription, match_report: MatchReport | None, llm) -> tuple[str, List[EvidenceQuote]]:
    skill_names = [s.name for s in cv.skills]
    missing_kws: List[str] = match_report.missing_keywords if match_report else []
    jd_tools = [r.text for r in jd.requirements if r.category.value in {"hard_skill", "tool"}]

    source = (
        f"Verified candidate skills: {', '.join(skill_names)}\n"
        f"JD required skills/tools: {', '.join(jd_tools[:20])}\n"
        f"Skill gaps to address if possible: {', '.join(missing_kws[:10])}"
    )
    evidence = [EvidenceQuote(quote=s.name, section_id="skills", confidence=1.0) for s in cv.skills[:5]]

    system = (
        f"You are a professional CV writer. Produce a 'Core Competencies' skills list "
        f"for a {jd.title} role.\n"
        f"Rules:\n"
        f"- Only include skills the candidate actually has (from 'Verified candidate skills').\n"
        f"- Prefer JD-matching terms; use the exact JD wording where skill is the same.\n"
        f"- Format as a compact pipe-separated list, e.g.: Python | REST APIs | Docker\n"
        f"- Do NOT add skills not verified in source data.\n"
        f"- Return only the skills list, no heading or explanation."
    )
    result = llm.generate(source, system_prompt=system)
    return result["content"].strip(), evidence


def _draft_experience(cv: CandidateMasterCV, jd: JobDescription, llm) -> tuple[str, List[EvidenceQuote]]:
    entries = []
    evidence: List[EvidenceQuote] = []
    for exp in cv.work_experience:
        start = exp.start_date.raw if exp.start_date else "?"
        end = exp.end_date.raw if exp.end_date else "Present"
        bullets_raw = "\n".join(f"- {b.text}" for b in exp.bullets)
        entries.append(
            f"{exp.job_title} @ {exp.company_name} ({start} – {end})\n{bullets_raw}"
        )
        for b in exp.bullets[:2]:
            evidence.append(EvidenceQuote(quote=b.text[:150], section_id=exp.experience_id, confidence=0.9))

    source = "\n\n".join(entries) or "No work experience found."
    keywords_str = _keywords_for_section(jd, "experience")

    system = (
        f"You are a professional CV writer. Rewrite the Work Experience section to target: {jd.title}.\n"
        f"Naturally incorporate keywords: {keywords_str}.\n"
        f"Rules:\n"
        f"- Use STAR method for each bullet (Action verb + measurable Result).\n"
        f"- Preserve company names, job titles, and date ranges exactly.\n"
        f"- Do NOT invent metrics or experiences not present in the source.\n"
        f"- Return formatted experience entries only, no explanation."
    )
    result = llm.generate(source, system_prompt=system)
    return result["content"].strip(), evidence


# ── Public tool function ──────────────────────────────────────────────────────

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

    cv: CandidateMasterCV = session.cv_data
    jd: JobDescription = session.jd_data
    match_report: MatchReport | None = session.match_report

    logger.log_event("TOOL_CALL", {"tool": "draft_section", "section": section})

    # Draft text + collect raw evidence
    if section == "summary":
        drafted_text, raw_evidence = _draft_summary(cv, jd, session.llm)
        title = "Professional Summary"
    elif section == "skills":
        drafted_text, raw_evidence = _draft_skills(cv, jd, match_report, session.llm)
        title = "Core Competencies"
    else:
        drafted_text, raw_evidence = _draft_experience(cv, jd, session.llm)
        title = "Work Experience"

    # Determine which requirement IDs this section targets
    req_ids = _priority_req_ids(jd, match_report, section)

    # Build structured output
    block = TailoredTextBlock(
        block_id=_new_id("blk"),
        text=drafted_text,
        source_evidence=raw_evidence,
        targeted_requirement_ids=req_ids,
    )
    tailored_section = TailoredSection(
        section_id=_new_id(section),
        title=title,
        blocks=[block],
    )

    session.tailored_sections[section] = tailored_section

    logger.log_event("TOOL_RESULT", {
        "tool": "draft_section",
        "section": section,
        "chars": len(drafted_text),
        "targeted_reqs": len(req_ids),
    })

    return drafted_text


def assemble_cv(_args: str = "") -> str:
    """Assemble all drafted sections into a TailoredCV object."""
    from src.tools._session import session

    if not session.cv_data:
        return "ERROR: No CV loaded."
    if not session.jd_data:
        return "ERROR: No JD loaded."
    if not session.tailored_sections:
        return "ERROR: No sections drafted yet. Call draft_section first."

    cv: CandidateMasterCV = session.cv_data
    jd: JobDescription = session.jd_data

    # Canonical section order: summary → skills → experience
    ordered_keys = ["summary", "skills", "experience"]
    sections = [session.tailored_sections[k] for k in ordered_keys if k in session.tailored_sections]

    metadata = ExtractionMetadata(
        source_type=SourceType.TEXT,
        extractor_name="section_drafter",
        extractor_version="2.0",
        extracted_at=datetime.now(timezone.utc),
    )

    tailored_cv = TailoredCV(
        metadata=metadata,
        target_job_title=jd.title,
        target_company_name=jd.company_name,
        contact=cv.contact,
        sections=sections,
        match_report=session.match_report,
    )
    session.tailored_cv = tailored_cv

    logger.log_event("TOOL_RESULT", {"tool": "assemble_cv", "sections": len(sections)})
    return f"TailoredCV assembled with {len(sections)} section(s): {', '.join(session.tailored_sections.keys())}."


def export_cv_markdown(_args: str = "") -> str:
    """Export the assembled TailoredCV as a markdown string (and save to file)."""
    from src.tools._session import session

    if not session.tailored_cv:
        return "ERROR: No TailoredCV assembled yet. Call assemble_cv first."

    tcv: TailoredCV = session.tailored_cv
    lines: List[str] = []

    # Header
    lines.append(f"# {tcv.contact.full_name}")
    contact = tcv.contact
    contact_parts = []
    if contact.email:
        contact_parts.append(contact.email)
    if contact.phone:
        contact_parts.append(contact.phone)
    if contact.location:
        contact_parts.append(contact.location)
    if contact.linkedin_url:
        contact_parts.append(str(contact.linkedin_url))
    if contact_parts:
        lines.append("  |  ".join(contact_parts))
    lines.append("")
    lines.append(f"**Target Role:** {tcv.target_job_title}" + (f" @ {tcv.target_company_name}" if tcv.target_company_name else ""))
    lines.append("")

    # Sections
    for section in tcv.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        for block in section.blocks:
            lines.append(block.text)
            lines.append("")

    # Match report summary
    if tcv.match_report:
        mr = tcv.match_report
        lines.append("---")
        lines.append("## ATS Match Summary")
        lines.append("")
        lines.append(f"- **Overall Score:** {mr.overall_score:.0f}/100")
        lines.append(f"- **Keyword Score:** {mr.keyword_score:.0f}/100")
        lines.append(f"- **Semantic Score:** {mr.semantic_score:.0f}/100")
        if mr.missing_keywords:
            lines.append(f"- **Still Missing:** {', '.join(mr.missing_keywords[:8])}")
        lines.append("")

    markdown = "\n".join(lines)

    # Save to file
    out_path = Path("tailored_cv.md")
    out_path.write_text(markdown, encoding="utf-8")

    logger.log_event("TOOL_RESULT", {"tool": "export_cv_markdown", "path": str(out_path), "chars": len(markdown)})
    return f"Markdown CV exported to '{out_path}' ({len(markdown)} chars).\n\n{markdown}"


# ── Tool descriptors ──────────────────────────────────────────────────────────

section_drafter_tool = {
    "name": "draft_section",
    "description": (
        "Rewrites a CV section using canonical CV data and match report to target the job's keywords. "
        "Requires extract_cv and extract_jd to be called first. "
        "Input: section name — one of: summary, experience, skills. "
        "Returns structured TailoredSection with source evidence and targeted requirement IDs."
    ),
    "function": draft_section,
}

assemble_cv_tool = {
    "name": "assemble_cv",
    "description": (
        "Assembles all drafted sections into a valid TailoredCV object. "
        "Requires at least one draft_section call first. No input needed."
    ),
    "function": assemble_cv,
}

export_cv_markdown_tool = {
    "name": "export_cv_markdown",
    "description": (
        "Exports the assembled TailoredCV as a readable markdown file (tailored_cv.md). "
        "Requires assemble_cv to be called first. No input needed."
    ),
    "function": export_cv_markdown,
}
