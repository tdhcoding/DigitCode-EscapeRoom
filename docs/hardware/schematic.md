# DigitCode v6 — Sơ đồ đấu nối phần cứng (Pin Map)

Bảng này là **nguồn chân lý chính xác** để đấu dây thật. Xem thêm bản vẽ trực quan tại `schematic.html`.

## 1. Kiến trúc bus

- **I2C dùng chung** (SDA=GPIO21, SCL=GPIO22) cho **OLED SSD1306** (địa chỉ `0x3C`) và **2 module PCF8574** (mỗi con chỉ có 8 chân GPIO — dùng linh kiện thật đang có thay vì MCP23017 16 chân như tài liệu gốc; 1 module làm HÀNG, 1 module làm CỘT của ma trận phím, phải đặt ở **2 địa chỉ I2C khác nhau** qua jumper A0-A2, thường trong dải `0x20-0x27`).
- **3 dây kiểu SPI bit-bang** cho **MAX7219**: DIN=GPIO23, CLK=GPIO18, CS=GPIO5.
- Toàn bộ 38 nút bấm đi qua 2 module PCF8574 trên bus I2C — không chiếm thêm GPIO nào của ESP32, không đụng chân strapping (0,2,12,15) hay chân flash (6-11).
- PCF8574 là chân **quasi-bidirectional** (không có thanh ghi hướng chân riêng như MCP23017): ghi `1` = chân ở trạng thái "đọc" (pull-up yếu ~100µA, cho phép bên ngoài kéo xuống LOW để phát hiện nhấn nút), ghi `0` = chân xuất LOW mạnh. Đây chính là cơ chế dùng để quét ma trận (hàng ghi LOW lần lượt, cột luôn ghi `1` rồi đọc lại).

## 2. Bảng pin tổng hợp (ESP32 DevKit)

