"""
jd_tool.py — Tool dict wrapper cho jd_extractor.extract_jd_requirements.
Không sửa jd_extractor.py, chỉ wrap lại thành format agent cần.

Agent gọi: Action: extract_jd(data/jd.pdf)
           Action: extract_jd(<raw jd text>)
"""
import tempfile
import os
from src.telemetry.logger import logger


def extract_jd(args: str) -> str:
    """
    Wrapper: nhận PDF path hoặc raw JD text, trả summary string cho agent.
    Kết quả JDExtraction được lưu vào session.jd_data.
    """
    from src.tools._session import session
    from src.tools.jd_extractor import extract_jd_requirements

    args = args.strip()

    # Nếu là file path tồn tại → gọi thẳng
    if os.path.exists(args):
        pdf_path = args
    else:
        # Raw text → ghi ra file PDF tạm để jd_extractor đọc được
        # (dùng pdfplumber nên cần file thật — dùng .txt là đủ vì parse_pdf_to_text
        #  chỉ đọc text layer; ta giả PDF bằng cách fake → thay vào đó inject raw_text
        #  trực tiếp qua client call thay vì extract_jd_requirements)
        from src.schemas.jd_analysis import JDExtraction
        from src.tools.jd_extractor import client  # instructor client

        logger.log_event("TOOL_CALL", {"tool": "extract_jd", "source": "raw_text"})

        structured = client.chat.completions.create(
            model="gpt-4o",
            response_model=JDExtraction,
            messages=[
                {"role": "system", "content": "You are an expert Technical Recruiter. Extract skills, levels, and requirements from the JD provided."},
                {"role": "user", "content": args},
            ],
            max_retries=3,
        )
        session.jd_data = structured
        return _summarize(structured)

    logger.log_event("TOOL_CALL", {"tool": "extract_jd", "source": pdf_path})
    structured = extract_jd_requirements(pdf_path)
    session.jd_data = structured
    return _summarize(structured)


def _summarize(jd) -> str:
    """Trả về summary ngắn để LLM đọc trong Observation."""
    hard = [s.skill_name for s in jd.technical_skills]
    soft = [s.skill_name for s in jd.soft_skills]
    logger.log_event("TOOL_RESULT", {
        "tool": "extract_jd",
        "job_title": jd.job_title,
        "hard_skills": hard,
    })
    return (
        f"Job: {jd.job_title}" +
        (f" @ {jd.company_name}" if jd.company_name else "") + "\n"
        f"Technical skills: {', '.join(hard)}\n"
        f"Soft skills: {', '.join(soft)}\n"
        f"Domain: {', '.join(jd.domain_knowledge) if jd.domain_knowledge else 'N/A'}\n"
        f"Summary: {jd.summary_requirements}"
    )


jd_tool = {
    "name": "extract_jd",
    "description": (
        "Extracts structured requirements from a Job Description. "
        "Input: a PDF file path OR raw JD text. "
        "Output: job title, required technical skills, soft skills, and summary."
    ),
    "function": extract_jd,
}
