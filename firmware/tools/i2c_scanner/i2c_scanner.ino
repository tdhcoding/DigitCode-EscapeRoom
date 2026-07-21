/*
 * Bring-up test #1: I2C Scanner (2 bus)
 *
 * Chạy TRƯỚC firmware chính. Xác nhận:
 * - Bus #1 (SDA=21,SCL=22): OLED (mong đợi 0x3C) + PCF8574 HÀNG (mong đợi 0x20)
 * - Bus #2 (SDA=4,SCL=16): PCF8574 CỘT (mong đợi 0x20 — dùng bus riêng nên
 *   không cần khác địa chỉ với module hàng; jumper A0-A2 trên module clone
 *   giá rẻ không đáng tin cậy nên tránh phụ thuộc vào nó).
 * Nếu thiếu thiết bị nào -> dừng lại, kiểm tra dây SDA/SCL/nguồn/GND
 * trước khi đấu tiếp (xem docs/hardware/schematic.md mục Cảnh báo).
 */
#include <Wire.h>

#define PIN_I2C_SDA 21
#define PIN_I2C_SCL 22
#define PIN_I2C2_SDA 4
#define PIN_I2C2_SCL 16

TwoWire WireCols = TwoWire(1);

void scanBus(TwoWire &bus, const char* busName) {
    int found = 0;
    for (uint8_t addr = 1; addr < 127; addr++) {
        bus.beginTransmission(addr);
        if (bus.endTransmission() == 0) {
            found++;
            Serial.printf("  [%s] Tim thay thiet bi tai dia chi 0x%02X", busName, addr);
            if (addr == 0x3C || addr == 0x3D) Serial.print("  <-- OLED SSD1306");
            if (addr >= 0x20 && addr <= 0x27) Serial.print("  <-- co the la PCF8574");
            Serial.println();
        }
    }
    if (found == 0) {
        Serial.printf("  [%s] Khong tim thay thiet bi nao.\n", busName);
    }
}

void setup() {
    Serial.begin(115200);
    delay(500);
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    WireCols.begin(PIN_I2C2_SDA, PIN_I2C2_SCL);
    Serial.println("\n[I2C SCANNER] Bat dau quet ca 2 bus I2C...");
}

void loop() {
    Serial.println("--- Bus #1 (SDA=21,SCL=22): mong doi OLED 0x3C + PCF8574 HANG 0x20 ---");
    scanBus(Wire, "BUS1");
    Serial.println("--- Bus #2 (SDA=4,SCL=16): mong doi PCF8574 COT 0x20 ---");
    scanBus(WireCols, "BUS2");
    Serial.println("=========================================");
    delay(3000);
}
