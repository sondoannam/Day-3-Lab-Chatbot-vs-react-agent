# Group Report: Lab 3 — Chatbot vs ReAct Agent
## CV Tailoring Agent System

- **Tên nhóm**: Group F2
- **Các thành viên**:
  - Member 1 — Đoàn Nam Sơn, 2A202600045 — Kiến trúc hệ thống, Pydantic Schemas, Setup Providers, Combine end-to-end pipeline
  - Member 2 — Nhữ Gia Bách, 2A202600248 — CV PDF Extraction (pdfplumber + LLM summary), Validate pipelines
  - Member 3 — Trần Quang Quí, 2A202600305 — Chatbot Baseline, Session State, Section Drafting, ATS Validator, Agent Loop
  - Member 4 — Vũ Đức Duy, 2A202600337 — JD Web Scraper to JSON, CV-JD Matcher, JD Dataset
  - Member 5 — Hoàng Vĩnh Giang, 2A202600079 — JD Extraction from PDF to JSON, Schema Fixes, ATS Validator Blueprint
- **Ngày triển khai**: 2026-04-06

---

## 1. Tóm tắt điều hành

Nhóm F2 hiện có ba lớp thực thi chính cho bài toán tailoring CV theo Job Description (JD):

- **Chatbot baseline** trong `src/chatbot.py`: gọi LLM một lần, không dùng tools.
- **ReAct agent** trong `src/agent/agent.py`: hỗ trợ Thought-Action-Observation và tool calls từng bước.
- **Deterministic end-to-end runner** trong `run.py`: đây là flow đã được xác thực gần nhất và tạo đầy đủ artifacts cho chấm bài.

Flow end-to-end hiện tại của project là:

`extract_cv -> extract_jd (PDF hoặc URL) -> match_cv_jd -> generate_cv_json -> export_cv_markdown -> validate_ats`

**Kết quả xác thực gần nhất** từ sample run ngày 2026-04-06:

- Pipeline hoàn thành thành công và sinh đủ artifacts trong `data/generated/`.
- Matcher tạo `MatchReport` với `overall_score = 5.7` cho cặp dữ liệu mẫu.
- ATS validator tạo báo cáo `52.0/100` và trạng thái `REVISION REQUIRED`.

Điểm số thấp ở sample run là hợp lý vì CV mẫu thuộc Software Engineering, còn JD mẫu là Human Resource Recruitment Officer. Điều này cho thấy pipeline đang hoạt động đúng và phát hiện mismatch thực tế, thay vì tạo kết quả đẹp một cách giả tạo.

---

## 2. Kiến trúc hệ thống & Công cụ

### 2.1 Chatbot Baseline

`src/chatbot.py` là baseline tối giản: nhận input, nối lịch sử hội thoại, gọi `self.llm.generate(...)` một lần và lưu lại history. Không có tool calls, không có session state dùng chung, không có bước validate ATS.

```python
class Chatbot:
    def chat(self, user_input: str) -> str:
        context = "\n".join(f"{msg['role'].upper()}: {msg['content']}"
                            for msg in self.history)
        prompt = f"{context}\nUSER: {user_input}\nASSISTANT:" if context else user_input
        result = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
        response = result["content"].strip()
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})
        return response
```

System prompt của baseline nhấn mạnh rằng chatbot **không có quyền truy cập external tools**, nên nó chỉ phù hợp với hỏi đáp đơn giản hoặc tư vấn chung, không phù hợp cho các tác vụ cần grounding từ CV/JD thật.

