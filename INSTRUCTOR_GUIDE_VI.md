# Hướng dẫn dành cho Giảng viên: Bài thực hành 3 - Từ Chatbot đến Agentic ReAct

Hướng dẫn này được thiết kế để giảng viên dẫn dắt một buổi thực hành chuyên sâu kéo dài 240 phút (4 giờ). Mục tiêu là đưa sinh viên từ việc "viết code chạy được" sang "kỹ thuật hệ thống có khả năng suy luận và tiến hóa."

---

## 🎯 Các Mục tiêu Học tập Cốt lõi
1.  **Cơ chế ReAct**: Hiểu được chu trình *Suy nghĩ (Thought) -> Hành động (Action) -> Quan sát (Observation)*.
2.  **Đo lường Hệ thống Sản xuất (Industry Observability)**: Học cách gỡ lỗi (debug) một "bộ não" LLM bằng cách sử dụng nhật ký (logs) JSON có cấu trúc.
3.  **Tối ưu Lặp lại (Iterative Refinement)**: Cải thiện hiệu suất bằng cách chẩn đoán nguyên nhân thất bại từ log, thay vì chỉ đoán mò qua việc đổi cấu trúc lệnh (prompt).

---

## ⏱️ Dòng thời gian & Tiến trình

### 01. Điểm Khởi đầu: Tại sao lại cần Agent? (15 phút)
- **Demo**: Trình diễn cho thấy một chatbot đơn giản gặp thất bại khi xử lý một yêu cầu đa bước (ví dụ: "Tìm mức giá rẻ nhất và tính tổng chi phí với 10% thuế").
- **Nhận thức Chính**: Chatbots giỏi giao tiếp/trò chuyện; Agents lại tối ưu cho việc *hành động*.

### 02. Giai đoạn 1: Thiết kế Công cụ (30 phút)
- **Hoạt động**: Sinh viên tự định nghĩa các công cụ trong thư mục `src/tools/`.
- **Trọng tâm Giảng dạy**: Nhấn mạnh tầm quan trọng của việc **Mô tả Công cụ (Tool Descriptions)**. LLM chỉ hiểu được công cụ thông qua đoạn mô tả dạng văn bản của nó.
- **Ví dụ**: So sánh một mô tả mơ hồ ("Tính toán thuế") với một mô tả chi tiết ("Tính thuế VAT 10% chỉ dành riêng cho các Quốc gia EU, nhận vào đối số là số thực").

### 03. Giai đoạn 2: Baseline của Chatbot (30 phút)
- **Hoạt động**: Chạy tập tin `chatbot.py` trên các test case có độ khó phức tạp.
- **Quan sát phân tích**: Nhiều sinh viên sẽ cố gắng "prompt engineer" (viết prompt thật dài và ảo diệu) cho chatbot để ép nó giải quyết bài toán đa bước. Hãy để họ thất bại. Điều này tạo tiền đề vững chắc cho việc tiếp cận ReAct ở bước sau.

### 04. Giai đoạn 3: Khởi tạo Agent v1 (60 phút) - Phần Trọng tâm
- **Hoạt động**: Thực hiện code file `agent/agent.py`.
- **Vai trò Giảng viên**: Hỗ trợ sinh viên về việc phân tích cú pháp Regex/JSON (lỗi phổ biến nhất cản trở tiến trình). Đảm bảo các bạn ấy nắm rõ việc `Observation` (Kết quả quan sát) phải được truyền ngược lại vào prompt cho bước tiếp theo.

### 05. Giai đoạn 4: Phân tích Lỗi (45 phút) - VÔ CÙNG QUAN TRỌNG
- **Hoạt động**: Mở thư mục `logs/`. Tìm các dòng chứa `LOG_EVENT: LLM_METRIC`.
- **Case Giảng dạy**: Tìm một trường hợp agent gọi sai công cụ hoặc "ảo giác" (hallucinate) ra đối số (arguments) sai.
- **Cách Khắc phục**: Hướng dẫn sinh viên cập nhật system prompt (từ v1 -> v2) hoặc cập nhật tài liệu kỹ thuật của công cụ dựa trên những *sự thật* từ log này, chứ không phải phân tích dựa trên trực giác.

### 06. Giai đoạn 5: Đánh giá Nhóm (30 phút)
- **Hoạt động**: Chạy toàn bộ các file test để chấm điểm (test suite). Tạo các bảng cho `GROUP_REPORT`.
- **Thảo luận**: Tại sao Agent lại chiến thắng trong các tình huống yêu cầu nhiều bước? Tại sao Chatbot lại giỏi ở các dạng hỏi đáp (Q&A) đơn giản?

---

## 💡 Mẹo và Vi dụ cho Giảng viên

### 🏦 Kịch bản khuyến nghị: "Trợ lý Thương mại Điện tử Thông minh"
- **Tool 1**: `check_stock(item_name)` -> Trả về số lượng hàng hóa còn lại.
- **Tool 2**: `get_discount(coupon_code)` -> Trả về phần trăm chiết khấu.
- **Tool 3**: `calc_shipping(weight, destination)` -> Trả về cước phí vận chuyển.
- **Test Case**: "Tôi muốn mua 2 chiếc iPhone sử dụng mã 'WINNER' và vận chuyển về Hà Nội. Tổng số tiền cần thanh toán là bao nhiêu?"

### ⚠️ Những Lỗi Cơ bản Cần Theo dõi
1.  **Vòng lặp vô tận (Infinite Loops)**: Agent bị kẹt, lặp đi lặp lại cùng một nội dung "Thought" vô tận.
    - *Cách Khắc phục*: Kiểm tra đoạn code xử lý giới hạn `max_steps` và cách nhận diện "Final Answer".
2.  **Lỗi cú pháp JSON**: LLM trả về các dấu backtick Markdown (vd: ```json ... ```) khiến cho JSON parser có thể bỏ qua và phân tích lỗi.
    - *Cách Khắc phục*: Dạy sinh viên viết phương thức trích xuất dữ liệu thô ổn định hoặc viết thêm chỉ thị vào prompt cho LLM "Chỉ trả về JSON thuần/thô (raw JSON)."
3.  **Quan sát rỗng (Empty Observations)**: Một tool trả về kết quả "Không có dữ liệu". 
    - *Cách Khắc phục*: Agent phản ứng thế nào khi gặp trục trặc? Nó có thử công cụ khác hay trực tiếp dừng lại ngay?

---

## 📈 Tiêu chí Thành công dành cho Giảng viên
Buổi thực hành của bạn đạt hiệu quả nếu:
- Sinh viên có thể trình chiếu một **Failed Trace** (Log ghi lại thất bại) và giải thích *tại sao* nó lại sai.
- Sinh viên có thể trình diễn cách **Chuyển đổi Provider** (từ OpenAI -> Gemini) và so sánh độ trễ (latency).
- Mỗi sinh viên đều có một **Báo cáo Cá nhân** phản ánh các đóng góp kỹ thuật của chính bản thân mình.

---

*“Trong thế giới AI, log (nhật ký) là chân lý. Hãy dạy học viên cách đọc log hệ thống.”*
