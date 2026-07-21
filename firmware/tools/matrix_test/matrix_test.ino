/*
 * Bring-up test #3: Ma trận 38 nút bấm (2x PCF8574: 1 hàng + 1 cột)
 *
 * Chạy SAU khi i2c_scanner đã OK. Quét ma trận 6 hàng x 7 cột, in ra Serial
 * nhãn logic của nút vừa nhấn. Bấm LẦN LƯỢT từng nút trong 38 nút và xác
 * nhận Serial Monitor in ĐÚNG nhãn mong đợi trước khi chuyển sang firmware
 * chính thức — đây là bước quan trọng nhất để bắt lỗi đấu chéo dây hàng/cột.
 *
 * !!! Sửa ROW_PCF_ADDR / COL_PCF_ADDR bên dưới cho khớp địa chỉ thật đã
 *     xác nhận qua i2c_scanner (2 module PCF8574 phải khác địa chỉ nhau,
 *     chỉnh jumper A0-A2 trên board nếu đang trùng) !!!
 */
#include <Wire.h>
#include <Adafruit_PCF8574.h>

#define PIN_I2C_SDA 21
#define PIN_I2C_SCL 22
#define PIN_I2C2_SDA 4
#define PIN_I2C2_SCL 16

#define ROW_PCF_ADDR 0x20
#define COL_PCF_ADDR 0x20

#define ROW_COUNT 6
#define COL_COUNT 7
static const uint8_t ROW_PINS[ROW_COUNT] = {0, 1, 2, 3, 4, 5};    // P0-P5 module HÀNG
static const uint8_t COL_PINS[COL_COUNT] = {0, 1, 2, 3, 4, 5, 6}; // P0-P6 module CỘT

// Nhãn mong đợi tại từng ô — dùng để in ra Serial cho người đấu dây đối chiếu.
static const char* LABELS[ROW_COUNT][COL_COUNT] = {
    {"BTN_Q1", "BTN_Q2", "BTN_Q3", "BTN_Q4", "BTN_VERIFY", "BTN_NEWGAME", "-"},
    {"T", "U", "V", "W", "X", "Y", "-"},
    {"DrawPad-A", "DrawPad-B", "DrawPad-C", "DrawPad-D", "DrawPad-E", "DrawPad-F", "DrawPad-G"},
    {"A", "B", "C", "D", "E", "F", "G"},
    {"H", "I", "J", "K", "L", "M", "N"},
    {"O", "P", "Q", "R", "S", "-", "-"},
};

Adafruit_PCF8574 pcfRows;
Adafruit_PCF8574 pcfCols;
TwoWire WireCols = TwoWire(1);
static bool prevPressed[ROW_COUNT][COL_COUNT] = {false};

void setup() {
    Serial.begin(115200);
    delay(500);
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    WireCols.begin(PIN_I2C2_SDA, PIN_I2C2_SCL);

    bool okRows = pcfRows.begin(ROW_PCF_ADDR, &Wire);
    bool okCols = pcfCols.begin(COL_PCF_ADDR, &WireCols);
    if (!okRows || !okCols) {
        Serial.println("[FATAL] Khong tim thay du 2 module PCF8574. Dung lai, kiem tra day I2C va dia chi truoc.");
        while (1) delay(1000);
    }

    for (int i = 0; i < ROW_COUNT; i++) {
        pcfRows.pinMode(ROW_PINS[i], OUTPUT);
        pcfRows.digitalWrite(ROW_PINS[i], HIGH);
    }
    for (int i = 0; i < COL_COUNT; i++) {
        pcfCols.pinMode(COL_PINS[i], INPUT_PULLUP);
    }

    Serial.println("[MATRIX TEST] San sang. Bam LAN LUOT tung nut trong 38 nut va doi chieu nhan in ra.");
}

void loop() {
    for (int r = 0; r < ROW_COUNT; r++) {
        for (int rr = 0; rr < ROW_COUNT; rr++) {
            pcfRows.digitalWrite(ROW_PINS[rr], rr == r ? LOW : HIGH);
        }
        delayMicroseconds(50);

        for (int c = 0; c < COL_COUNT; c++) {
            if (strcmp(LABELS[r][c], "-") == 0) continue;

            bool pressed = (pcfCols.digitalRead(COL_PINS[c]) == LOW);
            if (pressed && !prevPressed[r][c]) {
                Serial.printf("Nhan nut: hang=%d cot=%d  ->  nhan mong doi: %s\n", r, c, LABELS[r][c]);
            }
            prevPressed[r][c] = pressed;
        }
    }
    for (int rr = 0; rr < ROW_COUNT; rr++) {
        pcfRows.digitalWrite(ROW_PINS[rr], HIGH);
    }
    delay(15);
}