### 2.2 Vòng lặp ReAct — Thought-Action-Observation

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      ReActAgent.run()                       │
│                                                             │
│  ┌─────────────┐   LLM call    ┌────────────────────────┐  │
│  │   Prompt    │──────────────▶│  Thought + Action      │  │
│  │  (context)  │               └───────────┬────────────┘  │
│  └─────────────┘                           │ _parse_action  │
│        ▲                     ┌─────────────▼────────────┐  │
│        │  Observation        │    _execute_tool()       │  │
│        └─────────────────────│    tool["function"](args)│  │
│                              └──────────────────────────┘  │
│                                                             │
│  Loop until: Final Answer  OR  max_steps reached            │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Final Answer (based solely on Observations)
```

**Mỗi bước trong vòng lặp** (`src/agent/agent.py`):
1. Gọi LLM với `current_prompt` + system prompt
2. Parse `Thought:` → log event `THOUGHT`
3. Kiểm tra `Final Answer:` → nếu có thì kết thúc
4. Parse `Action: tool_name(args)` → gọi `_execute_tool()`
5. Append Observation vào `current_prompt` và lặp lại

Điểm quan trọng là agent hiện hỗ trợ loop ReAct đúng nghĩa, nhưng **flow được xác thực đầy đủ gần nhất của project lại là `run.py`**, không phải một agent session hoàn chỉnh từ đầu đến cuối. Vì vậy report này xem ReAct agent là một lớp tương tác, còn deterministic runner là execution path chính để kiểm thử và nộp bài.

**Session state** trong `src/tools/_session.py` là backbone của architecture. Các tool không truyền toàn bộ JSON dài vào prompt ở mọi bước, mà lưu canonical objects vào session typed:

```
session.cv_data: CandidateMasterCV    ← từ extract_cv
session.jd_data: JobDescription       ← từ extract_jd
session.match_report: MatchReport     ← từ match_cv_jd
session.tailored_sections: Dict[str, TailoredSection]  ← từ draft_section
session.tailored_cv: TailoredCV       ← từ assemble_cv
```

`CVSession` dùng `set_cv_data()` và `set_jd_data()` để validate payload ngay tại boundary, nhận được cả `dict` lẫn Pydantic object.

### 2.3 Định nghĩa công cụ

| Tên tool | Input | Output | Vai trò |
|---|---|---|---|
| `extract_cv` | `pdf_path: str` | `dict` + `session.cv_data` | Parse CV PDF thành canonical `CandidateMasterCV` |
| `extract_jd` | `pdf_path` hoặc raw JD text | Summary text + `session.jd_data` | Parse JD thành canonical `JobDescription` |
| `match_cv_jd` | _(optional input)_ | Summary text + `session.match_report` | So khớp CV/JD và tạo `MatchReport` |
| `draft_section` | `summary` \| `skills` \| `experience` | Drafted text + `TailoredSection` | Viết lại từng section dựa trên CV, JD và `MatchReport` |
| `assemble_cv` | _(empty)_ | Confirmation string | Ghép các `TailoredSection` thành `TailoredCV` |
| `export_cv_markdown` | _(empty)_ | Markdown text + file | Export markdown CV |
| `export_cv_json` | path tùy chọn | JSON file | Export `TailoredCV` thành JSON |
| `generate_cv_json` | path hoặc thư mục tùy chọn | JSON file | Draft summary/skills/experience, assemble và export JSON trong một lệnh |
| `validate_ats` | CV text hoặc empty | ATS report text | Chấm keyword coverage, section completeness và format heuristics |

Ngoài các tools trên, `run.py` còn dùng `JD_Web_Scraper` như helper để lấy JD từ URL, sau đó chuẩn hóa lại qua `extract_jd_text_requirements(...)`. File legacy `src/tools/jd_tool.py` không còn là một phần của active architecture và không được tính trong báo cáo này.

**Validated pipeline hiện tại trong `run.py`:**

```
extract_cv
→ extract_jd_requirements(...) hoặc extract_jd_text_requirements(...)
→ match_cv_jd
→ generate_cv_json
→ export_cv_markdown
→ validate_ats
```

Trong `section_drafter.py`, `draft_section` ưu tiên các requirement chưa match trong `MatchReport` trước, sau đó `generate_cv_json` gọi lần lượt `draft_section(summary)`, `draft_section(skills)`, `draft_section(experience)`, rồi `assemble_cv()` và `export_cv_json()`.

### 2.4 LLM Providers

| Vai trò | Provider | Model |
|---|---|---|
| Default provider toàn project | Gemini | `gemini-3-flash-preview` |
| Provider factory fallback | OpenRouter / OpenAI / Local | `qwen/qwen3.6-plus:free`, `gpt-4o`, GGUF |
| JD extraction | Gemini → OpenRouter → OpenAI | `GEMINI_JD_MODEL` / `OPENROUTER_JD_MODEL` / `OPENAI_JD_MODEL` |
| CV-JD matching | Gemini → OpenRouter → OpenAI | `GEMINI_MATCH_MODEL` / `OPENROUTER_MATCH_MODEL` / `OPENAI_MATCH_MODEL` |
| Section drafting / agent reasoning | Theo `session.llm` từ `create_provider(...)` | mặc định Gemini |
| CV extraction | Rule-based parser | _(no LLM)_ |
| ATS validation | Deterministic algorithm | _(no LLM)_ |

Tại thời điểm hiện tại, `.env.example` và `src/core/provider_factory.py` đều đặt **Gemini** làm mặc định, không còn là OpenRouter-first như một số phiên bản cũ.

---

## 3. Telemetry & Hiệu suất

Hệ thống logging trong `src/telemetry/logger.py` ghi JSON lines vào `logs/YYYY-MM-DD.log` và đồng thời in ra console. Log hiện không chỉ dành cho ReAct loop mà còn dùng cho tool-level events như drafting, export và ATS validation.

Các event quan sát được thực tế trong repo hiện tại gồm:

- `AGENT_START`, `LLM_RESPONSE`, `THOUGHT`, `ACTION`, `FINAL_ANSWER`, `AGENT_END`
- `TOOL_CALL`, `TOOL_RESULT`, `TOOL_ERROR`

Ví dụ trích từ file log ngày 2026-04-06:

```json
{"event": "LLM_RESPONSE", "data": {"step": 0, "usage": {"prompt_tokens": 170, "completion_tokens": 158, "total_tokens": 328}, "latency_ms": 6972}}
{"event": "ACTION", "data": {"step": 0, "tool": "extract_cv", "args": "data/Dev-Raj-Resume.pdf"}}
{"event": "LLM_RESPONSE", "data": {"step": 1, "usage": {"prompt_tokens": 1177, "completion_tokens": 1182, "total_tokens": 2359}, "latency_ms": 20083}}
{"event": "TOOL_RESULT", "data": {"tool": "draft_section", "section": "summary", "chars": 726, "targeted_reqs": 6}}
{"event": "TOOL_RESULT", "data": {"tool": "validate_ats", "score": 52.0, "is_ready": false}}
```

**Số liệu quan sát thực tế từ artifact/log hiện có:**

| Chỉ số | Giá trị |
|---|---|
| Agent sample call #1 | 328 tokens, 6972ms |
| Agent sample call #2 | 2359 tokens, 20083ms |
| Draft `summary` | 726 chars, ~11.5s |
| Draft `skills` | 234 chars, ~5.9s |
| Draft `experience` | 2136 chars, ~11.2s |
| Latest `MatchReport.overall_score` | 5.7/100 |
| Latest ATS score | 52.0/100 |
| Total cost | Chưa được track trong codebase |

Điểm cần lưu ý là repo hiện chưa có dashboard tính P50/P99 và cũng chưa chuẩn hóa cost accounting theo provider. Vì vậy phần hiệu suất trong report chỉ nên dùng các số liệu đã quan sát trực tiếp từ log/artifact, không nên điền các benchmark tổng quát chưa được đo.

---

## 4. Root Cause Analysis — Các lỗi chính gặp phải

### Case 1: Drift giữa schema cũ và canonical schema mới

**Mô tả:** Một phần code cũ dùng legacy JD schema, trong khi pipeline hiện tại đã chuẩn hóa sang `JobDescription` trong `src/schemas/cv_tailoring.py`. Khi các module downstream kỳ vọng Pydantic object nhưng upstream vẫn trả payload theo contract cũ, lỗi runtime hoặc mismatch logic sẽ xuất hiện.

**Nguyên nhân gốc rễ:** Không có canonical contract chung ở giai đoạn đầu; nhiều thành viên phát triển song song với assumptions khác nhau.

**Fix:** Toàn bộ active pipeline hiện dùng canonical schemas. `CVSession` ép kiểu và validate ngay tại boundary:

```python
def set_jd_data(self, payload: JobDescription | dict | None) -> Optional[JobDescription]:
    if isinstance(payload, JobDescription):
        self.jd_data = payload
    else:
        self.jd_data = JobDescription.model_validate(payload)
    return self.jd_data
