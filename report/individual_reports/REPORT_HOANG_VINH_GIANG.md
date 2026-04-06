# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Hoàng Vĩnh Giang
- **Student ID**: 2A202600079
- **Date**: 06-04-2026

---

## I. Technical Contribution (15 Points)


- **Modules Implementated**:
    - `src/tools/jd_extractor.py`: Tích hợp pdfplumber để trích xuất văn bản từ PDF và sử dụng instructor để ép kiểu dữ liệu thông qua OpenRouter (Gemini/GPT-4o).
    - `src/tools/ats_validator.py`: Xây dựng bộ chấm điểm ATS cục bộ (Deterministic Scoring) dựa trên trọng số Blueprint (40% Keyword, 40% Format, 20% Section).
- **Code Highlights**:
    - Sử dụng `instructor.from_openai()` để patch OpenAI client, cho phép Agent nhận về một Object Python thay vì JSON string không ổn định.
    - Triển khai logic `is_ready` trong `ats_validator` để điều hướng vòng lặp ReAct: chỉ dừng lại (Final Answer) khi điểm số đạt yêu cầu và không thiếu từ khóa "MUST".
- **Documentation**:
    - Tool `jd_extracter.py` là một trong những tool đầu vào của agent (CV và JD), đầu ra là một json body được quy định trước trong `cv_tailoring.py`.
    - Tool `ats_validator.py` đưa ra đánh giá về độ phù hợp giữa CV và JD dựa trên các Blueprint đã được định nghĩa trước.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Khi cố gắng cài đặt thư viện để hỗ trợ chạy model local, hệ thống báo lỗi: `Failed building wheel for llama-cpp-python và CMake must be installed to build the following extensions.`
- **Log Source**:
```powershell
Traceback (most recent call last):
  File "src/tools/jd_extractor.py", line 45, in extract_jd_requirements
    structured_data = client.chat.completions.create(
  File "venv/lib/site-packages/openai/_base_client.py", line 1070, in request
    raise self._make_status_error_from_response(err.response) from None
openai.AuthenticationError: Error code: 401 - {
    "error": {
        "message": "Incorrect API key provided. You can find your API key at https://platform.openai.com/account/api-keys.",
        "type": "invalid_request_error",
        "param": null,
        "code": "invalid_api_key"
    }
}
```
- **Diagnosis**: Dù đã khai báo đúng API Key của OpenRouter trong file `.env`, nhưng hệ thống vẫn trả về lỗi "Incorrect API key" từ domain của OpenAI (`platform.openai.com`). Trong code khởi tạo `OpenAI()`, team đã quên cấu hình tham số `base_url`. Thư viện OpenAI mặc định gửi request đến endpoint của OpenAI Global. Khi Server OpenAI nhận được một Key có định dạng `sk-or-v1-...` (của OpenRouter), nó nhận diện đây là key không hợp lệ đối với hệ thống của họ.
- **Solution**: Cập nhật lại khởi tạo client để trỏ đúng về cổng của OpenRouter
```python
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
```

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Trong khi Chatbot chỉ cố gắng dự đoán từ tiếp theo để trả lời, ReAct Agent sử dụng `Thought` để tự kiểm tra điều kiện cần từ đó đưa ra quyết định sử dụng bộ tools.
2.  **Reliability**: Độ tin cậy của Agent không chỉ nằm ở việc trả ra kết quả đúng, mà còn ở cách nó xử lý các điểm gãy (Failure points) của hệ thống. Một Chatbot thông thường sẽ bị "crash" hoặc trả về thông báo lỗi thô từ API gây khó hiểu cho người dùng. Ngược lại, một ReAct Agent được thiết kế tốt phải có khả năng nhận diện các mã lỗi này, phân tích chúng và đưa ra lộ trình xử lý thay thế (Graceful Degradation), đảm bảo luồng công việc không bị gián đoạn vô lý.
3.  **Observation**: Cơ chế này biến Agent từ một thực thể xử lý ngôn ngữ thuần túy thành một hệ thống có khả năng tự điều chỉnh (Self-correcting), có thể thực sự "nhìn" thấy các rào cản kỹ thuật và phản ứng lại một cách logic.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**:
    - Chuyển đổi các công cụ tốn thời gian như `jd_extractor` (quét PDF) sang cơ chế Asynchronous (Bất đồng bộ). Sử dụng `Celery` hoặc `Redis Queue` để Agent có thể xử lý nhiều yêu cầu cùng lúc mà không làm nghẽn hệ thống.
    - Thay thế `pdfplumber` bằng các giải pháp OCR mạnh mẽ hơn như `AWS Textract` hoặc `LlamaParse` để xử lý các CV có định dạng cột phức tạp hoặc file dạng ảnh quét.
- **Safety**:
    - Triển khai một Supervisor Agent (LLM thứ hai) chuyên trách việc kiểm tra (Audit) kết quả cuối cùng. Supervisor này sẽ đối chiếu CV đã tailor với Master CV để đảm bảo Agent không "bịa" (hallucination) ra các kinh nghiệm mà người dùng không có.

    - Mã hóa API Key và thông tin nhạy cảm của người dùng bằng HashiCorp Vault thay vì để trong file .env thuần túy.
- **Performance**:
    - Tích hợp Vector Database (ví dụ: Pinecone hoặc Milvus). Thay vì nạp toàn bộ Master CV vào prompt (gây tốn token), hệ thống sẽ chỉ truy xuất các đoạn kinh nghiệm (chunks) thực sự liên quan đến các từ khóa "MUST" của JD để đưa vào bối cảnh xử lý.

    - Áp dụng Semantic Cache: Lưu trữ kết quả của các JD tương tự nhau để giảm số lượng request gọi đến LLM, giúp tiết kiệm chi phí và tăng tốc độ phản hồi.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
