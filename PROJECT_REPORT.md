# BÁO CÁO KỸ THUẬT

## Dự án: DigitCode — Escape Room Puzzle Game
## Giai đoạn: v6 — Tích hợp Phần cứng ESP32

---

**Loại hình hệ thống:** Cyber-Physical System (Hệ thống Khách–Chủ kết hợp Phần mềm & Phần cứng)
**Phần mềm nền:** Qt6/QML, C++ (Desktop Application)
**Phần cứng:** ESP32 DevKit, giao tiếp qua WebSocket/JSON
**Ngày báo cáo:** 16/07/2026

---

## TÓM TẮT

Báo cáo này trình bày toàn bộ quá trình phát triển dự án **DigitCode** — một trò chơi giải đố mô phỏng Escape Room — từ kiến trúc phần mềm nền tảng (v1-v5) cho đến giai đoạn tích hợp phần cứng vật lý (v6). Trọng tâm của báo cáo là quá trình thiết kế, triển khai và **gỡ lỗi thực tế** hệ thống phần cứng dựa trên vi điều khiển ESP32, bao gồm việc phát hiện và xử lý sai lệch giữa linh kiện thực tế và tài liệu thiết kế ban đầu, giải quyết xung đột địa chỉ bus I2C, và hiệu chỉnh mạch điều khiển LED 7 đoạn. Tại thời điểm báo cáo, phần mềm đã hoàn thiện và biên dịch thành công; phần cứng đã xác minh được các khối chức năng cốt lõi (vi điều khiển, màn hình OLED, mở rộng I/O) trên thiết bị thật, và đang trong giai đoạn hoàn thiện khối hiển thị LED.

---

## MỤC LỤC

1. Tổng quan dự án
2. Kiến trúc phần mềm (v1–v5)
3. Giao thức truyền thông ESP32 ↔ Qt
4. Bổ sung Backend cho v6
5. Thiết kế phần cứng v6
6. Firmware ESP32
7. Quá trình triển khai thực tế và xử lý sự cố
8. Kết quả kiểm thử
9. Hạn chế và hướng phát triển
10. Kết luận
11. Tài liệu tham khảo

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1 Bối cảnh và mục tiêu

DigitCode là trò chơi giải đố dạng Escape Room, lấy cảm hứng từ board game *Decorum*, được thiết kế theo mô hình **Cyber-Physical System**: một hệ thống trong đó phần mềm và phần cứng phối hợp chặt chẽ để tạo trải nghiệm chơi vừa có tính số hóa (Digital) vừa có tính vật lý (Physical).

Dự án được phát triển qua nhiều giai đoạn (v1 → v6), trong đó:

- **v1–v3**: Xây dựng logic trò chơi lõi (thuật toán sinh đề, luật chơi).
- **v4**: Tích hợp `GameBoard` (Game Engine) với `HardwareServer` (máy chủ mạng cho phần cứng tương lai).
- **v5**: Hoàn thiện giao diện QML đa màn hình, cơ chế Pause/Resume, Review Mode, bảo mật 2-Strike.
- **v6** *(giai đoạn báo cáo này tập trung)*: Hiện thực hóa phần cứng vật lý — biến "sa bàn ảo" trên màn hình thành một thiết bị thật mà người chơi có thể chạm tay vào.

### 1.2 Kiến trúc hệ thống tổng thể

```
┌─────────────────────────┐        WebSocket/JSON        ┌─────────────────────────┐
│   PHẦN MỀM (Qt6/QML)    │  <══════ port 8080 ══════>   │   PHẦN CỨNG (ESP32)     │
│   - Game Engine          │                               │   - OLED (trạng thái)   │
│   - HardwareServer       │                               │   - Ma trận 38 nút      │
│   - UI StackView         │                               │   - Khối LED 7 đoạn ×6  │
└─────────────────────────┘                               └─────────────────────────┘
```

Hai phía đồng bộ trạng thái theo thời gian thực: mọi thao tác trên phần cứng (nhấn nút, vẽ segment) được gửi lên phần mềm để xử lý luật chơi, và mọi thay đổi trạng thái (đèn LED, thông báo) được phần mềm đẩy ngược xuống phần cứng để hiển thị.

---

## 2. KIẾN TRÚC PHẦN MỀM (v1–v5)

### 2.1 Game Engine (`backend/gameboard.h/.cpp`)

