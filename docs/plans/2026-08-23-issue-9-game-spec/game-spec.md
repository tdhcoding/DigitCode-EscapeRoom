# DigitCode — Canonical Competitive Game Specification

`ruleset_id`: **`digitcode-ruleset/1.0.0`**

Ticket: [Chốt competitive game specification chuẩn](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)
Branch: `feat/competitive-game-spec`

Đây là **luật chơi chuẩn duy nhất** cho bản web 1v1. Nó kế thừa standing
decisions ở Notes của map #1, dựa trên số liệu của
[Định lượng độ công bằng và khả năng giải của Puzzle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6),
và **cố ý không port** các hành vi native mà #6 xếp là bug hoặc lifecycle
coupling (đối chiếu đầy đủ ở mục 11).

Luật được đánh số để execution ticket và test trích dẫn trực tiếp. **MUST** là
bắt buộc; **MUST NOT** là cấm.

Fact-only reference cho cơ chế native, kèm `file:line`, nằm ở
[`clue-reference.md`](clue-reference.md). Nó **không** phải luật; nơi spec này
khác native, spec này thắng.

---

## 1. Từ vựng

Dùng đúng từ vựng ở [`CONTEXT.md`](../../../CONTEXT.md) tại repo root. Mười ba
thuật ngữ mà spec này chốt và đã đưa vào glossary: Clue, Player Board, Verify,
Strike, Forfeit, Draw, Match Clock, Solve Time, Ruleset, Bot State, Bot Score,
Bot Submission, Bot Terminal Status.

Một quy ước đọc: **Puzzle** là bí mật cộng các fact suy ra từ nó; **Player
Board** là thứ người chơi vẽ. Hai thứ này không bao giờ là một — native làm
chúng trông như một vì clue tự vẽ lên bàn cờ, và spec này bỏ hẳn điều đó
(R-C-09).

---

## 2. Puzzle

### 2.1 Hình học và định danh

- **R-P-01** Bàn là lưới **2 hàng × 3 cột**, sáu LED, định danh `T U V` (hàng
  trên, index 0–2) và `W X Y` (hàng dưới, index 3–5).
- **R-P-02** Mỗi LED có **7 segment** `a b c d e f g` theo quy ước bảy đoạn.
  Bàn có đúng `6 × 7 = 42` ô LED×segment.
- **R-P-03** Một Puzzle là một **mã bí mật sáu chữ số**, chữ số thứ `i` thuộc
  LED index `i`.

### 2.2 Ràng buộc sinh mã

- **R-P-04** Mã hợp lệ MUST thoả cả ba ràng buộc:
  1. mỗi chữ số xuất hiện **tối đa 2 lần** trong mã;
  2. hai LED **kề nhau theo hàng** MUST khác chữ số — bốn cặp `T-U`, `U-V`,
     `W-X`, `X-Y`;
  3. hai LED **kề nhau theo cột** MUST khác chữ số — ba cặp `T-W`, `U-X`,
     `V-Y`.
- **R-P-05** Tập mã hợp lệ có đúng **465.120** phần tử (EXACT, #6 xác nhận
  bằng ba đường độc lập).
- **R-P-06** Ba ràng buộc trên MUST NOT bị nới. Bỏ ràng buộc kề nhau sẽ khiến
  Q2 có ba đáp án thay vì hai và làm vô hiệu toàn bộ tính toán chi phí clue
  của #6.

### 2.3 Lấy mẫu

- **R-P-07** Puzzle MUST được rút **uniform** trên pool eligible: mọi mã trong
  pool có xác suất bằng nhau, chính xác.
- **R-P-08** Rejection sampler theo từng vị trí của native MUST NOT được dùng.
  Nó lệch `p_max/p_min = 9/7` **exact**. #6 chứng minh bias này không chuyển
  thành bias độ khó (trung bình 11,83 lần mua theo phân phối thật vs 11,84
  uniform), nên đây là quyết định về công bằng thống kê: không mất gì khi sửa,
  và giữ lại thì mở ra một khiếu nại không phản bác được ở Ranked.

### 2.4 Eligibility

- **R-P-09** **Practice Match**: pool là toàn bộ **465.120** mã.
- **R-P-10** **Ranked Match**: pool là **464.948** mã — loại 172 mã thuộc 86
  cặp collision.
- **R-P-11** Cặp collision là hai mã không phân biệt được **kể cả khi biết
  toàn bộ clue**. Cả 86 cặp là một họ duy nhất: **đổi chỗ cột trái và cột
  phải** (vị trí 0↔2 và 3↔5), với cặp chữ số `(4,6)` ở một hàng và `(5,7)` ở
  hàng kia. Ví dụ `406517` ↔ `604715`.
- **R-P-12** Vị từ eligibility MUST kiểm chứng được bằng test, không phụ thuộc
  bất kỳ tham số runtime nào.
- **R-P-16** Ngoài R-P-10, Ranked MUST NOT có thêm bất kỳ **ngưỡng độ khó** nào
  (ví dụ chặn dưới về chi phí clue tối thiểu). #6 đo được độ khó đã gần như
  đồng đều — trung vị 12, p99 15, worst case 16 lần mua — và một ngưỡng như vậy
  cần cây quyết định tối ưu mà khoảng `[8, 16]` của #6 chưa đóng. Đây là từ
  chối có chủ ý, không phải thiếu sót.

