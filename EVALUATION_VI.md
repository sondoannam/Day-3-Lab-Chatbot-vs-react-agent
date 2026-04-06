# Số liệu đánh giá Bài thực hành 3: Tư duy Agentic (Agentic reasoning)

Trong bài thực hành này, chúng ta không chỉ hỏi "Nó có hoạt động không?". Chúng ta phải tự hỏi rằng **"Nó hoạt động hiệu quả đến mức nào?"**.

## Các Số liệu Công nghiệp Trọng tâm

### 1. Tính hiệu quả Token (Số lượng Token)
- **Prompt so với Completion**: Prompt hệ thống của bạn có dài dòng quá mức không? Liệu Agent có đang sinh ra những nội dung "tán gẫu" không cần thiết trước khi gọi công cụ hay không?
- **Phân tích chi phí**: Số token ít = Chi phí thấp = Lợi tức đầu tư (ROI) cao hơn.

### 2. Độ trễ (Thời gian phản hồi)
- **Thời gian Token Đầu tiên (TTFT - Time-to-First-Token)**: LLM bắt đầu phản hồi nhanh đến mức nào?
- **Tổng thời gian**: Đối với agent ReAct, thời gian này bao gồm tất cả các vòng lặp + thời gian thực thi của các công cụ.
- **Mục tiêu**: Trong "môi trường thực tế" (production), người dùng mong đợi phản hồi trong khoảng 200ms-2s.

### 3. Số vòng lặp (Số bước)
- **Suy luận Đa bước**: Agent cần sử dụng bao nhiêu chu kỳ `Suy nghĩ->Hành động` (Thought->Action) để hoàn thành nhiệm vụ?
- **Chất lượng Kết thúc**: Agent có nhận biết chính xác khi nào nên gọi "Câu trả lời cuối cùng" không, hay nó bị kẹt trong "vòng lặp vô tận"?

### 4. Phân tích Lỗi (Mã lỗi)
- **Lỗi Phân tích JSON**: LLM đã xuất `Action` bằng một định dạng mà code của bạn không thể phân tích cú pháp (parse).
- **Lỗi Ảo giác**: LLM ảo tưởng ra một công cụ không tồn tại.
- **Quá thời gian (Timeout)**: Agent đã vượt quá số bước tối đa (`max_steps`).

## Cách sử dụng Logs
Tất cả các số liệu này được tự động ghi lại trong thư mục `logs/`. Sử dụng một kịch bản (script) để phân tích các tệp JSON này và tính toán **Độ tin cậy Tổng hợp** (Aggregate Reliability) giữa phiên bản 1 và phiên bản 2 của agent.
