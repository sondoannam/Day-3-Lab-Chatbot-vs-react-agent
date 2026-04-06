from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class SourceType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    URL = "url"
    TEXT = "text"


class RequirementCategory(str, Enum):
    HARD_SKILL = "hard_skill"
    SOFT_SKILL = "soft_skill"
    TOOL = "tool"
    DOMAIN = "domain"
    RESPONSIBILITY = "responsibility"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    LANGUAGE = "language"
    EXPERIENCE = "experience"
    KEYWORD = "keyword"
    OTHER = "other"


class RequirementPriority(str, Enum):
    MUST = "must"
    SHOULD = "should"
    NICE_TO_HAVE = "nice_to_have"


class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    TOOL = "tool"
    FRAMEWORK = "framework"
    CLOUD = "cloud"
    DOMAIN = "domain"
    SOFT = "soft"
    LANGUAGE = "language"
    OTHER = "other"


class ProficiencyLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    FREELANCE = "freelance"
    UNKNOWN = "unknown"


class WorkArrangement(str, Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    UNKNOWN = "unknown"


class SeniorityLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


class MatchType(str, Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    MANUAL = "manual"
    NO_MATCH = "no_match"


class SourceSpan(SchemaModel):
    page: Optional[int] = Field(default=None, ge=1)
    start_char: Optional[int] = Field(default=None, ge=0)
    end_char: Optional[int] = Field(default=None, ge=0)
    bbox: Optional[List[float]] = Field(default=None, min_length=4, max_length=4)


class EvidenceQuote(SchemaModel):
    quote: str = Field(..., min_length=1)
    section_id: Optional[str] = None
    span: Optional[SourceSpan] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ExtractionMetadata(SchemaModel):
    schema_version: str = "1.0"
    source_type: SourceType
    source_name: Optional[str] = None
    source_uri: Optional[str] = None
    extractor_name: str
    extractor_version: Optional[str] = None
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str = "en"
    overall_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)


class JobRequirement(SchemaModel):
    requirement_id: str
    category: RequirementCategory
    text: str
    normalized_value: Optional[str] = None
    priority: RequirementPriority = RequirementPriority.MUST
    required: bool = True
    min_years_experience: Optional[float] = Field(default=None, ge=0.0)
    aliases: List[str] = Field(default_factory=list)
    evidence: List[EvidenceQuote] = Field(default_factory=list)


class JobResponsibility(SchemaModel):
    responsibility_id: str
    text: str
    priority: RequirementPriority = RequirementPriority.SHOULD
    evidence: List[EvidenceQuote] = Field(default_factory=list)


class JobDescription(SchemaModel):
    metadata: ExtractionMetadata
    title: str
    company_name: Optional[str] = None
    company_industry: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    work_arrangement: WorkArrangement = WorkArrangement.UNKNOWN
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    seniority: SeniorityLevel = SeniorityLevel.UNKNOWN
    summary: Optional[str] = None
    responsibilities: List[JobResponsibility] = Field(default_factory=list)
    requirements: List[JobRequirement] = Field(default_factory=list)
    target_keywords: List[str] = Field(default_factory=list)
    compensation_summary: Optional[str] = None
    application_url: Optional[HttpUrl] = None
    raw_text: Optional[str] = None


class DateValue(SchemaModel):
    raw: str
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    month: Optional[int] = Field(default=None, ge=1, le=12)


class ContactInfo(SchemaModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None


class SkillEntry(SchemaModel):
    skill_id: str
    name: str
    normalized_name: Optional[str] = None
    category: SkillCategory = SkillCategory.OTHER
    proficiency: Optional[ProficiencyLevel] = None
    years_experience: Optional[float] = Field(default=None, ge=0.0)
    last_used_year: Optional[int] = Field(default=None, ge=1900, le=2100)
    evidence: List[EvidenceQuote] = Field(default_factory=list)


class CVBullet(SchemaModel):
    bullet_id: str
    text: str
    technologies: List[str] = Field(default_factory=list)
    competencies: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    evidence: List[EvidenceQuote] = Field(default_factory=list)


class WorkExperience(SchemaModel):
    experience_id: str
    company_name: str
    job_title: str
    location: Optional[str] = None
    start_date: Optional[DateValue] = None
    end_date: Optional[DateValue] = None
    is_current: bool = False
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    summary: Optional[str] = None
    bullets: List[CVBullet] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class EducationRecord(SchemaModel):
    education_id: str
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[DateValue] = None
    end_date: Optional[DateValue] = None
    gpa: Optional[str] = None
    honors: List[str] = Field(default_factory=list)
    evidence: List[EvidenceQuote] = Field(default_factory=list)


class CertificationRecord(SchemaModel):
    certification_id: str
    name: str
    issuer: Optional[str] = None
    issued_date: Optional[DateValue] = None
    expires_date: Optional[DateValue] = None
    credential_id: Optional[str] = None
    evidence: List[EvidenceQuote] = Field(default_factory=list)


class ProjectRecord(SchemaModel):
    project_id: str
    name: str
    role: Optional[str] = None
    summary: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    bullets: List[CVBullet] = Field(default_factory=list)
    start_date: Optional[DateValue] = None
    end_date: Optional[DateValue] = None


class LanguageEntry(SchemaModel):
    language: str
    proficiency: Optional[ProficiencyLevel] = None


class CustomSection(SchemaModel):
    section_id: str
    title: str
    content: List[str] = Field(default_factory=list)


class CandidateMasterCV(SchemaModel):
    metadata: ExtractionMetadata
    contact: ContactInfo
    headline: Optional[str] = None
    professional_summary: Optional[str] = None
    skills: List[SkillEntry] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[EducationRecord] = Field(default_factory=list)
    certifications: List[CertificationRecord] = Field(default_factory=list)
    projects: List[ProjectRecord] = Field(default_factory=list)
    languages: List[LanguageEntry] = Field(default_factory=list)
    custom_sections: List[CustomSection] = Field(default_factory=list)
    raw_text: Optional[str] = None


class RequirementMatch(SchemaModel):
    requirement_id: str
    requirement_text: str
    matched: bool
    match_type: MatchType = MatchType.NO_MATCH
    score: float = Field(..., ge=0.0, le=100.0)
    matched_skills: List[str] = Field(default_factory=list)
    cv_evidence: List[EvidenceQuote] = Field(default_factory=list)
    gap_reason: Optional[str] = None


class MatchReport(SchemaModel):
    job_title: str
    candidate_name: str
    keyword_score: float = Field(..., ge=0.0, le=100.0)
    semantic_score: float = Field(..., ge=0.0, le=100.0)
    completeness_score: float = Field(..., ge=0.0, le=100.0)
    overall_score: float = Field(..., ge=0.0, le=100.0)
    matched_requirements: List[RequirementMatch] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class TailoredTextBlock(SchemaModel):
    block_id: str
    text: str
    source_evidence: List[EvidenceQuote] = Field(default_factory=list)
    targeted_requirement_ids: List[str] = Field(default_factory=list)


class TailoredSection(SchemaModel):
    section_id: str
    title: str
    blocks: List[TailoredTextBlock] = Field(default_factory=list)


class TailoredCV(SchemaModel):
    metadata: ExtractionMetadata
    target_job_title: str
    target_company_name: Optional[str] = None
    contact: ContactInfo
    sections: List[TailoredSection] = Field(default_factory=list)
    match_report: Optional[MatchReport] = None