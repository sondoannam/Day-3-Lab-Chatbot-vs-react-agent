# Báo cáo cá nhân: Bài thực hành 3 - Chatbot vs ReAct Agent

- **Họ và tên sinh viên**: Vũ Đức Duy
- **Mã số sinh viên**: 2A202600337
- **Ngày tháng**: 2026-04-06

---

## I. Đóng góp kỹ thuật (15 Điểm)

- **Các module đã triển khai**: Trực tiếp phát triển, định tuyến và tối ưu hóa các module mã nguồn Python cho hai công cụ (tools) cốt lõi phục vụ hệ thống CV Tailoring Agentic:
  - **Tool 01 (JD Web Scraper)**: `src/tools/JD_Web_Scraper.py`
  - **Tool 02 (CV/JD Matcher)**: `src/tools/cv_jd_matcher.py`

- **Điểm nổi bật của mã nguồn**:

  - **Thiết kế luồng cào dữ liệu mạnh mẽ (Resilience Scraper)**: Tại `JD_Web_Scraper.py`, tôi đã xây dựng cơ chế trích xuất chính sử dụng đồng bộ Web Unlocker API (`Bright Data Proxy`) kết hợp với **cơ chế kết xuất HTML không đồng bộ chuyên sâu**. Cơ cấu phân tích cốt lõi này tích hợp sẵn bộ lọc thông minh (Pruning Filter), tự động bóc tách và chưng cất các tệp HTML hỗn tạp thành định dạng văn bản cô đọng (Markdown) cực kỳ sạch sẽ, hoàn toàn vắng bỏ mã định tuyến hay quảng cáo rác. Khi gặp lỗi chặn bot từ nền tảng gốc, mã tự kích hoạt luồng xử lý dự phòng (Fallback) qua API cào dữ liệu ngoài (sử dụng `SerpApi` với cấu hình `"engine": "google_jobs"`), đảm bảo tỷ lệ rủi ro bằng 0 và thời gian thực thi (SLA) cực thấp.
  
    *Đoạn mã cấu trúc Fallback:*
    ```python
    # STEP 1: Primary Extraction (Bright Data Web Unlocker + Async HTML Parser)
    raw_html = await self._fetch_with_bright_data(url)
    if raw_html:
        parsed_markdown = await self._parse_with_async_crawler(raw_html, url)
        if parsed_markdown:
            status = "success_primary"

    # STEP 2: Error Handling & SerpApi Fallback - Nếu Primary thất bại
    if status == "failed":
        fallback_result = await self._fetch_with_serp_api(url)
        if fallback_result:
            status = "success_fallback"
    ```

  - **Cơ chế so khớp Đa mô hình (Multi-provider) & Ép kiểu dữ liệu (Schema constraints)**: Tại `cv_jd_matcher.py`, mã nguồn được thiết kế bao gồm chức năng trích xuất dự phòng mạnh mẽ (qua nhiều API như `Gemini`, `OpenRouter`, `OpenAI` tự động hoán đổi khi gặp sự cố). Đặc biệt, tôi tự phát triển module `_extract_json_payload` kết hợp với thư viện `instructor` để cưỡng chế LLM tạo ra dữ liệu cấu trúc cực chuẩn, loại bỏ các thẻ markdown nhiễu nhằm tránh bị sinh lỗi Pydantic Error.
  
    *Đoạn mã chống nhiễu JSON Response:*
    ```python
    def _extract_json_payload(text: str) -> str:
        # Tự động bắt cặp payload JSON trong thẻ ```json ... ``` mở rộng
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fenced_match:
            return fenced_match.group(1)

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and start < end:
            return text[start:end + 1]

        raise ValueError("Model response did not contain a JSON object.")
    ```

- **Tài liệu**: Các script công cụ này biến tư duy của Agent (Thought) thành hành động thực tiễn (Action). Giúp chu trình ReAct của hệ thống nội bộ chạy cực kỳ ổn định, liền mạch do dữ liệu đầu ra được quy hoạch vào cùng một định chuẩn không-gây-bể-cấu-trúc (no structure breakages).

---

## II. Nghiên cứu tình huống gỡ lỗi (10 Điểm)

