/*
 * DigitCode v6 — Firmware ESP32
 *
 * Cầu nối phần cứng thật <-> Qt WebSocket server (backend/hardwareserver.cpp, port 8080).
 * Giao thức JSON được suy ngược 1:1 từ backend hiện có — xem docs/hardware/schematic.md.
 *
 * Board: ESP32 DevKit (Arduino core, không dùng ESP-IDF thuần)
 * Thư viện cần: WebSockets (links2004), ArduinoJson (7.x), Adafruit PCF8574 (x2 module: hàng + cột),
 *               LedControl (wayoda), Adafruit SSD1306 + Adafruit GFX Library
 */

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_PCF8574.h>
#include <LedControl.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// WIFI_SSID / WIFI_PASSWORD / QT_SERVER_IP / QT_SERVER_PORT nằm trong secrets.h
// (không commit — xem secrets.h.example để biết cách tạo file này).
#include "secrets.h"

// --------- Pin map (khớp docs/hardware/schematic.md) ---------
#define PIN_I2C_SDA   21   // Bus I2C #1 (Wire): OLED + PCF8574 HÀNG
#define PIN_I2C_SCL   22
#define PIN_I2C2_SDA  4    // Bus I2C #2 (Wire1): PCF8574 CỘT — bus riêng để tránh xung đột địa chỉ
#define PIN_I2C2_SCL  16
#define PIN_MAX_DIN   23
#define PIN_MAX_CLK   18
#define PIN_MAX_CS    5

// Ma trận phím dùng 2 module PCF8574 riêng biệt (mỗi con chỉ có 8 chân GPIO,
// không đủ 13 chân như 1 con MCP23017) - 1 con làm HÀNG, 1 con làm CỘT.
// Jumper địa chỉ A0-A2 trên module clone giá rẻ không đáng tin cậy (đã xác nhận
// qua thực nghiệm), nên thay vì đổi địa chỉ, PCF8574 CỘT được đặt trên bus I2C
// thứ 2 (Wire1, chân riêng) — cả 2 module giữ NGUYÊN địa chỉ mặc định 0x20.
#define ROW_PCF_ADDR  0x20
#define COL_PCF_ADDR  0x20
#define OLED_ADDR     0x3C
#define OLED_WIDTH    128
#define OLED_HEIGHT   64

#define ROW_COUNT 6
#define COL_COUNT 7
static const uint8_t ROW_PINS[ROW_COUNT] = {0, 1, 2, 3, 4, 5};    // P0-P5 trên module HÀNG
static const uint8_t COL_PINS[COL_COUNT] = {0, 1, 2, 3, 4, 5, 6}; // P0-P6 trên module CỘT

// --------- Thiết kế ma trận 6x7 (38 nút, xem Phần 2.2 kế hoạch) ---------
enum CellType { CELL_NONE, CELL_ACTION, CELL_TARGET, CELL_DRAW };

struct MatrixCell {
    CellType type;
    const char* label; // dùng cho CELL_ACTION / CELL_TARGET
    int segIdx;         // dùng cho CELL_DRAW (0=A..6=G, khớp SEG_MAP backend)
};

// Hàng 0: Q1-Q4, VERIFY, NEW GAME (giữ 5s mới kích hoạt - chống bấm nhầm)
// Hàng 1: T-Y (digit select)
// Hàng 2: Drawing Pad a-g (segIdx 0-6)
// Hàng 3-5: A-S (logic buttons, 19 nút)
static const MatrixCell MATRIX[ROW_COUNT][COL_COUNT] = {
    { {CELL_ACTION,"BTN_Q1",0}, {CELL_ACTION,"BTN_Q2",0}, {CELL_ACTION,"BTN_Q3",0}, {CELL_ACTION,"BTN_Q4",0}, {CELL_ACTION,"BTN_VERIFY",0}, {CELL_ACTION,"BTN_NEWGAME",0}, {CELL_NONE,nullptr,0} },
    { {CELL_TARGET,"T",0}, {CELL_TARGET,"U",0}, {CELL_TARGET,"V",0}, {CELL_TARGET,"W",0}, {CELL_TARGET,"X",0}, {CELL_TARGET,"Y",0}, {CELL_NONE,nullptr,0} },
    { {CELL_DRAW,nullptr,0}, {CELL_DRAW,nullptr,1}, {CELL_DRAW,nullptr,2}, {CELL_DRAW,nullptr,3}, {CELL_DRAW,nullptr,4}, {CELL_DRAW,nullptr,5}, {CELL_DRAW,nullptr,6} },
    { {CELL_ACTION,"A",0}, {CELL_ACTION,"B",0}, {CELL_ACTION,"C",0}, {CELL_ACTION,"D",0}, {CELL_ACTION,"E",0}, {CELL_ACTION,"F",0}, {CELL_ACTION,"G",0} },
    { {CELL_ACTION,"H",0}, {CELL_ACTION,"I",0}, {CELL_ACTION,"J",0}, {CELL_ACTION,"K",0}, {CELL_ACTION,"L",0}, {CELL_ACTION,"M",0}, {CELL_ACTION,"N",0} },
    { {CELL_ACTION,"O",0}, {CELL_ACTION,"P",0}, {CELL_ACTION,"Q",0}, {CELL_ACTION,"R",0}, {CELL_ACTION,"S",0}, {CELL_NONE,nullptr,0}, {CELL_NONE,nullptr,0} },
};

