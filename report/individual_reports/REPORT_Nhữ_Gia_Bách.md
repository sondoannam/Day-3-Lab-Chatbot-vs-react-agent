# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nhữ Gia Bách
- **Student ID**: 2A202600248
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Bối cảnh hệ thống

Bài toán tổng thể là xây dựng một **Hệ thống Tùy chỉnh CV tự động** theo kiến trúc ReAct Agent, bao gồm 5 lớp lớn: trích xuất dữ liệu (LlamaParse, Bright Data), điều phối LLM (Instructor + Pydantic), 4 agentic tools (Extract_Job_Requirements, Analyze_Master_CV, Draft_Tailored_Section, Validate_ATS_Compliance), UI Text Diff, và ATS Scoring Engine.

Phần tôi phụ trách trong lab này là **lớp nền tảng của vòng lặp ReAct** — cụ thể là tool đầu tiên trong pipeline và bộ khung agent để các tool khác có thể cắm vào.

### Modules Implemented

- `src/tools/cv_extractor.py` — Tool đầu tiên trong chuỗi agentic: đọc Master CV từ PDF và trả về text có cấu trúc
- `src/agent/agent.py` — Khung vòng lặp ReAct: generate → parse Thought/Action → execute tool → append Observation
- `run.py` — Script tích hợp: load env, khởi tạo OpenRouter provider, chạy agent với CV thực tế

### Code Highlights

**Cấu trúc tool dict — chuẩn chung để mọi tool trong hệ thống cắm vào agent:**
```python
cv_extractor_tool = {
    "name": "extract_cv",
    "description": (
        "Extracts the full text content from a CV PDF file. "
        "Input: the file path to the PDF. "
        "Output: the extracted CV text."
    ),
    "function": extract_cv,
}
```
Đây là shape chuẩn cho toàn bộ 4 tool trong blueprint — `name`, `description`, `function`. Các tool như `Analyze_Master_CV` hay `Validate_ATS_Compliance` sau này chỉ cần follow đúng shape này để `_execute_tool` gọi được tự động.

**Vòng lặp ReAct core trong `run()`:**
```python
result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
response_text = result["content"]

thought = self._parse_thought(response_text)
final_answer = self._parse_final_answer(response_text)
if final_answer:
    return final_answer

action = self._parse_action(response_text)
if action:
    tool_name, args = action
    observation = self._execute_tool(tool_name, args)
    current_prompt = (
        f"{current_prompt}\n"
        f"Thought: {thought}\n"
        f"Action: {tool_name}({args})\n"
        f"Observation: {observation}\n"
    )
```

**Dynamic tool dispatch trong `_execute_tool()`:**
```python
for tool in self.tools:
    if tool["name"] == tool_name:
        result = tool["function"](args)
        if isinstance(result, dict):
            if result.get("error"):
                return f"Error: {result['error']}"
            return result.get("content") or str(result)
        return str(result)
```

### Cách code tương tác với ReAct loop

`cv_extractor_tool` là tool đầu tiên được đăng ký vào `ReActAgent`. Khi LLM sinh ra `Action: extract_cv(data/Dev-Raj-Resume.pdf)`, `_parse_action()` bắt tên và argument, `_execute_tool()` tra cứu theo tên và gọi `tool["function"](args)`. Kết quả (nội dung CV text) được append vào prompt dưới dạng `Observation:` để LLM có ngữ liệu thực tế cho bước suy luận tiếp theo — đây chính là bước chuẩn bị đầu vào cho Tool 2 (`Analyze_Master_CV`) trong blueprint tổng thể.

---

## II. Debugging Case Study (10 Points)

### Problem Description

Sau khi agent loop chạy đúng, kết quả trả về là:
```
Final Answer: The file 'data/Dev-Raj-Resume.pdf' could not be located.
```
Mặc dù file thực sự tồn tại đúng tại đường dẫn đó.

### Log Source

```json
{
  "timestamp": "2026-04-06T08:34:40.006946",
  "event": "ACTION",
  "data": {
    "step": 0,
    "tool": "extract_cv",
    "args": "'data/Dev-Raj-Resume.pdf'"
  }
}
```

Chú ý: `args` là `'data/Dev-Raj-Resume.pdf'` — có dấu nháy đơn bao quanh, không phải `data/Dev-Raj-Resume.pdf`.

### Diagnosis

