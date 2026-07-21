# 🚀 PROJECT DIGITCODE: ESCAPE ROOM PUZZLE GAME (SYSTEM CONTEXT v5.0)

## 1. TỔNG QUAN DỰ ÁN (PROJECT VISION)

**DigitCode** là dự án game giải đố mô phỏng dạng Escape Room (kết hợp từ ý tưởng board game Decorum). Dự án được thiết kế theo mô hình **Cyber-Physical System (Hệ thống Khách - Chủ kết hợp Phần mềm & Phần cứng)**:

- **Phần mềm (Desktop App .exe/.app):** Viết bằng C++ (Qt6 / QML), đóng vai trò là "Sa bàn số" (Digital Board), máy chủ quản lý luật chơi (Game Engine) và trạm giao tiếp mạng.
- **Phần cứng (Embedded Device - Sẽ phát triển ở v6):** Chạy vi điều khiển ESP32, kết nối Wi-Fi với phần mềm thông qua WebSocket, bao gồm màn hình OLED, bàn phím chọn câu hỏi (Buttons) và một "Drawing Pad" vật lý để người chơi tương tác vạch LED.

---

## 2. KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)

Hệ thống được chia thành 3 lớp phân tách độc lập (Decoupled Architecture):

### A. C++ Backend & Game Engine (`gameboard.h` / `gameboard.cpp`)

- **Quản lý Máy trạng thái (State Machine):** Điều hướng 4 câu hỏi giải đố (`DEFAULT`, `WAIT_Q1`, `WAIT_Q2_1/2`, `WAIT_Q3`, `WAIT_Q4_1/2`).
- **Thuật toán sinh đề (`generateRandomPuzzle`):** Tự động tạo mã bí mật 6 chữ số (`m_secretCode`) tuân thủ ràng buộc kiểu Sudoku (chống lặp số theo quy tắc hàng/cột/nhóm).
- **Hệ thống Điểm & Thời gian:**
  - Quản lý đồng hồ chơi thực tế (`m_playTimeSeconds`).
  - Cứ mỗi 60 giây trôi qua -> Tự động trừ 1 điểm (`m_points`).
  - Mỗi lần bấm mua manh mối (Q1, Q2, Q3, Q4) -> Trừ 5 điểm.
  - Khung phạt chần chừ (`m_penaltyTimer`): Có 10 giây để chọn mục tiêu sau khi bấm nút câu hỏi, nếu hết thời gian mà chưa chọn -> Trừ 1 điểm, hủy lệnh.
- **Cơ chế Bảo mật 2-Strike (`verifyCode`):**
  - Người chơi nhấn nút VERIFY trên UI để nhập mã 6 số phá đảo.
  - **Sai lần 1:** Bắn tín hiệu `wrongGuessWarning()`, bật Popup nhấp nháy đỏ "ACCESS DENIED" trong 4 giây (thời gian ngầm vẫn đếm).
  - **Sai lần 2:** Điểm `m_points` về 0 -> Kích hoạt Game Over (`gameLost()`).
  - **Đúng mã:** Dừng toàn bộ đồng hồ -> Kích hoạt Chiến thắng (`gameWon()`), hiển thị thời gian Clear Time.

### B. Mạng & Giao tiếp ESP32 (`hardwareserver.h` / `hardwareserver.cpp`)

- Chạy máy chủ **QWebSocketServer** non-secure tại Port `8080`.
- Giao tiếp song phương theo thời gian thực bằng gói tin **JSON**:
  - **ESP32 -> Qt (Nhận lệnh vật lý):**
    - `{"type": "PAD_SELECT", "label": "T"}` -> Chọn LED mục tiêu (T đến Y).
    - `{"type": "PAD_DRAW", "segIdx": 2}` -> Chạm nét vẽ vạch LED số 2 (0-6).
    - `{"type": "ACTION", "btnId": "BTN_Q1"}` -> Bấm nút hỏi đáp Q1-Q4 hoặc A-S.
  - **Qt -> ESP32 (Đồng bộ sa bàn & OLED):**
    - `{"type": "DRAW", "ledIdx": 0, "segIdx": 1, "val": 1}` -> Cập nhật trạng thái vạch LED.
    - `{"type": "OLED", "layout": "text", "line1": "...", "line2": "..."}` -> In thông báo lên màn OLED vật lý.

### C. Giao diện QML Frontend (UI/UX)

