from importlib import import_module
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.schemas import (
    CandidateMasterCV,
    CertificationRecord,
    ContactInfo,
    CustomSection,
    DateValue,
    EducationRecord,
    EvidenceQuote,
    ExtractionMetadata,
    LanguageEntry,
    SkillEntry,
    SkillCategory,
    SourceType,
    WorkExperience,
    CVBullet,
)


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}")
URL_RE = re.compile(r"(?:https?://|www\.)\S+")
DATE_RANGE_RE = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)?"
    r"\s*(?:19|20)\d{2}\s*(?:-|to|–|—)\s*(?:Present|Current|Now|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)?\s*(?:19|20)\d{2})",
    re.IGNORECASE,
)

SECTION_ALIASES = {
    "professional_summary": {"summary", "professional summary", "profile", "objective", "about"},
    "skills": {"skills", "technical skills", "core competencies", "competencies", "tech stack"},
    "work_experience": {"experience", "work experience", "professional experience", "employment history"},
    "education": {"education", "academic background"},
    "certifications": {"certifications", "licenses", "certificates"},
    "projects": {"projects", "selected projects", "personal projects"},
    "languages": {"languages"},
}


def _load_pdfplumber():
    try:
        return import_module("pdfplumber")
    except ImportError as exc:
        raise RuntimeError(
            "pdfplumber is not installed. Add it to the environment before running extract_cv."
        ) from exc


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _normalize_heading(line: str) -> str:
    return re.sub(r"[^a-z ]", "", line.lower()).strip()


def _section_key_for_line(line: str) -> Optional[str]:
    normalized = _normalize_heading(line)
    for key, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return key
    return None


def _extract_pdf_text(pdf_path: Path) -> tuple[str, int]:
    pdfplumber = _load_pdfplumber()
    full_text: List[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=2, y_tolerance=3)
            if page_text:
                full_text.append(page_text.strip())

    return "\n\n".join(full_text), num_pages