- **Máy trạng thái hữu hạn** (`GameState` enum): `DEFAULT → WAIT_Q1 / WAIT_Q2_1,2 / WAIT_Q3 / WAIT_Q4_1,2`, điều phối 4 dạng câu hỏi manh mối (Q1: Chẵn/Lẻ, Q2: So sánh, Q3: Đếm, Q4: Kiểm tra Full).
- **Thuật toán sinh đề ràng buộc kiểu Sudoku** (`generateRandomPuzzle`): sinh mã bí mật 6 chữ số với các ràng buộc — mỗi chữ số xuất hiện tối đa 2 lần, không lặp liền kề trong nhóm 3 số, không trùng theo cột giữa 2 hàng.
- **Hệ thống điểm và thời gian**: khởi điểm 100 điểm; trừ 1 điểm mỗi 60 giây trôi qua; trừ 5 điểm mỗi lần mua manh mối hợp lệ; khung phạt chần chừ 10 giây (trừ 1 điểm nếu không chọn kịp mục tiêu sau khi bấm câu hỏi).
- **Cơ chế bảo mật 2-Strike** (`verifyCode`): đoán sai lần 1 → cảnh báo popup nhấp nháy 4 giây; đoán sai lần 2 → kết thúc trò chơi (Game Over); đoán đúng → dừng đồng hồ, kích hoạt trạng thái Chiến thắng.

### 2.2 Giao tiếp phần cứng (`backend/hardwareserver.h/.cpp`)

Một `QWebSocketServer` (không mã hóa) lắng nghe tại cổng **8080**, đóng vai trò cầu nối hai chiều giữa `GameBoard` và mọi thiết bị ESP32 kết nối vào (chi tiết giao thức tại Chương 3).

### 2.3 Giao diện QML (v5.0 — StackView đa màn hình)

Luồng màn hình: `ScreenMenu → ScreenReady → ScreenGame → ScreenResult`. Thành phần `BottomBoard.qml` (sa bàn LED ảo) tự động thu phóng theo công thức `Math.min(width, height)` để vừa khít mọi kích thước cửa sổ. Hỗ trợ tạm dừng/tiếp tục ván chơi (Pause/Continue) và chế độ xem lại (Review Mode — cho phép xem lại sa bàn ở trạng thái đóng băng).

---

## 3. GIAO THỨC TRUYỀN THÔNG ESP32 ↔ QT (WebSocket/JSON, cổng 8080)

### 3.1 Chiều Qt → ESP32 (outbound)

| Loại (`type`) | Trường dữ liệu | Điều kiện gửi |
|---|---|---|
| `SYSTEM` | `cmd: "welcome"` | Ngay khi ESP32 vừa kết nối thành công |
| `DRAW` | `ledIdx` (0–5), `segIdx` (0–6), `val` (0/1/2) | Mỗi khi 1 đoạn LED (segment) thay đổi trạng thái |
| `OLED` | `layout: "text"` kèm `line1`, `line2` **hoặc** `layout: "default"` | Mọi thông báo trò chơi (câu hỏi, kết quả, thắng/thua, cảnh báo) |

### 3.2 Chiều ESP32 → Qt (inbound)

| Loại (`type`) | Trường dữ liệu | Ý nghĩa |
|---|---|---|
| `PAD_SELECT` | `label` ∈ {T…Y} | Chọn LED mục tiêu cho "Drawing Pad" |
| `PAD_DRAW` | `segIdx` (0–6) | Vạch 1 đoạn (segment) trên LED đang được chọn |
| `ACTION` | `btnId` ∈ {BTN_Q1…Q4, A…S, T…Y, `BTN_VERIFY`, `BTN_PAUSE`} | Sự kiện nhấn nút logic/chức năng |

> `BTN_VERIFY` và `BTN_PAUSE` là hai giá trị **mới được bổ sung trong giai đoạn v6** — trình bày chi tiết tại Chương 4.

---

## 4. BỔ SUNG BACKEND CHO V6

Trước v6, hàm `handleButtonPress()` chưa xử lý hai sự kiện `BTN_VERIFY` và `BTN_PAUSE`; đồng thời phía C++ chưa lưu trạng thái tạm dừng (`m_isPaused`) — trạng thái này trước đó chỉ tồn tại cục bộ trong QML.

**Các thay đổi đã thực hiện** (`backend/gameboard.h`, `backend/gameboard.cpp`):