- **Kiến trúc StackView Đa màn hình (v5.0 Achievement):**
  - `ScreenMenu.qml`: Màn hình chính (Single Challenge, 1v1, Rules). Hỗ trợ nút **Continue** khi game đang Pause.
  - `ScreenReady.qml`: Màn hình chuẩn bị, bấm READY sẽ gọi C++ tạo đề mới và vào game.
  - `ScreenGame.qml`: Màn hình chơi chính. Tích hợp nút Pause & Menu, bảng OLED ảo, nút VERIFY nhập mã 6 số và sa bàn LED.
  - `ScreenResult.qml`: Màn hình Win/Lose. Hỗ trợ chế độ **Review Board** (cho phép xem lại sa bàn, thời gian, điểm số và các câu đã hỏi ở trạng thái đóng băng).
- **Responsive Auto-Scale (`BottomBoard.qml`):** Sử dụng thuật toán `Math.min(width, height)` trong Container để sa bàn tự động thu phóng vừa vặn mọi kích thước cửa sổ tab mà không cần thanh cuộn.
- **Mỹ thuật & Visual:** Cài đặt `qputenv("QT_QUICK_CONTROLS_STYLE", "Basic")` tại C++ để tùy biến tự do nút bấm, phân cấp phông chữ (chỉ Bold các nút sinh tử READY, VERIFY, ACCESS).

---

## 3. LUẬT CHƠI & CÁC CÂU HỎI MANH MỐI (Q1 - Q4)

Bàn chơi gồm **6 LED hiển thị** (chữ cái T, U, V, W, X, Y), được chia làm 2 hàng ngang x 3 cột dọc. Các vạch LED được định danh theo cột (`A` đến `I`) và theo hàng (`J` đến `S`).

- **Q1 (Even/Odd):** Chọn 1 LED (T-Y) -> Trả về dấu `..` (Chẵn) hoặc `.` (Lẻ) trên đỉnh LED.
- **Q2 (Compare):** Chọn 2 LED liền kề ngang/dọc -> Trả về mũi tên `<` hoặc `>` giữa 2 LED.
- **Q3 (Count):** Chọn 1 Hàng hoặc 1 Cột -> Trả về số lượng vạch LED đang sáng thực tế trong nhóm đó. Nếu số lượng bằng Max LED -> Khóa và sáng vĩnh viễn toàn bộ vạch trong nhóm.
- **Q4 (Check):** Chọn 2 Hàng/Cột -> Trả về trạng thái có bị FULL (sáng hết vạch) hay không. Nút trên QML sẽ tự động đổi màu Xanh lá (FULL) hoặc Đỏ (NOT FULL).
- **Review Mode:** Bấm nút A-S khi rảnh rỗi -> OLED hiển thị lại thông tin đã từng mua (không tốn điểm, không tốn timer).

---

## 4. MỤC TIÊU GIAI ĐOẠN TIẾP THEO (v6 - HARDWARE INTEGRATION)

- Thiết kế sơ đồ nguyên lý (Schematic) để đi dây breadboard cho thiết bị phần cứng sử dụng **ESP32**.
- Kết nối màn hình **OLED (SSD1306/SH1106 I2C)** để hứng gói tin `OLED` từ Qt Server.
- Thiết kế ma trận nút bấm (Matrix Buttons) cho các phím chức năng (Q1-Q4, A-S, T-Y).
- Xây dựng "Drawing Pad" vật lý (7 phím tương ứng 7 vạch cảm ứng/nút bấm của đèn LED 7 đoạn).
- Viết firmware C++ (Arduino/ESP-IDF) cho ESP32: Kết nối WebSocket Client tới Port 8080, parse JSON và gửi logic phím bấm.
- ⚙️ Danh sách linh kiện cốt lõi đang có
  - **Bộ não trung tâm:** Bo mạch **ESP32** (thuộc bộ kit ESP32 Basic Starter). Mạch này sẽ gánh vác việc xử lý tín hiệu và duy trì kết nối WebSocket thời gian thực tới Desktop App.
  - **Màn hình chính:** Module **OLED 0.96 inch (I2C)**. Dùng để làm màn hình "Decryption Terminal" hiển thị thời gian, điểm số và thông báo hệ thống (kết nối qua GPIO 21/SDA và 22/SCL).
  - **IC Mở rộng IO (I/O Expander):** Chip **MCP23017**. Thành phần bắt buộc phải có để mở rộng chân tín hiệu cho ESP32, giúp hệ thống đọc được toàn bộ ma trận 38 nút bấm vật lý (các nút A-S, T-Y và cụm Drawing Pad).
  - **IC Điều khiển LED:** Module **MAX7219**. Chịu trách nhiệm điều khiển khối hiển thị số và các cụm LED báo hiệu (mũi tên, dấu chấm), giao tiếp thông qua GPIO 23 (DIN), 18 (CLK) và 5 (CS).
  - **Công cụ thực hành:** **Breadboard** và cáp kết nối (để đi dây thực tế map 1:1 với sơ đồ mô phỏng trên Wokwi trước khi vẽ mạch PCB).

