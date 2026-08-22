# Tham chiếu cơ chế gợi ý & bàn chơi DigitCode — CHỈ SỰ THẬT (fact-only)

> **Tài liệu này chỉ ghi sự thật.** Được tạo cho ticket **#9 (canonical competitive game spec)**,
> trích xuất từ mã nguồn nhánh `feat/puzzle-fairness-characterization`
> (worktree `wt-issue6-puzzle-fairness`), engine Qt/C++ gốc.
>
> **Tài liệu này KHÔNG chọn bất kỳ chính sách nào**, KHÔNG đề xuất luật chơi,
> KHÔNG đánh giá đúng/sai. Mọi mục đều kèm trích dẫn `file:line`.
> Chỗ nào mã nguồn mơ hồ hoặc chưa xác minh được sẽ nằm ở mục
> [Chưa xác minh](#chưa-xác-minh) ở cuối, không suy đoán.

---

## 1. Hình học bàn chơi và định danh

### 1.1. Lưới 2x3 LED và ánh xạ nút `T,U,V,W,X,Y` -> index 0..5

Bàn chơi có **6 LED 7 đoạn**, khởi tạo trong constructor:

```
for (int i = 0; i < 6; i++) m_segStates.append(QVariantList({0,0,0,0,0,0,0}));
```
`backend/gameboard.cpp:36-38`

Ánh xạ nhãn nút -> chỉ số LED nằm ở `selectTargetDigit`:

```
QStringList digits = {"T", "U", "V", "W", "X", "Y"};
int idx = digits.indexOf(label);
```
`backend/gameboard.cpp:143-144`

| Nút | LED index | Hàng | Cột |
|-----|-----------|------|-----|
| `T` | 0 | trên (row 1) | 0 |
| `U` | 1 | trên (row 1) | 1 |
| `V` | 2 | trên (row 1) | 2 |
| `W` | 3 | dưới (row 2) | 0 |
| `X` | 4 | dưới (row 2) | 1 |
| `Y` | 5 | dưới (row 2) | 2 |

Cách bố trí 2 hàng x 3 cột được xác nhận độc lập bởi:

- `COL_LED_MAP` ghép **cặp trên/dưới cùng cột**: `{0,3}`, `{1,4}`, `{2,5}` —
  `backend/gameboard.cpp:14-18`.
- `lockAndLightUpFull` cho hàng dùng `offset = isRow2 ? 3 : 0` rồi lặp `i = 0..2`,
  tức hàng 1 = LED `{0,1,2}`, hàng 2 = LED `{3,4,5}` — `backend/gameboard.cpp:413-419`.
- `generateRandomPuzzle` tính `m_ansRowCounts` trên `{0,1,2}` và `{3,4,5}` —
  `backend/gameboard.cpp:547-556`.
- Chú thích trực tiếp trong QML: `property int ledIndex: 0 // 0=T, 1=U, 2=V, 3=W, 4=X, 5=Y`
  — `UI/LedDisplay.qml:8`.

### 1.2. 7 segment mỗi LED: id và thứ tự

`SEG_MAP` định nghĩa tên -> chỉ số:

```
static const QMap<QString, int> SEG_MAP = {
    {"a",0},{"b",1},{"c",2},{"d",3},{"e",4},{"f",5},{"g",6}
};
```
`backend/gameboard.cpp:5-7`

| Tên segment | segIdx | Vị trí hình học (theo QML) | Trích dẫn QML |
|-------------|--------|-----------------------------|---------------|
| `a` | 0 | thanh ngang trên cùng | `UI/LedDisplay.qml:75` |
| `b` | 1 | thanh dọc trên-phải | `UI/LedDisplay.qml:76` |
| `c` | 2 | thanh dọc dưới-phải | `UI/LedDisplay.qml:77` |
| `d` | 3 | thanh ngang dưới cùng | `UI/LedDisplay.qml:78` |
| `e` | 4 | thanh dọc dưới-trái | `UI/LedDisplay.qml:79` |
| `f` | 5 | thanh dọc trên-trái | `UI/LedDisplay.qml:80` |
| `g` | 6 | thanh ngang giữa | `UI/LedDisplay.qml:81` |

Đây là thứ tự 7 đoạn "chuẩn a-g" nhưng **KHÔNG** phải thứ tự bitmask 7-seg
thông dụng của phần cứng; mọi mảng 7 phần tử trong engine đều theo thứ tự
`[a,b,c,d,e,f,g]` = `[0,1,2,3,4,5,6]`.

Hai nhóm segment phụ dùng cho cột/hàng:

```
COL_GROUPS = { "0": {f,e},  "1": {a,g,d},  "2": {b,c} }
```
`backend/gameboard.cpp:8-10` — chia LED theo **3 dải dọc**: trái (`f`,`e`),
giữa (`a`,`g`,`d`), phải (`b`,`c`).

```
ROW_GROUPS = { "0": {a},  "1": {f,b},  "2": {g},  "3": {e,c},  "4": {d} }
```
`backend/gameboard.cpp:11-13` — chia LED theo **5 dải ngang** từ trên xuống.

### 1.3. `DIGIT_MAP` — segment nào sáng cho từng chữ số

`backend/gameboard.cpp:22-27`. Thứ tự phần tử là `[a,b,c,d,e,f,g]`.

| Digit | a | b | c | d | e | f | g | Segment sáng |
|-------|---|---|---|---|---|---|---|--------------|
| `0` | 1 | 1 | 1 | 1 | 1 | 1 | 0 | a,b,c,d,e,f |
| `1` | 0 | 1 | 1 | 0 | 0 | 0 | 0 | b,c |
| `2` | 1 | 1 | 0 | 1 | 1 | 0 | 1 | a,b,d,e,g |
| `3` | 1 | 1 | 1 | 1 | 0 | 0 | 1 | a,b,c,d,g |
| `4` | 0 | 1 | 1 | 0 | 0 | 1 | 1 | b,c,f,g |
| `5` | 1 | 0 | 1 | 1 | 0 | 1 | 1 | a,c,d,f,g |
| `6` | 1 | 0 | 1 | 1 | 1 | 1 | 1 | a,c,d,e,f,g |
| `7` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | a,b,c |
| `8` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | tất cả 7 |
| `9` | 1 | 1 | 1 | 1 | 0 | 1 | 1 | a,b,c,d,f,g |

Số đoạn sáng mỗi chữ số: `0`=6, `1`=2, `2`=5, `3`=5, `4`=4, `5`=5, `6`=6, `7`=3,
`8`=7, `9`=6.

### 1.4. Wire format gói `DRAW`

Gói `DRAW` được sinh ở **hai chỗ**, cùng một shape: **một gói cho MỖI segment**
(không phải một gói cho cả LED).

Khi có thay đổi (`onSegStateUpdated`) — gửi cả 7 segment của LED đó:

```
obj["type"]   = "DRAW";
obj["ledIdx"] = ledIdx;      // 0..5
obj["segIdx"] = i;           // 0..6, lặp i = 0..6
obj["val"]    = state[i].toInt();
```
`backend/hardwareserver.cpp:155-165`

Khi ESP32 mới kết nối (`onNewConnection`) — đồng bộ lại toàn bộ 6x7 = **42 gói**:

`backend/hardwareserver.cpp:64-74`

Serialize: `QJsonDocument(obj).toJson(QJsonDocument::Compact)` gửi qua
`sendTextMessage` (WebSocket text frame), server nghe cổng **8080**
(`backend/hardwareserver.cpp:12`).

Ví dụ một frame: `{"ledIdx":0,"segIdx":3,"type":"DRAW","val":1}`

**Lưu ý:** trường `val` là `state[i].toInt()` **nguyên trạng**, nên giá trị `2`
(hold) cũng được truyền xuống ESP32 y như vậy — engine không chuẩn hóa về 0/1
trên đường dây (`backend/hardwareserver.cpp:162`).

Các gói khác cùng kênh (để đối chiếu, không thuộc `DRAW`):

| type | Trường | Trích dẫn |
|------|--------|-----------|
| `STATS` | `time`, `points` | `backend/hardwareserver.cpp:32-38` |
| `OLED` | `layout:"default"` HOẶC `layout:"text"` + `line1` + `line2` | `backend/hardwareserver.cpp:168-188` |
| `SYSTEM` | `cmd:"welcome"`, `status:"connected_to_qt"` | `backend/hardwareserver.cpp:55-59` |

Chiều ngược lại (ESP32 -> Qt), `processTextMessage` chỉ nhận 3 loại:

| type | Trường | Gọi hàm | Trích dẫn |
|------|--------|---------|-----------|
| `PAD_SELECT` | `label` (`"T"`..`"Y"`) | `selectTargetDigit` | `backend/hardwareserver.cpp:116-119` |
| `PAD_DRAW` | `segIdx` (0..6) | `tapDrawingPad` | `backend/hardwareserver.cpp:123-126` |
| `ACTION` | `btnId` | `handleButtonPress("HW", btnId)` | `backend/hardwareserver.cpp:130-133` |

### 1.5. Ma trận nút phần cứng và vai trò kép của `T..Y`

Firmware quét ma trận **6 hàng × 7 cột = tối đa 42 ô, 38 nút thật**
(`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:45-70`):

| Hàng | Nội dung | Trích dẫn |
|------|----------|-----------|
| 0 | `BTN_Q1`, `BTN_Q2`, `BTN_Q3`, `BTN_Q4`, `BTN_VERIFY`, `BTN_NEWGAME`, (trống) | `:64` |
| 1 | `T`, `U`, `V`, `W`, `X`, `Y` (`CELL_TARGET`), (trống) | `:65` |
| 2 | Drawing Pad `segIdx` 0..6 (`CELL_DRAW`) | `:66` |
| 3 | `A`–`G` | `:67` |
| 4 | `H`–`N` | `:68` |
| 5 | `O`–`S`, (trống), (trống) | `:69` |

**Một lần bấm `T..Y` trên phần cứng phát HAI message:**

```
case CELL_TARGET:
    sendPadSelect(cell.label);
    sendAction(cell.label);
    selectActiveDigit(cell.label[0] - 'T');
```
`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:302-307`

Chú thích của chính firmware: "T-Y có 2 vai trò độc lập trong backend (chọn digit
vẽ / đáp án Q1-Q2) -> gửi cả 2 message, backend tự bỏ qua nhánh không áp dụng"
(`:303-304`). Nghĩa là mọi lần bấm `T..Y` vừa đổi `m_activeDigit`
(`backend/gameboard.cpp:142-150`) vừa đi vào `handleButtonPress`
(-> `processQ1` / `processQ2` / `processReviewTarget`). Trên QML thì hai vai trò
này ở hai chỗ bấm khác nhau: nhãn nút gọi `handleButtonPress`
(`UI/BottomBoard.qml:90`), còn vẽ segment gọi `tapSegment` trực tiếp
(`UI/LedDisplay.qml:39`).