static bool prevPressed[ROW_COUNT][COL_COUNT] = {false};
static unsigned long lastScanMs = 0;
const unsigned long SCAN_INTERVAL_MS = 20; // debounce đơn giản: chỉ xét lại mỗi 20ms

// NEW GAME là hành động hủy diệt (xóa ván đang chơi) -> yêu cầu giữ 5 giây
const unsigned long NEWGAME_HOLD_MS = 5000;
static unsigned long newGameHoldStart = 0;
static bool newGameSent = false;

// Độ sáng thấp (2/15): mạch chưa có tụ lọc nguồn, sáng nhiều vạch cùng lúc ở độ
// sáng cao gây sụt áp -> MAX7219 + ESP32 reset (đã gặp thực tế khi bring-up).
// Kèm cơ chế tự phục hồi: ghi lại thanh ghi điều khiển định kỳ (xem loop).
#define LED_INTENSITY 2
const unsigned long MAX_REINIT_INTERVAL_MS = 2000;
static unsigned long lastMaxReinitMs = 0;

Adafruit_PCF8574 pcfRows;
Adafruit_PCF8574 pcfCols;
TwoWire WireCols = TwoWire(1); // bus I2C phần cứng thứ 2 của ESP32, dành riêng cho PCF8574 CỘT
LedControl lc(PIN_MAX_DIN, PIN_MAX_CLK, PIN_MAX_CS, 1);
Adafruit_SSD1306 oled(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
WebSocketsClient webSocket;
bool wsConnected = false;

// ======================= OLED =======================
void oledShowText(const String& line1, const String& line2) {
    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);
    oled.setCursor(0, 0);
    oled.println(line1);
    oled.setCursor(0, 16);
    oled.println(line2);
    oled.display();
}

// --- Màn hình game trên OLED: bố cục giống OLED ảo trên app ---
// Dòng 1: TIME mm:ss + PTS (từ gói STATS backend đẩy mỗi giây)
// Dòng 2-3: thông báo game (từ gói OLED)
static int statTimeSec = 0;
static int statPoints = 100;
static String gameMsg1 = "Time is ticking...";
static String gameMsg2 = "";

void renderGameOled() {
    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);

    char top[26];
    snprintf(top, sizeof(top), "TIME %02d:%02d   PTS %d",
             statTimeSec / 60, statTimeSec % 60, statPoints);
    oled.setCursor(0, 0);
    oled.println(top);
    oled.drawFastHLine(0, 11, 128, SSD1306_WHITE);

    oled.setCursor(0, 20);
    oled.println(gameMsg1);
    oled.setCursor(0, 36);
    oled.println(gameMsg2);
    oled.display();
}

// ======================= MAX7219 (khối LED 7 đoạn) =======================
// segIdx của project: 0=A,1=B,2=C,3=D,4=E,5=F,6=G (khớp SEG_MAP trong gameboard.cpp)
// LedControl.setLed(addr,digit,column,state): column=0 là DP,
// column 1..7 tương ứng bit6..bit0 của thanh ghi MAX7219 = segment A..G.
// => LedControl column = segIdx + 1
void setSegment(int ledIdx, int segIdx, int val) {
    if (ledIdx < 0 || ledIdx > 5) return;
    if (segIdx < 0 || segIdx > 6) return;
    lc.setLed(0, ledIdx, segIdx + 1, val != 0);
}

// --- Đèn báo digit đang chọn (Drawing Pad): DP của LED đang chọn nhấp nháy ---
// ESP32 là nơi phát PAD_SELECT nên tự biết digit nào đang được chọn -> quản lý
// nhấp nháy cục bộ, không cần thêm message từ Qt. DP (column 0) không bao giờ
// bị message DRAW của Qt đụng tới (DRAW chỉ mang segIdx 0-6 -> column 1-7).
static int activeDigit = -1;
static bool dpBlinkState = false;
static unsigned long lastBlinkMs = 0;
const unsigned long DP_BLINK_INTERVAL_MS = 400;

