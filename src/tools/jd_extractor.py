import os
import re
from typing import Callable, List, Tuple

import instructor
import pdfplumber
from openai import OpenAI

from src.schemas.cv_tailoring import JobDescription, SourceType
from src.core.openrouter_provider import OpenRouterProvider

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        return None


load_dotenv()


def _is_configured_key(value: str | None) -> bool:
    if not value:
        return False
    lowered = value.strip().lower()
    return lowered not in {
        "",
        "your_openai_api_key_here",
        "your_openrouter_api_key_here",
    }


def _provider_attempts() -> List[Tuple[str, str, Callable[[], OpenAI]]]:
    attempts: List[Tuple[str, str, Callable[[], OpenAI]]] = []

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if _is_configured_key(openrouter_key):
        attempts.append(
            (
                "openrouter",
                os.getenv("OPENROUTER_JD_MODEL", "qwen/qwen3.6-plus:free"),
                lambda: OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=openrouter_key,
                ),
            )
        )

    openai_key = os.getenv("OPENAI_API_KEY")
    if _is_configured_key(openai_key):
        attempts.append(
            (
                "openai",
                os.getenv("OPENAI_JD_MODEL", "gpt-4o-mini"),
                lambda: OpenAI(api_key=openai_key),
            )
        )

    return attempts


def parse_pdf_to_text(pdf_path: str) -> dict:
    """Extract text and basic file metadata from a JD PDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Khong tim thay file: {pdf_path}")

    full_text = ""
    pages_content = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"
                pages_content.append({"page_number": i + 1, "content": text})

    return {
        "raw_text": full_text.strip(),
        "file_name": os.path.basename(pdf_path),
        "page_count": len(pages_content),
    }


def _extract_with_provider(
    provider_name: str,
    model_name: str,
    client_factory: Callable[[], OpenAI],
    raw_text: str,
) -> JobDescription:
    if provider_name == "openrouter":
        return _extract_with_openrouter(model_name=model_name, raw_text=raw_text)

    client = instructor.from_openai(client_factory())
    return client.chat.completions.create(
        model=model_name,
        response_model=JobDescription,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract the job description into the provided schema. "
                    "Ensure every requirement includes evidence quotes copied from the JD. "
                    "Keep output factual and do not invent missing data."
                ),
            },
            {"role": "user", "content": raw_text},
        ],
        max_retries=3,
    )


def _extract_json_payload(text: str) -> str:
    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        return text[start:end + 1]

    raise ValueError("Model response did not contain a JSON object.")


def _extract_with_openrouter(model_name: str, raw_text: str) -> JobDescription:
    provider = OpenRouterProvider(model_name=model_name)
    schema_json = JobDescription.model_json_schema()
    system_prompt = (
        "Extract the job description into valid JSON only. "
        "Return exactly one JSON object and no markdown. "
        "Use enum values exactly as defined in the schema. "
        "Every requirement and responsibility must include evidence quotes copied verbatim from the JD. "
        f"Schema: {schema_json}"
    )
    result = provider.generate(raw_text, system_prompt=system_prompt)
    payload = _extract_json_payload(result["content"])
    return JobDescription.model_validate_json(payload)


def extract_jd_requirements(pdf_path: str) -> JobDescription:
    data = parse_pdf_to_text(pdf_path)
    attempts = _provider_attempts()
    if not attempts:
        raise RuntimeError(
            "No JD extraction provider is configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
        )

    provider_errors: List[str] = []

    for provider_name, model_name, client_factory in attempts:
        try:
            structured_data = _extract_with_provider(
                provider_name=provider_name,
                model_name=model_name,
                client_factory=client_factory,
                raw_text=data["raw_text"],
            )
            structured_data.metadata.source_name = data["file_name"]
            structured_data.metadata.source_type = SourceType.PDF
            structured_data.metadata.source_uri = os.path.abspath(pdf_path)
            structured_data.metadata.extractor_name = f"{provider_name}_jd_extractor"
            structured_data.metadata.extractor_version = model_name

            if provider_errors:
                structured_data.metadata.warnings.append(
                    "Fallback used after provider failure(s): " + " | ".join(provider_errors)
                )

            return structured_data
        except Exception as error:
            provider_errors.append(f"{provider_name}: {error}")

    raise RuntimeError(
        "All JD extraction providers failed. " + " | ".join(provider_errors)
    )


def extract_jd_text_requirements(raw_text: str) -> JobDescription:
    attempts = _provider_attempts()
    if not attempts:
        raise RuntimeError(
            "No JD extraction provider is configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
        )

    provider_errors: List[str] = []

    for provider_name, model_name, client_factory in attempts:
        try:
            structured_data = _extract_with_provider(
                provider_name=provider_name,
                model_name=model_name,
                client_factory=client_factory,
                raw_text=raw_text,
            )
            structured_data.metadata.source_name = "inline_jd"
            structured_data.metadata.source_type = SourceType.TEXT
            structured_data.metadata.extractor_name = f"{provider_name}_jd_extractor"
            structured_data.metadata.extractor_version = model_name

            if provider_errors:
                structured_data.metadata.warnings.append(
                    "Fallback used after provider failure(s): " + " | ".join(provider_errors)
                )

            return structured_data
        except Exception as error:
            provider_errors.append(f"{provider_name}: {error}")

    raise RuntimeError(
        "All JD extraction providers failed. " + " | ".join(provider_errors)
    )


def _summarize_jd(jd: JobDescription) -> str:
    must_requirements = [req.normalized_value or req.text for req in jd.requirements if req.required][:8]
    nice_to_have = [req.normalized_value or req.text for req in jd.requirements if not req.required][:5]

    lines = [
        f"Job: {jd.title}" + (f" @ {jd.company_name}" if jd.company_name else ""),
        f"Required keywords: {', '.join(must_requirements) if must_requirements else 'N/A'}",
    ]
    if nice_to_have:
        lines.append(f"Nice-to-have: {', '.join(nice_to_have)}")
    if jd.summary:
        lines.append(f"Summary: {jd.summary}")
    return "\n".join(lines)


def extract_jd(args: str) -> str:
    from src.tools._session import session

    value = args.strip()
    if not value:
        return "ERROR: Missing JD input. Provide a file path or raw JD text."

    if os.path.exists(value):
        structured = extract_jd_requirements(value)
    else:
        structured = extract_jd_text_requirements(value)

    session.set_jd_data(structured)
    session.clear_generated_state()
    return _summarize_jd(structured)


jd_extractor_tool = {
    "name": "extract_jd",
    "description": (
        "Extracts structured requirements from a Job Description into the canonical JobDescription schema. "
        "Input: a JD PDF path or raw JD text. "
        "Output: concise summary of title, keywords, and job overview."
    ),
    "function": extract_jd,
}
