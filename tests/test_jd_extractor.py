import os
import sys
from dotenv import load_dotenv

# Thêm path để nhận diện module src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.jd_extractor import extract_jd_requirements

load_dotenv()

def run_test():
    # Đường dẫn file PDF test của bạn
    pdf_path = "data/jds/jd_recruitment_officer_final.pdf" 
    
    if not os.path.exists(pdf_path):
        print(f"❌ Lỗi: Không tìm thấy file tại {pdf_path}")
        return

    print(f"🚀 Đang bắt đầu test với Schema mới...")

    try:
        # Gọi tool trích xuất
        result = extract_jd_requirements(pdf_path)

        print("\n✅ TRÍCH XUẤT THÀNH CÔNG!")
        print("=" * 50)
        
        # 1. Kiểm tra thông tin chung (Lưu ý: dùng .title thay vì .job_title)
        print(f"🔍 Thông tin chung:")
        print(f" - Vị trí: {result.title}") # Schema mới dùng 'title'
        print(f" - Công ty: {result.company_name}")
        print(f" - Hình thức: {result.work_arrangement}") # Trả về Enum (Remote/Hybrid...)
        
        # 2. Kiểm tra Requirements (Kỹ năng)
        print(f"\n🛠️ Danh sách Yêu cầu (Requirements):")
        for req in result.requirements[:5]: # Lấy 5 cái đầu tiên
            # req.category sẽ trả về Enum (hard_skill, soft_skill...)
            # req.priority sẽ trả về Enum (must, should...)
            print(f" - [{req.category.upper()}] {req.text}")
            print(f"   + Độ ưu tiên: {req.priority}")
            if req.min_years_experience:
                print(f"   + Kinh nghiệm: {req.min_years_experience} năm")
            
            # Kiểm tra Evidence (Bằng chứng trích dẫn)
            if req.evidence:
                print(f"   + Bằng chứng: \"{req.evidence[0].quote}\"")

        # 3. Kiểm tra Responsibilities (Trách nhiệm)
        print(f"\n📝 Trách nhiệm chính:")
        for resp in result.responsibilities[:3]:
            print(f" - {resp.text}")

        # 4. Xuất toàn bộ JSON ra file để kiểm tra kỹ hơn
        with open("test_output.json", "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=4))
        print("\n💾 Đã lưu kết quả chi tiết vào file 'test_output.json'")

    except Exception as e:
        print(f"❌ Quá trình test thất bại với lỗi:")
        import traceback
        traceback.print_exc() # In chi tiết lỗi để dễ debug

if __name__ == "__main__":
    run_test()