Lý do R-P-10: với một cặp collision, người chơi suy luận hoàn hảo vẫn còn hai
ứng viên và buộc phải tung đồng xu — đúng vào lúc Score hai bên chênh nhau ít
nhất. Loại 0,037% pool rẻ hơn nhiều so với thêm clue phá đối xứng (phải tính
lại toàn bộ chi phí clue) hoặc đổi luật đoán sai (không xoá được 50/50, chỉ
đổi giá của nó).

### 2.5 Định danh và phân phát

- **R-P-13** Một Match có **đúng một** Puzzle, sinh lúc tạo Match, dùng chung
  cho Player và Opponent.
- **R-P-14** Puzzle MUST được giữ server-side và MUST được lưu bền cùng Match.
  Client nhận một `puzzle_id` **mờ**, và chỉ sau khi Match kết thúc (R-T-11).
  Hình dạng bản ghi thuộc [#14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14).
- **R-P-15** Mọi đáp án Clue MUST được tính trên server theo từng yêu cầu.

---

## 3. Player Board

- **R-B-01** Player Board có 42 ô LED×segment. Mỗi ô có đúng **hai** trạng
  thái: **tắt (0)** hoặc **bật (1)**.
- **R-B-02** Trạng thái thứ ba MUST NOT tồn tại ở phía server. Native có
  `hold = 2` và chính nó đẻ ra hai đường thắng chấm cùng một bàn cờ ra hai kết
  quả khác nhau.
- **R-B-03** Ghi chú nháp của người chơi (đánh dấu ứng viên) MAY tồn tại thuần
  client. Nó MUST NOT được gửi lên server và MUST NOT thuộc Player State.
- **R-B-04** Player Board **giải mã được** khi cả sáu LED đều khớp chính xác
  mẫu bảy đoạn của một chữ số `0..9`. Kết quả giải mã là một mã sáu chữ số.
- **R-B-05** Việc Player Board hiện **giải mã được hay không** MUST luôn sẵn
  có cho chính Player đó trước khi Verify, miễn phí. Tín hiệu này là hàm của
  riêng Player Board nên không rò rỉ bit nào về Puzzle. Cách trình bày thuộc
  [#13](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13).
- **R-B-06** Chỉ Player mới ghi được vào Player Board của mình. Không cơ chế
  nào khác được phép ghi vào nó.

---

## 4. Clue

### 4.1 Catalogue

- **R-C-01** Có đúng **32 Clue** mua được, chia ba họ:

| Họ | Số Clue | Mục tiêu | Đáp án |
| --- | --- | --- | --- |
| **Q1 — chẵn/lẻ** | 6 | một LED `T..Y` | `EVEN` hoặc `ODD` |
| **Q2 — so sánh** | 7 | một cặp LED kề nhau | `GREATER` hoặc `LESS` |
| **Q3 — bộ đếm** | 19 | một dải `A..S` | số nguyên |

- **R-C-02** Họ **Q4 (kiểm tra FULL) bị loại bỏ**. #6 chứng minh Q4 suy hoàn
  toàn từ Q3 (0 vi phạm trên toàn bộ 465.120 mã) và đứng một mình thì thô hơn
  Q3 **24,6 lần**. Giá trị thật duy nhất của nó là tác dụng phụ tự vẽ, mà
  R-C-09 cấm.

### 4.2 Q1 — chẵn/lẻ

- **R-C-03** Mục tiêu là một LED trong `T U V W X Y`. Đáp án là chữ số ở LED
  đó chẵn hay lẻ. `0` là chẵn.

### 4.3 Q2 — so sánh

- **R-C-04** Mục tiêu là một trong đúng **bảy cặp LED kề nhau**: `T-U`, `U-V`,
  `W-X`, `X-Y` (ngang) và `T-W`, `U-X`, `V-Y` (dọc). Cặp không kề nhau MUST bị
  từ chối là id không hợp lệ (R-I-04).
- **R-C-05** Đáp án là so sánh hai chữ số theo thứ tự cặp đã nêu: `GREATER`
  hoặc `LESS`.
- **R-C-06** Đáp án `EQUAL` MUST NOT tồn tại. R-P-04 cấm hai LED kề nhau bằng
  nhau, nên nhánh này là luật chết dưới ràng buộc sinh mã hiện hành. Native
  vẫn mang nhánh `'='` và một fallback `return 0`; sao chép chúng sẽ giấu một
  quyết định thiết kế chưa từng được đưa ra.

### 4.4 Q3 — bộ đếm

- **R-C-07** Mục tiêu là một trong 19 dải `A..S`. Đáp án là **số ô LED×segment
  đang sáng trong mã bí mật** thuộc dải đó. Đếm trên Puzzle, **không** đếm
  trên Player Board.

Chín dải **cột** (mỗi dải phủ hai LED cùng cột):

| ID | LED | Segment | Trần danh nghĩa | **Miền đạt được** |
| --- | --- | --- | --- | --- |
| `A` | `T`,`W` | `f`,`e` | 0–4 | 0–4 |
| `B` | `T`,`W` | `a`,`g`,`d` | 0–6 | **1–6** |
| `C` | `T`,`W` | `b`,`c` | 0–4 | **2–4** |
| `D` | `U`,`X` | `f`,`e` | 0–4 | 0–4 |
| `E` | `U`,`X` | `a`,`g`,`d` | 0–6 | **1–6** |
| `F` | `U`,`X` | `b`,`c` | 0–4 | **2–4** |
| `G` | `V`,`Y` | `f`,`e` | 0–4 | 0–4 |
| `H` | `V`,`Y` | `a`,`g`,`d` | 0–6 | **1–6** |
| `I` | `V`,`Y` | `b`,`c` | 0–4 | **2–4** |

Mười dải **hàng** (mỗi dải phủ ba LED cùng hàng):

| ID | LED | Segment | Trần danh nghĩa | **Miền đạt được** |
| --- | --- | --- | --- | --- |
| `J` | `T`,`U`,`V` | `a` | 0–3 | 0–3 |
| `K` | `T`,`U`,`V` | `f`,`b` | 0–6 | **3–6** |
| `L` | `T`,`U`,`V` | `g` | 0–3 | 0–3 |
| `M` | `T`,`U`,`V` | `e`,`c` | 0–6 | **3–6** |
| `N` | `T`,`U`,`V` | `d` | 0–3 | 0–3 |
| `O` | `W`,`X`,`Y` | `a` | 0–3 | 0–3 |
| `P` | `W`,`X`,`Y` | `f`,`b` | 0–6 | **3–6** |
| `Q` | `W`,`X`,`Y` | `g` | 0–3 | 0–3 |
| `R` | `W`,`X`,`Y` | `e`,`c` | 0–6 | **3–6** |
| `S` | `W`,`X`,`Y` | `d` | 0–3 | 0–3 |

- **R-C-08** Hai tập này là **hai phân hoạch độc lập của cùng 42 ô**: `A..I`
  phủ đúng 42 ô mỗi ô một lần, `J..S` cũng vậy.
- **R-C-16** Ma trận 19 bộ đếm có **hạng 17**, tức có đúng **hai** quan hệ
  tuyến tính nguyên thuỷ:

```text
  A + C + D + F + G + I  =  K + M + P + R
  B + E + H              =  J + L + N + O + Q + S
```

  Quan hệ quen thuộc `ΣA..I = ΣJ..S` chỉ là **tổng** của hai quan hệ trên, nên
  luôn có **hai** bộ đếm suy được từ 17 bộ còn lại, không phải một. Đây là tính
  chất **cố ý giữ lại** — xem R-C-14.

### 4.5 Mua Clue

- **R-C-09** Clue MUST chỉ trả **thông tin**. Nó MUST NOT ghi vào Player
  Board, MUST NOT bật hay khoá segment nào. Native tự vẽ và khoá nhóm khi kết
  quả là FULL, khiến hai Clue cùng giá 5 điểm có giá trị khác hẳn nhau tuỳ đáp
  án trả về.
- **R-C-10** MUST NOT tồn tại trạng thái "đang chờ chọn mục tiêu": loại Clue và
  mục tiêu của nó được chọn cùng nhau, nên không có khoảnh khắc nào Player đã
  cam kết mua mà chưa biết mình mua gì.
- **R-C-11** Không có **pending-question timeout**. Khung 10 giây và khoản
  phạt −1 điểm của native bị xoá hẳn: chúng là hệ quả của bàn phím sáu nút,
  không phải luật chơi.
- **R-C-12** Giá là **5 Score cho một Clue, một mục tiêu**, phẳng cho cả ba họ.
- **R-C-13** Mua lại **đúng một Clue đã sở hữu** MUST bị từ chối **tường minh
  và miễn phí**: không trừ Score, không tính là lần mua, không đổi state. Quy
  tắc này áp dụng như nhau cho cả ba họ.
- **R-C-14** Clue **suy ra được bằng logic** từ các Clue đã sở hữu (ví dụ bộ
  đếm thứ 19 theo R-C-08) MUST NOT bị chặn. Chỉ chặn trùng **cú pháp**. Nhận
  ra một Clue là dư thừa chính là kỹ năng của trò chơi; còn chặn suy diễn thì
  phải giải hệ ngay trong đường mua Clue và sẽ phá vỡ ngân sách mà #6 đã tính.
- **R-C-15** Mọi Clue đã mua và đáp án của nó MUST luôn sẵn có lại **miễn phí
  và không giới hạn** cho chính Player đó tới hết Match, kể cả sau khi Player
  đó vào terminal state. Đây là truy cập **chỉ-đọc** nên R-T-02 không chặn.

---

## 5. Score và đồng hồ

- **R-S-01** Mỗi Player khởi đầu **100 Score**.
- **R-S-02** Mỗi Match có **một Match Clock duy nhất**, wall-clock, chạy từ
  lúc Match bắt đầu. Mọi thời hạn đọc từ đồng hồ này.
- **R-S-03** **Không có Pause.** Native cho pause dừng đồng hồ, huỷ vĩnh viễn
  khung phạt và có thể khiến người chơi bất tử — #6 xếp là exploit hoàn chỉnh.
- **R-S-04** Mất kết nối MUST NOT dừng Match Clock.
- **R-S-05** Mỗi Player mất **1 Score mỗi 60 giây** Match Clock. Hao mòn
  **dừng** ngay khi Player đó vào terminal state: Score của họ được đóng băng
  làm bản ghi (R-V-06, R-V-10).
- **R-S-06** Deadline của Match là **15 phút** Match Clock, áp cho cả hai
  phía: Player và Opponent.
- **R-S-07** Score MUST NOT xuống dưới **0**. Hao mòn thời gian và phạt Wrong
  Guess đều dừng ở 0.
- **R-S-08** Mua Clue khi Score < 5 MUST bị từ chối tường minh. Không mua
  chịu, không Score âm.
- **R-S-09** Score bằng 0 **không** phải terminal. Player vẫn chơi tiếp, vẫn
  Verify được.

Ngân sách suy ra từ R-S-01, R-S-05, R-S-06 và R-C-12:

```text
100 Score, 5/Clue, −1 mỗi 60 giây, deadline 15:00

  hao mòn tối đa tới deadline : 15 Score
  còn lại cho Clue            : 85 Score -> 17 lần mua (kết thúc ở đúng 0)

  #6, adaptive greedy worst case : 16 lần mua   <- trần phủ được, dư 1
  #6, adaptive greedy p99        : 15 lần mua
  #6, adaptive greedy trung vị   : 12 lần mua
  #6, adaptive lower bound       :  8 lần mua
```

- **R-S-12** Trần này là **17**, không phải 16 như bảng ngân sách của #6. #6
  tính dưới luật native "Score ≤ 0 là thua", nên phải chừa lại ít nhất 1 Score;
  R-S-09 bỏ luật đó, nên lần mua thứ 17 hợp lệ và kết thúc ở đúng 0. Cùng lý
  do, con số cho hao mòn 30 giây là **14**, không phải 13.

- **R-S-10** Ngân sách này cố ý giữ tính chất: **không thể mua hết Clue**.
  32 Clue × 5 = 160 Score > 100.
- **R-S-11** Hao mòn 60 giây được chọn thay vì 30 giây của Notes map #1. Ở 30
  giây, trần là 14 lần mua — **thấp hơn** worst case 16 của chiến lược adaptive
  tốt nhất đã biết, nên ở những Puzzle khó nhất, người chơi giỏi nhất vẫn buộc
  phải đoán **theo chiến lược tốt nhất mà #6 trưng ra được**. Ở 60 giây, trần
  17 phủ được worst case đó với đúng một lần mua dư.
  Biên độ đó mỏng có chủ ý, và 16 mới chỉ là chặn trên heuristic — cây tối ưu
  có thể cần ít hơn, không bao giờ cần nhiều hơn.

  **Bổ sung sau khi #6 đóng** (`docs/plans/2026-08-24-clue-bounds/findings.md`,
  mục 2.3 và 2.4). Khoảng `[8, 16]` mà đoạn trên nhắc tới đã thu hẹp về
  `[10, 16]`; chặn dưới 10 là EXACT, chặn trên 16 vẫn là HEURISTIC. Chặn trên
  16 **tái lập được độc lập** — ba luật phá hoà khác nhau và nhiều clue mở đầu
  khác nhau đều đạt 16 — nên lập luận của R-S-11 đứng vững: cây tối ưu không
  bao giờ cần **hơn** 16, và trần 17 phủ được nó.

  Nhưng biên "dư đúng một lần mua" chỉ đúng với **cây tốt nhất đã biết**, không
  đúng với một chiến lược greedy bất kỳ. Quét 4 luật phá hoà × 32 clue mở đầu
  (128 lượt dựng cây đầy đủ) cho: **30 lượt đạt 16, 88 lượt cho 17, 10 lượt cho
  18**. Nghĩa là 98/128 cấu hình greedy hợp lý **dùng sạch trần 17 hoặc vượt
  nó**. Con số 16 mà R-S-11 dựa vào là thiểu số trong họ chiến lược của chính
  nó, và nó phụ thuộc một quy tắc phá hoà mà #6 **không ghi lại**.

  Điều này **không** đảo kết luận chọn 60 giây: ở 30 giây trần là 14, thấp hơn
  cả chặn trên 16 lẫn worst case 17 của đa số cấu hình greedy. 60 giây vẫn là
  lựa chọn đúng trong hai lựa chọn. Đoạn này chỉ ghi lại rằng **lý do** mỏng
  hơn con số "dư 1" ngụ ý, để ticket sau không thừa kế một biên an toàn không
  có thật.

---

## 6. Verify và Wrong Guess

- **R-V-01** Đường Solve **duy nhất của Player** là hành động **Verify tường
  minh** do Player phát ra.
- **R-V-02** Player Board khớp mã bí mật MUST NOT tự kích hoạt thắng. Native
  cho thắng ngay khi bàn cờ khớp, khiến đoán bằng cách vẽ trở nên **miễn phí
  và vô hạn lượt** và biến toàn bộ chính sách Wrong Guess thành trang trí:
  người chơi chỉ cần thu hẹp về ≤ 8 ứng viên (trung bình 9,43 lần mua) rồi vẽ
  thử cả 8, tiết kiệm khoảng 12 Score mỗi ván.
- **R-V-03** Server MUST NOT phát bất kỳ tín hiệu nào cho biết Player Board
  hiện đang đúng.
- **R-V-04** Verify **không bao giờ tốn Score** và MUST NOT bị giới hạn số
  lần, kể cả khi Score = 0. Nó khả dụng với Player đang `ACTIVE`, trừ đúng hai
  ngoại lệ: cửa sổ khoá 10 giây của R-V-08, và bàn cờ không giải mã được
  (R-V-05).
- **R-V-05** Verify trên Player Board **không giải mã được** (R-B-04) MUST bị
  từ chối **tường minh**: không phải Wrong Guess, không tính Strike, không mất
  Score, không đổi state. Đúng định nghĩa Wrong Guess trong `CONTEXT.md`.
- **R-V-06** Verify trên Player Board giải mã được, mã khớp Puzzle → **Solve**.
  Score tại thời điểm đó và **Solve Time** (mili giây từ Match start) MUST được
  ghi bền, vì R-T-05 xếp hạng dựa trên chúng. Player chuyển sang `SOLVED`.
- **R-V-07** Verify trên Player Board giải mã được, mã không khớp → **Wrong
  Guess**, tăng Strike.
- **R-V-08** **Strike thứ nhất**: −10 Score (sàn 0 theo R-S-07) và **khoá
  Verify 10 giây** Match Clock. Khoá chỉ khoá Verify; Player vẫn mua Clue và
  vẽ được. Đồng hồ vẫn chạy, nên khoá đã là hình phạt thật.
- **R-V-09** **Strike thứ hai**: Player chuyển sang `ELIMINATED` ngay.
- **R-V-10** `ELIMINATED` MUST NOT đưa Score về 0. Score là bản ghi lịch sử;
  thứ hạng đã do R-T-04 quyết định.
- **R-V-11** Hình phạt Wrong Guess là **state của server**. Mọi client MUST
  thấy giống hệt nhau. Native để hình phạt lần một nằm trong popup QML nên
  người chơi phần cứng không nhận gì cả.

---

## 6A. Bot Opponent contract

- **R-BOT-01** Bot Opponent MUST NOT là Player và MUST NOT có Player Board.
  Trạng thái riêng của nó là **Bot State**.
- **R-BOT-02** Bot Opponent nhận cùng Puzzle theo R-P-13 và được mua đúng cùng
  catalogue **32 Clue thật** ở R-C-01, với cùng giá, duplicate policy và quyền
  đọc lại. Đáp án Clue MUST được tính server-side và chỉ đưa vào Bot State của
  Bot Opponent đã mua; mã bí mật MUST NOT được đưa cho Bot Opponent. Mua Clue
  khi Bot Score < 5 MUST bị từ chối tường minh, miễn phí và không đổi Bot State.
- **R-BOT-03** **Bot Score** tại thời điểm `t` là:

  ```text
  max(0, 100 - 5 × số Clue đã mua
             - floor(t / 60 giây)
             - 10 × số Bot Submission sai)
  ```

  `t` đọc từ Match Clock và dừng tại thời điểm Bot Opponent vào terminal. Bot
  Score MUST đóng băng ở thời điểm đó và MUST NOT xuống dưới 0.
- **R-BOT-04** Bot Opponent dùng cùng Match Clock, cùng deadline **15 phút** và
  cùng quy tắc không Pause. Khi Match Clock chạm 15:00 mà Bot Opponent còn
  `ACTIVE`, Bot Terminal Status của nó chuyển thành `EXPIRED`.
- **R-BOT-05** **Bot Submission** là đường duy nhất có thể đưa Bot Opponent tới
  `SOLVED`. Bot Submission đúng Puzzle MUST ghi bền Bot Score và Solve Time rồi
  đặt Bot Terminal Status thành `SOLVED`. Không trạng thái nội bộ hay suy luận
  đúng nào được tự kích hoạt Solve.
- **R-BOT-06** Bot Submission không phải mã sáu chữ số hợp lệ MUST bị từ chối
  tường minh, miễn phí và không đổi Bot State. Bot Submission hợp lệ nhưng sai
  Puzzle MUST trừ **10 Bot Score** với sàn 0. Lần sai thứ nhất khoá riêng Bot
  Submission trong **10 giây Match Clock**; lần sai thứ hai đặt Bot Terminal
  Status thành `ELIMINATED`. Bot Submission trong cửa sổ khoá MUST bị từ chối
  tường minh, miễn phí và không đổi Bot State; Bot Opponent vẫn được mua Clue.
- **R-BOT-07** Bot Opponent bắt đầu `ACTIVE`. Bot Terminal Status chỉ có
  `SOLVED`, `ELIMINATED` hoặc `EXPIRED`; Bot Opponent MUST NOT có `FORFEITED`.
  Cả ba status là terminal và absorbing: sau đó mọi hành động làm đổi Bot State
  MUST bị từ chối, còn Clue đã mua vẫn đọc lại được.
- **R-BOT-08** Thứ tự outcome và tiebreak ở R-T-04 và R-T-05 áp dụng không đổi
  khi Opponent là Bot Opponent. Khi cả hai Solve, Score của Player được so với
  Bot Score; bằng nhau thì Solve Time sớm hơn thắng, rồi mới Draw.
- **R-BOT-09** Match có Bot Opponent chỉ kết thúc khi Player ở terminal state
  và Bot Opponent có Bot Terminal Status. Một phía terminal sớm không kết thúc
  Match.
- **R-BOT-10** Trong khi Match đang chạy, Player và Bot Opponent MUST bị che
  thông tin đối ứng: Player không thấy Bot State, Bot Score, Clue đã mua, Bot
  Submission hay Bot Terminal Status; Bot Opponent không nhận Player State,
  Score, Clue đã mua, Player Board, Verify hay terminal state. Bot Opponent
  MUST luôn được gắn nhãn nhìn thấy rõ và MUST NOT được trình bày trạng thái
  kết nối giả.
- **R-BOT-11** Server là authoritative cho toàn bộ Bot State, Bot Score, Bot
  Submission và Bot Terminal Status. Chỉ sau khi Match kết thúc theo R-BOT-09,
  kết quả cuối mới MUST công bố mã bí mật, terminal state của Player, Bot
  Terminal Status, Score, Bot Score, các Solve Time có tồn tại và Match outcome.

---

## 7. Terminal state và Match outcome

- **R-T-01** Mỗi Player trong Match có đúng một trạng thái:

| State | Vào bằng |
| --- | --- |
| `ACTIVE` | Match bắt đầu |
| `SOLVED` | Verify đúng (R-V-06) |
| `ELIMINATED` | Strike thứ hai (R-V-09) |
| `EXPIRED` | Match Clock chạm 15:00 khi còn `ACTIVE` |
| `FORFEITED` | Player chủ động bỏ cuộc (R-T-06) |

- **R-T-02** Bốn state sau là **terminal và absorbing**. Sau khi vào terminal,
  **mọi hành động làm đổi state** của Player đó MUST bị từ chối: không Verify,
  không mua Clue, không vẽ, không bỏ cuộc. Không ngoại lệ. Truy cập **chỉ-đọc**
  vào Clue đã mua vẫn mở (R-C-15). Đây là bug nghiêm trọng nhất của native —
  thua không xoá mã bí mật nên vẫn mua Clue và vẫn "thắng" lại được sau đó.
- **R-T-03** Hết Score **không** phải terminal (R-S-09).
- **R-T-04** Thứ hạng terminal giữa **hai state khác nhau**, cao xuống thấp:

```text
  SOLVED  >  ELIMINATED  =  EXPIRED  >  FORFEITED
```

  Khi Player và Opponent cùng ở `SOLVED`, R-T-05.1 quyết định; khi cùng ở một
  terminal label không phải `SOLVED`, kết quả là Draw (R-T-05.4).

- **R-T-05** Match outcome:
  1. **Player và Opponent đều `SOLVED`** → so Score của Player với Score của
     Opponent nếu Opponent là Player, hoặc với Bot Score nếu Opponent là Bot
     Opponent. Giá trị cao hơn thắng; bằng nhau → **Solve Time sớm hơn** thắng;
     bằng nhau cả hai → **Draw**.
  2. **Đúng một phía `SOLVED`** → phía đó thắng, không xét Score hoặc Bot Score.
  3. **Không phía nào `SOLVED`, đúng một Player `FORFEITED`** → Opponent của
     Player đó thắng.
  4. **Không phía nào `SOLVED`, còn lại** → **Draw**, bất kể Score, Bot Score
     và lý do terminal.
- **R-T-06** Bỏ cuộc là **hành động chủ động, tường minh**. Nó là **thua**,
  bất kể đối thủ đang ở state nào. Nếu bỏ cuộc chỉ đưa về `ELIMINATED` thì
  người đang thua có thể **ép hoà** bằng cách bỏ cuộc khi đối thủ cũng chưa
  Solve — R-T-04 xếp `FORFEITED` dưới cùng chính để bịt đường đó.
- **R-T-07** Mất kết nối rồi không quay lại **không phải** bỏ cuộc: đồng hồ
  chạy tiếp tới deadline rồi `EXPIRED`. Không thể phân biệt rage-quit với rớt
  mạng, nên MUST NOT cố phân biệt.
- **R-T-08** Match đang chạy MUST NOT bị huỷ, reset hay sinh lại Puzzle bởi
  bất kỳ ai — Ranked lẫn Practice, không kể Player, đối thủ hay người vận hành.
  Bỏ cuộc (R-T-06) là đường thoát duy nhất, và nó là thua chứ không phải huỷ.
  Native để `generateRandomPuzzle()` là lệnh huỷ diệt không xác nhận, gọi được
  bất cứ lúc nào bởi bất kỳ client nào.
- **R-T-11** **Match kết thúc** khi Player và Opponent đều terminal.
  Đến lúc đó mới đánh giá R-T-05, mới lộ thông tin theo R-O-02, và mới phát
  `puzzle_id` theo R-P-14. Một Player vào terminal sớm **không** kết thúc Match;
  Opponent vẫn chơi tới hết deadline nếu còn active.

Lý do nhánh Draw ở R-T-05.4: xếp hạng bằng Score còn lại sẽ thưởng cho người
**không mua Clue**, tức thưởng cho việc không chơi.

---

## 8. Thông tin đối thủ

- **R-O-01** Trong lúc Match đang chạy, một Player MUST thấy Match Clock chung
  và loại Opponent. Nếu Opponent là Player, Player đó MUST thấy trạng thái kết
  nối online/offline; nếu Opponent là Bot Opponent, nhãn **Bot** MUST luôn hiện
  rõ và trạng thái kết nối MUST NOT được dựng giả.
- **R-O-02** Score hoặc Bot Score của Opponent, số Clue đã mua, Player Board
  nếu Opponent là Player, Bot State, và **việc Opponent đã Solve hay chưa**
  MUST NOT lộ ra trước khi Match kết thúc (R-T-11).
- **R-O-03** Khi Match kết thúc, Player MUST thấy: mã bí mật, terminal state
  của Player, terminal state hoặc Bot Terminal Status của Opponent, Score cuối,
  Score hoặc Bot Score cuối của Opponent, các Solve Time có tồn tại, và Match
  outcome. Clue nào Opponent đã mua thuộc phạm vi lịch sử đấu ở
  [#14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14).

Lý do R-O-02: biết đối thủ đã Solve sẽ biến phần còn lại thành đoán liều, mà
theo R-V-08 đoán liều bị phạt — kết quả khi đó do ai nhận tín hiệu trước quyết
định, không phải do suy luận.

---

## 9. Toàn vẹn

Mục này đặt **ràng buộc luật chơi** lên threat model; nó không thay thế
[Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12).

- **R-I-01** Server là **authoritative** cho toàn bộ Score, Bot Score, Strike,
  Clue đã mua, Player State, Bot State, Bot Submission, Bot Terminal Status và
  đồng hồ.
- **R-I-02** Mã bí mật MUST NOT rời server trong khi Match còn chạy: không
  trong payload, không trong log, không trong response nào, không suy ra được
  từ đáp án Clue của người khác. Nó chỉ được phát **một lần duy nhất**, trong
  kết quả cuối, sau R-T-11. MUST NOT ghi ra log ở bất kỳ thời điểm nào.
- **R-I-03** Đáp án Clue MUST chỉ được cung cấp cho đúng Player hoặc Bot
  Opponent đã mua Clue đó.
- **R-I-04** Mọi id MUST được kiểm bằng **whitelist chính xác**: `T..Y` cho
  LED, đúng bảy cặp cho Q2, `A..S` cho bộ đếm. Id ngoài whitelist → lỗi tường
  minh, không mất Score, không đổi state. Native "validate" bằng so sánh chuỗi
  lexicographic nên `"AB"` lọt lưới và được xử lý như cột `A`.
- **R-I-05** Input không hợp lệ MUST NOT bị nuốt im lặng. Native `return` lặng
  lẽ ở nhiều nhánh, khiến người chơi tưởng đã hành động trong khi đồng hồ phạt
  vẫn chạy.
- **R-I-06** Một hành động của Player MUST mang đúng **một** nghĩa luật chơi.
  Native để một lần bấm nút vừa trả lời Clue vừa đổi LED đang vẽ.

---

## 10. Ruleset và giá trị configurable

- **R-K-01** Ruleset là một object **có tên và version**. Mọi Match MUST ghi
  bền `ruleset_id` mà nó được chơi dưới đó. Đổi bất kỳ giá trị nào ở R-K-02 là
  **bump version**.
- **R-K-02** **Configurable**:

| Tham số | Giá trị `1.0.0` |
| --- | --- |
| Score khởi đầu | 100 |
| Giá Clue | 5 |
| Chu kỳ hao mòn | 60 giây |
| Deadline Match | 15 phút |
| Phạt Wrong Guess lần đầu | −10 |
| Thời lượng khoá Verify | 10 giây |
| Số Strike tối đa | 2 |
| Ranked loại collision | bật |

- **R-K-03** **Không configurable** — đổi là đổi trò chơi, MUST sửa spec và
  bump minor/major: hình học bàn 2×3, catalogue Clue và semantics của Q1/Q2/Q3,
  ba ràng buộc sinh mã (R-P-04), và các điều kiện kích hoạt Solve (R-V-01,
  R-BOT-05).
- **R-K-04** Hai Match chỉ so sánh được về mặt luật chơi nếu **cùng
  `ruleset_id`**. Spec này không quyết định Elo xử lý ra sao khi ruleset đổi —
  đó là đầu vào cứng cho
  [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15).
- **R-K-05** Một Ruleset hợp lệ MUST giữ `Score khởi đầu < 32 × giá Clue`, nếu
  không thì tính chất "không bao giờ mua hết Clue" ở R-S-10 bị phá âm thầm.

---

## 11. Đối chiếu: 20 hành vi native cấm đóng băng

Danh sách gốc ở `native-behaviors.md` mục 2 của #6. Cột cuối là cách spec này
xử lý — không mục nào bị port.

| # | Hành vi native | Spec xử lý |
| --- | --- | --- |
| 1 | Thắng tự động khi bàn cờ khớp mã | Bỏ. R-V-01, R-V-02 |
| 2 | Auto-fill không kích hoạt kiểm tra thắng | Không tồn tại. R-C-09 bỏ auto-fill; R-V-01 bỏ auto-detect |
| 3 | `hold = 2` được VERIFY nhận nhưng auto-detect từ chối | Không tồn tại. R-B-01 chỉ hai trạng thái; Player chỉ còn một đường Solve |
| 4 | Thua không xoá mã bí mật (không có terminal) | Bỏ. R-T-02 terminal absorbing |
| 5 | `pauseGame`/`resumeGame` | Bỏ. R-S-03 |
| 6 | Kiểm tra thua chỉ chạy trong slot timer | Không tồn tại. R-S-07/09 bỏ hẳn nhánh thua vì hết Score |
| 7 | Sai lần 1 không mất gì, phần cứng không nhận phản hồi | Bỏ. R-V-08, R-V-11 |
| 8 | Q4 tính tiền câu trùng, Q1–Q3 thì không | Không tồn tại. R-C-02 bỏ Q4; R-C-13 thống nhất mọi họ |
| 9 | Q3 khoá Q4 nhưng Q4 không khoá Q3 | Không tồn tại. R-C-02 |
| 10 | Nhánh `'='` của Q2 và fallback `return 0` | Bỏ. R-C-06 |
| 11 | Bias phân phối của rejection sampler | Bỏ. R-P-07, R-P-08 |
| 12 | Validate id bằng so sánh chuỗi | Bỏ. R-I-04 |
| 13 | WebSocket không xác thực, broadcast đáp án | Bỏ. R-I-01, R-I-02, R-I-03, R-O-02 |
| 14 | In mã bí mật ra log | Bỏ. R-I-02 |
| 15 | −1 mỗi 60 giây, không deadline | Quyết định lại có chủ ý: R-S-05 giữ 60 giây (lý do ở R-S-11), R-S-06 thêm deadline |
| 16 | Một nút vừa trả lời Clue vừa chọn LED | Bỏ. R-C-10, R-I-06 |
| 17 | State ván cũ rò sang ván mới | Không tồn tại. R-P-13 Puzzle gắn Match; R-T-08 cấm reset |
| 18 | Code chết (`m_backups`, `DraftGrid`, …) | Không port. Ghi chú nháp nếu có là thuần client, R-B-03 |
| 19 | Giá phẳng 5 điểm kể cả Clue suy ra được | Giữ có chủ ý. R-C-12, R-C-14 — lý do ở R-C-14 |
| 20 | Auto-fill khi FULL làm hộ thao tác vẽ | Bỏ. R-C-09 |

Mục 15 và 19 là hai mục spec **cố ý giữ giá trị của native**, nhưng là quyết
định chủ động kèm lý do, không phải kế thừa mặc định.

---

## 12. Spec này KHÔNG quyết định

Thuộc ticket khác, MUST tôn trọng luật ở trên:

| Vấn đề | Ticket |
| --- | --- |
| Match lifecycle chi tiết, reconnect handshake, concurrency/idempotency của đường Room; biến thể cho Matchmaking Queue | [#4](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4), [#31](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/31) |
| Threat model, anti-cheat, rate limit | [#12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) |
| Elo: Draw settlement, provisional, đối thủ lặp lại, correction | [#15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| Data model, lịch sử đấu, quyền riêng tư | [#14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| UX cụ thể của Player Board, Clue và Verify | [#13](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| Repo topology và coexistence với Qt/ESP32 | [#11](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/11) |
| Hàm hiệu chuẩn Ranked Rating thành Bot Score mục tiêu và hành vi solver | [#30](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30) |
| Telemetry tối thiểu để kiểm chứng cân bằng gameplay | [#35](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/35) |

**Đầu vào cứng** mà các ticket đó MUST nhận nguyên trạng: R-P-14 và R-I-02 (mã
bí mật không rời server tới hết Match), R-S-04 và R-T-07 (đồng hồ không dừng khi
mất kết nối), R-T-11 và R-BOT-09 (Match kết thúc khi Player và Opponent đều
terminal), và R-K-04 (chỉ Match cùng `ruleset_id` mới so sánh được).

---

## 13. Invariant mà test MUST ghim

Mỗi dòng dưới đây kiểm chứng được mà không cần chạy web app:

1. Tập mã hợp lệ có đúng **465.120** phần tử; pool Ranked có đúng **464.948**.
2. Đúng **86** cặp collision, và cả 86 thuộc họ đổi cột đã mô tả ở R-P-11.
3. Lấy mẫu Ranked là uniform: mọi mã trong pool có xác suất bằng nhau, kiểm
   bằng số học chính xác chứ không bằng tần suất.
4. `A..I` và `J..S` mỗi bên phủ đúng 42 ô LED×segment, mỗi ô đúng một lần.
5. Với mỗi bộ đếm, tập giá trị **thực sự đạt được** trên pool đúng bằng cột
   "Miền đạt được" ở R-C-07 — mười trong mười chín bộ hẹp hơn trần danh nghĩa,
   và mọi miền đều liên tục.
6. Ma trận 19 bộ đếm có hạng **17**, tức đúng hai quan hệ tuyến tính nguyên
   thuỷ như R-C-16 (không phải một).
7. Không mã hợp lệ nào khiến Q2 trả `EQUAL`.
8. Mua đủ 32 Clue tốn 160 Score > 100 — không ván nào mua hết được.
9. Ở deadline 15:00 với hao mòn 60 giây, trần là **17** lần mua; với hao
   mòn 30 giây là **14**. Dưới luật native "Score ≤ 0 là thua" hai con số
   này là 16 và 13 — chênh lệch đúng bằng hệ quả của R-S-09.
10. Mọi hành động làm đổi state sau terminal đều bị từ chối, với cả bốn terminal state.
11. Verify trên Player Board không giải mã được không làm đổi Score lẫn Strike.
12. Bot Opponent không có Player Board; chỉ Bot Submission đúng mới đưa nó tới
    `SOLVED`.
13. Với mọi Bot State, Bot Score bằng đúng
    `max(0, 100 - 5 × clue - floor(t/60 giây) - 10 × submission sai)` và không
    đổi sau `SOLVED`, `ELIMINATED` hoặc `EXPIRED`.
14. Bot Terminal Status không bao giờ là `FORFEITED`; Match Player-vs-Bot chỉ
    kết thúc khi Player và Bot Opponent đều terminal, và trước đó Player không
    nhận bất kỳ Bot State ẩn nào ngoài nhãn Bot.
