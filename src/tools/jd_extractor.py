import os
import pdfplumber
import instructor
from openai import OpenAI
from src.schemas.jd_analysis import JDExtraction
from dotenv import load_dotenv
load_dotenv()

# Khởi tạo Instructor client
client = instructor.from_openai(OpenAI())

def parse_pdf_to_text(pdf_path: str) -> str:
    """
    Trích xuất văn bản thô từ file PDF JD bằng pdfplumber.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file PDF tại: {pdf_path}")
    
    text_content = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
    
    if not text_content.strip():
        raise ValueError("File PDF trống hoặc không thể trích xuất văn bản (có thể là ảnh quét).")
    
    return text_content

def extract_jd_requirements(pdf_path: str) -> JDExtraction:
    """
    Tool chính: 
    1. Đọc PDF -> Text
    2. Dùng Instructor + LLM -> Structured JSON (JDExtraction)
    """
    # Bước 1: Lấy văn bản từ PDF
    raw_text = parse_pdf_to_text(pdf_path)
    
    # Bước 2: Ép kiểu dữ liệu qua Instructor
    structured_data = client.chat.completions.create(
        model="gpt-4o",
        response_model=JDExtraction,
        messages=[
            {
                "role": "system", 
                "content": "You are an expert Technical Recruiter. Extract skills, levels, and requirements from the JD provided."
            },
            {"role": "user", "content": raw_text}
        ],
        max_retries=3
    )
    
    return structured_data