| Tín hiệu | ESP32 GPIO | Đích | Ghi chú |
|---|---|---|---|
| I2C SDA | 21 | OLED + 2× PCF8574 | Dùng chung 1 bus |
| I2C SCL | 22 | OLED + 2× PCF8574 | Dùng chung 1 bus |
| MAX7219 DIN | 23 | MAX7219 | |
| MAX7219 CLK | 18 | MAX7219 | |
| MAX7219 CS | 5 | MAX7219 | |
| Nguồn MAX7219 | **5V/VIN** | MAX7219 VCC | KHÔNG lấy từ chân 3.3V (xem cảnh báo #2) |
| Nguồn OLED, PCF8574 ×2 | 3.3V | VCC | |
| GND | — | Tất cả | Dùng chung 1 rail cho toàn bộ breadboard |
| PCF8574 #1 (HÀNG) | — | addr `0x20` (mặc định, jumper A0-A2 hở) | Xác nhận qua i2c_scanner |
| PCF8574 #2 (CỘT) | — | addr `0x21` (đổi 1 jumper, vd A0) | Phải KHÁC địa chỉ #1 |

## 3. Ma trận phím 6 hàng × 7 cột (2× PCF8574, mỗi con 8 chân)

| Hàng | Chân PCF8574 #1 (HÀNG) | Cột 0 | Cột 1 | Cột 2 | Cột 3 | Cột 4 | Cột 5 | Cột 6 |
|---|---|---|---|---|---|---|---|---|
| 0 | P0 | Q1 | Q2 | Q3 | Q4 | VERIFY | PAUSE | — |
| 1 | P1 | T | U | V | W | X | Y | — |
| 2 | P2 | a | b | c | d | e | f | g |
| 3 | P3 | A | B | C | D | E | F | G |
| 4 | P4 | H | I | J | K | L | M | N |
| 5 | P5 | O | P | Q | R | S | — | — |

Cột: **PCF8574 #2**, chân P0-P6 (input pull-up nội tại kiểu quasi-bidirectional). `P7` của cả 2 module dự phòng, không dùng (mỗi module chỉ dùng 6-7/8 chân).
Tổng: 6+6+7+7+7+5 = **38 nút** — khớp chính xác số lượng trong tài liệu gốc. Còn dư 3 module PCF8574 làm dự phòng/mở rộng sau này.

## 3b. Khối LED 7 đoạn: MAX7219 (IC trần DIP-24) ↔ 6× LED 5161AS

MAX7219 là IC trần nên cần mạch phụ trợ: **trở 10kΩ (RSET) nối chân 18 (ISET) → chân 19 (V+)** — theo đúng datasheet gốc Analog Devices/Maxim: *"ISET: Connect to V+ through a resistor (RSET) to set the peak segment current"*. Kèm tụ lọc 100nF giữa V+ và GND (khuyến nghị, có thể bổ sung sau). Lưu ý: một số trang tổng hợp datasheet (vd components101) ghi sai là nối GND — nối GND sẽ làm màn hình tối hoàn toàn (đã kiểm chứng thực tế trên mạch của dự án này).

### MAX7219 ↔ ESP32

| Chân MAX7219 | Nối tới |
|---|---|
| 1 (DIN) | GPIO23 |
| 13 (CLK) | GPIO18 |
| 12 (LOAD/CS) | GPIO5 |
| 19 (V+) | 5V/VIN |
| 4 **và** 9 (GND) | GND chung — nối cả 2 chân |
| 24 (DOUT) | Bỏ trống |

### Bus segment (dùng CHUNG cho cả 6 LED — kiểu multiplexing)

| Chân MAX7219 | Segment | Chân LED 5161AS |
|---|---|---|
| 14 (SEG A) | a | 10 |
| 16 (SEG B) | b | 9 |
| 20 (SEG C) | c | 4 |
| 23 (SEG D) | d | 2 |
| 21 (SEG E) | e | 1 |
| 15 (SEG F) | f | 7 |
| 17 (SEG G) | g | 6 |
| 22 (SEG DP) | dp | 5 — **có dùng**: DP của LED đang chọn để vẽ sẽ nhấp nháy (đèn báo Drawing Pad, firmware quản lý cục bộ) |

### Đường COM riêng từng LED (chọn LED đang quét)

Mỗi LED chập 2 chân COM (chân 3 + 8) rồi nối về đúng 1 chân DIG:

| Chân MAX7219 | LED |
|---|---|
| 2 (DIG0) | T |
| 11 (DIG1) | U |
| 6 (DIG2) | V |
| 7 (DIG3) | W |
| 3 (DIG4) | X |
| 10 (DIG5) | Y |

## 4. ⚠️ Cảnh báo rủi ro đấu sai (đọc trước khi cấp nguồn)

1. **MAX7219 lệch mức logic**: chip cần VCC 4-5.5V, ESP32 xuất tín hiệu 3.3V ở DIN/CLK/CS — dưới ngưỡng HIGH lý thuyết. Giữ dây DIN/CLK/CS ngắn (<20cm); nếu LED nhòe/lỗi, thêm level-shifter 3.3V↔5V.
2. **[NGHIÊM TRỌNG] Cấp nguồn MAX7219 từ chân 3.3V**: chip không đủ điện áp hoạt động (<4V min). Bắt buộc lấy 5V từ VIN/5V.
3. **2 module PCF8574 trùng địa chỉ I2C** (hoặc jumper A0-A2 tiếp xúc lỏng gây địa chỉ nhảy loạn): phải chỉnh 1 trong 2 module sang địa chỉ khác (đổi jumper, ví dụ A0), rồi chạy `i2c_scanner` nhiều lần liên tiếp xác nhận ổn định — nếu địa chỉ nhảy qua lại giữa các lần quét, dây/jumper A0-A2 đang tiếp xúc lỏng, cần cắm chắc lại.
4. **Thiếu GND chung**: I2C/tín hiệu số lỗi ngẫu nhiên hoặc không chạy nếu các module không chia sẻ 1 rail GND. Đo thông mạch trước khi cấp nguồn.
5. **[NGHIÊM TRỌNG] Đấu ngược VCC/GND** trên OLED hoặc MCP23017: có thể cháy chip vĩnh viễn. Đối chiếu ký hiệu in trên module trước khi cắm.
6. **Ngắn mạch giữa hàng/cột ma trận** do lệch chân breadboard: có thể hỏng chân MCP23017 hoặc gây "phantom press". Đấu và test từng hàng một qua Serial Monitor.
7. **Nguồn USB không đủ dòng**: có thể gây sụt áp, ESP32 tự reset giữa ván chơi. Dùng cổng sạc 5V/1A trở lên.
8. **Trở kéo I2C**: hầu hết module rời đã có sẵn; nếu dùng IC trần cần thêm trở 4.7kΩ từ SDA/SCL lên 3.3V.
9. **Trở ISET của MAX7219 nối sai xuống GND**: theo datasheet GỐC (Analog Devices/Maxim), trở RSET phải nối **chân 18 → chân 19 (V+)**. Nối nhầm xuống GND làm mạch tạo dòng tham chiếu không hoạt động → màn hình tối hoàn toàn dù firmware chạy đúng (thường không hỏng chip, nhưng mất thời gian gỡ lỗi). Bài học thực tế của dự án: trang tổng hợp thứ cấp có thể tóm tắt sai datasheet — khi mâu thuẫn, chỉ tin văn bản datasheet gốc của nhà sản xuất.
10. **Cắm ngược chiều IC DIP-24**: dấu khuyết/chấm tròn trên thân IC đánh dấu phía chân 1. Cắm xoay 180° sẽ đặt V+ chồng lên GND, dễ cháy IC ngay khi cấp điện.

## 5. Chiến lược bring-up (bắt lỗi sớm thay vì đấu-xong-chạy-luôn)

1. `firmware/tools/i2c_scanner` — xác nhận 2 địa chỉ I2C (0x3C, 0x20) hiện diện.
2. `firmware/tools/max7219_test` — xác nhận đúng LED/segment sáng đúng vị trí.
3. `firmware/tools/matrix_test` — xác nhận cả 38 nút cho đúng nhãn qua Serial Monitor.
4. `firmware/DigitCodeFirmware` — firmware chính thức, chỉ chạy sau khi 3 bước trên đều OK.
