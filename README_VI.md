# Bài thực hành 3: Chatbot vs ReAct Agent (Industry Edition)

Chào mừng bạn đến với Giai đoạn 3 của khóa học Agentic AI! Bài thực hành này tập trung vào việc chuyển đổi từ một Chatbot được hỗ trợ bởi LLM đơn giản thành một hệ thống **ReAct Agent** phức tạp và tinh vi hơn đi kèm với bộ giám sát (monitoring) đạt chuẩn cấp độ sản xuất trong công nghiệp.

## 🚀 Hướng dẫn Cài đặt

### 1. Thiết lập Môi trường
Sao chép tệp `.env.example` thành `.env` và điền vào các API keys của bạn:
```bash
cp .env.example .env
```

### 2. Cài đặt các thư viện (Dependencies)
```bash
pip install -r requirements.txt
```

### 3. Cấu trúc Thư mục
- `src/tools/`: Điểm mở rộng để phát triển các tool tùy chỉnh của bạn.

## 🏠 Chạy các Model Cục bộ (Bằng CPU)

Nếu bạn không muốn sử dụng OpenAI hoặc Gemini, bạn có toàn quyền chạy các model nguồn mở (như Phi-3) trực tiếp trên CPU của máy tính bằng gói tiện ích `llama-cpp-python`.

### 1. Tải Model
Tải model **Phi-3-mini-4k-instruct-q4.gguf** (khoảng 2.2GB) từ Hugging Face:
- [Phi-3-mini-4k-instruct-GGUF](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
- Tải trực tiếp qua file: [phi-3-mini-4k-instruct-q4.gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf)

### 2. Đặt Model vào Dự án
Hãy tạo thư mục `models/` nằm trong thư mục gốc dự án và di chuyển tệp `.gguf` mới tải xuống vào bên trong đó.

### 3. Cập nhật `.env`
Hãy thay đổi tham số `DEFAULT_PROVIDER` và thiết lập biến môi trường chỉ hướng đường dẫn model của bạn:
```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## 🎯 Mục tiêu của Bài Thực hành

1.  **Baseline Chatbot**: Quan sát và nhận diện các giới hạn của một LLM tiêu chuẩn khi phải đối mặt với các bài toán yêu cầu các bước suy luận liên tiếp (multi-step reasoning).
2.  **Vòng lặp ReAct**: Triển khai thiết kế thành công chu trình `Suy nghĩ-Hành động-Quan sát` (Thought-Action-Observation) trong tệp `src/agent/agent.py`.
3.  **Thay đổi Provider**: Chuyển đổi qua lại nhịp nhàng giữa OpenAI và Gemini áp dụng interface `LLMProvider`.
4.  **Phân tích Thất bại**: Dùng dữ liệu log có cấu trúc chuẩn tại `logs/` để chẩn bệnh tại sao agent không thành công (lỗi ảo tưởng model, lỗi cú pháp).
5.  **Chấm Điểm & Bonus**: Làm theo các nội dung ở [SCORING.md](file:///Users/tindt/personal/ai-thuc-chien/day03-lab-agent/SCORING.md) nhằm nhận được tổng lượng điểm cao nhất có thể cũng như cày thêm điểm thưởng thông số đánh giá mở rộng.

## 🛠️ Sử dụng Code Baseline này Thế nào
Code được thiết kế đóng vai trò như một **Bản mẫu Production** (Production Prototype). Mã nguồn cấu thành từ:
- **Hệ thống Telemetry (Thu thập dữ liệu theo dõi)**: Mọi thao tác/hành động làm ra đều được in thành log theo dạng văn bản JSON chuẩn nhất hỗ trợ quá trình phân tích dữ liệu hiệu quả cao trong các khâu về sau.
- **Provider Pattern Đảm bảo Bền bỉ**: Nhanh chóng tích hợp vào bất kể thiết kế cổng LLM API mà không lo gián đoạn luồng code.
- **Bộ khung Dự án Rõ ràng (Clean Skeletons)**: Hãy chỉ chú tâm vào xử lý thuật toán tối quan trọng nhất – chính là phương thức giải quyết thông tin nội hàm tư duy suy diễn nơi cơ quan đầu não con Agent.

---

*Chúc các bạn Coding vui vẻ! Hãy cùng nhau xây dựng ra các agents thực sự có thế làm việc được đem vào thực tế.*