`BTN_NEWGAME` là ngoại lệ duy nhất về cách phát: phải **giữ đủ 5000 ms**
(`NEWGAME_HOLD_MS`) mới gửi, và chỉ gửi một lần cho mỗi lần giữ
(`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:77`, `:282-293`). Mọi nút còn
lại phát theo cạnh nhấn (`:297`), chống rung bằng chu kỳ quét 20 ms (`:74`).

Firmware chuẩn hoá `val` khi vẽ LED thật: `lc.setLed(0, ledIdx, segIdx + 1, val != 0)`
(`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:143`) — tức trạng thái `2`
(hold) hiển thị **giống hệt** `1` trên sa bàn vật lý, không phân biệt được bằng mắt.
`segIdx + 1` vì cột 0 của MAX7219 dành cho đèn DP báo digit đang chọn (`:148-149`).

## 2. Mô hình trạng thái segment

### 2.1. Giá trị lưu trữ

Trạng thái là `QVariantList m_segStates` gồm 6 phần tử, mỗi phần tử là một
`QVariantList` 7 `int` (`backend/gameboard.h:84`, `backend/gameboard.cpp:36-38`).

| Giá trị | Ý nghĩa | Nơi được đặt |
|---------|---------|---------------|
| `0` | Tắt / chưa vẽ | init `backend/gameboard.cpp:37`; reset ván mới `:459`; `tapSegment` khi đang là 1 `:742` |
| `1` | Đã vẽ / sáng | `tapSegment` (từ 0 hoặc từ 2) `:742`; `lockAndLightUpFull` `:430`; `setLedDigit` qua `DIGIT_MAP` `:771`; `setLedSegState` tùy caller `:779` |
| `2` | "hold" / đánh dấu (nhấn giữ) | **chỉ** `holdSegment` `backend/gameboard.cpp:752` |

Chu trình `tapSegment`:

```
int next = (cur == 0) ? 1 : (cur == 2) ? 1 : 0;
```
`backend/gameboard.cpp:742` — tức `0 -> 1`, `1 -> 0`, `2 -> 1`. Không có đường
nào từ tap sang `2`; chỉ `holdSegment` (`pressAndHold`, `holdDuration: 1000` ms,
`UI/LedDisplay.qml:10`, `:68-71`) đặt được `2`.

Ý nghĩa hiển thị theo QML: `2` = đỏ `#e5484d`, `>0` = hổ phách `#ffb000`,
`0` = mờ `#241a05` — `UI/LedDisplay.qml:28-32`.

### 2.2. Khoá segment — `lockAndLightUpFull`

`backend/gameboard.cpp:391-436`.

1. Xác định tập `targets` là các cặp `(ledIdx, segIdx)`:
   - Nút cột `A..I`: lấy `COL_LED_MAP[btnId]` -> `(ledTop, ledBot)`, lấy
     `COL_IDX_MAP[btnId]` -> `colIdx`, lấy `COL_GROUPS[colIdx]` -> danh sách
     segment; thêm **cả LED trên và LED dưới** cho mỗi segment
     (`backend/gameboard.cpp:395-404`).
   - Nút hàng `J..S`: `isRow2 = (btnId >= "O")`, `rowIdx` là vị trí trong
     `{J,K,L,M,N}` hoặc `{O,P,Q,R,S}`, lấy `ROW_GROUPS[rowIdx]`,
     `offset = isRow2 ? 3 : 0`, thêm `(offset + i, sIdx)` với `i = 0..2`
     (`backend/gameboard.cpp:406-420`).
2. Với mỗi target:
   - Chèn khoá `m_lockedSegments.insert("<ledIdx>-<segIdx>")`
     (`backend/gameboard.cpp:427`).
   - **Đặt giá trị `1`** (`led[sIdx] = 1;`) — `backend/gameboard.cpp:430`.
   - `emit segStatesChanged()` + `emit segStateUpdated(lIdx, led)` **trong vòng lặp**,
     mỗi target một lần (`backend/gameboard.cpp:433-434`).

Hiệu lực của khoá: `tapSegment` (`:738`) và `holdSegment` (`:750`) `return` sớm
nếu key `"<ledIdx>-<segIdx>"` có trong `m_lockedSegments`. Không có API nào gỡ
khoá ngoài `generateRandomPuzzle` (`m_lockedSegments.clear()`,
`backend/gameboard.cpp:456`).

**Chú ý — không gọi `checkWinCondition`:** `lockAndLightUpFull` ghi thẳng vào
`m_segStates[lIdx]` (`backend/gameboard.cpp:431`) chứ không đi qua `updateSeg`,
nên **không** kích hoạt `checkWinCondition()`. Chỉ `updateSeg`
(`backend/gameboard.cpp:764`) và `setLedSegState` (`backend/gameboard.cpp:783`)
gọi hàm này.