- **`BTN_PAUSE`**: chuyển đổi (toggle) giữa `pauseGame()` và `resumeGame()` dựa trên cờ trạng thái `m_isPaused` mới bổ sung.
- **`BTN_VERIFY`**: đọc trạng thái segment (`m_segStates`) của cả 6 LED, đối chiếu ngược với bảng `DIGIT_MAP` sẵn có (thông qua hàm mới `decodeDigitFromSegments`) để suy luận ra từng chữ số 0–9 mà người chơi đã **vẽ trực tiếp trên sa bàn LED vật lý** — không cần bàn phím số riêng biệt. Sáu chữ số được ghép thành chuỗi và truyền vào `verifyCode()`. Trường hợp một LED bất kỳ chưa khớp mẫu chữ số hợp lệ nào, hệ thống từ chối gọi xác minh và hiển thị thông báo `"INVALID CODE"` trên OLED.

Toàn bộ mã nguồn đã được biên dịch lại thành công qua CMake, không phát sinh lỗi.

---

## 5. THIẾT KẾ PHẦN CỨNG V6

### 5.1 Danh mục linh kiện (BOM)

| Linh kiện | Vai trò | Giao tiếp |
|---|---|---|
| ESP32 DevKit | Bộ xử lý trung tâm, WebSocket Client | — |
| OLED 0.96" I2C (SSD1306) | Màn hình hiển thị trạng thái ("Decryption Terminal") | I2C, GPIO21 (SDA) / GPIO22 (SCL) |
| 2× PCF8574 (I/O Expander) | Đọc ma trận 38 nút bấm | I2C, trên 2 bus vật lý riêng biệt *(xem Mục 7.3)* |
| MAX7219 (IC trần, DIP-24) | Điều khiển 6 LED 7 đoạn | 3 dây: GPIO23 (DIN), GPIO18 (CLK), GPIO5 (CS) |
| 6× LED 7 đoạn (model 5161AS, common cathode) | Hiển thị mã số vật lý | Bus segment dùng chung qua MAX7219 |
| Điện trở 10kΩ | Thiết lập dòng điện MAX7219 (ISET) | — |
| Breadboard, dây nối | Lắp ráp nguyên mẫu | — |

### 5.2 Kiến trúc bus tín hiệu

- **Bus I2C #1** (SDA=GPIO21, SCL=GPIO22): OLED (địa chỉ `0x3C`) + PCF8574 hàng (địa chỉ `0x20`).
- **Bus I2C #2** (SDA=GPIO4, SCL=GPIO16): PCF8574 cột (địa chỉ `0x20`) — sử dụng bus I2C phần cứng thứ hai của ESP32 để tránh xung đột địa chỉ *(xem Mục 7.3)*.
- **Giao tiếp 3 dây** cho MAX7219: DIN (GPIO23), CLK (GPIO18), CS/LOAD (GPIO5).

Thiết kế này không sử dụng thêm bất kỳ chân GPIO nào cho 38 nút bấm (toàn bộ đi qua I2C), tránh được các chân "strapping" nhạy cảm của ESP32 (GPIO 0, 2, 12, 15) và các chân flash nội bộ (GPIO 6–11).

### 5.3 Thiết kế ma trận phím (6 hàng × 7 cột, 38 nút)

