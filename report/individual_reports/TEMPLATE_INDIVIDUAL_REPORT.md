# Báo cáo cá nhân: Bài thực hành 3 - Chatbot vs ReAct Agent

- **Họ và tên sinh viên**: [Tên của bạn ở đây]
- **Mã số sinh viên**: [Mã số của bạn ở đây]
- **Ngày tháng**: [Ngày tháng ở đây]

---

## I. Đóng góp kỹ thuật (15 Điểm)

*Mô tả đóng góp cụ thể của bạn vào mã nguồn (ví dụ: triển khai một công cụ cụ thể, sửa lỗi bộ phân tích cú pháp, v.v.).*

- **Các module đã triển khai**: [ví dụ: `src/tools/search_tool.py`]
- **Điểm nổi bật của mã nguồn**: [Sao chép các đoạn mã hoặc liên kết số dòng]
- **Tài liệu**: [Giải thích ngắn gọn cách mã của bạn tương tác với vòng lặp ReAct]

---

## II. Nghiên cứu tình huống gỡ lỗi (10 Điểm)

*Phân tích một sự cố lỗi cụ thể mà bạn gặp phải trong quá trình thực hành bằng hệ thống ghi lỗi (logging system).*

- **Mô tả vấn đề**: [ví dụ: Agent bị kẹt trong vòng lặp vô hạn với `Action: search(None)`]
- **Nguồn log**: [Liên kết hoặc đoạn trích từ `logs/YYYY-MM-DD.log`]
- **Chẩn đoán**: [Tại sao LLM lại làm điều này? Do prompt, mô hình hay định nghĩa công cụ?]
- **Giải pháp**: [Bạn đã sửa nó như thế nào? (ví dụ: cập nhật các ví dụ `Thought` trong system prompt)]

---

## III. Góc nhìn cá nhân: Chatbot vs ReAct (10 Điểm)

*Suy ngẫm về sự khác biệt trong khả năng suy luận.*

1.  **Suy luận**: Khối `Thought` (Suy nghĩ) đã giúp agent như thế nào so với một câu trả lời trực tiếp từ Chatbot?
2.  **Độ tin cậy**: Trong những trường hợp nào Agent thực sự hoạt động *kém hơn* Chatbot?
3.  **Quan sát**: Phản hồi từ môi trường (những quan sát - observations) đã ảnh hưởng đến các bước tiếp theo như thế nào?

---

## IV. Cải tiến trong tương lai (5 Điểm)

*Bạn sẽ mở rộng quy mô hệ thống này như thế nào cho một hệ thống AI agent cấp độ sản xuất?*

- **Khả năng mở rộng**: [ví dụ: Sử dụng hàng đợi bất đồng bộ cho các lệnh gọi công cụ]
- **Tính an toàn**: [ví dụ: Triển khai một LLM 'Giám sát' để kiểm tra các hành động của agent]
- **Hiệu suất**: [ví dụ: Vector DB để truy xuất công cụ trong hệ thống có nhiều công cụ]

---

> [!NOTE]
> Nộp báo cáo này bằng cách đổi tên thành `REPORT_[TÊN_CỦA_BẠN].md` và đặt vào thư mục này.
