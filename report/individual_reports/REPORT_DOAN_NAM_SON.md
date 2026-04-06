# Báo cáo cá nhân: Bài thực hành 3 - Chatbot vs ReAct Agent

- **Họ và tên sinh viên**: Đoàn Nam Sơn
- **Mã số sinh viên**: 2A202600045
- **Ngày tháng**: 2026-04-06

---

## I. Đóng góp kỹ thuật (15 Điểm)

Trong project này, phần việc chính của tôi tập trung vào ba lớp nền tảng: chuẩn hóa schema dữ liệu, cấu hình provider để hệ thống chạy ổn định, và ghép các thành phần rời rạc thành một pipeline end-to-end có thể kiểm thử trực tiếp.

- **Các module đã triển khai**: `src/schemas/cv_tailoring.py`, `src/core/provider_factory.py`, `src/core/gemini_provider.py`, `run.py`
- **Các module phối hợp/chỉnh sửa để đồng bộ contract**: `src/tools/_session.py`, `src/tools/jd_extractor.py`, `src/tools/cv_jd_matcher.py`, `src/tools/section_drafter.py`, `.env.example`

### 1. Thiết kế schema chuẩn cho toàn pipeline

Tôi xây dựng lớp schema Pydantic canonical để mọi stage của hệ thống cùng nói chung một ngôn ngữ dữ liệu: CV extraction, JD extraction, matching, drafting và export. Việc này giúp giảm lỗi do mỗi thành viên dùng một object shape khác nhau.

Điểm nổi bật là schema không chỉ mô tả dữ liệu đầu vào/đầu ra, mà còn encode cả metadata, evidence và typing cho business workflow.

```python
class JobDescription(SchemaModel):
	metadata: ExtractionMetadata
	title: str
	company_name: Optional[str] = None
	responsibilities: List[JobResponsibility] = Field(default_factory=list)
	requirements: List[JobRequirement] = Field(default_factory=list)
	target_keywords: List[str] = Field(default_factory=list)
```

```python
class CandidateMasterCV(SchemaModel):
	metadata: ExtractionMetadata
	contact: ContactInfo
	professional_summary: Optional[str] = None
	skills: List[SkillEntry] = Field(default_factory=list)
```

Schema layer này tương tác trực tiếp với vòng lặp ReAct thông qua session state: tools có thể trả summary ngắn cho LLM, nhưng vẫn lưu object đầy đủ vào `session.cv_data`, `session.jd_data`, `session.match_report` để các bước sau dùng lại mà không cần bơm toàn bộ JSON vào prompt.

### 2. Thiết lập provider factory và đổi mặc định sang Gemini

Tôi chuẩn hóa lớp tạo provider để hệ thống có thể đổi giữa Gemini, OpenAI, OpenRouter và local model mà không sửa business logic ở tool layer. Đồng thời, tôi chuyển mặc định của project sang Gemini để thống nhất execution path hiện tại.

```python
def create_provider(provider_name: Optional[str] = None, model_name: Optional[str] = None) -> LLMProvider:
	provider = (provider_name or os.getenv("DEFAULT_PROVIDER", "gemini")).strip().lower()
	model = model_name or os.getenv("DEFAULT_MODEL")

	if provider in {"google", "gemini"}:
		return GeminiProvider(model_name=model or "gemini-3-flash-preview")
```

Đóng góp này quan trọng với ReAct loop vì `session.llm` và các tool downstream không cần biết cụ thể đang dùng provider nào. Agent chỉ làm việc với interface `LLMProvider`, còn provider factory xử lý phần chọn model/backend.

### 3. Ghép pipeline end-to-end trong `run.py`

Thay vì chỉ demo từng tool riêng lẻ, tôi ghép toàn bộ flow thành một CLI runner có thể chạy một lệnh để tạo artifacts hoàn chỉnh. Đây là phần tôi coi là đóng góp thực dụng nhất vì giúp cả nhóm có một “golden path” để kiểm thử và nộp bài.

```python
def main() -> None:
	args = parse_args()
	output_dir = Path(args.output_dir).expanduser().resolve()

	session.reset()
	session.llm = create_provider(args.provider, args.model)

	run_cv_extraction(cv_path, output_dir)
	run_jd_extraction_from_pdf(jd_pdf_path, output_dir)
	run_matching(output_dir)
	run_tailored_cv_generation(output_dir)
	run_ats_validation(output_dir)
```

Pipeline này còn hỗ trợ cả `--jd-pdf` và `--jd-url`, nên có thể dùng chung một orchestration path cho hai nguồn dữ liệu JD khác nhau.

### 4. Tài liệu cách phần việc của tôi tương tác với ReAct loop

Phần việc của tôi không chỉ là viết code “backend utility”, mà là tạo hạ tầng để ReAct agent và runner dùng chung dữ liệu một cách nhất quán:

- Schema canonical giúp observation ngắn nhưng state đầy đủ.
- Provider factory giúp agent đổi model mà không cần sửa tool definitions.
- End-to-end runner đóng vai trò execution path ổn định khi agent reasoning chưa đủ reliable.

Nói ngắn gọn, phần tôi làm là **lớp contract + orchestration**, giúp các tool của các thành viên khác có thể ghép lại thành một hệ thống thật sự chạy được.

---

## II. Nghiên cứu tình huống gỡ lỗi (10 Điểm)

