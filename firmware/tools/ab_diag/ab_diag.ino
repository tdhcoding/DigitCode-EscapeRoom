/*
 * Chan doan chuyen biet: hien tuong A+B cung sang tren LED T.
 *
 * Sang tung vach cham (3 giay/vach) theo trinh tu: T.a -> T.b -> U.a -> U.b
 * De phan xu giua cac gia thuyet:
 *   1. T.a sang -> thay A+B, T.b sang -> thay A+B  ==> chap cung giua chan 10-9
 *      cua LED T (chan cong gap duoi bung LED cham nhau?). Neu vay U.a/U.b cung
 *      se bi doi (vi cau chap noi 2 bus voi nhau qua chan LED T).
 *   2. T.a sang -> thay A+B, T.b sang -> TOI THUI    ==> day trich b cua T cam
 *      nham vao hang bus A tren breadboard.
 *   3. T.a sang -> chi A, T.b -> chi B               ==> het benh (do scan-limit cu).
 */
#include <LedControl.h>

#define PIN_MAX_DIN 23
#define PIN_MAX_CLK 18
#define PIN_MAX_CS  5
#define LED_INTENSITY 2

LedControl lc(PIN_MAX_DIN, PIN_MAX_CLK, PIN_MAX_CS, 1);

void reinit() {
    lc.shutdown(0, false);
    lc.setScanLimit(0, 7);
    lc.setIntensity(0, LED_INTENSITY);
}

void showOne(int led, int segCol, const char* label) {
    lc.clearDisplay(0);
    reinit();
    Serial.printf(">>> DANG SANG: %s (3 giay) - quan sat xem thuc te vach nao sang\n", label);
    lc.setLed(0, led, segCol, true);
    delay(3000);
    lc.setLed(0, led, segCol, false);
}

void setup() {
    Serial.begin(115200);
    delay(500);
    reinit();
    lc.clearDisplay(0);
    Serial.println("[AB DIAG] Trinh tu: T.a -> T.b -> U.a -> U.b -> nghi 2s -> lap lai");
}

void loop() {
    showOne(0, 1, "LED T - vach A (tren)");        // segIdx 0 -> column 1
    showOne(0, 2, "LED T - vach B (tren-phai)");   // segIdx 1 -> column 2
    showOne(1, 1, "LED U - vach A (tren)");
    showOne(1, 2, "LED U - vach B (tren-phai)");
    Serial.println("--- Nghi 2 giay, lap lai ---");
    delay(2000);
}