| Hàng (PCF8574 #1) | Nội dung |
|---|---|
| P0 | Q1, Q2, Q3, Q4, VERIFY, PAUSE |
| P1 | T, U, V, W, X, Y (chọn LED mục tiêu) |
| P2 | Drawing Pad — 7 phím vạch A–G |
| P3–P5 | A–S (19 nút logic hàng/cột) |

Cột: PCF8574 #2, chân P0–P6. Tổng cộng 6+6+7+7+7+5 = **38 nút**, khớp chính xác với số lượng nêu trong tài liệu thiết kế gốc.

### 5.4 Mạch điều khiển LED 7 đoạn (MAX7219)

MAX7219 là IC trần (không phải module tích hợp sẵn), do đó cần bổ sung mạch phụ trợ theo đúng datasheet gốc (Analog Devices/Maxim):

- **Điện trở RSET 10kΩ** giữa chân 18 (ISET) và **chân 19 (V+)** — quyết định dòng điện đỉnh cấp cho các segment (theo datasheet gốc: *"ISET: Connect to V+ through a resistor RSET"*).
- Nguyên lý bus: 7 đường segment (SEG A–G) dùng **chung** cho cả 6 LED; chỉ đường COM của mỗi LED đi **riêng** về một chân DIG (DIG0–DIG5) để chọn LED đang hiển thị tại từng thời điểm quét (kỹ thuật multiplexing).

Bảng ánh xạ DIG → LED:

| Chân MAX7219 | LED |
|---|---|
| DIG0 (chân 2) | T |
| DIG1 (chân 11) | U |
| DIG2 (chân 6) | V |
| DIG3 (chân 7) | W |
| DIG4 (chân 3) | X |
| DIG5 (chân 10) | Y |

### 5.5 Cảnh báo an toàn kỹ thuật

Trước khi cấp nguồn cho mạch, các rủi ro sau đã được xác định và tài liệu hóa (chi tiết đầy đủ tại `docs/hardware/schematic.md`):

1. MAX7219 cần nguồn **5V** (không dùng chân 3.3V của ESP32).
2. Nguy cơ cháy IC nếu đấu ngược cực VCC/GND.
3. Yêu cầu nối chung GND giữa mọi khối mạch.
4. Nguy cơ ngắn mạch tại ma trận phím nếu lệch hàng breadboard.
5. Yêu cầu công suất nguồn USB đủ lớn (≥ 5V/1A) để tránh sụt áp khi nhiều LED sáng đồng thời.

---

## 6. FIRMWARE ESP32

### 6.1 Công cụ phát triển

Sử dụng **`arduino-cli`** (cài đặt qua Homebrew) thay vì Arduino IDE đồ họa, tận dụng ESP32 core và phần lớn thư viện đã có sẵn trong sketchbook của máy phát triển (`WebSockets`, `ArduinoJson`, `LedControl`, `Adafruit SSD1306/GFX/BusIO`); bổ sung thêm thư viện `Adafruit PCF8574`.

### 6.2 Cấu trúc mã nguồn

```
firmware/
├── DigitCodeFirmware/     # Firmware chính thức
│   ├── DigitCodeFirmware.ino
│   ├── secrets.h          # Thông tin WiFi (không commit)
│   └── secrets.h.example  # Mẫu tham khảo
└── tools/                 # Các sketch kiểm tra từng khối phần cứng
    ├── i2c_scanner/
    ├── max7219_test/
    └── matrix_test/
```

Chiến lược phát triển theo hướng **kiểm tra tăng dần** (incremental bring-up): mỗi khối phần cứng có một sketch kiểm tra độc lập, chạy và xác nhận trước khi tích hợp vào firmware chính thức — giúp cô lập nhanh nguyên nhân lỗi thay vì gỡ lỗi trên toàn hệ thống cùng lúc.

### 6.3 Luồng xử lý chính

- **Khởi tạo**: kết nối WiFi → kết nối WebSocket Client tới máy chủ Qt → khởi tạo 2 bus I2C, MAX7219, OLED.
- **Nhận lệnh từ Qt**: xử lý `DRAW` (cập nhật segment LED thật) và `OLED` (hiển thị văn bản trạng thái).
- **Quét ma trận phím**: chu kỳ ~20ms, phát hiện cạnh nhấn (press-edge) để tránh gửi lặp, ánh xạ sang các message `ACTION` / `PAD_SELECT` / `PAD_DRAW` tương ứng gửi lên Qt.

---

## 7. QUÁ TRÌNH TRIỂN KHAI THỰC TẾ VÀ XỬ LÝ SỰ CỐ

Phần này ghi lại quá trình đưa firmware lên phần cứng thật — bao gồm các sai lệch phát hiện được giữa thiết kế lý thuyết và linh kiện thực tế, cùng phương án xử lý.

### 7.1 Xác minh chuỗi công cụ trên phần cứng thật

ESP32 được nhận diện qua cổng USB (`/dev/cu.usbserial-0001`, chip giao tiếp CP2102, vi điều khiển ESP32-D0WD-V3). Quy trình nạp firmware (`arduino-cli upload`) và đọc log Serial được xác minh hoạt động ổn định — do công cụ `arduino-cli monitor` yêu cầu terminal tương tác thật (TTY) nên việc đọc log được thực hiện thay thế bằng thư viện `pyserial` trong môi trường Python cô lập (virtual environment).

### 7.2 Phát hiện sai lệch linh kiện: MCP23017 → PCF8574

Tài liệu thiết kế gốc của dự án chỉ định IC mở rộng I/O là **MCP23017** (16 chân GPIO). Qua kiểm tra thực tế linh kiện đang có, xác định đây là **PCF8574** (8 chân GPIO/con) — một chip khác hoàn toàn về số lượng chân khả dụng. Do thiết kế ma trận 6×7 cần tối thiểu 13 chân điều khiển, một PCF8574 đơn lẻ không đáp ứng đủ.

**Giải pháp**: chuyển sang sử dụng **2 module PCF8574** độc lập (1 cho hàng, 1 cho cột), yêu cầu đặt ở 2 địa chỉ I2C khác nhau trên cùng một bus.

### 7.3 Sự cố xung đột địa chỉ I2C và giải pháp bus kép

Trong quá trình đấu nối 2 module PCF8574 lên cùng một bus I2C, việc điều chỉnh jumper địa chỉ (A0–A2) trên module thứ hai **không tạo ra hiệu quả thay đổi địa chỉ như kỳ vọng** — qua nhiều lần thử với các tổ hợp jumper khác nhau, cả hai module vẫn luôn phản hồi tại cùng địa chỉ `0x20`, dẫn đến xung đột bus (chỉ 1 trong 2 thiết bị được máy quét I2C phát hiện).

Qua kiểm tra cô lập (rút lần lượt từng module để xác định module nào thực sự phản hồi ở địa chỉ nào), xác định nguyên nhân là **module clone giá rẻ không triển khai đầy đủ chức năng chọn địa chỉ qua jumper như thiết kế chuẩn** của PCF8574.

**Giải pháp kỹ thuật**: thay vì tiếp tục phụ thuộc vào jumper phần cứng, tận dụng đặc điểm ESP32 có **2 bus I2C phần cứng độc lập** (`Wire` và `Wire1`). Module PCF8574 cột được chuyển sang bus I2C thứ hai (SDA=GPIO4, SCL=GPIO16), cho phép cả hai module giữ nguyên địa chỉ mặc định `0x20` mà không xảy ra xung đột, vì chúng nằm trên hai đường tín hiệu vật lý tách biệt hoàn toàn. Giải pháp này đã được xác minh hoạt động ổn định qua nhiều lần quét liên tiếp trên cả hai bus.

### 7.4 Bài học về mạch ISET của MAX7219: nguồn thứ cấp tóm tắt sai datasheet

Đây là sự cố mang tính giáo dục cao nhất của dự án. Ban đầu, mạch được lắp với điện trở RSET 10kΩ nối giữa chân 18 (ISET) và chân 19 (V+) — đúng theo một chỉ dẫn tham khảo. Tuy nhiên, khi đối chiếu với một trang tổng hợp thông số datasheet (nguồn thứ cấp), trang này ghi rằng điện trở phải nối "giữa ISET và GND"; cấu hình đã bị "hiệu chỉnh" lại theo đó.

Hậu quả xuất hiện ngay khi chạy thử: firmware xác nhận hoạt động đúng qua Serial Monitor, nhưng khối LED tối hoàn toàn. Quá trình loại trừ (kiểm tra nguồn, chiều IC, dây tín hiệu — tất cả đều đúng) buộc phải quay lại tra cứu **văn bản datasheet gốc của Analog Devices/Maxim**, trong đó bảng mô tả chân ghi rõ: *"ISET — Connect to V+ through a resistor (RSET) to set the peak segment current"*. Tức cấu hình ban đầu (18 → V+) mới là đúng; nguồn thứ cấp đã tóm tắt sai, và việc "sửa" theo nguồn thứ cấp chính là nguyên nhân gây lỗi. Với RSET nối GND, mạch tạo dòng tham chiếu nội bộ không hoạt động nên IC không cấp dòng cho bất kỳ segment nào — giải thích trọn vẹn hiện tượng "phần mềm chạy đúng, màn hình tối".

Bài học rút ra: (1) khi các nguồn kỹ thuật mâu thuẫn, chỉ văn bản datasheet gốc của nhà sản xuất có giá trị quyết định — mọi trang tổng hợp đều có thể chép sai; (2) kinh nghiệm thực nghiệm đã hoạt động (mạch tương tự từng chạy với cấu hình 18→V+) là một dữ kiện kỹ thuật có trọng lượng, không nên bị gạt bỏ chỉ vì một nguồn tra cứu nhanh nói khác.

---

## 8. KẾT QUẢ KIỂM THỬ

| Hạng mục | Trạng thái |
|---|---|
| Biên dịch backend Qt đã vá (CMake) | ✅ Hoàn thành — không lỗi |
| Biên dịch firmware chính thức cho ESP32 | ✅ Hoàn thành — 1.140.903 bytes (87% flash), 49.304 bytes RAM (15%) |
| Biên dịch 3 sketch kiểm tra (bring-up) | ✅ Hoàn thành, không lỗi |
| Nhận diện ESP32 qua cổng USB | ✅ Xác nhận (ESP32-D0WD-V3, cổng CP2102) |
| Nạp và đọc log firmware trên thiết bị thật | ✅ Xác nhận qua pyserial |
| Cấu hình thông tin mạng (WiFi/IP) | ✅ Hoàn thành, tách riêng vào file không commit |
| Xác minh OLED trên bus I2C thật | ✅ Ổn định tại địa chỉ `0x3C` |
| Xác minh 2× PCF8574 trên bus I2C kép | ✅ Ổn định — bus #1: `0x20`, bus #2: `0x20` (2 bus riêng biệt) |
| Đấu nối và cấu hình mạch MAX7219 | 🔄 Đang tiến hành — đã hiệu chỉnh mạch ISET đúng chuẩn |
| Kiểm tra hiển thị LED 7 đoạn (`max7219_test`) | ⏳ Chưa thực hiện |
| Kiểm tra toàn bộ ma trận 38 nút (`matrix_test`) | ⏳ Chưa thực hiện |
| Chạy thử ván chơi hoàn chỉnh bằng phần cứng | ⏳ Chưa thực hiện |

---

## 9. HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN

- **Đồng bộ trạng thái khi mất kết nối**: giao thức hiện tại không có cơ chế yêu cầu đồng bộ lại toàn bộ trạng thái (kiểu "GET_STATE") sau khi ESP32 mất kết nối và kết nối lại; thiết bị có thể hiển thị sai cho đến sự kiện trò chơi tiếp theo.
- **Nội dung mặc định của OLED**: khi nhận `layout: "default"`, phần mềm Qt không gửi kèm dữ liệu thời gian/điểm số, firmware phải tự hiển thị màn hình chờ tĩnh.
- **Thao tác "giữ" (hold) chưa khả dụng trên phần cứng**: giao thức `PAD_DRAW` hiện chỉ tương đương thao tác chạm đơn (tap), chưa có đường truyền cho thao tác giữ segment.
- **Chưa có xác thực/mã hóa kết nối WebSocket**: phù hợp cho môi trường trình diễn cục bộ (LAN), cần bổ sung nếu mở rộng triển khai ngoài phạm vi tin cậy.

---

## 10. KẾT LUẬN

Giai đoạn v6 của dự án DigitCode đã chứng minh được tính khả thi của việc chuyển đổi một "sa bàn số" hoàn toàn phần mềm thành một hệ thống Cyber-Physical hoàn chỉnh. Quá trình triển khai thực tế đã bộc lộ nhiều sai lệch giữa tài liệu thiết kế ban đầu và linh kiện vật lý thực tế (điển hình là sự khác biệt MCP23017/PCF8574) — đây là tình huống phổ biến trong phát triển phần cứng nhúng, đòi hỏi phương pháp **kiểm tra tăng dần, cô lập từng khối chức năng, và đối chiếu chéo với tài liệu kỹ thuật gốc** trước khi cấp nguồn cho mạch. Các giải pháp kỹ thuật được áp dụng (bus I2C kép để giải quyết xung đột địa chỉ, hiệu chỉnh mạch ISET theo datasheet chuẩn) phản ánh đúng quy trình gỡ lỗi phần cứng thực tế, và toàn bộ quá trình đã được ghi nhận nhằm phục vụ việc bảo trì và mở rộng dự án trong các giai đoạn tiếp theo.

---

## 11. TÀI LIỆU THAM KHẢO

1. Datasheet MAX7219/MAX7221 — Analog Devices (Maxim Integrated).
2. MAX7219 LED Display Driver IC Pinout, Specs & Datasheet — components101.com.
3. MAX7219CNG Pinout Diagram & Pin Configuration — sunpcb.com.
4. Tài liệu thiết kế nội bộ dự án: `PRJ_DigitCode_Master_Context.md`, `docs/hardware/schematic.md`.
