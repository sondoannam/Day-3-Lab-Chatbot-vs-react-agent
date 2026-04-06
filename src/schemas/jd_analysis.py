from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class SkillLevel(str, Enum):
    """Định nghĩa các cấp độ kỹ năng tiêu chuẩn để tránh LLM ghi tự do"""
    BEGINNER = "Beginner"           # Cơ bản, mới học
    INTERMEDIATE = "Intermediate"   # Đã làm việc thạo, có kinh nghiệm
    ADVANCED = "Advanced"           # Chuyên gia, có khả năng tối ưu/thiết kế
    EXPERT = "Expert"               # Cực kỳ thành thạo, dẫn dắt đội ngũ
    NOT_SPECIFIED = "Not Specified" # Không đề cập rõ trong JD

class SkillRequirement(BaseModel):
    """Thông tin chi tiết cho từng kỹ năng"""
    skill_name: str = Field(..., description="Tên kỹ năng, ví dụ: Python, AWS, Docker")
    level: SkillLevel = Field(default=SkillLevel.NOT_SPECIFIED, description="Cấp độ yêu cầu")
    years_required: Optional[float] = Field(None, description="Số năm kinh nghiệm tối thiểu yêu cầu cho kỹ năng này")
    is_mandatory: bool = Field(default=True, description="Kỹ năng này là bắt buộc (Must-have) hay điểm cộng (Nice-to-have)")

class JDExtraction(BaseModel):
    """Cấu trúc tổng thể của một JD sau khi trích xuất"""
    job_title: str = Field(..., description="Tên vị trí công việc")
    company_name: Optional[str] = Field(None, description="Tên công ty (nếu có)")
    
    # Phân loại kỹ năng để Agent dễ đối soát với các phần trong CV
    technical_skills: List[SkillRequirement] = Field(
        ..., description="Danh sách các kỹ năng cứng, ngôn ngữ lập trình, framework"
    )
    soft_skills: List[SkillRequirement] = Field(
        ..., description="Các kỹ năng mềm như làm việc nhóm, giao tiếp, tư duy logic"
    )
    
    domain_knowledge: List[str] = Field(
        default_factory=list, 
        description="Kiến thức nghiệp vụ cụ thể, ví dụ: Fintech, E-commerce, Healthcare"
    )
    
    summary_requirements: str = Field(
        ..., description="Tóm tắt ngắn gọn các yêu cầu cốt lõi nhất của JD này"
    )