- **Mô tả vấn đề**: Trong quá trình phát triển Tool 02 (Matching & Grounding Agent), LLM đôi khi tự ý làm tròn số năm kinh nghiệm để khớp với yêu cầu JD, dẫn đến đánh giá sai lệch, hoặc in thẻ định dạng markdown ````json ```` bao bọc kết quả, làm module Pydantic parse bị lỗi.
- **Nguồn log**: Các phiên bản log ghi nhận lỗi "Pydantic Validation Error" do chuỗi JSON không hợp lệ, hoặc False Positive khi báo cáo đánh giá đạt chỉ tiêu đối với ứng viên còn yếu.
- **Chẩn đoán**: Sự cường điệu, thoả hiệp tự nhiên của LLM làm bẻ cong sự thật (mong muốn làm vừa lòng User). Việc bọc markdown là do LLM quen in định dạng Code block theo bản năng.
- **Giải pháp**: Xây dựng hệ cơ chế chặn chéo: viết luật **NEGATIVE CONSTRAINTS** trong file System Prompt cấm LLM làm tròn số, và bổ sung ép buộc ngầm trong lệnh khởi chạy Python (nhằm phủ quyết cả mẫu định dạng ở trong Prompt cũ):
    ```python
    # Ép buộc LLM chỉ tuân theo cấu trúc Python Schema từ Instructor/Pydantic
    sys_prompt = master_prompt + "\n\nQUAN TRỌNG: Bạn BẮT BUỘC bỏ qua ví dụ Schema ở trên và CHỈ XUẤT JSON trả về tương ứng trinh khớp hoàn toàn với FUNCTION STRUCTURE / PYDANTIC SCHEMA được truyền vào theo system definition."
    ```
    Bằng sự kết hợp giữa logic Prompting tĩnh và Ép kiểu động trong Code (`_extract_json_payload`), tool đã ổn định và cắt hẳn sự cố Ảo giác (Hallucination).

---

## III. Góc nhìn cá nhân: Chatbot vs ReAct (10 Điểm)

1.  **Suy luận**: Khối `Thought` giúp ReAct Agent trở nên "biết suy nghĩ trước khi hành động". So với một Chatbot truyền thống sẽ kết luận kết quả lập tức một cách cảm tính, ReAct chia nhỏ JD thành các tiêu chí và biết dựa vào thông báo tìm kiếm của Tools để lần mò chéo từng dòng văn bản kinh nghiệm.
2.  **Độ tin cậy**: Agent dễ dàng hoạt động *kém hơn* Chatbot khi dính phải các yêu cầu văn bản quá mở hoặc giao tiếp hỏi han đời thường, vì chi phí vòng lặp chạy Tool (về thời gian, request token) để kết nối (ví dụ hàm `match_cv_jd`) không cần thiết sẽ đánh vào tốc độ trả lời.
3.  **Quan sát**: Khối `Observation` hoạt động như một lưới lọc thực tại (Reality Check). Nhờ việc xác thực bằng Class `MatchReport` cứng nhắc từ mã nguồn, mô hình buộc phải tìm thấy nội dung "cv_evidence" trong chính kết quả JSON trả ra. Điều này vô hình trói hệ thống, tự động hạ mức `NO_MATCH` nếu không thấy dẫn chứng nguồn khớp.

---

## IV. Cải tiến trong tương lai (5 Điểm)

- **Khả năng mở rộng**: Cần triển khai kiến trúc API luồng bất đồng bộ (trải ra qua `asyncio` task chunking) để xử lý tự động so khớp Jobs số lượng cực lớn đồng loạt.
- **Tính an toàn**: Áp dụng mô hình định chuẩn **Supervisor LLM** hoặc **Human-in-the-loop** đối với các báo cáo đánh giá CV quá hoàn hảo nhằm phát hiện sớm các rủi ro điểm nghẽn hoặc thiên kiến ngầm (AI Bias) trước khi gửi Offer.
- **Hiệu suất**: Mở hướng lưu trữ Embeddings qua **Vector DB (như Chroma)** để "cache" lại các phân tích JSON đối với các JD đã từng giải phóng qua Tool, tiết kiệm triệt để lượng token API cho mỗi lần so khớp lặp lại.
