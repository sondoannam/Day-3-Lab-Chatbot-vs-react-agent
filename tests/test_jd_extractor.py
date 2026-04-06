import os
import json
import sys

# Thêm thư mục gốc vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.jd_extractor import extract_jd_requirements
# ... các code còn lại
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
from src.tools.jd_extractor import extract_jd_requirements

# 1. Load các biến môi trường (API Key)
load_dotenv()

def run_test():
    # 2. Cấu hình đường dẫn file PDF test
    # Bạn hãy thay bằng đường dẫn file thực tế trong máy bạn
    pdf_path = "data/jds/jd_recruitment_officer_final.pdf" 
    
    if not os.path.exists(pdf_path):
        print(f"❌ Lỗi: Không tìm thấy file tại {pdf_path}")
        print("Vui lòng kiểm tra lại đường dẫn hoặc để file PDF vào đúng thư mục.")
        return

    print(f"🚀 Đang bắt đầu test trích xuất từ: {pdf_path}")
    print("-" * 50)

    try:
        # 3. Gọi tool trích xuất
        # Hàm này bên trong đã dùng pdfplumber và Instructor
        result = extract_jd_requirements(pdf_path)

        # 4. Hiển thị kết quả trích xuất dưới dạng JSON đẹp
        print("\n✅ TRÍCH XUẤT THÀNH CÔNG!")
        print("=" * 50)
        
        # model_dump_json() là hàm của Pydantic để chuyển object sang string JSON
        print(result.model_dump_json(indent=4))
        
        print("=" * 50)
        
        # 5. Kiểm tra thử logic truy cập dữ liệu
        print(f"\n🔍 Kiểm tra nhanh:")
        print(f" - Vị trí: {result.job_title}")
        print(f" - Số lượng kỹ năng kỹ thuật: {len(result.technical_skills)}")
        
        if result.technical_skills:
            top_skill = result.technical_skills[0]
            print(f" - Kỹ năng tiêu biểu: {top_skill.skill_name} (Level: {top_skill.level})")

    except Exception as e:
        print(f"❌ Quá trình test thất bại với lỗi:")
        print(str(e))

if __name__ == "__main__":
    run_test()