/*
 * Bring-up test #2: MAX7219 / khối LED 7 đoạn
 *
 * Chạy SAU khi i2c_scanner đã OK. Sáng lần lượt từng segment (A->G) của
 * từng LED (0->5) để xác nhận: đúng thứ tự DIN/CLK/CS, đúng ledIdx vật lý
 * khớp với LED T,U,V,W,X,Y trên sa bàn, và không có segment nào đấu chéo.
 *
 * segIdx: 0=A,1=B,2=C,3=D,4=E,5=F,6=G (khớp SEG_MAP trong backend/gameboard.cpp)
 */
#include <LedControl.h>

#define PIN_MAX_DIN 23
#define PIN_MAX_CLK 18
#define PIN_MAX_CS  5

LedControl lc(PIN_MAX_DIN, PIN_MAX_CLK, PIN_MAX_CS, 1);

void setSegment(int ledIdx, int segIdx, bool on) {
    lc.setLed(0, ledIdx, segIdx + 1, on); // column 0 = DP (khong dung), 1..7 = A..G
}

// Do sang thap (2/15): mach chua co tu loc nguon, pha all-on o do sang cao
// rut dong dot ngot lam sut ap -> MAX7219 + ESP32 reset (da gap thuc te)
#define LED_INTENSITY 2

void setup() {
    Serial.begin(115200);
    delay(500);
    lc.shutdown(0, false);
    lc.setIntensity(0, LED_INTENSITY);
    lc.clearDisplay(0);
    Serial.println("[MAX7219 TEST] Bat dau. Quan sat tung LED/segment sang dung thu tu.");
}

void loop() {
    // Tu ghi lai thanh ghi dieu khien moi chu ky: neu MAX7219 bi brownout reset
    // (mat tu loc nguon), cac thanh ghi ve trang thai mac dinh: shutdown BAT va
    // scan limit = chi quet digit 0 (chi LED T sang). Phai ghi lai CA HAI.
    lc.shutdown(0, false);
    lc.setScanLimit(0, 7);
    lc.setIntensity(0, LED_INTENSITY);

    const char* segNames[7] = {"A(top)", "B(top-right)", "C(bottom-right)", "D(bottom)", "E(bottom-left)", "F(top-left)", "G(middle)"};

    for (int led = 0; led < 6; led++) {
        Serial.printf("--- LED index %d (nen la vi tri T,U,V,W,X,Y thu %d) ---\n", led, led + 1);
        for (int seg = 0; seg < 7; seg++) {
            Serial.printf("  Sang segment %s ...\n", segNames[seg]);
            setSegment(led, seg, true);
            delay(400);
            setSegment(led, seg, false);
            delay(150);
        }
        // DP (cham thap phan) - dung lam den bao digit dang chon o firmware chinh
        Serial.println("  Sang segment DP (cham) ...");
        lc.setLed(0, led, 0, true);  // column 0 = DP
        delay(400);
        lc.setLed(0, led, 0, false);
        delay(150);
    }

    Serial.println("[MAX7219 TEST] Sang tat ca 6 LED hinh so 8 trong 2 giay de kiem tra tong the...");
    for (int led = 0; led < 6; led++)
        for (int seg = 0; seg < 7; seg++)
            setSegment(led, seg, true);
    delay(2000);
    for (int led = 0; led < 6; led++)
        for (int seg = 0; seg < 7; seg++)
            setSegment(led, seg, false);

    delay(1000);
}