LLM sinh ra action theo format Python tự nhiên:
```
Action: extract_cv('data/Dev-Raj-Resume.pdf')
```
Regex `([^)]*)` trong `_parse_action` giữ nguyên toàn bộ nội dung bên trong dấu ngoặc, bao gồm cả dấu nháy đơn. Kết quả là `pdfplumber.open()` nhận đường dẫn `'data/Dev-Raj-Resume.pdf'` với ký tự `'` ở đầu và cuối — không tồn tại trên filesystem nên trả về `FileNotFoundError`. Lỗi nằm ở bước parse argument, không phải ở tool hay model.

### Solution

Thêm `.strip("'\"")` vào bước xử lý args:

```python
def _parse_action(self, text: str) -> Optional[tuple[str, str]]:
    match = re.search(r"Action:\s*(\w+)\(([^)]*)\)", text)
    if match:
        tool_name = match.group(1).strip()
        args = match.group(2).strip().strip("'\"")  # loại bỏ dấu nháy từ LLM
        return tool_name, args
    return None
```

Sau khi sửa, agent gọi đúng đường dẫn và `pdfplumber` đọc file thành công.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — Block Thought giúp gì so với Chatbot thông thường?

Với yêu cầu *"trích xuất và tóm tắt CV"*, một chatbot thông thường sẽ trả lời ngay từ kiến thức nội tại — không có file nào được đọc thực sự. Block `Thought` buộc agent phải lập luận rõ ràng: *"Tôi cần gọi extract_cv trước để có dữ liệu thực"*. Đây là sự khác biệt cốt lõi — agent nhận thức được mình đang thiếu thông tin và biết cách đi lấy thông tin đó từ môi trường bên ngoài, thay vì hallucinate.

Điều này đặc biệt quan trọng trong blueprint tổng thể: yêu cầu **Zero Hallucination** (không bịa thông tin CV) chỉ có thể đảm bảo khi agent thực sự đọc Master CV thay vì suy diễn từ prompt.

### 2. Reliability — Trường hợp Agent thực sự tệ hơn Chatbot

Agent kém hơn chatbot trong một số tình huống cụ thể:

- **Câu hỏi đơn giản không cần tool**: Mỗi bước lặp mất 5–54 giây (quan sát từ log thực tế), chatbot trả lời ngay lập tức.
- **LLM tự thêm format sai**: LLM sinh ra `extract_cv('path')` với dấu nháy — chatbot không có vấn đề này vì không cần parse output thành lệnh gọi.
- **Chi phí token tăng theo vòng lặp**: Log cho thấy `total_tokens` tăng từ 319 → 362 → 697 → 2652 qua 4 bước — conversation context ngày càng phình to.

### 3. Observation — Feedback môi trường ảnh hưởng như thế nào?

Log thực tế từ lab:
```
step 0: completion_tokens = 149   (LLM chưa có CV, chỉ lên kế hoạch)
step 1: completion_tokens = 132   (gọi tool, chờ observation)
step 2: completion_tokens = 439   (đã có CV text, bắt đầu phân tích)
step 3: completion_tokens = 2368  (viết tóm tắt đầy đủ)
```
`completion_tokens` tăng vọt ở bước 3 chứng minh agent đang thực sự **xây dựng hiểu biết dần dần** từ dữ liệu thực, không phải đoán mò từ đầu. Đây là cơ chế nền tảng để các bước sau trong blueprint (Draft_Tailored_Section, ATS scoring) có thể hoạt động chính xác.

---

## IV. Future Improvements (5 Points)

### Scalability

Hiện tại toàn bộ vòng lặp là synchronous và blocking. Để hỗ trợ nhiều người dùng đồng thời tùy chỉnh CV, cần chuyển sang **async tool execution** với `asyncio`, hoặc dùng task queue (Celery + Redis) để các tool nặng như LlamaParse hay Bright Data scraping chạy song song mà không block lẫn nhau.

### Safety

Thêm **Supervisor LLM** như trong blueprint đề xuất: trước khi `_execute_tool` thực thi, Supervisor kiểm tra action có hợp lệ không — đúng tên tool, argument không chứa path traversal (`../../`), không gọi tool nhạy cảm quá N lần/session. Đây cũng là lớp bảo vệ chống lại prompt injection từ nội dung JD độc hại khi scrape từ LinkedIn/Indeed.

### Performance

Khi hệ thống mở rộng đủ 4 tool theo blueprint, đưa toàn bộ descriptions vào system prompt mỗi lần gọi rất tốn token. Giải pháp là **Vector DB** (ChromaDB) embed description của từng tool, semantic search ra top-K tool phù hợp nhất với `user_input` trước khi build system prompt — giảm đáng kể token đầu vào và tránh confuse LLM với quá nhiều tool options.

---