void selectActiveDigit(int ledIdx) {
    if (activeDigit == ledIdx) return;
    if (activeDigit >= 0) {
        lc.setLed(0, activeDigit, 0, false); // tắt DP của LED chọn trước đó
    }
    activeDigit = ledIdx;
    dpBlinkState = true;
    lastBlinkMs = millis();
    if (activeDigit >= 0) {
        lc.setLed(0, activeDigit, 0, true);
    }
}

void updateDpBlink() {
    if (activeDigit < 0) return;
    unsigned long now = millis();
    if (now - lastBlinkMs >= DP_BLINK_INTERVAL_MS) {
        lastBlinkMs = now;
        dpBlinkState = !dpBlinkState;
        lc.setLed(0, activeDigit, 0, dpBlinkState);
    }
}

// ======================= Gửi lên Qt =======================
void sendJson(JsonDocument& doc) {
    String out;
    serializeJson(doc, out);
    webSocket.sendTXT(out);
}

void sendAction(const char* btnId) {
    JsonDocument doc;
    doc["type"] = "ACTION";
    doc["btnId"] = btnId;
    sendJson(doc);
}

void sendPadSelect(const char* label) {
    JsonDocument doc;
    doc["type"] = "PAD_SELECT";
    doc["label"] = label;
    sendJson(doc);
}

void sendPadDraw(int segIdx) {
    JsonDocument doc;
    doc["type"] = "PAD_DRAW";
    doc["segIdx"] = segIdx;
    sendJson(doc);
}

// ======================= Nhận từ Qt =======================
void handleInboundMessage(const char* payload, size_t length) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, payload, length);
    if (err) return;

    const char* type = doc["type"] | "";

    if (strcmp(type, "DRAW") == 0) {
        int ledIdx = doc["ledIdx"] | -1;
        int segIdx = doc["segIdx"] | -1;
        int val = doc["val"] | 0;
        setSegment(ledIdx, segIdx, val);
    } else if (strcmp(type, "OLED") == 0) {
        const char* layout = doc["layout"] | "default";
        if (strcmp(layout, "text") == 0) {
            String line1 = doc["line1"] | "";
            String line2 = doc["line2"] | "";
            // Backend gửi placeholder "Time: [mm:ss]" khi bắt đầu ván — QML thay
            // bằng câu mặc định, firmware phải làm y hệt để 2 màn hình khớp nhau.
            if (line1.indexOf("[mm:ss]") >= 0) {
                gameMsg1 = "Time is ticking...";
                gameMsg2 = "";
            } else {
                gameMsg1 = line1;
                gameMsg2 = line2;
            }
        } else {
            gameMsg1 = "Time is ticking...";
            gameMsg2 = "";
        }
        renderGameOled();
    } else if (strcmp(type, "STATS") == 0) {
        // Thời gian/điểm backend đẩy mỗi giây — vẽ lại dòng trạng thái
        statTimeSec = doc["time"] | 0;
        statPoints = doc["points"] | 0;
        renderGameOled();
    }
    // type == "SYSTEM" (welcome) -> không cần xử lý gì thêm
}

// ======================= WebSocket callback =======================
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_CONNECTED:
            wsConnected = true;
            oledShowText("Connected", "Waiting for game...");
            break;
        case WStype_DISCONNECTED:
            wsConnected = false;
            oledShowText("Disconnected", "Reconnecting...");
            break;
        case WStype_TEXT:
            handleInboundMessage((const char*)payload, length);
            break;
        default:
            break;
    }
}

