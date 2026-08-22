# Tính toàn vẹn Elo cho Match mời riêng

Ngày nghiên cứu: 2026-08-22
Wayfinder ticket: [#10](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10)
Map liên quan: [#1](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)

## Kết luận nghiên cứu

Không có một policy “Elo chuẩn” tự quyết định cách xử lý provisional, forfeit,
disconnect, timeout, đối thủ lặp lại hay correction. Elo chỉ biến một kết quả đã
được hệ thống chấp nhận thành thay đổi rating. DigitCode cần chốt riêng các policy
này, nhưng có thể giữ các invariant kỹ thuật độc lập với policy:

1. Với cùng một hệ số `K`, score bổ sung nhau (`S_B = 1 - S_A`) và cùng một quy
   tắc lượng tử hóa, cập nhật 1v1 có thể zero-sum chính xác bằng cách tính một
   transfer rồi áp `+T/-T` (chứng minh tại §1.3).
2. `1000` chỉ là gốc hiển thị; xác suất chỉ phụ thuộc chênh lệch rating. `K=32`
   điều khiển tốc độ thích nghi và độ lớn transfer, không phải hằng số được FIDE
   quy định phổ quát. ([FIDE §8.1-8.3][fide-rating])
3. Draw là `0.5/0.5`, nhưng chỉ không đổi rating khi hai người có expected score
   bằng nhau. Người rating thấp được điểm sau một draw với người rating cao
   (ví dụ tại §1.4; score source: [FIDE §8.3.2][fide-rating]).
4. Forfeit/timeout là policy eligibility trước khi là input Elo. Nguồn chính
   thống cũng chọn khác nhau theo bối cảnh: FIDE không tính game chưa chơi do
   forfeit, trong khi FIDE Online Arena xử disconnect quá 60 giây thành thua.
   ([FIDE §5.1][fide-rating]; [FIDE Online Arena §2.4][fide-online])
5. Provisional có thể chỉ là nhãn, có thể đổi `K`, hoặc có thể trì hoãn/protect
   rating. Hai lựa chọn sau dễ xung đột với strict zero-sum nếu hai bên nhận hệ số
   khác nhau hoặc chỉ một bên được cập nhật. ([FIDE §7.1.4, §8.3.3][fide-rating];
   [FIDE Online Arena §3.6-3.10][fide-online])
6. Zero-sum không ngăn boosting: collusion vẫn chuyển điểm từ donor sang
   recipient. Tài khoản mới ở baseline tạo nguồn donor mới; việc donor rời khỏi
   tập active có thể làm rating của nhóm active trông bị inflation dù tổng điểm
   trên toàn bộ tài khoản vẫn được bảo toàn. ([Lichess Terms][lichess-terms] định
   nghĩa boosting/sandbagging; hệ quả transfer tại §4.2.)
7. Trong population nhỏ, nhiều game cùng một cặp chủ yếu đo chênh lệch trong cặp;
   các nhóm không có game nối chéo không cung cấp bằng chứng để so sánh tuyệt đối.
   Vì vậy opponent diversity và repeated-pair handling là policy riêng, không
   phải tính chất sẵn có của Elo. ([Bradley & Terry 1952][bradley-terry]; §4.1.)
8. Idempotency theo `match_id` chỉ chặn settlement trùng cùng Match; nó không chặn
   lost update khi hai Match khác nhau cùng cập nhật một Player. Cần transaction
   atomic cộng với row lock theo thứ tự cố định hoặc serializable transaction có
   retry. ([PostgreSQL Transactions][pg-transactions]; [Locking][pg-locking];
   [Isolation][pg-isolation])
9. Elo phụ thuộc thứ tự. Hệ thống phải có một total order bền vững cho rating
   events; chỉ dùng timestamp từ client hoặc để race ngẫu nhiên quyết định order
   sẽ làm kết quả khó tái dựng (counterexample tại §5.3).
10. Audit ledger nên append-only và lưu đủ input/output/formula version. Tuy
     nhiên, reversal ở thời điểm hiện tại chỉ hoàn lại điểm; nó không tương đương
     replay lịch sử vì các expected score về sau đã dùng rating sai.
     ([TigerBeetle correction pattern][tb-corrections]; hệ quả Elo tại §7.2.)

Đây là resolution bằng dữ kiện và decision inputs, **không chọn policy thay sản
phẩm**.

## Phạm vi và cách đọc

Phạm vi là Ranked Match 1v1 invite-only, population thấp. Các preference đang có
từ map là rating ban đầu `1000`, `K=32`, không dùng margin of victory; Practice
Match không cập nhật Elo. Tài liệu không thiết kế UI, không chọn database và không
triển khai app.

Mỗi kết luận được gắn một loại:

- **FACT**: điều nguồn sơ cấp/chính thống thực sự quy định hoặc triển khai.
- **MATH**: hệ quả suy ra từ công thức, không phải policy của nguồn.
- **CHOICE**: quyết định sản phẩm/kiến trúc DigitCode còn phải chốt.

FIDE là ví dụ authoritative về vận hành rating cờ vua, không phải đặc tả game
DigitCode. Lichess là nguồn first-party cho định nghĩa abuse đang được một dịch vụ
rating vận hành dùng, không phải nguồn cho công thức Elo. TigerBeetle là nguồn
first-party cho pattern ledger/idempotency/correction, không phải đề xuất thêm nó
vào stack.

## 1. Công thức, baseline và zero-sum

### 1.1 Phần được nguồn authoritative xác nhận

**FACT.** FIDE gọi rating scale là tùy ý, đặt class interval 200 điểm, đổi chênh
lệch rating thành expected score bằng bảng `PD`, rồi tính mỗi game theo
`Delta R = score - PD`, với score là `1`, `0.5` hoặc `0`; tổng được nhân với `K`.
FIDE hiện dùng `K=40`, `20` hoặc `10` tùy trạng thái Player, không có một `K` phổ
quát. ([FIDE Rating Regulations §8.1-8.3][fide-rating])

**FACT.** Bảng FIDE cho expected score xấp xỉ `0.76/0.24` ở chênh lệch khoảng
200 điểm. Quy định FIDE là bảng rời rạc, không phải lời xác nhận rằng mọi sản phẩm
phải dùng đúng một biểu thức logistic liên tục. ([FIDE Rating Regulations
§8.1.2][fide-rating])

**FACT.** Mô hình paired-comparison Bradley-Terry gán xác suất thắng
`P(A>B) = p_A / (p_A + p_B)` từ hai strength dương. Đây là paper gốc về paired
comparisons trên incomplete block designs. ([Bradley & Terry 1952][bradley-terry])

### 1.2 Một dạng liên tục để DigitCode cân nhắc

**CHOICE.** Nếu DigitCode chọn mapping `p_i = 10^(R_i/400)` cho mô hình
Bradley-Terry, ta có dạng logistic liên tục quen thuộc:

```text
E_A = 1 / (1 + 10^((R_B - R_A) / 400))
E_B = 1 - E_A

Delta_A = K * (S_A - E_A)
Delta_B = K * (S_B - E_B)

R'_A = R_A + Delta_A
R'_B = R_B + Delta_B
```

Trong đó `S=1` cho win, `S=0.5` cho draw, `S=0` cho loss. Dạng này cho
`E=0.759746...` ở chênh lệch 200, gần giá trị `0.76` trong bảng FIDE. DigitCode
vẫn phải chốt dùng logistic liên tục hay lookup/interpolation, có cap chênh lệch
hay không, và precision/rounding nào. FIDE, chẳng hạn, áp một cap 400 điểm trong
một số trường hợp; đó là policy của FIDE chứ không phải hệ quả bắt buộc của Elo.
([FIDE Rating Regulations §8.3.1][fide-rating])

Không nên mô tả biểu thức liên tục trên là “công thức gốc bắt buộc của Elo” dựa
chỉ vào FIDE: nguồn FIDE được trích ở đây công bố bảng conversion và update rule.

### 1.3 Chứng minh zero-sum

**MATH.** Với cùng `K`, `S_B=1-S_A` và `E_B=1-E_A`:

```text
Delta_A + Delta_B
= K(S_A - E_A) + K((1 - S_A) - (1 - E_A))
= 0
```

Do đó một Match hợp lệ có thể là transfer điểm, không sinh/hủy điểm. Nếu cần
zero-sum **sau khi làm tròn**, cách biểu diễn invariant là tính đúng một lượng:

```text
T = quantize(K * (S_A - E_A))
R'_A = R_A + T
R'_B = R_B - T
```

Đây là constraint thiết kế, không phải yêu cầu từ FIDE.

### 1.4 Ví dụ với preference `1000`, `K=32`

Các số dưới đây dùng logistic liên tục và chưa làm tròn:

| `R_A` | `R_B` | Kết quả A | `E_A` | `Delta_A` | `Delta_B` |
| ---: | ---: | --- | ---: | ---: | ---: |
| 1000 | 1000 | win | 0.5000 | +16.0000 | -16.0000 |
| 1000 | 1000 | draw | 0.5000 | 0.0000 | 0.0000 |
| 1000 | 1200 | win | 0.2403 | +24.3119 | -24.3119 |
| 1000 | 1200 | draw | 0.2403 | +8.3119 | -8.3119 |
| 1000 | 1200 | loss | 0.2403 | -7.6881 | +7.6881 |

**MATH.** Draw không đồng nghĩa “không đổi rating”; nó kéo cặp về gần nhau trừ
khi `E_A=E_B=0.5`.

**MATH.** Cộng cùng một hằng số vào mọi rating không đổi expected score. Vì vậy
baseline `1000` đặt gốc hiển thị và tổng điểm được seed cho mỗi account, không
mang ý nghĩa xác suất riêng. Điều này phù hợp với nhận định của FIDE rằng scale
là tùy ý. ([FIDE Rating Regulations §8.1][fide-rating])

### 1.5 Những cách làm mất zero-sum

**MATH.** Strict zero-sum bị phá khi có ít nhất một điều sau:

- hai Player dùng `K` khác nhau;
- score không bổ sung nhau, ví dụ “double loss” `0/0`;
- làm tròn hoặc clamp hai phía độc lập;
- rating floor chặn một phía nhưng không chuyển phần dư;
- provisional/penalty/admin adjustment chỉ cập nhật một phía;
- correction sửa/xóa một current rating mà không có entry đối ứng.

Ví dụ equal-rating, provisional dùng `K_A=40`, established dùng `K_B=20`, A
thắng: A nhận `+20`, B mất `-10`, tổng pool tăng `10`. Đây là hệ quả toán học của
per-player `K`; FIDE thực tế dùng các `K` khác nhau, nên không nên lấy FIDE làm
bằng chứng rằng mọi cập nhật của họ strict zero-sum. ([FIDE Rating Regulations
§8.3.3][fide-rating])

Với cùng `K`, tổng thay đổi khi score pair không bổ sung là:

```text
Delta_total = K * (S_A + S_B - 1)
```

Vì vậy `0/0` làm mất đúng `K` điểm, còn `1/1` sinh đúng `K` điểm. “Cả hai đều
thua” nên được coi là một product choice có tác động đến pool, không phải biến thể
vô hại của draw.

## 2. Draw, forfeit, disconnect và timeout

### 2.1 Elo không quyết định eligibility

**FACT.** FIDE không count game chưa chơi do forfeiture hoặc lý do khác. Ngoại
trừ force majeure/fair-play, game mà cả hai đã đi ít nhất một nước thì được rate.
([FIDE Rating Regulations §5.1][fide-rating])

**FACT.** FIDE Online Arena lại quy định client thử reconnect và, nếu không thể
trong 60 giây, game được tuyên thua cho Player bị disconnect. ([FIDE Online Arena
§2.4][fide-online])

Hai quy định cùng thuộc FIDE nhưng phục vụ hai bối cảnh khác nhau. Chúng là bằng
chứng rằng “forfeit/timeout luôn là loss” hoặc “forfeit không bao giờ được rate”
đều không phải fact phổ quát của Elo.

### 2.2 Ma trận cần chốt cho DigitCode

**CHOICE.** Mỗi terminal reason cần được map riêng sang `(rating_eligible,
S_A, S_B)`; không nên suy ra chỉ từ một cột `winner_id`.

| Terminal reason cần phân biệt | Input Elo hợp lệ nếu rate | Câu hỏi policy |
| --- | --- | --- |
| Kết thúc game bình thường | `1/0`, `0/1` hoặc `0.5/0.5` | Game rule nào tạo draw sau khi so Score và Solve time? |
| Bị loại theo luật game | thường là `0/1` hoặc `1/0` | Đây có luôn là competitive loss hay có case void? |
| Resign/forfeit sau khi Match đã bắt đầu | nếu rate thì `0/1` | Mốc nào chứng minh Match thực sự bắt đầu? |
| No-show, invite hết hạn, chưa có gameplay | không có input bắt buộc | Unrated/void hay rated forfeit? |
| Client disconnect | nếu rate thì phía lỗi nhận `0` | Reconnect grace, bằng chứng lỗi phía nào, và server outage? |
| Deadline 15 phút | kết quả bổ sung nhau nếu rate | Một người solved, cả hai unsolved, hoặc trạng thái hòa được xử thế nào? |
| Lỗi platform/DB/realtime | không có input bắt buộc | Void hay phục hồi Match; ai có quyền xác nhận? |
| Cả hai vi phạm/bỏ cuộc | `0/0` không zero-sum | Void, draw, hay non-zero-sum double loss có chủ ý? |
| Admin/fair-play invalidation | tùy correction policy | Reverse forward-only hay replay lịch sử? |

**MATH.** Nếu strict zero-sum là invariant, mọi rated outcome phải có
`S_A+S_B=1`; các trạng thái không thỏa điều này phải void hoặc được thiết kế rõ là
adjustment ngoài Elo.

## 3. Provisional handling

### 3.1 Các practice chính thống không đồng nhất

**FACT.** FIDE chỉ publish initial rating sau ít nhất 5 game với rated opponents;
sau đó dùng `K=40` cho Player mới cho đến khi hoàn thành ít nhất 30 game, rồi có
thể chuyển sang `K=20` hoặc `10`. ([FIDE Rating Regulations §7.1.4,
§8.2-8.3][fide-rating])

**FACT.** FIDE Online Arena yêu cầu Player unrated trước hết phải draw/win một
rated opponent rồi hoàn thành thêm 4 game với rated opponents để tạo first rating;
Arena không đổi rating của rated opponent trong giai đoạn đó, rồi dùng `K=40` đến
30 rated games. Arena giữ hai chữ số thập phân nội bộ và chỉ round rating để
display. ([FIDE Online Arena §3.1, §3.6-3.13][fide-online])

Đây là các lựa chọn vận hành của FIDE. Chúng cho thấy provisional có thể tác động
đến publication, initialization, opponent protection, `K` và precision, nhưng
không chứng minh DigitCode phải sao chép bất kỳ ngưỡng nào.

### 3.2 Các option và hệ quả

**CHOICE.** Các option dưới đây loại trừ hoặc kết hợp được tùy policy; bảng không
xếp hạng chúng.

| Option provisional | Zero-sum | Hệ quả cần chấp nhận |
| --- | --- | --- |
| Update từ game đầu với `K=32`, chỉ gắn nhãn/ẩn display | Có thể giữ | Provisional không làm rating hội tụ nhanh hơn; chỉ truyền đạt độ non trẻ |
| Match-level K cao hơn khi ít nhất một bên provisional, cùng transfer `+T/-T` | Có thể giữ | Cả established opponent cũng biến động mạnh hơn |
| Per-player K cao cho provisional, thấp cho established | Không tự giữ | Pool sinh/hủy điểm theo upset và draw |
| Provisional thay đổi, established được bảo vệ | Không giữ theo từng Match | Tạo rating một phía, tương tự một practice của FIDE Online Arena |
| Chờ đủ `N` game rồi tính initial rating theo batch | Không phải transfer tuần tự đơn giản | Phải định nghĩa ảnh hưởng lên opponents và xử kết quả đến muộn |
| Freeze ở `1000` đến đủ điều kiện | Không phản ánh evidence trong thời gian freeze | Dễ tạo expected score sai cho các Match đầu |

Các input cần chốt cùng policy:

- `N` game nào kết thúc provisional;
- chỉ count Rated settled/non-void hay cả Practice/forfeit;
- có yêu cầu số đối thủ khác nhau hay không;
- repeated games với cùng một opponent count bao nhiêu;
- provisional rating được hiển thị, ẩn hay kèm nhãn;
- trạng thái provisional có quay lại sau inactivity/correction hay không;
- `K=32` áp cho mọi Player hay chỉ established.

## 4. Population thấp, đối thủ lặp lại và collusion

### 4.1 Điều có thể suy ra từ mô hình

**MATH.** Expected score chỉ dùng `R_A-R_B`. Trong graph mà node là Player và
edge là rated Match, dữ liệu trong một connected component không chứa bằng chứng
để đặt component đó cao/thấp hơn một component không có edge nối chéo. Baseline
chung có thể ép mean ban đầu của mỗi component về `1000`, nhưng đó là prior/policy,
không phải so sánh được quan sát giữa hai nhóm. Bradley-Terry được xây cho paired
comparisons, kể cả incomplete block designs; tính bất biến theo một offset chung
là hệ quả trực tiếp của xác suất theo tỷ lệ strength. ([Bradley & Terry
1952][bradley-terry])

**MATH.** Nhiều game chân thực cùng một cặp tiếp tục cung cấp evidence về chênh
lệch trong cặp, nhưng không tăng connectivity của pool. Vì vậy “repeated opponent”
không tự nó là abuse, đặc biệt trong population nhỏ.

### 4.2 Zero-sum không ngăn boosting

**FACT.** Lichess định nghĩa boosting là làm rating tăng giả tạo, ví dụ dàn xếp
win trước; sandbagging là cố tình làm rating giảm, ví dụ resign sớm hoặc cố tình
loss/draw không nỗ lực. Lichess cũng hạn chế multiple accounts. Đây là policy
first-party của một rating service, không phải theorem Elo. ([Lichess Terms,
“Fair Play Violations”][lichess-terms])

**MATH.** Nếu một Player luôn được dàn xếp thắng cùng donor, từ `1000/1000` và
`K=32`, sau 10 win liên tiếp (không rounding) cặp thành khoảng
`1110.4725/889.5275`. Tổng vẫn `2000`; collusion đã chuyển khoảng `110.47` điểm.
Transfer mỗi game giảm dần khi chênh lệch tăng, nhưng không bằng 0.

Tài khoản donor mới ở `1000` tạo một điểm bắt đầu mới. Account creation không
phải match inflation: nó thêm cả `1000` điểm lẫn một account vào full pool. Tuy
nhiên, nếu donor cố tình thua rồi inactive/đóng tài khoản, mean của **active
subset** và rating của recipient tăng. Nhiều donor mới cũng tránh phần lớn hiệu
ứng diminishing của việc chỉ farm một donor.

### 4.3 Các control để Wayfinder cân nhắc

**CHOICE.** Invite-only không loại bỏ collusion; nó cho Player quyền chọn opponent,
nên cần chốt control và false-positive budget. Không có nguồn nào ở đây chứng minh
một ngưỡng lặp cụ thể là tối ưu.

| Control candidate | Tác dụng | Chi phí/tác dụng phụ |
| --- | --- | --- |
| Chỉ policy + audit, mọi game hợp lệ đều rate | Không chặn game hợp pháp | Phụ thuộc phát hiện và correction sau sự kiện |
| Cap số rated Match cho mỗi unordered pair trong một window | Chặn farm một cặp | Population nhỏ có thể nhanh hết đối thủ; cần định nghĩa timezone/window |
| Các Match vượt cap tự thành Practice | Giữ khả năng chơi | UX phải báo trước; cap vẫn bị Sybil bypass |
| Giảm match-level K theo số lần gặp, vẫn dùng cùng `+T/-T` | Giảm lợi ích farm và giữ zero-sum | Làm rating phụ thuộc pair history; formula/version phức tạp hơn |
| Yêu cầu opponent diversity để thoát provisional | Tăng connectivity | Có thể khiến user hợp pháp provisional rất lâu |
| Eligibility cho account mới trước khi được chơi Ranked | Giảm nguồn donor mới | Tăng friction; magic-link/Google auth không chứng minh một người-một-account |
| Flag/review theo pattern, chưa tự phạt | Giảm false positive tự động | Cần moderation capacity và retention dữ liệu |
| Quarantine rating event nghi vấn | Hạn chế lan truyền | Phải định nghĩa khi nào publish và cách release/replay |

Các signal có thể giữ cho quyết định detection sau này: tỷ trọng Match theo pair,
chuỗi outcome một chiều, duration bất thường, tỷ lệ forfeit/timeout, account age,
opponent diversity, và graph các account mới liên tục donate cho một recipient.
Việc thu thập IP/device fingerprint vượt phạm vi nghiên cứu này và cần quyết định
privacy riêng; không nên mặc định chỉ vì nó có thể giúp chống Sybil.

## 5. Atomicity, concurrency và idempotency

### 5.1 Các guarantee từ nguồn database/protocol

**FACT.** PostgreSQL transaction gom nhiều bước thành all-or-nothing; trạng thái
trung gian không lộ ra ngoài, và failure trước commit không để lại update một
phần. Đây là guarantee cần cho việc update hai Player cùng ledger event.
([PostgreSQL, Transactions][pg-transactions])

**FACT.** `UNIQUE` bảo đảm một key/combination không lặp; `INSERT ... ON CONFLICT`
có thể chọn action thay vì unique violation và `ON CONFLICT DO UPDATE` bảo đảm
atomic insert-or-update dưới concurrency. ([PostgreSQL, Unique Constraints][pg-constraints];
[PostgreSQL, INSERT / ON CONFLICT][pg-insert])

**FACT.** `SELECT ... FOR UPDATE` chặn writers/lockers khác trên cùng row đến hết
transaction. PostgreSQL cảnh báo deadlock khi lock nhiều object khác thứ tự và
khuyên mọi code path lock theo một thứ tự nhất quán. ([PostgreSQL, Row-level
Locks và Deadlocks][pg-locking])

**FACT.** Serializable bảo đảm effect của các transaction đã commit tương đương
một serial order, nhưng application phải retry serialization failure. Read
Committed vẫn cho phép serialization anomaly. ([PostgreSQL, Transaction
Isolation][pg-isolation])

**FACT.** RFC 9110 định nghĩa request method là idempotent khi nhiều request giống
nhau có intended effect giống một request; `POST` không mặc nhiên nằm trong nhóm
idempotent. Vì vậy HTTP retry semantics một mình không bảo vệ settlement command.
([RFC 9110 §9.2.2][rfc-idempotency])

**FACT.** TigerBeetle dùng object `id` làm idempotency key: lần tạo đầu thành
công, lần sau cùng ID trả `exists`; tài liệu reliable submission yêu cầu retry
dùng lại cùng ID. Đây là một first-party pattern cho event có giá trị, không phải
yêu cầu dùng TigerBeetle. ([TigerBeetle Requests, “Idempotency”][tb-requests];
[Reliable Transaction Submission][tb-reliable])

### 5.2 Hai race khác nhau phải giải quyết

**MATH/ARCHITECTURE CONSEQUENCE.** Có hai lỗi độc lập:

1. **Duplicate settlement của cùng Match.** Hai delivery/retry có thể tính Elo
   hai lần. Một domain idempotency key ổn định, tự nhiên nhất là identity của
   initial settlement cho `match_id`, phải cho at most one initial rating event.
2. **Hai Match khác nhau chạm cùng Player.** Hai transaction có thể cùng đọc
   rating cũ rồi ghi đè nhau. `UNIQUE(match_id)` không giải quyết race này; cần
   serialize current-rating rows hoặc toàn bộ operation.

Một settlement boundary tối thiểu để đánh giá stack sau này, không phải code
implementation, gồm:

1. Xác minh Match là Ranked, terminal và có canonical result/reason.
2. Claim initial rating event bằng key ổn định; nếu đã tồn tại thì trả đúng event
   cũ, không tính lại từ current rating mới.
3. Lock hai current-rating row theo thứ tự Player ID cố định, hoặc chạy toàn bộ
   operation ở Serializable với retry.
4. Đọc cả hai rating tại cùng serial point; tính **một** transfer theo formula
   version đã chọn.
5. Trong cùng atomic transaction, append ledger event, cập nhật cả hai current
   rating và đánh dấu settlement đã áp dụng.
6. Chỉ publish success sau commit.

Nếu terminal Match và rating nằm khác datastore, transaction đơn không còn bao
trùm cả hai; Wayfinder phải chọn synchronous same-store settlement hoặc một
durable outbox/inbox workflow vẫn có idempotency. Nghiên cứu này không chọn topology.

**CHOICE.** Retry với cùng key nhưng canonical payload khác (khác participants,
outcome hoặc formula intent) nên được định nghĩa riêng. Trả event cũ một cách im
lặng che giấu data corruption; overwrite lại phá audit. Pattern first-party như
Stripe so sánh parameters của retry và báo lỗi khi key bị reuse với parameters
khác, nhưng DigitCode vẫn phải chốt contract của mình. ([Stripe,
Idempotent requests][stripe-idempotency])

### 5.3 Elo phụ thuộc thứ tự

**MATH.** Hai update Elo nói chung không commutative. Ví dụ A, B, C đều `1000`,
`K=32`; A thắng B và thua C:

| Thứ tự settlement | Rating cuối A | B | C |
| --- | ---: | ---: | ---: |
| A-B rồi A-C | 999.2637 | 984.0000 | 1016.7363 |
| A-C rồi A-B | 1000.7363 | 983.2637 | 1016.0000 |

Cùng hai outcome nhưng final ratings khác. Vì vậy cần chốt:

- order theo server commit sequence, terminal timestamp hay một sequence domain;
- xử lý hai Match terminal cùng lúc;
- xử lý result đến muộn nhưng có event time sớm hơn;
- replay có giữ historical processing order hay reorder theo corrected event time.

Row lock/Serializable tạo ra **một** serial order hợp lệ, nhưng database không tự
chọn order mang ý nghĩa sản phẩm. Ledger phải lưu order đã dùng để rebuild được.

## 6. Precision, rounding và invariant lưu trữ

**FACT.** FIDE round tổng rating change của rating period về integer; FIDE Online
Arena giữ hai chữ số thập phân cho calculation và chỉ display integer, nhằm không
làm mất các thay đổi nhỏ. ([FIDE Rating Regulations §8.3.4][fide-rating];
[FIDE Online Arena §3.1, §3.12-3.14][fide-online])

**CHOICE.** DigitCode cần chốt bốn thứ tách biệt:

- precision dùng để tính expected score;
- precision lưu current rating và delta;
- quy tắc quantize transfer;
- quy tắc chỉ dùng để display.

Nếu current rating là integer nhưng strict zero-sum bắt buộc, nên định nghĩa một
hàm quantize duy nhất trên signed transfer rồi negate cho phía còn lại. Round hai
biểu thức floating-point độc lập, clamp floor độc lập hoặc dùng quy tắc tie không
đối xứng có thể tạo sai lệch. Ledger nên lưu ít nhất input ratings, expected score,
raw delta, applied delta và formula/rounding version để audit.

Rating floor cũng là **CHOICE**. Floor dễ hiểu cho UX nhưng xung đột với strict
zero-sum nếu loser chạm floor; cần chốt bỏ phần transfer, chuyển phần thực tế còn
lại, hay cho phép rating thấp hơn floor.

## 7. Correction và audit ledger

### 7.1 Append-only là pattern audit, không giải quyết toàn bộ Elo

**FACT.** TigerBeetle coi transfers là immutable; correction được ghi bằng
additional reversing/adjusting transfers để lịch sử giữ cả lỗi ban đầu, thời điểm
lỗi và các lần sửa. ([TigerBeetle, Correcting Transfers][tb-corrections])

**CHOICE.** Áp pattern tương tự cho rating event tạo audit tốt hơn việc sửa/xóa
row cũ. Mỗi event ban đầu/correction tối thiểu cần đủ để giải thích:

- immutable event ID, `match_id`, event kind và event order;
- hai Player và canonical terminal outcome/reason;
- rating eligibility và score pair;
- before ratings, expected scores, `K`, raw/applied transfer, after ratings;
- formula, cap, precision và rounding version;
- settlement/correction idempotency key;
- created/committed time và source command;
- với correction: event bị supersede/reverse, actor/authority và reason.

Current rating có thể là materialized state để đọc nhanh, nhưng phải rebuild hoặc
đối chiếu được từ effective ledger theo policy đã chọn.

### 7.2 Reversal không tương đương replay

**MATH.** Nếu erroneous event A-B được reverse sau khi B đã chơi C, cộng delta
đối ứng ở hiện tại có thể khôi phục tổng điểm nhưng không làm expected score của
Match B-C trong quá khứ trở thành giá trị counterfactual đúng. Nếu recalculation
B-C đổi rating C, các Match sau của C cũng có thể đổi; ảnh hưởng có thể lan qua
toàn connected component.

**CHOICE.** Correction semantics cần chọn rõ một trong các family, hoặc quy tắc
khi nào dùng family nào:

| Family | Audit | Tính đúng counterfactual | Chi phí/hệ quả |
| --- | --- | --- | --- |
| Forward reversal/adjustment | Tốt nếu append-only | Không, khi có event về sau | Đơn giản; current rating có discontinuity có chủ ý |
| Replay deterministic từ điểm lỗi | Tốt nếu giữ version/supersession | Có theo order/formula đã định | Có thể cascade rộng; cần snapshot/rebuild và publication policy |
| Admin reset/rebase | Có nếu là event riêng | Không phải replay | Cần giải thích rõ discontinuity và zero-sum impact |
| Mutate/delete event cũ | Kém | Khó chứng minh | Mất lịch sử và làm idempotent retry mơ hồ |

Các câu hỏi phụ: correction có hiệu lực ngay hay quarantine; history hiển thị old
và corrected values thế nào; appeal/fair-play evidence giữ bao lâu; ai được tạo
correction; correction command được dedupe ra sao.

## 8. Decision inputs cần đưa về Wayfinder

Các quyết định sau chưa thể suy ra chỉ từ nguồn:

1. **Expectation function:** bảng FIDE hay logistic liên tục; denominator `400`;
   có cap rating difference không.
2. **Numeric policy:** precision lưu/tính, display rounding, transfer quantization,
   rating floor.
3. **Zero-sum scope:** invariant cho mọi Ranked Match, hay cho phép explicit
   non-zero-sum event như provisional/admin/double loss.
4. **K policy:** `K=32` cho mọi Player hay chỉ established; nếu provisional đổi K,
   dùng match-level transfer hay per-player delta.
5. **Outcome eligibility:** matrix chính thức cho draw, elimination, resign,
   no-show, disconnect, Match deadline, platform failure và double abandonment.
6. **Provisional:** ngưỡng, opponent diversity, game nào được count, display và
   ảnh hưởng lên established opponent.
7. **Repeated pair:** count toàn bộ, cap/window, chuyển sang Practice, giảm K hay
   chỉ detect/review; UX báo policy vào lúc nào.
8. **Identity/Sybil:** điều kiện account được chơi Ranked và mức friction chấp
   nhận được trong invite-only MVP.
9. **Settlement order:** total order canonical và rule cho late result/concurrent
   Match.
10. **Idempotency contract:** key của initial settlement/correction, response khi
    retry, và behavior khi cùng key nhưng payload khác.
11. **Correction semantics:** forward adjustment, replay hay reset; phạm vi
    cascade và cách publish history.
12. **Audit/operations:** trường ledger, retention, quyền correction, invariant
    reconciliation và cách rebuild current rating.

## 9. Acceptance invariants sau khi policy được chọn

Đây là checklist cho spec/execution ticket sau này, không phải implementation
trong research ticket:

- Một Ranked Match có nhiều delivery nhưng tối đa một initial settlement effect.
- Retry cùng identity và cùng canonical payload trả cùng outcome, không đổi rating.
- Cùng identity nhưng payload khác không được âm thầm overwrite.
- Hai current ratings và ledger event commit tất cả hoặc không gì cả.
- Hai Match khác nhau chạm cùng Player có một serial order và không lost update.
- Non-Ranked/Practice/void Match không tạo Elo transfer.
- Mọi rated score pair thỏa invariant zero-sum đã chọn; nếu có ngoại lệ, event kind
  và lý do phải explicit.
- Nếu strict zero-sum, applied deltas sau quantization thỏa
  `delta_A + delta_B = 0`.
- Rebuild ledger theo stored order/formula version cho đúng current state.
- Correction không xóa dấu vết event gốc và bản thân correction cũng idempotent.
- Concurrent duplicate, serialization retry, timeout sau commit và response bị
  mất đều không thể áp transfer lần hai.
- Reconciliation phát hiện chênh lệch giữa current materialized rating và ledger.

## Nguồn

Tất cả nguồn dưới đây là primary/authoritative hoặc first-party. Không dùng bài
tổng hợp thứ cấp để gán claim.

- [FIDE Rating Regulations, effective 2024 và amendments hiện hành][fide-rating]:
  §§5, 7, 8 cho unplayed game, initial rating, expected score, score, K và rounding.
- [FIDE Online Arena Rating Regulations][fide-online]: §§2-4 cho disconnect,
  initial/provisional handling, precision và per-game update.
- [Bradley, R. A. & Terry, M. E. (1952), “Rank Analysis of Incomplete Block
  Designs: I. The Method of Paired Comparisons”][bradley-terry], DOI
  `10.2307/2334029`: primary paired-comparison model.
- [Lichess Terms of Service][lichess-terms]: first-party definitions của boosting,
  sandbagging và multiple-account abuse.
- [PostgreSQL: Transactions][pg-transactions], [Constraints][pg-constraints],
  [INSERT][pg-insert], [Explicit Locking][pg-locking], và [Transaction
  Isolation][pg-isolation]: official database guarantees.
- [RFC 9110 §9.2.2][rfc-idempotency]: normative HTTP definition của idempotent
  method.
- [TigerBeetle Requests][tb-requests], [Reliable Transaction
  Submission][tb-reliable], và [Correcting Transfers][tb-corrections]: first-party
  examples về stable IDs, retry và immutable corrections.
- [Stripe API: Idempotent requests][stripe-idempotency]: first-party example về
  parameter comparison khi reuse idempotency key.

[fide-rating]: https://handbook.fide.com/chapter/B022024
[fide-online]: https://handbook.fide.com/chapter/B11FOARatingRegulations
[bradley-terry]: https://doi.org/10.2307/2334029
[lichess-terms]: https://lichess.org/terms-of-service
[pg-transactions]: https://www.postgresql.org/docs/current/tutorial-transactions.html
[pg-constraints]: https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS
[pg-insert]: https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT
[pg-locking]: https://www.postgresql.org/docs/current/explicit-locking.html
[pg-isolation]: https://www.postgresql.org/docs/current/transaction-iso.html
[rfc-idempotency]: https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2
[tb-requests]: https://docs.tigerbeetle.com/coding/requests/#idempotency
[tb-reliable]: https://docs.tigerbeetle.com/coding/reliable-transaction-submission/
[tb-corrections]: https://docs.tigerbeetle.com/coding/recipes/correcting-transfers/
[stripe-idempotency]: https://docs.stripe.com/api/idempotent_requests