```

**Kết quả:** `run.py`, matcher, drafter và ATS validator đều làm việc trên cùng một contract dữ liệu.

### Case 2: Refactor `tailored_sections` làm vỡ ATS validator

**Mô tả:** Sau khi `section_drafter.py` chuyển từ plain string sang `TailoredSection` và `TailoredTextBlock`, `validate_ats` cũ không còn đọc được trực tiếp nội dung đã draft.

**Fix:** `validate_ats` hiện build text từ `session.tailored_cv.sections` hoặc `session.tailored_sections.values()`, rồi mới chạy keyword/format heuristics:

```python
if session.tailored_sections:
    blocks = []
    for section in session.tailored_sections.values():
        blocks.append(section.title)
        blocks.extend(block.text for block in section.blocks)
    text = "\n\n".join(blocks)
```

**Kết quả:** ATS validator giờ tương thích với structured drafting path và cả assembled `TailoredCV`.

### Case 3: OpenRouter free-model structured output không ổn định

**Mô tả:** Với các model free trên OpenRouter, structured extraction bằng Instructor/tool-calling không đủ ổn định cho JD extraction và CV-JD matching.

**Nguyên nhân gốc rễ:** OpenRouter free-model path không đảm bảo tương thích hoàn toàn với cơ chế structured output mà OpenAI/Instructor mong đợi.

**Fix hiện tại trong codebase:**

- `src/tools/jd_extractor.py` dùng Gemini/OpenRouter theo hướng **prompt-to-JSON + schema validation**.
- `src/tools/cv_jd_matcher.py` cũng parse JSON từ model output, rồi validate bằng `MatchReport.model_validate_json(...)`.
- OpenAI vẫn giữ vai trò fallback structured-output path khi có key.

**Kết quả:** Pipeline không còn phụ thuộc duy nhất vào một provider-specific structured mode.


---

## 5. Ablation Studies & Thử nghiệm

### Thử nghiệm 1: Chatbot baseline vs tool-grounded system

| Trường hợp | Chatbot | Tool-grounded system | Đánh giá |
|---|---|---|---|
| Hỏi đáp chung | Nhanh, đủ dùng | Làm được nhưng thừa công cụ | **Chatbot** |
| Tailor CV theo JD thật | Không có grounding từ PDF/JD | Có thể dựa trên artifacts thật | **Tool-grounded** |
| Xuất file JSON/Markdown | Không hỗ trợ | Có qua `generate_cv_json`, `export_cv_markdown` | **Tool-grounded** |
| ATS validation | Không có | Có `validate_ats` deterministic | **Tool-grounded** |

Kết luận: baseline phù hợp để so tốc độ/phản hồi đơn giản; pipeline có tools phù hợp cho bài lab CV tailoring vì có grounding, artifacts và kiểm tra ATS.

### Thử nghiệm 2: ReAct agent vs deterministic runner

| Tiêu chí | ReAct agent | `run.py` deterministic runner | Đánh giá |
|---|---|---|---|
| Tương tác nhiều bước | Tốt hơn | Kém linh hoạt hơn | **Agent** |
| Reproducibility | Phụ thuộc vào reasoning từng vòng | Cao, flow cố định | **Runner** |
| Sinh artifacts để chấm bài | Có thể làm, nhưng không tự động đầy đủ | Có, mặc định sinh đủ JSON/Markdown/TXT | **Runner** |
| Dễ smoke test | Trung bình | Rất dễ với CLI | **Runner** |

Kết luận: agent phù hợp cho demo ReAct và tương tác trong editor; runner phù hợp hơn làm "golden path" để kiểm thử và báo cáo kết quả cuối.

### Thử nghiệm 3: JD PDF vs JD URL input

Runner hiện hỗ trợ hai đường ingest JD:

- `--jd-pdf`: đọc PDF rồi parse bằng `extract_jd_requirements(...)`
- `--jd-url`: scrape markdown bằng `JD_Web_Scraper`, sau đó chuẩn hóa qua `extract_jd_text_requirements(...)`

Điểm mạnh của thiết kế này là cả hai input modes đều hội tụ về cùng canonical `JobDescription`, nên downstream matcher/drafter/validator không cần viết logic riêng cho từng nguồn dữ liệu.

---

## 6. Đánh giá Production Readiness

### Bảo mật & Guardrails

- **Input sanitization**: PDF path xử lý qua `Path` object và `pdfplumber`, không gọi shell command.
- **Canonical schema boundary**: CV/JD/match/tailored output đều đi qua Pydantic validation.
- **Provider abstraction**: `create_provider(...)` tách riêng Gemini/OpenAI/OpenRouter/Local và cho phép fallback.
- **Deterministic ATS scan**: phần kiểm tra ATS không phụ thuộc LLM, giúp kết quả dễ giải thích hơn.

### Những điểm chưa production-ready

| Vấn đề | Impact | Hướng xử lý |
|---|---|---|
| Session là singleton module-level | Không hỗ trợ multi-user concurrent | Per-request session object + context var |
| Flow runner vẫn tuần tự | Độ trễ cao khi JD extraction, matching, drafting chạy nối tiếp | Tách stage song song khi hợp lý hoặc thêm queue/background jobs |
| `validate_ats` dùng heuristic section names cố định | CV được sinh mới hiện chỉ có summary/skills/experience nên dễ mất điểm completeness | Mở rộng generator cho education/projects hoặc nới rule theo variant CV |
| `export_cv_markdown` ghi file `tailored_cv.md` ở root rồi `run.py` mới copy sang output dir | Artifact path chưa nhất quán | Cho phép export trực tiếp vào output dir |
| Logger chưa có guard chống add handler lặp lại | Có thể log trùng nếu logger được init nhiều lần | Kiểm tra `if not self.logger.handlers` trước khi add |
| Agent prompt chưa enforce đầy đủ validated sequence mới | ReAct path chưa bắt buộc `match_cv_jd`/`generate_cv_json` trước khi kết thúc | Cập nhật system prompt/tool policy cho agent |

### Hướng mở rộng dài hạn

- **Unify CLI và agent orchestration**: để agent có thể gọi đúng validated pipeline thay vì tự ghép tool sequence một cách lỏng hơn.
- **Cost/latency dashboard**: hiện log có token và latency từng call, nhưng chưa có lớp tổng hợp P50/P99/cost.
- **Better ATS policy**: tách rule cho `required sections` theo loại JD/CV thay vì dùng một danh sách cố định.
- **Robust web ingestion**: chuẩn hóa thêm retry, timeout, và raw artifact management cho JD URL path.
