import os
import pdfplumber
import instructor
from openai import OpenAI
from src.schemas.cv_tailoring import *
from dotenv import load_dotenv
load_dotenv()

# Khởi tạo Instructor client
client = instructor.from_openai(OpenAI())

import pdfplumber
import os

def parse_pdf_to_text(pdf_path: str) -> dict:
    """
    Trích xuất văn bản và thông tin bổ trợ để khớp với Schema JobDescription.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file: {pdf_path}")

    full_text = ""
    pages_content = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"
                # Lưu text theo từng trang để sau này điền vào SourceSpan nếu cần
                pages_content.append({"page_number": i + 1, "content": text})
                
    return {
        "raw_text": full_text.strip(),
        "file_name": os.path.basename(pdf_path),
        "page_count": len(pages_content)
    }

def extract_jd_requirements(pdf_path: str) -> JobDescription:
    # 1. Lấy dữ liệu thô từ pdfplumber
    data = parse_pdf_to_text(pdf_path)
    
    # 2. Gọi Instructor
    # Chúng ta có thể cung cấp một phần metadata trước để LLM không phải đoán
    structured_data = client.chat.completions.create(
        model="gpt-4o",
        response_model=JobDescription,
        messages=[
            {
                "role": "system", 
                "content": "Extract JD details. Format dates as ISO strings. Ensure every requirement has an evidence quote."
            },
            {"role": "user", "content": data["raw_text"]}
        ],
        max_retries=3
    )

    # 3. Ghi đè metadata thực tế (Tùy chọn)
    structured_data.metadata.source_name = data["file_name"]
    structured_data.metadata.source_type = SourceType.PDF
    
    return structured_data