def _split_sections(raw_text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {"header": []}
    current_section = "header"

    for raw_line in raw_text.splitlines():
        line = _normalize_line(raw_line)
        if not line:
            continue

        next_section = _section_key_for_line(line)
        if next_section:
            current_section = next_section
            sections.setdefault(current_section, [])
            continue

        sections.setdefault(current_section, []).append(line)

    return sections


def _normalize_url(url: str) -> str:
    cleaned = url.strip().rstrip(",.;")
    if cleaned.startswith("www."):
        return f"https://{cleaned}"
    return cleaned


def _extract_contact(header_lines: List[str], raw_text: str) -> ContactInfo:
    email_match = EMAIL_RE.search(raw_text)
    phone_match = PHONE_RE.search(raw_text)
    urls = [_normalize_url(match.group(0)) for match in URL_RE.finditer(raw_text)]

    linkedin_url = next((url for url in urls if "linkedin.com" in url.lower()), None)
    github_url = next((url for url in urls if "github.com" in url.lower()), None)
    portfolio_url = next(
        (
            url
            for url in urls
            if "linkedin.com" not in url.lower() and "github.com" not in url.lower()
        ),
        None,
    )

    full_name = header_lines[0] if header_lines else "Unknown Candidate"
    location = None
    for line in header_lines[1:5]:
        if email_match and email_match.group(0) in line:
            continue
        if phone_match and phone_match.group(0) in line:
            continue
        if URL_RE.search(line):
            continue
        if len(line.split()) <= 8:
            location = line
            break

    return ContactInfo(
        full_name=full_name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        location=location,
        linkedin_url=linkedin_url,
        github_url=github_url,
        portfolio_url=portfolio_url,
    )


def _make_evidence(text: str, section_id: str) -> List[EvidenceQuote]:
    return [EvidenceQuote(quote=text, section_id=section_id)] if text else []


def _infer_skill_category(skill_name: str) -> SkillCategory:
    lowered = skill_name.lower()
    if lowered in {"python", "java", "javascript", "typescript", "c#", ".net", "go", "php", "ruby"}:
        return SkillCategory.TECHNICAL
    if lowered in {"react", "vue", "angular", "asp.net", "spring boot", "django", "flask", "fastapi"}:
        return SkillCategory.FRAMEWORK
    if lowered in {"aws", "azure", "gcp", "kubernetes", "docker"}:
        return SkillCategory.CLOUD
    if lowered in {"jira", "confluence", "figma", "salesforce", "power bi", "tableau"}:
        return SkillCategory.TOOL
    if lowered in {"leadership", "communication", "mentoring", "problem solving", "stakeholder management"}:
        return SkillCategory.SOFT
    return SkillCategory.OTHER


def _parse_skills(skill_lines: List[str]) -> List[SkillEntry]:
    if not skill_lines:
        return []

    tokens: List[str] = []
    for line in skill_lines:
        cleaned = line.lstrip("-• ")
        tokens.extend(re.split(r"\s*[|,/;]\s*|\s+[-:]\s+", cleaned))

    seen = set()
    skills: List[SkillEntry] = []
    for token in tokens:
        name = token.strip()
        if not name or len(name) < 2:
            continue
        normalized = name.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        skills.append(
            SkillEntry(
                skill_id=f"skill_{len(skills) + 1}",
                name=name,
                normalized_name=normalized,
                category=_infer_skill_category(name),
                evidence=_make_evidence(name, "skills"),
            )
        )
    return skills


def _parse_education(education_lines: List[str]) -> List[EducationRecord]:
    records: List[EducationRecord] = []
    for line in education_lines:
        cleaned = line.lstrip("-• ")
        if not cleaned:
            continue
        records.append(
            EducationRecord(
                education_id=f"education_{len(records) + 1}",
                institution=cleaned,
                evidence=_make_evidence(cleaned, "education"),
            )
        )
    return records


def _parse_simple_custom_section(section_id: str, title: str, lines: List[str]) -> Optional[CustomSection]:
    content = [line.lstrip("-• ") for line in lines if line.strip()]
    if not content:
        return None
    return CustomSection(section_id=section_id, title=title, content=content)


def _parse_certifications(certification_lines: List[str]) -> List[CertificationRecord]:
    records: List[CertificationRecord] = []
    for line in certification_lines:
        cleaned = line.lstrip("-• ")
        if not cleaned:
            continue
        records.append(
            CertificationRecord(
                certification_id=f"certification_{len(records) + 1}",
                name=cleaned,
                evidence=_make_evidence(cleaned, "certifications"),
            )
        )
    return records


def _parse_languages(language_lines: List[str]) -> List[LanguageEntry]:
    if not language_lines:
        return []

    tokens: List[str] = []
    for line in language_lines:
        cleaned = line.lstrip("-• ")
        tokens.extend(re.split(r"\s*[|,/;]\s*", cleaned))

    languages: List[LanguageEntry] = []
    seen = set()
    for token in tokens:
        value = token.strip()
        if not value:
            continue
        normalized = value.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        languages.append(LanguageEntry(language=value))
    return languages


def _looks_like_experience_header(line: str) -> bool:
    if DATE_RANGE_RE.search(line):
        return True
    lowered = line.lower()
    if " at " in lowered:
        return True
    if "|" in line and len(line.split()) <= 16:
        return True
    return False


def _parse_date_from_text(text: str) -> Optional[DateValue]:
    match = re.search(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\s*(?:19|20)\d{2}|Present|Current|Now)", text, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1).strip()
    year_match = re.search(r"(19|20)\d{2}", raw)
    month_match = re.search(r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec", raw, re.IGNORECASE)
    month_lookup = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "sept": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    return DateValue(
        raw=raw,
        year=int(year_match.group(0)) if year_match else None,
        month=month_lookup.get(month_match.group(0).lower()) if month_match else None,
    )


def _parse_work_experience(experience_lines: List[str]) -> List[WorkExperience]:
    if not experience_lines:
        return []

    blocks: List[List[str]] = []
    current_block: List[str] = []
    for line in experience_lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        if _looks_like_experience_header(cleaned) and current_block:
            blocks.append(current_block)
            current_block = [cleaned]
            continue
        current_block.append(cleaned)
    if current_block:
        blocks.append(current_block)

    experiences: List[WorkExperience] = []
    for index, block in enumerate(blocks, start=1):
        header = block[0]
        title = header
        company = "Unknown Company"

        if " at " in header.lower():
            parts = re.split(r"\bat\b", header, maxsplit=1, flags=re.IGNORECASE)
            title = parts[0].strip(" |-:") or header
            company = parts[1].strip(" |-:") if len(parts) > 1 else company
        elif "|" in header:
            pieces = [piece.strip() for piece in header.split("|") if piece.strip()]
            if len(pieces) >= 2:
                title = pieces[0]
                company = pieces[1]

        bullet_lines = block[1:] if len(block) > 1 else []
        bullets = [
            CVBullet(
                bullet_id=f"experience_{index}_bullet_{bullet_index}",
                text=line.lstrip("-• "),
                evidence=_make_evidence(line, f"work_experience_{index}"),
            )
            for bullet_index, line in enumerate(bullet_lines, start=1)
        ]

        date_match = DATE_RANGE_RE.search(" ".join(block))
        start_date = None
        end_date = None
        if date_match:
            date_text = date_match.group(0)
            parts = re.split(r"-|to|–|—", date_text)
            if parts:
                start_date = _parse_date_from_text(parts[0])
            if len(parts) > 1:
                end_date = _parse_date_from_text(parts[1])

        experiences.append(
            WorkExperience(
                experience_id=f"experience_{index}",
                company_name=company,
                job_title=title,
                start_date=start_date,
                end_date=end_date,
                is_current=bool(end_date and end_date.raw.lower() in {"present", "current", "now"}),
                bullets=bullets,
                summary=bullet_lines[0].lstrip("-• ") if bullet_lines else None,
                skills=[],
            )
        )

    return experiences


def extract_cv(pdf_path: str) -> Dict[str, Any]:
    """
    Extract a CV PDF into the normalized CandidateMasterCV schema.

    Args:
        pdf_path: Absolute or relative path to the CV PDF file.

    Returns:
        A JSON-serializable dict following CandidateMasterCV on success.
        If extraction fails, returns a dict with an "error" field.
    """
    try:
        resolved_path = Path(pdf_path).expanduser().resolve()
        raw_text, num_pages = _extract_pdf_text(resolved_path)
        sections = _split_sections(raw_text)

        header_lines = sections.get("header", [])
        contact = _extract_contact(header_lines, raw_text)
        headline = header_lines[1] if len(header_lines) > 1 else None
        professional_summary = " ".join(sections.get("professional_summary", [])) or None

        skills = _parse_skills(sections.get("skills", []))
        education = _parse_education(sections.get("education", []))
        work_experience = _parse_work_experience(sections.get("work_experience", []))

        certifications = _parse_certifications(sections.get("certifications", []))
        languages = _parse_languages(sections.get("languages", []))

        custom_sections: List[CustomSection] = []
        for section_key, title in [("projects", "Projects")]:
            section = _parse_simple_custom_section(section_key, title, sections.get(section_key, []))
            if section:
                custom_sections.append(section)

        warnings: List[str] = []
        if not skills:
            warnings.append("No skills section was confidently parsed.")
        if not work_experience:
            warnings.append("No work experience section was confidently parsed.")
        if not education:
            warnings.append("No education section was confidently parsed.")

        candidate = CandidateMasterCV(
            metadata=ExtractionMetadata(
                source_type=SourceType.PDF,
                source_name=resolved_path.name,
                source_uri=str(resolved_path),
                extractor_name="pdfplumber_cv_extractor",
                extractor_version="1.0",
                overall_confidence=0.65,
                warnings=warnings,
            ),
            contact=contact,
            headline=headline,
            professional_summary=professional_summary,
            skills=skills,
            work_experience=work_experience,
            education=education,
            certifications=certifications,
            languages=languages,
            custom_sections=custom_sections,
            raw_text=raw_text,
        )

        result = candidate.model_dump(mode="json")
        result["metadata"]["warnings"].append(f"Extracted from {num_pages} page(s).")
        return result

    except FileNotFoundError:
        return {
            "error": f"File not found: {pdf_path}",
        }
    except Exception as e:
        return {
            "error": str(e),
        }


# Tool dict — this is what gets passed into ReActAgent(tools=[...])
cv_extractor_tool = {
    "name": "extract_cv",
    "description": (
        "Extracts a CV PDF file into the CandidateMasterCV JSON schema. "
        "Input: the file path to the PDF. "
        "Output: normalized CV JSON."
    ),
    "function": extract_cv,
}