**Chú ý — giá trị khoá là `1`, không phải `2`:** QML chú thích `2` là
"khoá (Q3 full)" (`UI/LedDisplay.qml:29`) nhưng mã C++ đặt `1`
(`backend/gameboard.cpp:430`). Xem mục [Chưa xác minh](#chưa-xác-minh).

### 2.3. Phân kỳ giữa auto-detect và VERIFY

Đây là điểm phân kỳ **chính xác** giữa hai đường nhận thắng.

**Auto-detect — `checkWinCondition()`** (`backend/gameboard.cpp:63-92`):

```
QVariantList currentState = m_segStates[i].toList();
QVariantList targetState  = DIGIT_MAP[m_secretCode[i]].toList();
if (currentState != targetState) { won = false; break; }
```
`backend/gameboard.cpp:68-73`

So sánh **danh sách nguyên trạng**, phần tử-với-phần tử, với mẫu `DIGIT_MAP`
chỉ chứa `0` và `1`. Do đó:

- Chấp nhận: chỉ các giá trị **`0` và `1`** khớp đúng mẫu.
- **Từ chối**: bất kỳ segment nào mang giá trị **`2` (hold)**, kể cả khi hình
  vẽ nhìn bằng mắt là đúng chữ số — vì `2 != 1`.

**VERIFY — `decodeDigitFromSegments()`** (`backend/gameboard.cpp:562-578`):

```
normalized.append(v.toInt() != 0 ? 1 : 0);
```
`backend/gameboard.cpp:569`

Chuẩn hoá **mọi giá trị khác 0 thành 1** trước khi dò `DIGIT_MAP`. Chú thích
ngay trong mã nói rõ: "coi mọi giá trị khác 0 (kể cả trạng thái `hold`=2) là
sáng" (`backend/gameboard.cpp:565-566`). Do đó:

- Chấp nhận: `0` = tắt; **`1` và `2` đều tính là sáng** (và về nguyên tắc mọi
  giá trị khác 0).

| Đường | Hàm | Xử lý `hold = 2` | Trích dẫn |
|-------|-----|-------------------|-----------|
| Auto-detect | `checkWinCondition` | **Không khớp** -> không thắng | `backend/gameboard.cpp:70` |
| Nút VERIFY | `decodeDigitFromSegments` -> `verifyCode` | **Tính là sáng** -> có thể thắng | `backend/gameboard.cpp:567-570` |

Hệ quả trực tiếp: một bàn cờ vẽ đúng hình nhưng có ít nhất một segment ở trạng
thái `2` sẽ **không** tự động thắng, nhưng **sẽ** thắng nếu người chơi bấm
`BTN_VERIFY`.

## 3. Q1 — Chẵn/Lẻ (even/odd)

Hàm: `GameBoard::processQ1` — `backend/gameboard.cpp:250-280`.

### 3.1. Tập mục tiêu (target set)

```
if (btnId < "T" || btnId > "Y") return;
```
`backend/gameboard.cpp:252`

So sánh chuỗi `QString`. Tập hợp lệ trên thực tế: **`T, U, V, W, X, Y`** (6 nút,
tương ứng 6 LED). Mọi `btnId` nằm ngoài khoảng này bị **bỏ qua im lặng** — không
trừ điểm, không đổi trạng thái, không dừng đồng hồ phạt (`return` trần).

### 3.2. Miền đáp án (answer domain)

Đáp án được tính sẵn khi sinh đề:

```
m_ansEvenOdd.append(m_secretCode[i].digitValue() % 2 == 0 ? 0 : 1);
```
`backend/gameboard.cpp:493-495`

| Giá trị | Ý nghĩa |
|---------|---------|
| `0` | chữ số **chẵn** |
| `1` | chữ số **lẻ** |

Miền đáp án = `{0, 1}`. Tra cứu:

```
int index = QString("TUVWXYZ").indexOf(btnId);
bool isOdd = m_ansEvenOdd[index].toInt() == 1;
```
`backend/gameboard.cpp:271-272`

Giá trị này cũng được đẩy sang QML nguyên trạng qua
`revealClueToUI("Q1_EODOT", btnId, m_ansEvenOdd[index])`
(`backend/gameboard.cpp:276`). QML vẽ `".."` cho `0` (even) và `"."` cho `1`
(odd) — `UI/BottomBoard.qml:35-38`, `:92-93`.

### 3.3. Chuỗi OLED

| Tình huống | line1 | line2 | Trích dẫn |
|-----------|-------|-------|-----------|
| Vào chế độ hỏi (bấm `BTN_Q1`) | `"Q1: Pick one..."` | `""` | `backend/gameboard.cpp:212` |
| Trả lời — số lẻ | `"<btnId>: ODD (.)"` | `""` | `backend/gameboard.cpp:273` |
| Trả lời — số chẵn | `"<btnId>: EVEN (..)"` | `""` | `backend/gameboard.cpp:273` |
| Hỏi trùng | `"Forget? Find it in ur mind"` | `"Or in my mind I guess..."` | `backend/gameboard.cpp:256` |

Format code: `QString("%1: %2").arg(btnId, isOdd ? "ODD (.)" : "EVEN (..)")`.
Ví dụ: `U: ODD (.)`.

Sau khi trả lời, `m_oledClearTimer->start(3000)` (`backend/gameboard.cpp:278`) —
sau 3 giây OLED về layout mặc định **nếu** state đang là `DEFAULT`
(`backend/gameboard.cpp:55-60`).

### 3.4. Giá

`m_points -= 5;` — `backend/gameboard.cpp:266`. **5 điểm mỗi lần hỏi thành công.**
Nhánh hỏi trùng và nhánh `btnId` ngoài miền **không** trừ điểm.

### 3.5. Chống hỏi trùng

Tập `QSet<QString> m_askedQ1` (`backend/gameboard.h:128`).

```
if (m_askedQ1.contains(btnId)) { ...; m_currentState = DEFAULT; m_penaltyTimer->stop(); return; }
```
`backend/gameboard.cpp:255-261`

Hỏi trùng: **không trừ điểm**, in thông điệp "Forget?...", **hủy** đồng hồ phạt,
và đưa state về `DEFAULT` — tức là **mất lượt** (phải bấm `BTN_Q1` lại).
Chèn vào tập xảy ra ở `backend/gameboard.cpp:265`, tập được xoá ở
`generateRandomPuzzle` (`backend/gameboard.cpp:451`).

### 3.6. Chuyển trạng thái

| Từ | Sự kiện | Sang | Trích dẫn |
|----|---------|------|-----------|
| bất kỳ | `BTN_Q1` | `WAIT_Q1` + `m_penaltyTimer->start(10000)` + xoá `m_tempTarget1` | `backend/gameboard.cpp:208-211`, `:224` |
| `WAIT_Q1` | `btnId` ngoài `T..Y` | `WAIT_Q1` (giữ nguyên, timer vẫn chạy) | `backend/gameboard.cpp:252` |
| `WAIT_Q1` | `btnId` đã hỏi rồi | `DEFAULT`, timer dừng | `backend/gameboard.cpp:258-259` |
| `WAIT_Q1` | `btnId` hợp lệ, mới | `DEFAULT`, timer dừng, -5 điểm | `backend/gameboard.cpp:264`, `:279` |
| `WAIT_Q1` | hết 10s | `DEFAULT`, -1 điểm | `backend/gameboard.cpp:120-139` |

### 3.7. Xem lại miễn phí (Review)

Ở state `DEFAULT`, bấm `T..Y` gọi `processReviewTarget`
(`backend/gameboard.cpp:232-233`, `:699-728`): in lại đáp án Q1 **nếu đã mua**
(`"<btnId>: ODD (.)"` / `"EVEN (..)"`), ngược lại in `"<btnId>: No cheating..."`
(`backend/gameboard.cpp:703-709`). **Không trừ điểm, không dùng đồng hồ phạt.**

## 4. Q2 — So sánh (comparison)

Hàm: `GameBoard::processQ2` — `backend/gameboard.cpp:282-326`.

### 4.1. Bảy cặp hợp lệ và cách tính kề nhau

`GameBoard::isAdjacent` — `backend/gameboard.cpp:365-373`. **Không** tính toán
hình học; nó tra **hai tập chuỗi cứng** chứa sẵn cả hai chiều:

```
QSet<QString> hPairs = {"T-U", "U-V", "W-X", "X-Y", "U-T", "V-U", "X-W", "Y-X"};
QSet<QString> vPairs = {"T-W", "W-T", "U-X", "X-U", "V-Y", "Y-V"};
QString pair = btn1 + "-" + btn2;
return hPairs.contains(pair) || vPairs.contains(pair);
```

Kết quả: đúng **7 cặp không thứ tự** (4 ngang + 3 dọc). Sau khi chuẩn hoá
alphabetical (`backend/gameboard.cpp:299`) chúng là:

| # | Cặp (chuẩn hoá) | Hướng | LED so sánh | Nguồn đáp án | Trích dẫn |
|---|-----------------|-------|-------------|--------------|-----------|
| 1 | `T-U` | ngang, hàng trên | 0 vs 1 | `m_ansHCmp[0]` | `backend/gameboard.cpp:501`, `:689` |
| 2 | `U-V` | ngang, hàng trên | 1 vs 2 | `m_ansHCmp[1]` | `backend/gameboard.cpp:502`, `:690` |
| 3 | `W-X` | ngang, hàng dưới | 3 vs 4 | `m_ansHCmp[2]` | `backend/gameboard.cpp:503`, `:691` |
| 4 | `X-Y` | ngang, hàng dưới | 4 vs 5 | `m_ansHCmp[3]` | `backend/gameboard.cpp:504`, `:692` |
| 5 | `T-W` | dọc, cột 0 | 0 vs 3 | `m_ansVCmp[0]` | `backend/gameboard.cpp:507`, `:693` |
| 6 | `U-X` | dọc, cột 1 | 1 vs 4 | `m_ansVCmp[1]` | `backend/gameboard.cpp:508`, `:694` |
| 7 | `V-Y` | dọc, cột 2 | 2 vs 5 | `m_ansVCmp[2]` | `backend/gameboard.cpp:509`, `:695` |

**Không hợp lệ**: các cặp chéo (`T-X`, `U-W`, `U-Y`, `V-X`), cặp cách quãng
(`T-V`, `W-Y`, `T-Y`, `V-W`), và mọi cặp có 1 nút không thuộc `T..Y`.
Cặp `T-V` và `W-Y` **không** hợp lệ dù cùng hàng (chỉ kề trực tiếp mới tính).

Vì `T < U < V < W < X < Y` theo thứ tự chuỗi, chuẩn hoá alphabetical luôn cho ra
đúng 7 khoá trên, và `cmpValueForPair` chỉ nhận đúng 7 khoá đó — mọi khoá khác
trả `0` (`backend/gameboard.cpp:696`).

### 4.2. Miền đáp án

```
auto cmp = [](int a, int b) -> int { return a > b ? 1 : a < b ? -1 : 0; };
```
`backend/gameboard.cpp:498`

| Giá trị | Ý nghĩa | Ký hiệu OLED |
|---------|---------|--------------|
| `1` | trái **lớn hơn** phải | `>` |
| `-1` | trái **nhỏ hơn** phải | `<` |
| `0` | **bằng nhau** | `=` |

Miền được mã hỗ trợ = `{-1, 0, 1}`. **Nhưng giá trị `0` là nhánh chết
(dead branch) với mọi mã bí mật hợp lệ**: bộ sinh đề cấm hai LED liền kề mang
cùng chữ số — ràng buộc ngang C2 phủ đúng `T-U, U-V, W-X, X-Y`
(`backend/gameboard.cpp:478`) và ràng buộc dọc C3 phủ đúng `T-W, U-X, V-Y`
(`backend/gameboard.cpp:479`), tức **chính xác 7 cặp Q2**. Vậy trên thực tế
`cmpValueForPair` chỉ trả `1` hoặc `-1`. Điều này được ghi nhận độc lập trong
mô hình đối chiếu tại `tools/analysis/digitcode.py:194-201` ("Trả 0 là bất khả
thi với secret hợp lệ"). Xem thêm [Phụ lục](#phụ-lục--luật-sinh-mã-bí-mật).

Chuyển sang ký hiệu:
`QString rel = val > 0 ? ">" : (val < 0 ? "<" : "=");` — `backend/gameboard.cpp:318`.

Giá trị số được đẩy sang QML: `revealClueToUI("Q2_ARROW", pair, val)`
(`backend/gameboard.cpp:321`). QML chỉ vẽ mũi tên khi `cmpVal !== 0`
(`UI/BottomBoard.qml:49`, `:64`), tức **trường hợp `=` không có biểu tượng nào
trên sa bàn QML** — chỉ OLED nói.

### 4.3. Chuỗi OLED

| Tình huống | line1 | line2 | Trích dẫn |
|-----------|-------|-------|-----------|
| Bấm `BTN_Q2` | `"Q2: Pick two..."` | `""` | `backend/gameboard.cpp:215` |
| Đã chọn nút thứ 1 | `"Q2: Another one..."` | `""` | `backend/gameboard.cpp:288` |
| Hai nút không kề nhau | `"INVALID, pick again..."` | `""` | `backend/gameboard.cpp:294` |
| Trả lời | `"<A> <rel> <B>"` | `""` | `backend/gameboard.cpp:319` |
| Hỏi trùng | `"Forget? Find it in ur mind"` | `"Or in my mind I guess..."` | `backend/gameboard.cpp:302` |

Format: `QString("%1 %2 %3").arg(pair.left(1), rel, pair.right(1))` — lấy ký tự
đầu và ký tự cuối của chuỗi cặp đã chuẩn hoá. Ví dụ: `T > U`, `V = Y`, `W < X`.
Vì chuỗi luôn đã chuẩn hoá alphabetical, vế trái luôn là chữ cái đứng trước.

### 4.4. Giá

`m_points -= 5;` — `backend/gameboard.cpp:311`. **5 điểm mỗi lần hỏi thành công**
(một cặp). Nhánh `INVALID` và nhánh trùng **không** trừ điểm.

### 4.5. Chống hỏi trùng

Tập `QSet<QString> m_askedQ2` (`backend/gameboard.h:129`), khoá là **cặp đã
chuẩn hoá alphabetical**:

```
QString pair = (m_tempTarget1 < btnId) ? (m_tempTarget1 + "-" + btnId) : (btnId + "-" + m_tempTarget1);
```
`backend/gameboard.cpp:299`

Chú thích mã nói rõ mục đích: "chống trùng lặp chiều ngược (V-U = U-V)"
(`backend/gameboard.cpp:298`). Nghĩa là hỏi `U` rồi `T` và hỏi `T` rồi `U` là
**cùng một câu**. Xử lý trùng giống Q1: không trừ điểm, dừng timer, về `DEFAULT`,
mất lượt (`backend/gameboard.cpp:301-307`).

### 4.6. Cơ chế chọn mục tiêu hai bước

```
if (m_currentState == WAIT_Q2_1) {
    m_tempTarget1 = btnId;
    m_currentState = WAIT_Q2_2;
    emit oledUpdateRequested("Q2: Another one...", "");
    return;
}
```
`backend/gameboard.cpp:285-290`

| Từ | Sự kiện | Sang | Ghi chú |
|----|---------|------|---------|
| bất kỳ | `BTN_Q2` | `WAIT_Q2_1`, `m_tempTarget1` xoá, timer 10s **start** | `backend/gameboard.cpp:213-215`, `:208`, `:224` |
| `WAIT_Q2_1` | nút `T..Y` | `WAIT_Q2_2`, lưu `m_tempTarget1` | `backend/gameboard.cpp:286-287` |
| `WAIT_Q2_1` | nút ngoài `T..Y` | `WAIT_Q2_1` (bỏ qua) | `backend/gameboard.cpp:283` |
| `WAIT_Q2_2` | nút **không kề** nút 1 | `WAIT_Q2_2` (bắt chọn lại) | `backend/gameboard.cpp:293-296` |
| `WAIT_Q2_2` | cặp đã hỏi | `DEFAULT`, timer stop | `backend/gameboard.cpp:301-307` |
| `WAIT_Q2_2` | cặp hợp lệ mới | `DEFAULT`, timer stop, -5 | `backend/gameboard.cpp:309-324` |

**Quan trọng:** bước chuyển `WAIT_Q2_1 -> WAIT_Q2_2` **không** khởi động lại đồng
hồ phạt (`backend/gameboard.cpp:290` `return` trước khi chạm timer). Nhánh
`INVALID` cũng không (`backend/gameboard.cpp:295`). Vậy **10 giây bao trọn cả hai
bước chọn**, không phải 10 giây cho mỗi bước.

Chú ý thêm: `WAIT_Q2_2` **không** cấm chọn lại chính nút thứ nhất — nếu chọn
`T` rồi `T`, `isAdjacent("T","T")` trả `false` nên rơi vào nhánh `INVALID`
(`backend/gameboard.cpp:293`). Đây là kết quả gián tiếp, không phải guard riêng
(khác Q4, xem mục 6.4).

### 4.7. Xem lại miễn phí

`processReviewTarget` (`backend/gameboard.cpp:711-723`): ghép nút vừa bấm với
`m_lastReviewTarget` (nút `T..Y` bấm ngay trước đó ở chế độ `DEFAULT`), chuẩn hoá
alphabetical, và nếu cặp đó **đã mua** thì in ra `line2` dạng `"<A> <rel> <B>"`.
Không trừ điểm, không timer. `m_lastReviewTarget` cập nhật mỗi lần
(`backend/gameboard.cpp:724`), reset khi sinh đề mới (`backend/gameboard.cpp:450`).

## 5. Q3 — Bộ đếm (counters) `A..S`

Hàm: `GameBoard::processQ3` — `backend/gameboard.cpp:328-363`.

### 5.1. Bảng đầy đủ 19 mục tiêu

Đáp án được tính một lần khi sinh đề (`backend/gameboard.cpp:512-556`) và tra
cứu lúc hỏi:

```
int index = (btnId <= "I") ? (btnId.at(0).unicode() - 'A') : (btnId.at(0).unicode() - 'J');
int count = (btnId <= "I") ? m_ansColCounts[index].toInt() : m_ansRowCounts[index].toInt();
```
`backend/gameboard.cpp:345-346`

Mỗi bộ đếm trả về **số segment ĐANG SÁNG trong mã bí mật** thuộc tập
(LED × segment) của nó — mỗi ô LED×segment đếm **1**, đếm trên `st[]` là
`DIGIT_MAP` của mã bí mật (`backend/gameboard.cpp:486-489`), **không** đếm trên
bàn vẽ hiện tại của người chơi.

`A..I` = **9 bộ đếm cột** (3 dải dọc × 3 cột LED, mỗi cột gồm LED trên + LED dưới):

| ID | LED đếm | Nút LED | Segment đếm | Max | Nguồn đáp án | Nguồn max |
|----|---------|---------|-------------|-----|--------------|-----------|
| `A` | 0, 3 | T, W | `f`, `e` | 4 | `:525` | `:377` |
| `B` | 0, 3 | T, W | `a`, `g`, `d` | 6 | `:526` | `:378` |
| `C` | 0, 3 | T, W | `b`, `c` | 4 | `:527` | `:379` |
| `D` | 1, 4 | U, X | `f`, `e` | 4 | `:528` | `:377` |
| `E` | 1, 4 | U, X | `a`, `g`, `d` | 6 | `:529` | `:378` |
| `F` | 1, 4 | U, X | `b`, `c` | 4 | `:530` | `:379` |
| `G` | 2, 5 | V, Y | `f`, `e` | 4 | `:531` | `:377` |
| `H` | 2, 5 | V, Y | `a`, `g`, `d` | 6 | `:532` | `:378` |
| `I` | 2, 5 | V, Y | `b`, `c` | 4 | `:533` | `:379` |

`J..S` = **10 bộ đếm hàng** (5 dải ngang × 2 hàng LED, mỗi hàng gồm 3 LED):

| ID | LED đếm | Nút LED | Segment đếm | Max | Nguồn đáp án | Nguồn max |
|----|---------|---------|-------------|-----|--------------|-----------|
| `J` | 0, 1, 2 | T, U, V | `a` | 3 | `:547` | `:381` |
| `K` | 0, 1, 2 | T, U, V | `f`, `b` | 6 | `:548` | `:382` |
| `L` | 0, 1, 2 | T, U, V | `g` | 3 | `:549` | `:383` |
| `M` | 0, 1, 2 | T, U, V | `e`, `c` | 6 | `:550` | `:384` |
| `N` | 0, 1, 2 | T, U, V | `d` | 3 | `:551` | `:385` |
| `O` | 3, 4, 5 | W, X, Y | `a` | 3 | `:552` | `:381` |
| `P` | 3, 4, 5 | W, X, Y | `f`, `b` | 6 | `:553` | `:382` |
| `Q` | 3, 4, 5 | W, X, Y | `g` | 3 | `:554` | `:383` |
| `R` | 3, 4, 5 | W, X, Y | `e`, `c` | 6 | `:555` | `:384` |
| `S` | 3, 4, 5 | W, X, Y | `d` | 3 | `:556` | `:385` |

(Tất cả trích dẫn dòng ở hai bảng trên thuộc `backend/gameboard.cpp`.)

Tổng cộng **19 mục tiêu** (`A`–`S`), khớp bố cục 19 nút trong firmware
(`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:67-69`) và trong QML
(`UI/BottomBoard.qml:122` cho `A..I`, `:14-15` cho `J..N` / `O..S`).

Hai nguồn định nghĩa **độc lập nhưng nhất quán**:
`generateRandomPuzzle` dùng danh sách segment viết tay
(`backend/gameboard.cpp:525-556`), còn `lockAndLightUpFull` suy ra qua
`COL_LED_MAP` + `COL_IDX_MAP` + `COL_GROUPS` / `ROW_GROUPS`
(`backend/gameboard.cpp:395-420`). Đã đối chiếu: hai bên khớp nhau cho cả 19 mục.
`getMaxLed` (`backend/gameboard.cpp:375-388`) cũng khớp: max = (số segment trong
dải) × (số LED trong nhóm).

**Tính chất phân hoạch (partition).** Bàn có `6 LED × 7 segment = 42` ô.
9 mục tiêu cột `A..I` phủ **đúng 42 ô, mỗi ô đúng một lần**; 10 mục tiêu hàng
`J..S` cũng phủ **đúng 42 ô, mỗi ô đúng một lần**. Tổng max: cột
`3×(4+6+4) = 42`, hàng `2×(3+6+3+6+3) = 42`. Tính chất này được kiểm tra tự
động trong worktree tại `tools/analysis/digitcode.py:258-267` (`_self_check`) và
`tools/analysis/test_analysis.py:42-50`.

### 5.2. Miền đáp án

Số nguyên `0 .. getMaxLed(btnId)`:

| Nhóm | Miền |
|------|------|
| `A,C,D,F,G,I` (cột 2 segment) | `0..4` |
| `B,E,H` (cột 3 segment) | `0..6` |
| `J,L,N,O,Q,S` (hàng 1 segment) | `0..3` |
| `K,M,P,R` (hàng 2 segment) | `0..6` |

Giá trị được đẩy sang QML: `revealClueToUI("Q3_COUNTER", btnId, count)`
(`backend/gameboard.cpp:359`); QML in số vào ô `CBox` (`UI/BottomBoard.qml:71-77`,
`:209-211`, `:225`, `:229`).

### 5.3. Chuỗi OLED

| Tình huống | line1 | line2 | Trích dẫn |
|-----------|-------|-------|-----------|
| Bấm `BTN_Q3` | `"Q3: Pick a row/column..."` | `""` | `backend/gameboard.cpp:218` |
| Trả lời | `"<btnId> has <count> demon(s)"` | `""` | `backend/gameboard.cpp:355-356` |
| Hỏi trùng / đã khoá FULL | `"Forget? Find it in ur mind"` | `"Or in my mind I guess..."` | `backend/gameboard.cpp:332` |

Format: `QString("%1 has %2 demon(s)").arg(btnId).arg(count)`. Ví dụ:
`B has 4 demon(s)`. Chuỗi luôn dùng `demon(s)`, không chia số ít/nhiều.

### 5.4. Giá

`m_points -= 5;` — `backend/gameboard.cpp:341`. **5 điểm mỗi lần hỏi thành công.**

### 5.5. Chống hỏi trùng

```
if (m_askedQ3.contains(btnId) || m_lockedFull.contains(btnId)) { ... }
```
`backend/gameboard.cpp:331`

Guard kiểm tra **hai** tập:

- `m_askedQ3` — đã hỏi Q3 mục tiêu này rồi (`backend/gameboard.h:130`, chèn ở `:340`).
- `m_lockedFull` — mục tiêu này đã được xác nhận FULL (qua Q3 **hoặc** Q4) và đã
  bị khoá (`backend/gameboard.h:132`, chèn ở `:350` và `:634`).

Guard **KHÔNG** kiểm tra `m_askedQ4`. Nghĩa là một mục tiêu từng được hỏi Q4 và
trả về **NOT FULL** vẫn có thể mua tiếp bằng Q3 để biết con số chính xác
(đối chiếu `backend/gameboard.cpp:331` với `:607-608`).

Xử lý trùng giống Q1/Q2: không trừ điểm, dừng đồng hồ phạt, về `DEFAULT`, mất
lượt (`backend/gameboard.cpp:332-336`).

### 5.6. Tác dụng phụ FULL (đầy đủ)

```
if (count == getMaxLed(btnId)) {
    m_lockedFull.insert(btnId);
    lockAndLightUpFull(btnId);
}
```
`backend/gameboard.cpp:349-352`

Khi `count` bằng đúng max của mục tiêu, chuỗi tác dụng phụ là:

1. `m_lockedFull.insert(btnId)` — chặn hỏi lại mục tiêu này ở cả Q3
   (`backend/gameboard.cpp:331`) và Q4 (`:607-608`); ở Review Mode đây là nhánh
   ưu tiên cao nhất, in `"<btnId> FULL"` (`:662-666`).
2. `lockAndLightUpFull(btnId)` (`backend/gameboard.cpp:391-436`), với mỗi
   `(ledIdx, segIdx)` thuộc mục tiêu:
   - chèn `"<ledIdx>-<segIdx>"` vào `m_lockedSegments` -> người chơi **không thể
     tap/hold** segment đó nữa (`:427`, chặn ở `:738` và `:750`);
   - **ghi giá trị `1`** vào `m_segStates` -> segment được **tự động bật sáng**
     (`:430-431`);
   - `emit segStatesChanged()` + `emit segStateUpdated(lIdx, led)` -> QML cập
     nhật và `HardwareServer` gửi gói `DRAW` xuống ESP32 (`:433-434`, kéo theo
     `backend/hardwareserver.cpp:155-165`).
3. **Không** gọi `checkWinCondition()` — vì ghi thẳng vào `m_segStates` chứ không
   qua `updateSeg` (`backend/gameboard.cpp:431` so với `:764`). Nếu nước khoá này
   là nước cuối cùng hoàn thiện mã, engine **không** tự nhận thắng ngay lúc đó.
4. Số lượng segment bị bật/khoá: bằng đúng `getMaxLed(btnId)` (4, 6 hoặc 3 ô).

Ghi chú: `lockAndLightUpFull` bật sáng **toàn bộ** ô thuộc mục tiêu. Điều này
nhất quán vì `count == max` nghĩa là mọi ô trong mục tiêu đều sáng trong mã bí mật.

### 5.7. Xem lại miễn phí

`processReview` (`backend/gameboard.cpp:658-685`), chỉ chạy khi state là
`DEFAULT` (`:229-231`). Thứ tự ưu tiên:

| Điều kiện | line1 | Trích dẫn |
|-----------|-------|-----------|
| `m_lockedFull` chứa `btnId` | `"<btnId> FULL"` | `:662-664` |
| `m_askedQ3` chứa `btnId` | `"<btnId> has <count> demon(s)"` | `:667-672` |
| `m_askedQ4` chứa `btnId` | `"<btnId> not full, guess how many...."` | `:675-677` |
| còn lại | `"No cheating..."` | `:680-682` |

Mọi nhánh: không trừ điểm, không timer phạt, `m_oledClearTimer->start(3000)`.

## 6. Q4 — Kiểm tra FULL

Hàm: `GameBoard::processQ4` — `backend/gameboard.cpp:589-656`.

### 6.1. Hình dạng yêu cầu: đúng hai mục tiêu

Q4 **bắt buộc** chọn **2 mục tiêu** trong `A..S`, theo hai bước:

```
if (btnId < "A" || btnId > "S") return;                 // :590
if (m_currentState == WAIT_Q4_1) { m_tempTarget1 = btnId; m_currentState = WAIT_Q4_2; ... return; }  // :592-597
if (m_currentState == WAIT_Q4_2) { ... }                // :599
```

Không có đường nào cho phép hỏi Q4 chỉ 1 mục tiêu: state `WAIT_Q4_2` chỉ thoát
khi có nút thứ hai hợp lệ, khi bấm `BTN_Q1..Q4` khác (override,
`backend/gameboard.cpp:204-226`), hoặc khi đồng hồ phạt hết giờ
(`backend/gameboard.cpp:137`).

### 6.2. Miền đáp án

```
bool isFull = (count == getMaxLed(node));
```
`backend/gameboard.cpp:632`

Miền = **boolean** cho **mỗi** mục tiêu: `true` (FULL) / `false` (NOT FULL). Q4
**không** tiết lộ con số — chỉ trả lời "đã đầy hay chưa". Giá trị gửi sang QML:
`revealClueToUI("Q4_FULL", node, isFull)` (`backend/gameboard.cpp:639`); QML tô
nút xanh `#b7d84b` khi `true`, đỏ `#e5484d` khi `false` (`UI/BottomBoard.qml:25`).

Một yêu cầu Q4 sinh ra **hai** tín hiệu `clueRevealed`, một cho mỗi mục tiêu
(`backend/gameboard.cpp:647-648` gọi lambda hai lần).

### 6.3. Chuỗi OLED

| Tình huống | line1 | line2 | Trích dẫn |
|-----------|-------|-------|-----------|
| Bấm `BTN_Q4` | `"Q4: Pick a row/column..."` | `""` | `backend/gameboard.cpp:221` |
| Đã chọn mục tiêu 1 | `"Q4: Pick another row/column..."` | `""` | `backend/gameboard.cpp:595` |
| Chọn lại đúng mục tiêu 1 | `"INVALID, pick again..."` | `""` | `backend/gameboard.cpp:602` |
| Trả lời | `"<target1> FULL"` hoặc `"<target1> NOT FULL"` | `"<target2> FULL"` hoặc `"<target2> NOT FULL"` | `backend/gameboard.cpp:642-643`, `:651` |
| Một trong hai đã hỏi/khoá | `"Forget? Find it in ur mind"` | `"Or in my mind I guess..."` | `backend/gameboard.cpp:611` |

Đây là **câu hỏi duy nhất dùng cả hai dòng OLED** cho phần đáp án
(`emit oledUpdateRequested(result1, result2)` — `backend/gameboard.cpp:651`).

### 6.4. Giá: theo YÊU CẦU, không theo mục tiêu

```
m_penaltyTimer->stop();
m_points -= 5;
emit pointsChanged();
```
`backend/gameboard.cpp:619-621`

Trừ điểm **một lần duy nhất**, nằm **ngoài** lambda `checkNode`
(`backend/gameboard.cpp:624-644`), tức **5 điểm cho cả hai mục tiêu**, không
phải 5 điểm mỗi mục tiêu. Đối chiếu: Q1/Q2/Q3 cũng là 5 điểm nhưng chỉ cho một
mục tiêu (Q1/Q3) hoặc một cặp (Q2).

### 6.5. Guard

| Guard | Kiểm tra gì | Hành vi | Trích dẫn |
|-------|-------------|---------|-----------|
| Miền input | `btnId < "A" \|\| btnId > "S"` | `return` im lặng, giữ nguyên state và timer | `:590` |
| Hai nút phải khác nhau | `btnId == m_tempTarget1` | `"INVALID, pick again..."`, **giữ nguyên** `WAIT_Q4_2` và timer đang chạy | `:601-604` |
| Trùng/đã khoá | `m_askedQ3.contains(x) \|\| m_lockedFull.contains(x)` cho **cả hai** nút | `"Forget?..."`, timer stop, về `DEFAULT`, **không trừ điểm** | `:607-616` |

**Guard KHÔNG kiểm tra `m_askedQ4`.** Một mục tiêu đã hỏi Q4 và trả về NOT FULL
có thể bị hỏi Q4 lại vô số lần (đối chiếu `:607-608` với `:625`). `m_askedQ4`
chỉ được **ghi** (`:625`) và chỉ được **đọc** trong Review Mode (`:675`).

**Guard là "cả gói"**: chỉ cần **một** trong hai nút vướng, cả yêu cầu bị huỷ —
không mục tiêu nào được trả lời, không trừ điểm, mất lượt (`:610-616`).

### 6.6. Tác dụng phụ tự bật/khoá

Bên trong lambda `checkNode`, cho **mỗi** mục tiêu độc lập
(`backend/gameboard.cpp:624-644`):

1. `m_askedQ4.insert(node)` — luôn luôn, kể cả khi NOT FULL (`:625`).
2. Tra `count` từ `m_ansColCounts` / `m_ansRowCounts` (`:628-629`) — giống hệt
   Q3 nhưng **không** in ra.
3. Nếu `isFull`: `m_lockedFull.insert(node)` + `lockAndLightUpFull(node)`
   (`:633-636`) — **cùng một tác dụng phụ đầy đủ như mục 5.6**: khoá segment vào
   `m_lockedSegments`, tự bật sáng giá trị `1`, phát `segStateUpdated` xuống
   ESP32, và **không** gọi `checkWinCondition`.
4. `revealClueToUI("Q4_FULL", node, isFull)` (`:639`).
5. Trả chuỗi cho OLED (`:642-643`).

Nếu **cả hai** mục tiêu đều FULL, `lockAndLightUpFull` chạy hai lần trong cùng
một yêu cầu 5 điểm.

## 7. Câu hỏi đang chờ / đồng hồ phạt

### 7.1. Máy trạng thái

```
enum GameState { DEFAULT, WAIT_Q1, WAIT_Q2_1, WAIT_Q2_2, WAIT_Q3, WAIT_Q4_1, WAIT_Q4_2 };
```
`backend/gameboard.h:19-25`. Biến: `GameState m_currentState`
(`backend/gameboard.h:118`), khởi tạo `DEFAULT` (`backend/gameboard.cpp:32`).

Phân luồng chính trong `handleButtonPress` (`backend/gameboard.cpp:159-248`),
theo đúng thứ tự ưu tiên sau:

| Ưu tiên | Điều kiện | Hành động | Trích dẫn |
|---------|-----------|-----------|-----------|
| 0 | `btnId == "BTN_NEWGAME"` | `generateRandomPuzzle()` rồi `return` — bất kể state | `:163-166` |
| 1 | `m_ansEvenOdd.isEmpty()` | OLED `"No game running"` / `"Hold NEW GAME 5s"`, `return` | `:171-175` |
| 2 | `btnId == "BTN_VERIFY"` | xem mục 8 | `:177-201` |
| 3 | `btnId` là `BTN_Q1..BTN_Q4` | **override**: đặt state `WAIT_*`, xoá `m_tempTarget1`, `m_oledClearTimer->stop()`, `m_penaltyTimer->start(10000)` | `:204-226` |
| 4 | `m_currentState == DEFAULT` | Review Mode: `A..S` -> `processReview`, `T..Y` -> `processReviewTarget` | `:229-236` |
| 5 | còn lại | `switch (m_currentState)` -> `processQ1/Q2/Q3/Q4` | `:239-247` |

Ưu tiên 3 là "bẻ lái" (override): đang dở `WAIT_Q2_2` mà bấm `BTN_Q3` thì bỏ hết
tiến trình cũ, sang `WAIT_Q3`, và **khởi động lại** đồng hồ 10s.

### 7.2. Cửa sổ 10 giây

```
m_penaltyTimer = new QTimer(this);
m_penaltyTimer->setSingleShot(true);
connect(m_penaltyTimer, &QTimer::timeout, this, &GameBoard::onPenaltyTimeout);
```
`backend/gameboard.cpp:41-43` — **single-shot**, không tự lặp.

```
m_penaltyTimer->start(10000); // Khởi động/Reset lại đồng hồ 10s
```
`backend/gameboard.cpp:224` — **đây là nơi DUY NHẤT gọi `start()` cho đồng hồ này.**

| Sự kiện | Ảnh hưởng tới đồng hồ phạt | Trích dẫn |
|---------|-----------------------------|-----------|
| Bấm `BTN_Q1/Q2/Q3/Q4` | **START / RESTART** ở 10000 ms | `:224` |
| Q1 trả lời hợp lệ | **STOP** | `:264` |
| Q1 hỏi trùng | **STOP** | `:259` |
| Q2 chọn nút thứ 1 (`WAIT_Q2_1 -> WAIT_Q2_2`) | **không đụng đến** (tiếp tục đếm) | `:285-290` |
| Q2 cặp không kề nhau (`INVALID`) | **không đụng đến** | `:293-296` |
| Q2 trả lời hợp lệ | **STOP** | `:309` |
| Q2 hỏi trùng | **STOP** | `:305` |
| Q3 trả lời hợp lệ | **STOP** | `:339` |
| Q3 hỏi trùng | **STOP** | `:335` |
| Q4 chọn mục tiêu 1 | **không đụng đến** | `:592-597` |
| Q4 chọn trùng mục tiêu 1 (`INVALID`) | **không đụng đến** | `:601-604` |
| Q4 trả lời hợp lệ | **STOP** | `:619` |
| Q4 trùng/đã khoá | **STOP** | `:614` |
| `btnId` ngoài miền của câu hỏi | **không đụng đến** (`return` trần) | `:252`, `:283`, `:329`, `:590` |
| `pauseGame()` | **STOP** | `:796` |
| `resumeGame()` | **KHÔNG** khởi động lại (chỉ `m_globalTimer`) | `:799-804` |
| `generateRandomPuzzle()` | **STOP** nếu đang chạy | `:464` |
| Thắng (`checkWinCondition` / `verifyCode`) | **STOP** | `:79`, `:810` |
| Thua (hết điểm / sai 2 lần) | **STOP** | `:111`, `:829` |

Hệ quả cần ghi nhận: 10 giây là ngân sách cho **toàn bộ** một lượt hỏi, kể cả
câu hai bước (Q2, Q4). Không có bước nào gia hạn.

### 7.3. Chi phí khi hết giờ

`GameBoard::onPenaltyTimeout` — `backend/gameboard.cpp:120-139`:

1. `m_points -= 1; emit pointsChanged();` (`:121-122`) — **trừ 1 điểm**.
2. Nếu `m_points <= 0`: ép về `0`, dừng `m_globalTimer`, OLED
   `"YOU DIED..."` / `"Better luck next life"`, `emit gameLost()`, `return`
   (`:125-132`).
3. Ngược lại: OLED `"Playing with me?"` / `"-1 Point"` (`:134`),
   `m_oledClearTimer->start(3000)` (`:135`).
4. `m_currentState = DEFAULT; m_tempTarget1.clear();` (`:137-138`) — **huỷ lượt
   hỏi đang dở**, không hoàn lại gì.

Đồng hồ **không** tự khởi động lại (single-shot, và `onPenaltyTimeout` không gọi
`start`). Tức là trong một lượt hỏi bị bỏ dở, người chơi chỉ mất **đúng 1 điểm**,
không bị trừ liên tục.

### 7.4. Các nguồn trừ điểm khác (để đối chiếu)

| Nguồn | Thay đổi điểm | Trích dẫn |
|-------|---------------|-----------|
| Điểm khởi đầu | `100` | `backend/gameboard.cpp:30`, reset ở `:445` |
| Trôi thời gian | `-1` mỗi **60 giây** (`m_playTimeSeconds % 60 == 0`) | `:99-103` |
| Hết giờ 10s | `-1` | `:121` |
| Q1 / Q2 / Q3 / Q4 hợp lệ | `-5` mỗi lần | `:266`, `:311`, `:341`, `:620` |
| Đoán sai lần 2 | ép `m_points = 0` | `:825` |
| Review Mode (`A..S`, `T..Y`) | `0` (miễn phí) | `:658-685`, `:699-728` |

Điều kiện thua vì cạn điểm chỉ được kiểm tra trong `onGlobalTimerTick` (`:106`)
và `onPenaltyTimeout` (`:125`) — **không** kiểm tra ngay sau khi trừ 5 điểm ở
Q1–Q4. Nghĩa là điểm có thể xuống `<= 0` ngay sau một câu hỏi mà game chỉ kết
thúc ở nhịp tick 1 giây kế tiếp.

### 7.5. Đồng hồ OLED 3 giây

`m_oledClearTimer`, single-shot (`backend/gameboard.cpp:50-52`). Khi hết giờ,
`onOledClearTimeout` chỉ phát `oledUpdateRequested("", "DEFAULT_LAYOUT")`
**nếu** `m_currentState == DEFAULT` (`:55-60`). Bị `stop()` khi bấm `BTN_Q1..Q4`
(`:206`) và khi thắng/thua (`:80`, `:112`, `:811`, `:830`).

## 8. Luồng VERIFY

### 8.1. Đường phần cứng: nút vật lý -> thắng/thua

1. **Firmware** — nút `BTN_VERIFY` nằm ở hàng 0, cột 4 của ma trận 6x7
   (`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:64`), phát theo cạnh nhấn:
   `sendAction("BTN_VERIFY")` -> `{"type":"ACTION","btnId":"BTN_VERIFY"}`
   (`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:185-190`, `:299`).
   (Khác `BTN_NEWGAME` — nút đó phải **giữ 5000 ms** mới gửi,
   `:77`, `:282-293`.)
2. **HardwareServer** — `processTextMessage` gặp `type == "ACTION"` gọi
   `m_board->handleButtonPress("HW", btnId)`
   (`backend/hardwareserver.cpp:130-133`).
3. **`handleButtonPress`** — `backend/gameboard.cpp:177-201`:
   - Guard sớm ở `:171-175`: nếu `m_ansEvenOdd.isEmpty()` (chưa từng sinh ván
     nào) -> OLED `"No game running"` / `"Hold NEW GAME 5s"`, `return`.
   - Guard `:180-184`: nếu `m_secretCode.isEmpty()` (chưa bắt đầu, hoặc ván đã
     kết thúc) -> OLED `"No active game"` / `"Hold NEW GAME 5s"`, `return`.
     Chú thích mã nêu rõ lý do: nếu không chặn, mọi mã đoán đều "sai" so với
     `m_secretCode` rỗng -> ăn strike oan (`:178-179`).
   - Giải mã sa bàn thành mã 6 chữ số:
     ```
     for (int i = 0; i < 6; i++) {
         int digit = decodeDigitFromSegments(getSegState(i));
         if (digit == -1) { valid = false; break; }
         guess += QString::number(digit);
     }
     ```
     `backend/gameboard.cpp:188-192`
   - Nếu bất kỳ LED nào không khớp mẫu `DIGIT_MAP` -> OLED `"INVALID CODE"` /
     `"Draw digit 0-9 first"`, `m_oledClearTimer->start(3000)`, `return`
     (`:196-199`) — **không** tính là một lần đoán sai.
   - Ngược lại gọi `verifyCode(guess)` (`:195`).

`decodeDigitFromSegments` (`backend/gameboard.cpp:562-578`) chuẩn hoá mọi giá trị
khác `0` thành `1` (`:569`) rồi dò tuyến tính toàn bộ `DIGIT_MAP` (`:572-576`),
trả `-1` nếu không mẫu nào khớp hoặc danh sách không đủ 7 phần tử (`:563`).

**`BTN_VERIFY` không đi qua máy trạng thái `WAIT_*`** — nó được xử lý ở ưu tiên 2,
trước cả nhánh `BTN_Q1..Q4` (`backend/gameboard.cpp:177`), nên bấm được ở mọi
state; nó cũng **không** dừng `m_penaltyTimer` nếu đang có lượt hỏi dở dang.

### 8.2. Đường phần mềm (QML)

Nút `VERIFY` mở popup nhập tay 6 chữ số (`UI/ScreenGame.qml:142-159`,
`:162-202`), `TextField` giới hạn `maximumLength: 6` và validator `^[0-9]{0,6}$`
(`:186`, `:189`), nút `ACCESS` chỉ bật khi đủ 6 ký tự (`:196`) rồi gọi
**thẳng** `gameBoard.verifyCode(txtCodeInput.text)` (`UI/ScreenGame.qml:199`).

Đường này **không đi qua `handleButtonPress`**, nên **bỏ qua cả hai guard**
`m_ansEvenOdd.isEmpty()` và `m_secretCode.isEmpty()`. QML chỉ hiện nút khi
`root.gameActive` (`UI/ScreenGame.qml:149`), tức chỉ được chặn ở tầng giao diện.

### 8.3. `verifyCode` — so sánh và đếm lượt đoán

`backend/gameboard.cpp:806-838`. So sánh là **chuỗi với chuỗi**:

```
if (guessCode == m_secretCode) { ... }
```
`backend/gameboard.cpp:807`

Không so trực tiếp segment với segment — mã đoán đã được quy về chuỗi 6 chữ số
trước đó (giải mã ở đường phần cứng, gõ tay ở đường QML). Đây là điểm khác biệt
so với `checkWinCondition`, hàm này so **danh sách segment** với `DIGIT_MAP`
(xem mục 2.3).

| Nhánh | Hành động | Trích dẫn |
|-------|-----------|-----------|
| **Đúng** | `m_globalTimer->stop()`; stop `m_penaltyTimer` và `m_oledClearTimer` nếu đang chạy; `m_secretCode = ""`; OLED `"YOU ESCAPED!"` / `"Clear time: mm:ss"`; `emit gameWon()` | `:807-818` |
| **Sai, lần 1** | `m_guessCount++`; `emit wrongGuessWarning()` — **không trừ điểm**, đồng hồ vẫn chạy | `:821`, `:836` |
| **Sai, lần 2 trở đi** (`m_guessCount >= 2`) | `m_points = 0`; `emit pointsChanged()`; stop cả 3 đồng hồ; OLED `"ACCESS DENIED..."` / `"System Locked"`; `emit gameLost()` | `:823-833` |

`m_guessCount` (`backend/gameboard.h:123`) chỉ được đặt về `0` trong
`generateRandomPuzzle` (`backend/gameboard.cpp:442`) — **không** được khởi tạo
trong constructor (`backend/gameboard.cpp:29-33`).

Chuỗi thời gian: `QString("%1:%2").arg(m, 2, 10, QChar('0')).arg(s, 2, 10, QChar('0'))`
với `m = m_playTimeSeconds / 60`, `s = m_playTimeSeconds % 60`
(`backend/gameboard.cpp:814-816`) — định dạng `mm:ss` đệm số 0.

### 8.4. Đường tự động (auto-detect) — để đối chiếu

`checkWinCondition` (`backend/gameboard.cpp:63-92`) được gọi từ đúng **hai** chỗ:
`updateSeg` (`:764`) và `setLedSegState` (`:783`). Nó:

1. `return` ngay nếu `m_secretCode.isEmpty()` (`:64`).
2. So từng LED: `m_segStates[i].toList() != DIGIT_MAP[m_secretCode[i]].toList()`
   -> thua (`:68-73`).
3. Nếu khớp cả 6: dừng 3 đồng hồ, `m_secretCode = ""`, OLED
   `"YOU ESCAPED!"` / `"Clear time: mm:ss"`, `emit gameWon()` (`:76-91`) —
   **cùng chuỗi OLED và cùng tín hiệu** như nhánh thắng của `verifyCode`.

Hai đường **không** cùng bộ tiêu chí (mục 2.3), và `checkWinCondition` **không**
đụng tới `m_guessCount`.

### 8.5. Tín hiệu phát ra và phía QML tiêu thụ

| Tín hiệu | Phát ở | QML xử lý |
|----------|--------|-----------|
| `gameWon()` | `:90`, `:818` | `UI/ScreenGame.qml:27` -> `gameActive = false`, push `ScreenResult.qml` với `isWin: true` |
| `gameLost()` | `:115`, `:130`, `:833` | `UI/ScreenGame.qml:28` -> push `ScreenResult.qml` với `isWin: false` |
| `wrongGuessWarning()` | `:836` | `UI/ScreenGame.qml:49-52` -> đóng `verifyPopup`, mở `deniedPopup` ("ACCESS DENIED / YOU HAVE ONE LAST CHANCE", `:219`) |
| `oledUpdateRequested(line1,line2)` | khắp nơi | `UI/ScreenGame.qml:43-47` và `backend/hardwareserver.cpp:168-188` -> ESP32 |
| `clueRevealed(type,id,value)` | `:585` | `UI/ScreenGame.qml:36-41` -> nạp vào `revealedQ1..Q4` |
| `segStateUpdated(ledIdx,state)` | `:434`, `:460`, `:762`, `:773`, `:781` | `UI/LedDisplay.qml:20-24`; `backend/hardwareserver.cpp:155-165` -> gói `DRAW` |
| `puzzleGenerated()` | `:559` | `UI/ScreenGame.qml:30-34` -> xoá manh mối cũ, `gameActive = true` |

## Phụ lục — Luật sinh mã bí mật

`generateRandomPuzzle` — `backend/gameboard.cpp:471-482`. Vòng lặp bốc ngẫu nhiên
`0..9` và bỏ qua ứng viên vi phạm một trong ba ràng buộc:

| # | Điều kiện loại bỏ | Ý nghĩa | Dòng |
|---|-------------------|---------|------|
| 1 | `code.count(ch) >= 2` | mỗi chữ số xuất hiện **tối đa 2 lần** trong 6 vị trí | `:477` |
| 2 | `currentLength % 3 != 0 && code.at(currentLength-1) == ch` | không trùng chữ số **liền kề ngang** trong cùng hàng (bỏ qua kiểm tra ở vị trí 0 và 3 — đầu hàng) | `:478` |
| 3 | `currentLength >= 3 && code.at(currentLength-3) == ch` | không trùng chữ số **cùng cột** giữa hàng trên và hàng dưới | `:479` |

Cơ chế thử lại: khi một ứng viên bị loại, `continue` quay lại đầu vòng `while`
với `code` **không đổi**, tức **bốc lại chính vị trí đó** chứ không dựng lại cả
mã (`backend/gameboard.cpp:472-481`).

Mã được in ra console: `qDebug() << "[PUZZLE GENERATOR] New Secret Code:" << m_secretCode;`
(`backend/gameboard.cpp:483`).

**Hệ quả đã được mô hình hoá sẵn trong worktree** (ghi lại như dữ kiện, không
phải kết luận của tài liệu này): mô hình port 1-1 tại `tools/analysis/digitcode.py`
đếm được **465 120** mã hợp lệ (`tools/analysis/test_analysis.py:30`), và ghi
nhận rằng vì mỗi vị trí được bốc lại độc lập nên phân phối **không đều
(non-uniform)** trên tập mã hợp lệ, với
`P(code) = prod_i 1/|A_i(prefix_i)|` (`tools/analysis/digitcode.py:122-126`,
hàm `secret_probability` ở `:174-179`).

Ràng buộc C2 + C3 cộng lại cấm đúng 7 quan hệ "hai LED liền kề bằng nhau" — trùng
khít với 7 cặp Q2 (mục 4.1) — nên đáp án `=` của Q2 không bao giờ xuất hiện
(mục 4.2).

## Chưa xác minh

Các điểm dưới đây là chỗ mã nguồn **mơ hồ, tự mâu thuẫn, hoặc tôi không xác minh
được** trong phạm vi các file đã đọc. Ghi lại nguyên trạng, **không suy đoán ý đồ**.

1. **`lockAndLightUpFull` ghi `1` nhưng QML mô tả `2` là "khoá".**
   `backend/gameboard.cpp:430` đặt `led[sIdx] = 1`, trong khi
   `UI/LedDisplay.qml:29` viết `if (segState[idx] === 2) return "#e5484d" // khoá (Q3 full)`.
   Không có đường mã nào đặt `2` ngoài `holdSegment` (`backend/gameboard.cpp:752`).
   Chưa xác minh được đây là chủ ý hay lệch pha; tôi **không** kết luận màu nào
   là đúng.

2. **Chú thích "5 GIÂY" vs `start(10000)`.**
   Tiêu đề hàm ghi `// --- LOGIC PHẠT TIMER 5 GIÂY ---`
   (`backend/gameboard.cpp:119`) nhưng giá trị thực gọi là `10000` ms
   (`backend/gameboard.cpp:224`). Giá trị **thực thi** là 10 giây; chú thích là
   dấu vết cũ. Không có nơi nào khác đặt thời lượng này.

3. **`QString("TUVWXYZ")` trong `processQ1` có chữ `Z` thừa.**
   `backend/gameboard.cpp:271` dùng `"TUVWXYZ"`, còn `processReviewTarget`
   (`backend/gameboard.cpp:704`) dùng `"TUVWXY"`. Với `btnId` trong `T..Y` cả hai
   cho cùng chỉ số `0..5`, nên **không** thấy khác biệt hành vi; chưa xác minh
   được có tình huống nào `Z` lọt vào (guard `:252` chặn `> "Y"`).

4. **Thứ tự tương đối của `m_askedQ4` và `m_askedQ3` khi cùng một mục tiêu.**
   Đã xác nhận Q3 và Q4 **không** đọc `m_askedQ4` trong guard
   (`backend/gameboard.cpp:331`, `:607-608`). Nhưng tôi **chưa** kiểm chứng bằng
   chạy thật hệ quả tổ hợp đầy đủ (ví dụ: Q4 NOT FULL nhiều lần liên tiếp cùng
   một cặp) — kết luận trên thuần suy ra từ đọc mã.

5. **`m_guessCount` không được khởi tạo trong constructor.**
   Danh sách khởi tạo `backend/gameboard.cpp:29-33` không có `m_guessCount`;
   nó chỉ được gán trong `generateRandomPuzzle` (`:442`). Trong luồng chuẩn
   (luôn `generateRandomPuzzle` trước khi chơi — `UI/ScreenReady.qml:39`,
   `UI/ScreenRealLife.qml:92`, `UI/ScreenResult.qml:56`) điều này không lộ ra.
   Chưa xác minh được có đường nào gọi `verifyCode` trước lần sinh đề đầu tiên.

6. **`m_backups` khai báo nhưng không dùng.**
   `backend/gameboard.h:85` khai báo `QVariantMap m_backups`; `grep` toàn bộ
   `backend/` không thấy lần dùng nào khác. Tương tự, `UI/LedDisplay.qml:45-46`
   gọi `gameBoard.turnOnGroupQml(...)` và `gameBoard.restoreGroupQml(...)` —
   **hai hàm này không tồn tại** trong `GameBoard` (không có trong
   `backend/gameboard.h` hay `backend/gameboard.cpp`). Chưa xác minh được có
   thành phần QML nào thực sự gọi hai hàm đó lúc chạy (`turnOnGroup` /
   `restoreGroup` trong `LedDisplay.qml` không được gọi từ đâu trong các file
   QML đã đọc).

7. **`handleButtonPress` bỏ qua tham số `source`.**
   Chữ ký nhận `const QString& source` (`backend/gameboard.h:46`,
   `backend/gameboard.cpp:159`) nhưng thân hàm không dùng biến này. QML truyền
   `"SW"` (`UI/ScreenGame.qml:119`, `UI/BottomBoard.qml:90` v.v.),
   `HardwareServer` truyền `"HW"` (`backend/hardwareserver.cpp:132`). Không có
   khác biệt hành vi giữa hai nguồn trong mã hiện tại.

8. **So sánh `QVariantList` trong `checkWinCondition`.**
   `backend/gameboard.cpp:70` dựa vào `operator==` của `QVariantList`. Tôi đã
   xác nhận cả hai phía đều là danh sách 7 `int` (`:37`, `:22-27`), nên phép so
   sánh phần tử-với-phần tử là hợp lệ, nhưng **chưa chạy thử** để loại trừ khả
   năng khác kiểu `QVariant` ngầm (ví dụ nếu `setLedSegState` được QML gọi với
   `double`). `setLedSegState` (`:777-784`) chấp nhận `QVariantList` bất kỳ và
   **không kiểm tra kích thước hay kiểu**.

9. **Không có kiểm thử tự động nào chạy trực tiếp trên C++.**
   Worktree **có** bộ kiểm thử `tools/analysis/test_analysis.py`, nhưng nó ghim
   **mô hình Python** `tools/analysis/digitcode.py` chứ không thực thi
   `backend/gameboard.cpp` — chính header của nó ghi rõ: "Các test này KHÔNG
   kiểm tra kết luận phân tích; chúng ghim mô hình trong `digitcode.py` vào
   những dữ kiện suy được độc lập từ `backend/gameboard.cpp`"
   (`tools/analysis/test_analysis.py:6-9`). Tôi dùng nó làm **đối chiếu độc lập**
   cho hình học bàn, `MAX_LED`, và 7 cặp Q2 — cả ba đều khớp với mã C++. Tôi
   **không** chạy bộ test này và **không** áp dụng bất kỳ kết luận phân tích nào
   của `analysis_*.py` (chúng thuộc phạm vi issue #6, không phải tài liệu này).
   Mọi khẳng định ở đây đến từ **đọc mã tĩnh**, không từ chạy engine thực.

10. **Chưa xác minh hành vi khi bấm `T..Y` trên phần cứng lúc đang ở `WAIT_Q3`
    hoặc `WAIT_Q4_*`.** Theo mã: `processQ3`/`processQ4` guard `btnId < "A" || btnId > "S"`
    (`backend/gameboard.cpp:329`, `:590`) — mà `"T" > "S"` — nên `return` im lặng;
    đồng thời `PAD_SELECT` vẫn đổi `m_activeDigit`
    (`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:303-307` ->
    `backend/gameboard.cpp:142-150`). Nghĩa là người chơi vẫn chọn được LED để vẽ
    trong khi câu hỏi đang treo, và đồng hồ phạt vẫn chạy. Đây là suy luận từ
    đọc mã; **chưa chạy thử để xác nhận**.

11. *(Đã xác minh, không còn là nghi vấn — giữ lại để khỏi ai đi kiểm tra lại.)*
    `ScreenRealLife.qml` **không** có đường VERIFY riêng và **không** đổi luật
    nào. Nó chỉ là màn chờ kết nối ESP32 (hiện `hwServer.serverAddress`,
    chặn `START` tới khi `hwServer.connected`), rồi
    `stackView.replace("ScreenGame.qml", { "realLifeMode": true })` +
    `gameBoard.generateRandomPuzzle()` (`UI/ScreenRealLife.qml:90-93`).
    Cờ `realLifeMode` chỉ ảnh hưởng **một** thứ trong `ScreenGame.qml`: ẩn nút
    Back/Pause khi ván đang chạy (`visible: !root.realLifeMode || !root.gameActive`,
    `UI/ScreenGame.qml:63`).