// ======================= Quét ma trận phím =======================
void scanMatrix() {
    for (int r = 0; r < ROW_COUNT; r++) {
        // Kéo hàng đang quét xuống LOW, các hàng khác giữ HIGH
        for (int rr = 0; rr < ROW_COUNT; rr++) {
            pcfRows.digitalWrite(ROW_PINS[rr], rr == r ? LOW : HIGH);
        }
        delayMicroseconds(50); // chờ ổn định tín hiệu trước khi đọc cột

        for (int c = 0; c < COL_COUNT; c++) {
            const MatrixCell& cell = MATRIX[r][c];
            if (cell.type == CELL_NONE) continue;

            bool pressed = (pcfCols.digitalRead(COL_PINS[c]) == LOW);

            // NEW GAME: không gửi theo cạnh nhấn mà phải GIỮ đủ NEWGAME_HOLD_MS
            if (cell.type == CELL_ACTION && strcmp(cell.label, "BTN_NEWGAME") == 0) {
                if (pressed && !prevPressed[r][c]) {
                    newGameHoldStart = millis();
                    newGameSent = false;
                }
                if (pressed && prevPressed[r][c] && !newGameSent
                    && millis() - newGameHoldStart >= NEWGAME_HOLD_MS) {
                    sendAction("BTN_NEWGAME");
                    newGameSent = true;
                }
                prevPressed[r][c] = pressed;
                continue;
            }

            // Chỉ xử lý khi vừa chuyển từ nhả -> nhấn (press edge), tránh gửi lặp
            if (pressed && !prevPressed[r][c]) {
                switch (cell.type) {
                    case CELL_ACTION:
                        sendAction(cell.label);
                        break;
                    case CELL_TARGET:
                        // T-Y có 2 vai trò độc lập trong backend (chọn digit vẽ / đáp án Q1-Q2)
                        // -> gửi cả 2 message, backend tự bỏ qua nhánh không áp dụng.
                        sendPadSelect(cell.label);
                        sendAction(cell.label);
                        selectActiveDigit(cell.label[0] - 'T'); // DP của LED đang chọn sẽ nhấp nháy
                        break;
                    case CELL_DRAW:
                        sendPadDraw(cell.segIdx);
                        break;
                    default:
                        break;
                }
            }
            prevPressed[r][c] = pressed;
        }
    }
    // Thả hết các hàng về HIGH sau khi quét xong
    for (int rr = 0; rr < ROW_COUNT; rr++) {
        pcfRows.digitalWrite(ROW_PINS[rr], HIGH);
    }
}

// ======================= setup / loop =======================
void setup() {
    Serial.begin(115200);

    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);       // Bus #1: OLED + PCF8574 hàng
    WireCols.begin(PIN_I2C2_SDA, PIN_I2C2_SCL); // Bus #2: PCF8574 cột (bus riêng)

    // --- OLED ---
    if (!oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
        Serial.println("[FATAL] Khong tim thay OLED tai dia chi 0x3C - kiem tra day I2C");
    }
    oledShowText("Booting...", "");

    // --- 2x PCF8574 (1 cho hàng trên bus #1, 1 cho cột trên bus #2) ---
    if (!pcfRows.begin(ROW_PCF_ADDR, &Wire)) {
        Serial.println("[FATAL] Khong tim thay PCF8574 (HANG) tren bus I2C #1 - kiem tra day SDA(21)/SCL(22)");
    }
    if (!pcfCols.begin(COL_PCF_ADDR, &WireCols)) {
        Serial.println("[FATAL] Khong tim thay PCF8574 (COT) tren bus I2C #2 - kiem tra day SDA(4)/SCL(16)");
    }
    for (int i = 0; i < ROW_COUNT; i++) {
        pcfRows.pinMode(ROW_PINS[i], OUTPUT);
        pcfRows.digitalWrite(ROW_PINS[i], HIGH);
    }
    for (int i = 0; i < COL_COUNT; i++) {
        pcfCols.pinMode(COL_PINS[i], INPUT_PULLUP);
    }

    // --- MAX7219 ---
    lc.shutdown(0, false);
    lc.setIntensity(0, LED_INTENSITY);
    lc.clearDisplay(0);

    // --- WiFi ---
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    oledShowText("Connecting WiFi", WIFI_SSID);
    while (WiFi.status() != WL_CONNECTED) {
        delay(300);
        Serial.print(".");
    }
    Serial.println();
    Serial.print("WiFi OK, IP: ");
    Serial.println(WiFi.localIP());

    // --- WebSocket client ---
    webSocket.begin(QT_SERVER_IP, QT_SERVER_PORT, "/");
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(3000);
}

void loop() {
    webSocket.loop();

    unsigned long now = millis();
    if (now - lastScanMs >= SCAN_INTERVAL_MS) {
        lastScanMs = now;
        scanMatrix();
    }

    updateDpBlink(); // nhấp nháy DP của LED đang được chọn để vẽ

    // Tự phục hồi MAX7219: nếu chip bị brownout reset, thanh ghi về mặc định:
    // shutdown BẬT (tối hết) và scan limit = chỉ quét digit 0 (chỉ LED T sáng).
    // Ghi lại cả 3 thanh ghi điều khiển mỗi 2s (không đụng dữ liệu segment nên
    // không gây chớp).
    if (now - lastMaxReinitMs >= MAX_REINIT_INTERVAL_MS) {
        lastMaxReinitMs = now;
        lc.shutdown(0, false);
        lc.setScanLimit(0, 7);
        lc.setIntensity(0, LED_INTENSITY);
    }
}
