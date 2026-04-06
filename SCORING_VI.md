# Tiêu chí chấm điểm bài thực hành: Chatbot vs ReAct Agent

Tài liệu này trình bày các tiêu chí chấm điểm cho Bài thực hành 3. Mục tiêu là thể hiện sự hiểu biết sâu sắc về tư duy agent (agentic reasoning), giám sát hệ thống (monitoring) mạnh mẽ và kỹ năng cải thiện liên tục.

## 👥 1. Điểm Nhóm (45 Điểm Cơ bản + 15 Điểm Thưởng = Tối đa 60)

Điểm số này phản ánh kết quả làm việc chung của nhóm. Tổng điểm nhóm (Cơ bản + Thưởng) được giới hạn ở **60 điểm**.

| Hạng mục | Mô tả | Điểm |
| :--- | :--- | :--- |
| **Chatbot Baseline** | Triển khai được một chatbot baseline sạch sẽ, tối giản. | 2 |
| **Agent v1 (Hoạt động)** | Triển khai thành công vòng lặp ReAct (2+ công cụ). | 7 |
| **Agent v2 (Cải tiến)** | Logic agent được cải thiện để khắc phục các lỗi phát hiện ở v1. | 7 |
| **Phát triển thiết kế Tool** | Tài liệu rõ ràng về quá trình tiến hóa thông số kỹ thuật của công cụ. | 4 |
| **Chất lượng Trace** | Ghi nhận chi tiết cả dấu vết hành động (traces) thành công và thất bại. | 9 |
| **Đánh giá & Phân tích** | So sánh dựa trên dữ liệu (Chatbot vs Agent). | 7 |
| **Lưu đồ & Kiến thức rút ra** | Biểu đồ logic trực quan và các điểm học hỏi của nhóm. | 5 |
| **Chất lượng mã nguồn** | Mã nguồn sạch, dễ modul hóa và tích hợp telemetry. | 4 |

> [!TIP]
> **Nộp bài theo Nhóm**: Các nhóm phải sử dụng tệp [TEMPLATE_GROUP_REPORT.md] nằm trong thư mục `report/group_report/` để nộp bài cuối cùng.

### 🎁 Điểm Thưởng Nhóm (Tối đa +15)

Có thể kiếm được điểm thưởng để đạt tới **giới hạn 60 điểm** hoặc bù đắp cho các điểm cơ bản còn thiếu:

| Hạng mục Thưởng | Mô tả | Điểm |
| :--- | :--- | :--- |
| **Giám sát hệ thống Bổ sung** | Thêm các số liệu đo lường công nghiệp phức tạp (Chi phí, tỷ lệ Token, v.v.). | +3 |
| **Công cụ Bổ sung** | Triển khai các công cụ nâng cao (Lướt web, Tìm kiếm, v.v.). | +2 |
| **Xử lý Lỗi** | Logic thử lại tinh vi hơn hoặc thiết lập các rào cản bảo vệ (guardrails). | +3 |
| **Demo Hệ thống Trực tiếp** | Trình diễn trực tiếp và thành công với giảng viên. | +5 |
| **Thí nghiệm Cắt giảm (Ablation)** | So sánh giữa các biến thể khác nhau của prompt/tool. | +2 |

---

## 👤 2. Điểm Cá nhân (40 Điểm)

Để đạt trọn vẹn 40 điểm, mỗi sinh viên phải nộp báo cáo cá nhân `individual_report.md` tại thư mục `report/individual_reports/`.

| Thành phần | Tiêu chí / Yêu cầu | Điểm |
| :--- | :--- | :--- |
| **I. Đóng góp Kỹ thuật** | Liệt kê các module code, tool hoặc test suite cụ thể đã thực hiện. Bằng chứng về chất lượng và độ rõ ràng của mã nguồn. | 15 |
| **II. Nghiên cứu Tình huống Debug** | Phân tích chi tiết một trường hợp lỗi (ảo giác, lặp vô hạn, lỗi trình phân tích cú pháp) và cách khắc phục sử dụng Telemetry/Log. | 10 |
| **III. Nhận định Cá nhân** | Đánh giá và suy ngẫm sâu sắc về những điểm khác biệt cơ bản giữa LLM Chatbot truyền thống và Agent ReAct thông qua kết quả của bài thực hành. | 10 |
| **IV. Cải tiến Tương lai** | Đề xuất để mở rộng hệ thống agent này đạt đến quy mô RAG hoặc hệ thống nhiều agent cấp độ sản xuất. | 5 |

---

## 🏎️ Tính Tổng Điểm

Điểm cuối cùng cho mỗi sinh viên được tính như sau:
**Tổng = MIN(60, Điểm Nhóm Cơ bản + Điểm Thưởng Nhóm) + Điểm Cá nhân (tối đa 40) = Tối đa 100 Điểm**

> [!IMPORTANT]
> **Sự Minh bạch trong Chấm điểm**: Có thể tìm thấy mẫu chi tiết cho báo cáo cá nhân tại thư mục `report/individual_reports/TEMPLATE_INDIVIDUAL_REPORT.md`.

> [!IMPORTANT]
> **Trách nhiệm Thành viên**: Trọng số cá nhân 40% được thiết kế nhằm đảm bảo mỗi cá nhân đều có đóng góp đáng kể và nắm rõ cơ chế hoạt động của vòng lặp agentic.

---

> [!IMPORTANT]
> **"Thất bại sớm, Học hỏi nhanh"**: Chúng tôi đánh giá chất lượng **Phân tích Lỗi** ngang hàng với mã nguồn thực tế ở cuối kỳ. Một chuỗi dữ liệu (trace) báo cáo lỗi được ghi chú kỹ càng giá trị hơn cả một hệ thống "hoàn hảo" nhưng không hề có sự diễn giải cụ thể.
