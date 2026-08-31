# Bot Calibration Profile 1.0.0

Profile ID: **`digitcode-bot-calibration/1.0.0`**
Ruleset ID: **`digitcode-ruleset/1.0.0`**
Ticket: [Chốt hàm hiệu chuẩn Ranked Rating thành Score mục tiêu](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)

Đây là artifact planning chốt contract hiệu chuẩn Bot Opponent cho Ranked
Match. Nó không phải production implementation và không thay đổi 95 luật của
`digitcode-ruleset/1.0.0`.

## 1. Identity và input

Bot Calibration Profile là immutable và được version độc lập với Ruleset. Mỗi
profile MUST bind với đúng một `ruleset_id`; profile này chỉ bind với
`digitcode-ruleset/1.0.0`. Thay anchor, solver, tie-break, pacing hoặc semantic
khác MUST tạo profile version mới, không sửa profile đã publish tại chỗ.

Input duy nhất là snapshot Ranked Rating authoritative ngay trước Match, được
đóng dấu tại Match Start. Target Bot Score và inference Clue budget MUST đọc
cùng snapshot đó và MUST NOT đổi trong Match.

## 2. Target Bot Score

Target Bot Score là **median Bot Score, conditional on Bot Opponent `SOLVED`**,
trên uniform Ranked Puzzle pool của Ruleset đã bind. Với tập có số phần tử
chẵn, median là trung bình cộng của hai giá trị giữa sau khi sắp tăng dần.

Nó không phải expected Bot Score, không đặt nghĩa cho Bot Score khi Bot Opponent
không Solve, và không phải giới hạn Bot Score hợp lệ trên từng Puzzle.

```text
target_score(R) = clamp(floor((R - 500) / 25), 0, 40)
```

| Ranked Rating snapshot | Target median Bot Score |
| ---: | ---: |
| 500 | 0 |
| 1000 | 20 |
| 1500 | 40 |

Hàm không giảm. `40` là target median lớn nhất, không phải maximum Bot Score:
Puzzle dễ có thể kết thúc trên 40.

## 3. Inference solver

Solver deterministic, không dùng RNG và dùng một strategy ở mọi Rating:

1. Bắt đầu với toàn bộ Ranked Puzzle pool làm candidate set.
2. Với từng Clue chưa mua, partition candidate set theo đáp án Clue đó.
3. Chọn Clue có partition lớn nhất nhỏ nhất.
4. Nếu hoà, chọn Clue có nhiều partition không rỗng nhất.
5. Nếu vẫn hoà, chọn Clue sớm nhất theo canonical order.
6. Mua Clue, giữ lại partition khớp đáp án, rồi lặp lại.

Canonical order là:

```text
Q1: T, U, V, W, X, Y
Q2: T-U, U-V, W-X, X-Y, T-W, U-X, V-Y
Q3: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S
```

Bot Submission chỉ được phép khi còn đúng một candidate. Solver MUST NOT cố ý
submit candidate sai. Đây là greedy-minimax heuristic đã đo, không phải tuyên
bố về cây quyết định tối ưu.

## 4. Inference Clue budget

Budget đếm số Clue dùng để đạt singleton. Extra Clue mua sau đó để hạ Bot
Score không tính vào budget này.

```text
budget(R) = 5                                           if R <= 500
            floor(5 + 6 * (R - 500) / 500)             if 500 < R <= 1000
            floor(11 + 5 * (R - 1000) / 500)           if 1000 < R < 1500
            16                                          if R >= 1500
```

| Ranked Rating snapshot | Inference Clue budget |
| ---: | ---: |
| 500 | 5 |
| 1000 | 11 |
| 1500 | 16 |

Nếu hết budget mà candidate set chưa là singleton, Bot Opponent MUST ngừng mua
inference Clue, MUST NOT tạo Bot Submission, và chuyển sang `EXPIRED` tại
deadline bình thường. Solved-Puzzle set ở Rating cao hơn MUST là superset của
set ở Rating thấp hơn.

## 5. Legal Bot Score degradation và pacing

Profile giữ biến thiên tự nhiên giữa các Puzzle, không ép từng Match đạt target.
Với mỗi distinct pair `(target, budget)`:

1. Chạy solver trên toàn bộ Ranked pool và lấy các Puzzle đạt singleton trong
   budget.
2. Tính natural Bot Score của từng Puzzle, với mọi inference action hoàn tất
   trước decay boundary đầu tiên và chưa mua extra Clue.
3. Lấy median natural Bot Score `M` của solved set và tính common offset
   `D = M - target`.
4. Sau khi biết singleton, mua `floor(D / 5)` Clue chưa mua theo canonical
   order.
5. Sau khi action hoàn tất, submit tại thời điểm sớm nhất mà absolute Match
   Clock đạt bucket `D mod 5`, tức `floor(t / 60 seconds) = D mod 5`.

Bot Score cuối phải do đúng action ledger của R-BOT-03 tạo ra:

```text
max(0, natural Bot Score - D)
```

Không được gán hoặc overwrite final Bot Score. Extra Clue chỉ được mua sau khi
đã biết singleton. Delay là bucket tuyệt đối từ Match Start, không phải thời
lượng cộng thêm sau inference. Khi đạt target Bot Score bucket, Bot Opponent submit
ngay; Solve Time không có target độc lập.

Offline construction đã kiểm chứng mọi action được admission hợp lệ, nhiều
nhất 20 Clue tổng cộng và delay bucket nhiều nhất 4 phút. Production
implementation MUST bảo đảm toàn bộ action không delay hoàn tất trước mốc 60
giây đầu tiên.

## 6. Monotonic strength