- **Mô tả vấn đề**: Agent path không đủ ổn định để dùng làm execution path chính cho toàn bộ bài toán tailoring CV. Trong log ngày 2026-04-06, agent chỉ gọi `extract_cv(...)` rồi kết thúc bằng một `Final Answer`, thay vì đi tiếp qua JD extraction, matching và ATS validation.
- **Nguồn log**: `logs/2026-04-06.log`

```json
{"timestamp": "2026-04-06T08:52:16.833554", "event": "ACTION", "data": {"step": 0, "tool": "extract_cv", "args": "data/Dev-Raj-Resume.pdf"}}
{"timestamp": "2026-04-06T08:52:37.174317", "event": "FINAL_ANSWER", "data": {"step": 1, "answer": "Based on the extracted CV, here is the summary of Dev Raj Singh's profile: ..."}}
```

- **Chẩn đoán**: Vấn đề không nằm ở tool `extract_cv`, mà nằm ở orchestration reliability. Với một số prompt và model, agent có thể dừng sớm ngay khi thấy mình đã “trả lời được một phần” câu hỏi, dù hệ thống tổng thể vẫn chưa hoàn thành pipeline cần thiết cho bài lab. Điều này cho thấy ReAct loop phù hợp cho tương tác linh hoạt, nhưng chưa đủ ổn định để làm đường chạy mặc định cho việc sinh artifacts chuẩn hóa.
- **Giải pháp**: Tôi xử lý vấn đề theo hướng kiến trúc thay vì chỉ prompt-tuning. Cụ thể:

1. Chuẩn hóa dữ liệu qua schema canonical để mọi stage downstream dùng cùng contract.
2. Tạo `run.py` làm deterministic runner để ép đúng thứ tự pipeline.
3. Đưa provider selection vào `create_provider(...)` để test và chạy pipeline nhất quán hơn.
4. Giữ agent như một lớp tương tác, nhưng không dùng agent làm con đường duy nhất để kiểm thử cuối.

Sau khi chuyển trọng tâm sang runner end-to-end, hệ thống đã chạy trọn pipeline và sinh đủ các artifacts trong `data/generated/`, bao gồm `example-resume.json`, `jd_recruitment_officer_final.json`, `match_report.json`, `tailored_cv.json`, `tailored_cv.md` và `ats_validation.txt`.

---

## III. Góc nhìn cá nhân: Chatbot vs ReAct (10 Điểm)

### 1. Suy luận: Khối `Thought` đã giúp agent như thế nào?

Khối `Thought` có giá trị lớn ở chỗ nó buộc mô hình biểu lộ ra bước tiếp theo cần làm thay vì trả lời ngay. Với bài toán CV tailoring, điều này đặc biệt hữu ích vì tác vụ vốn là chuỗi nhiều bước: extract CV, extract JD, đối sánh, sinh nội dung, rồi mới kiểm tra ATS. Chatbot không có lớp suy luận trung gian này nên thường trả lời “trông có vẻ hợp lý” nhưng thiếu grounding thực tế.

### 2. Độ tin cậy: Khi nào Agent hoạt động kém hơn Chatbot?

Theo quan sát của tôi, agent hoạt động kém hơn chatbot trong hai tình huống:

- Khi câu hỏi rất đơn giản, không cần tool. Lúc đó agent có overhead do reasoning và tool policy.
- Khi orchestration chưa được khóa chặt. Agent có thể dừng sớm hoặc đi sai nhánh, trong khi chatbot ít nhất vẫn cho ra một câu trả lời trực tiếp nhanh hơn.

Vì vậy tôi cho rằng agent không phải lúc nào cũng “tốt hơn”, mà chỉ tốt hơn khi bài toán thật sự cần multi-step grounding.

### 3. Quan sát: Observation đã ảnh hưởng đến các bước tiếp theo như thế nào?

Observation là phần làm cho agent khác chatbot rõ nhất. Sau mỗi tool call, agent không còn suy luận trên trí nhớ chung chung nữa mà suy luận trên bằng chứng cụ thể từ môi trường. Ví dụ:

- `extract_cv` đưa thông tin ứng viên thật.
- `extract_jd` đưa requirements thật của JD.
- `match_cv_jd` chỉ ra gap requirements.
- `validate_ats` phản hồi trực tiếp score, missing MUST keywords và lỗi format.

Chính chuỗi observations này khiến bước tiếp theo có tính định hướng hơn. Nếu không có observation, model chỉ đang “phỏng đoán hợp lý”; còn khi có observation, model bắt đầu “ra quyết định dựa trên trạng thái hệ thống”.

---

## IV. Cải tiến trong tương lai (5 Điểm)

- **Khả năng mở rộng**: Tách runner hiện tại thành các stage bất đồng bộ hoặc job queue để CV extraction, JD ingestion, matching và drafting có thể scale theo request thay vì dùng session singleton module-level.
- **Tính an toàn**: Thêm một lớp supervisor hoặc validation policy ở cuối pipeline để chặn trường hợp tailored CV vẫn còn thiếu nhiều MUST requirements nhưng người dùng vẫn muốn xuất bản ngay.
- **Hiệu suất**: Tối ưu artifact pipeline bằng cách export markdown trực tiếp vào output directory, cache JD URL scrape results, và bổ sung dashboard tổng hợp latency/token thay vì chỉ có raw logs.
