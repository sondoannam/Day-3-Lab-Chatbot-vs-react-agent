# Báo cáo nhóm: Bài thực hành 3 - Hệ thống Agent cấp độ sản xuất

- **Tên nhóm**: [Tên]
- **Các thành viên**: [Thành viên 1, Thành viên 2, ...]
- **Ngày triển khai**: [NĂM-THÁNG-NGÀY]

---

## 1. Tóm tắt điều hành

*Đánh giá tổng quan về mục tiêu của agent và tỷ lệ thành công so với hệ thống chatbot cơ bản.*

- **Tỷ lệ thành công**: [ví dụ: 85% trên 20 trường hợp kiểm thử]
- **Kết quả chính**: [ví dụ: "Agent của chúng tôi giải quyết được nhiều hơn 40% số truy vấn đa bước so với chatbot cơ bản bằng cách sử dụng đúng công cụ Tìm kiếm."]

---

## 2. Kiến trúc hệ thống & Công cụ

### 2.1 Triển khai vòng lặp ReAct
*Sơ đồ hoặc mô tả về vòng lặp Suy nghĩ - Hành động - Quan sát (Thought-Action-Observation).*

### 2.2 Định nghĩa công cụ (Danh sách)
| Tên công cụ | Định dạng đầu vào | Trường hợp sử dụng |
| :--- | :--- | :--- |
| `calc_tax` | `json` | Tính thuế VAT dựa trên mã quốc gia. |
| `search_api` | `string` | Truy xuất thông tin theo thời gian thực từ Google Tìm kiếm. |

### 2.3 Các nhà cung cấp LLM được sử dụng
- **Chính**: [ví dụ: GPT-4o]
- **Phụ (Dự phòng)**: [ví dụ: Gemini 1.5 Flash]

---

## 3. Khởi trắc học & Bảng điều khiển hiệu suất

*Phân tích các chỉ số chuẩn ngành được thu thập trong lần chạy kiểm thử cuối cùng.*

- **Độ trễ trung bình (P50)**: [ví dụ: 1200ms]
- **Độ trễ tối đa (P99)**: [ví dụ: 4500ms]
- **Số token trung bình mỗi tác vụ**: [ví dụ: 350 token]
- **Tổng chi phí của bộ kiểm thử**: [ví dụ: $0.05]

---

## 4. Phân tích nguyên nhân gốc rễ (RCA) - Lỗi

*Nghiên cứu chuyên sâu về lý do tại sao agent thất bại.*

### Nghiên cứu tình huống: [ví dụ: Ảo giác đối số]
- **Đầu vào**: "Thuế cho 500 ở Việt Nam là bao nhiêu?"
- **Quan sát**: Agent gọi `calc_tax(amount=500, region="Asia")` trong khi công cụ chỉ chấp nhận mã quốc gia gồm 2 chữ cái.
- **Nguyên nhân gốc rễ**: System prompt thiếu đủ các ví dụ `Few-Shot` (few-shot prompting) về định dạng đối số nghiêm ngặt của công cụ.

---

## 5. Nghiên cứu loại bỏ (Ablation Studies) & Thử nghiệm

### Thử nghiệm 1: Prompt v1 so với Prompt v2
- **Điểm khác biệt**: [ví dụ: Thêm "Luôn kiểm tra lại các đối số của công cụ trước khi gọi".]
- **Kết quả**: Giảm các lỗi gọi công cụ không hợp lệ đi [ví dụ: 30%].

### Thử nghiệm 2 (Thưởng): Chatbot so với Agent
| Trường hợp | Kết quả Chatbot | Kết quả Agent | Đánh giá |
| :--- | :--- | :--- | :--- |
| Câu hỏi đơn giản | Đúng | Đúng | Hòa |
| Đa bước | Ảo giác | Đúng | **Agent** |

---

## 6. Đánh giá mức độ sẵn sàng cho sản xuất

*Những cân nhắc khi đưa hệ thống này ra môi trường thực tế.*

- **Bảo mật**: [ví dụ: Làm sạch đầu vào cho các đối số công cụ.]
- **Kiểm soát rào chắn (Guardrails)**: [ví dụ: Tối đa 5 vòng lặp để ngăn ngừa việc tiêu tốn vô hạn chi phí thanh toán.]
- **Mở rộng**: [ví dụ: Chuyển đổi sang LangGraph cho việc phân nhánh phức tạp hơn.]

---

> [!NOTE]
> Nộp báo cáo này bằng cách đổi tên thành `GROUP_REPORT_[TÊN_NHÓM].md` và đặt vào thư mục này.