Trên cùng một Ranked Puzzle, Rating cao hơn MUST không tạo Bot Opponent yếu hơn:

- nó Solve mọi Puzzle mà Rating thấp hơn Solve;
- nếu cả hai Solve, Bot Score của Rating cao hơn không thấp hơn;
- nếu Bot Score bằng nhau, Solve Time của Rating cao hơn không muộn hơn.

Invariant này phải kiểm theo từng Puzzle, không chỉ theo aggregate median.

## 7. Calibrated domain

Miền hiệu chuẩn là `500..1500`. Profile clamp xuống hành vi tại 500 ở bên dưới
và clamp lên hành vi tại 1500 ở bên trên; Bot Opponent không yếu hơn hoặc mạnh
hơn nữa ngoài hai đầu.

Solver đã biết không được chứng minh là tối ưu hay bất bại. Vì vậy kết quả này
không hỗ trợ tuyên bố rằng rating luôn hội tụ về true strength hoặc rằng leo
qua true strength là bất khả thi về mặt toán học. [Chốt chính sách Elo và
result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
MUST chọn cap hoặc saturation semantic tương đương và MUST NOT trình bày Rating
ngoài miền này là vẫn được hiệu chuẩn.

## 8. Offline verification

Verifier MUST chạy exhaustive trên mọi distinct profile và toàn bộ 464.948
Ranked Puzzle, không giữ representative của 86 collision class đã bị Ranked
loại. Integer Rating từ 500 đến 1500 tạo 1.001 Rating input nhưng chỉ 45 distinct
pair `(target Score, inference Clue budget)`.

Evidence đã dựng lại cho profile này:

```text
solver depth histogram = {
  5: 5, 6: 240, 7: 1984, 8: 9424, 9: 27999, 10: 57445,
  11: 90449, 12: 108124, 13: 95638, 14: 55810, 15: 17122, 16: 708
}
total = 464948
mean = 11.834452454898182
median = 12
p99 = 15
worst = 16
```

| Budget | Solved Puzzle | Solve rate |
| ---: | ---: | ---: |
| 5 | 5 | 0.0011% |
| 11 | 187,546 | 40.3370% |
| 16 | 464,948 | 100% |

Mỗi lần verify MUST kiểm ít nhất:

- target median chính xác;
- action hợp lệ và đúng R-BOT-03;
- không Bot Submission trước singleton và không submit sai;
- solved sets lồng nhau;
- per-Puzzle Score/Solve Time dominance;
- không quá 20 Clue tổng cộng và không quá delay bucket 4 phút;
- kết quả deterministic giữa các lần chạy.

## 9. Live balance validation

Balance trung tính theo calibration nghĩa là:

```text
P(Player win) approximately equals P(Bot Opponent win)
decisive share = Player wins / (Player wins + Bot Opponent wins)
```

Draw rate MUST báo riêng. Dataset gồm mọi Ranked Match giữa Player và Bot
Opponent đã finalized mà [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
phân loại rating-eligible, group theo cùng exact `ruleset_id`, cùng exact Bot
Calibration Profile ID và pre-Match Ranked Rating snapshot.

Dùng 11 band rộng 100 Rating, tâm tại `500, 600, ..., 1500`. Band 500 nhận mọi
Rating `< 550`; các band giữa là `[center - 50, center + 50)`; band 1500 nhận
mọi Rating `>= 1450`.

Với mỗi band, tính Wilson 95% confidence interval hai phía cho decisive share:

- `INSUFFICIENT_EVIDENCE` khi chưa có decisive Match; không tính decisive share
  hoặc interval với mẫu số 0;
- `VALIDATED` khi toàn interval nằm trong `40%..60%`;
- `OUT_OF_TOLERANCE` khi toàn interval nằm dưới 40% hoặc trên 60%;
- `INSUFFICIENT_EVIDENCE` trong các trường hợp còn lại.

Ở observed split chính xác 50/50, tối thiểu 94 decisive Match mới cho Wilson
95% interval `[40.0927%, 59.9073%]` nằm trọn trong tolerance. Không auto-tune
profile đã publish; correction phải tạo profile version mới qua review.

[Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17)
quyết định validation status nào cho phép launch. [Chốt telemetry tối thiểu để
kiểm chứng cân bằng gameplay](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/35)
quyết định event, storage, privacy và production aggregation.

## 10. Ownership exclusions

Artifact này không quyết định:

| Vấn đề | Ticket owner |
| --- | --- |
| Matchmaking Queue lifecycle | [Chốt Match lifecycle cho đường Matchmaking Queue](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/31) |
| Schema, history và privacy | [Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| UX | [Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| Rating eligibility, settlement, cap và saturation | [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| Telemetry implementation | [Chốt telemetry tối thiểu để kiểm chứng cân bằng gameplay](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/35) |

## 11. Canonical sources

- [`CONTEXT.md`](../../../CONTEXT.md): Player là người; Bot Opponent không phải
  Player; Bot Score, Ranked Rating, Match Clock, Solve Time và Ruleset là các
  khái niệm tách biệt.
- [Canonical Competitive Game Specification](../2026-08-23-issue-9-game-spec/game-spec.md):
  R-P-07, R-P-10, R-C-01, R-C-03, R-C-04, R-C-07, R-C-12..15,
  R-BOT-01..11 và R-K-01..05.
- [Clue-bound findings](../2026-08-24-clue-bounds/findings.md): greedy-minimax
  phụ thuộc tie-break, worst case 16 chỉ là HEURISTIC, và Ranked loại toàn bộ
  172 collision secret thay vì giữ class representative.
- [ADR 0001](../../adr/0001-ranked-match-leaves-the-room.md): lý do Ranked Match
  rời Room và dùng shared calibration yardstick.
