# Balance Telemetry cho Production MVP

Contract ID: **`digitcode-balance-telemetry/1.0.0`**
Ruleset ID: **`digitcode-ruleset/1.0.0`**
Ticket: [Chốt telemetry tối thiểu để kiểm chứng cân bằng gameplay](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/35)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)

Đây là artifact planning chốt **bộ quan sát tối thiểu** để kiểm chứng cân bằng
gameplay của Production MVP: đơn vị ghi, bộ trường, dữ liệu tuyệt đối không được
ghi, cách tổng hợp lên 11 band, và bốn ranh giới tách biệt mà telemetry MUST NOT
vượt qua. Nó không phải production implementation, không thay đổi 95 luật của
`digitcode-ruleset/1.0.0`, không đổi nội dung Bot Calibration Profile hay ngưỡng
tolerance, và không quyết định schema, retention hay quyền đọc.

## 1. Balance Telemetry là gì, và không là gì

**Balance Telemetry** là tập bản ghi phi-định-danh được phát ra khi một Match
kết thúc, tồn tại vì đúng một mục đích: kiểm chứng rằng luật chơi và hiệu chuẩn
Bot Opponent hành xử như đã chốt.

Bốn thứ nó MUST NOT bị trộn vào, và lý do mỗi thứ đã có chủ:

| Không phải | Vì | Chủ |
| --- | --- | --- |
| Match history | Phục vụ Player đọc lại trận của chính mình; định danh, có quyền đọc, có nghĩa vụ xoá | [Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| Anti-cheat evidence | Phục vụ case có người review; tập dữ liệu và retention riêng (90 ngày sau Match / 30 ngày sau khi case đóng) | [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) |
| Product analytics | Đo hành vi sản phẩm, không đo luật chơi | không thuộc destination của map |
| Vendor-quota monitoring | Đo mức tiêu thụ hạ tầng để giữ chi phí bằng 0 | [Chốt quality gate, zero-cost operations và release criteria](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16) |

Ranh giới này được giữ bằng **cấu trúc**, không bằng kỷ luật người dùng: §4 cắt
mọi khoá cho phép nối Balance Telemetry với ba tập còn lại.

## 2. Đơn vị ghi: Telemetry Fact

Đơn vị là **Telemetry Fact** — một bản ghi bất biến cho **một phía** của **một**
Match đã finalized.

- Mỗi Match finalized MUST phát đúng **hai** Telemetry Fact: một cho mỗi phía.
  Phía có thể là Player hoặc Bot Opponent.
- Fact MUST được phát **bên trong** transaction finalization đã tồn tại
  ([Chốt Match lifecycle, reconnect và concurrency semantics](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4)
  chốt finalization là atomic và idempotent). Không thêm scheduled job, không
  thêm request, không thêm invocation nào ngoài cái vốn đã chạy.
- Idempotency của finalization MUST bao trùm việc phát fact: finalization chạy
  lại MUST NOT tạo fact thứ ba.
- Fact MUST là append-only. Không sửa, không xoá tại chỗ, không backfill.
- Telemetry MUST NOT đọc Match history để dựng fact. Toàn bộ trường ở §3 phải
  lấy được từ trạng thái đang nằm trong chính transaction finalization.

**Vì sao không derive từ Match history.** Ticket này đang **chặn**
[Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14).
Một thiết kế đọc schema của issue 14 sẽ làm blocker phụ thuộc vào thứ nó chặn,
và hợp nhất telemetry với đúng tập dữ liệu mà §1 tách ra.

**Vì sao không phải event stream trong lúc chơi.** Mọi invocation đều tính vào
quota. [Chốt Match lifecycle, reconnect và concurrency semantics](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4)
đã đo rằng lưu lượng theo từng hành động là chỗ ngân sách zero-cost chết — ví dụ
poll 5 giây trong 15 phút tốn gấp bốn lần toàn bộ lối chơi. Một event stream còn
nhân bản replay timeline mà
[Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12)
đã định nghĩa cho mục đích khác.

## 3. Bộ trường tối thiểu

Mỗi Telemetry Fact MUST mang đúng 20 trường sau, không hơn.

| # | Trường | Miền giá trị | Ghi chú |
| ---: | --- | --- | --- |
| 1 | `mode` | `RANKED` \| `PRACTICE` | |
| 2 | `subject_kind` | `PLAYER` \| `BOT` | phía mà fact này mô tả |
| 3 | `opponent_kind` | `PLAYER` \| `BOT` | phía đối diện |
| 4 | `ruleset_id` | chuỗi | thành phần Rating Generation |
| 5 | `profile_id` | chuỗi \| `null` | `null` khi Match không có Bot Opponent |
| 6 | `formula_version` | chuỗi | thành phần Rating Generation |
| 7 | `observed_on` | ngày UTC | §6 |
| 8 | `subject_pseudonym` | chuỗi \| `null` | `null` khi `subject_kind = BOT`; §5 |
| 9 | `terminal_status` | `SOLVED` \| `ELIMINATED` \| `EXPIRED` \| `FORFEITED` | `FORFEITED` không hợp lệ khi `subject_kind = BOT` (R-BOT-07) |
| 10 | `opponent_terminal_status` | như trên | bắt buộc, vì §4 cấm khoá ghép hai fact |
| 11 | `outcome` | `WIN` \| `LOSS` \| `DRAW` | theo góc nhìn subject |
| 12 | `final_score` | số nguyên `>= 0` | Score, hoặc Bot Score khi subject là Bot |
| 13 | `solve_time_ms` | số nguyên \| `null` | `null` khi `terminal_status != SOLVED` |
| 14 | `clue_purchase_count` | số nguyên `>= 0` | |
| 15 | `clue_purchase_count_by_family` | đếm theo họ Clue | chỉ số đếm; không thứ tự, không đáp án |
| 16 | `strike_count` | `0` \| `1` \| `2` | R-V-07 đến R-V-09 |
| 17 | `pre_match_rating_snapshot` | số nguyên \| `null` | `null` khi `mode = PRACTICE` hoặc `subject_kind = BOT` |
| 18 | `rating_domain_flag` | `IN_DOMAIN` \| `BELOW_DOMAIN` \| `ABOVE_DOMAIN` \| `null` | `null` khi không có snapshot; §8 |
| 19 | `puzzle_pool` | `RANKED_RESTRICTED` \| `UNRESTRICTED` | 464.948 mã (R-P-10) so với 465.120 mã (R-P-09) |
| 20 | `puzzle_difficulty_class` | nhãn hữu hạn | §7 |

`outcome` MUST được dẫn xuất theo đúng ma trận của
[Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
§7, không phải bằng một quy tắc mới: cả hai `SOLVED` thì so `final_score` rồi
`solve_time_ms`, bằng nhau là `DRAW`; đúng một bên `SOLVED` thì bên đó `WIN`;
không bên nào `SOLVED` mà đúng một bên `FORFEITED` thì bên kia `WIN`; mọi tổ hợp
còn lại là `DRAW`.

`clue_purchase_count_by_family` giữ lại vì "hành vi mua Clue" là một trong sáu
thứ ticket này phải đo được, và một con số tổng không phân biệt được người mua
mười Clue cùng một họ với người mua mười Clue trải đều — hai hiện tượng độ khó
khác hẳn nhau.

## 4. Dữ liệu tuyệt đối không được ghi

Telemetry Fact MUST NOT chứa, dưới bất kỳ dạng nào kể cả đã băm hay mã hoá:

1. Mã bí mật của Puzzle (R-I-02, R-P-14).
2. Đáp án Clue hoặc nội dung Clue đã mua (R-I-03, R-C-15).
3. Player Board, kể cả một phần, kể cả ở dạng dẫn xuất (R-B-01, R-B-06).
4. Ghi chú nháp của Player (R-B-03 đã loại nó khỏi Player State).
5. `puzzle_id`, kể cả dạng mờ.
6. `match_id`, hoặc bất kỳ khoá nào ghép được hai fact của cùng một Match, hoặc
   ghép fact với Match history, anti-cheat evidence hay security log.
7. `player_id`, Player Identity, Linked Identity hay bất kỳ định danh bền nào.
8. Display name, Player Tag, email, số điện thoại.
9. Invite Code (đã bị cấm rời server bởi
   [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12)).
10. IP, device fingerprint, user-agent, thông tin vị trí.
11. Skill Estimate, hoặc bất kỳ giá trị nào dẫn xuất từ nó — nó là số ẩn
    (`CONTEXT.md`: "It is never shown to a Player") và không cần cho mục tiêu nào
    ở §1.
12. Raw command payload.
13. Access token, refresh token, cookie, magic-link hoặc auth code — đã bị
    [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12)
    cấm khỏi operational log, và không trường nào ở §3 mang được chúng.
14. Giờ, phút, giây — xem §6.

Điểm 6 là cái làm ranh giới §1 thành cấu trúc. Hệ quả được chấp nhận có ý thức:
hai fact của cùng một Match không bao giờ nối lại được, nên không thể dựng lại
replay từ Balance Telemetry. Đó là lý do trường 10 tồn tại.

## 5. Pseudonym, và vì sao cần đếm chủ thể

Wilson confidence interval giả định các quan sát độc lập. Nếu một Player chiếm
phần lớn mẫu của một band, interval hẹp một cách giả tạo và cả `VALIDATED` lẫn
`OUT_OF_TOLERANCE` đều không đáng tin — trong khi `OUT_OF_TOLERANCE` kích hoạt
một Bot Calibration Profile version mới cho toàn hệ thống. Vì vậy telemetry cần
đếm được chủ thể riêng biệt, và chỉ thế.

- `subject_pseudonym` MUST là hàm một chiều của cặp (Player, Rating Generation).
- Nó MUST đổi khi Rating Generation đổi — đúng lúc dữ liệu cũ cũng hết so sánh
  được ([Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
  §8: hai Ranked Rating khác Generation không so sánh được).
- Nó MUST NOT được dùng cho bất kỳ mục đích nào ngoài hai việc: đếm chủ thể riêng
  biệt trong một band, và phát hiện mẫu bị một chủ thể chi phối.
- Nó MUST NOT xuất hiện trên bất kỳ bề mặt nào ngoài Balance Telemetry.

Aggregate của mỗi band MUST báo `distinct_subject_count` cạnh mẫu số của nó. Một
band có 94 decisive Match từ 3 chủ thể MUST NOT được đọc như một band có 94
decisive Match từ 90 chủ thể.

Vì fact không mang `player_id`, việc xoá tài khoản không tạo nghĩa vụ mới trên
tập này: [Chốt identity, profile và invite-room lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2)
đã chốt tombstone **giữ** `player_id`, và ở đây thậm chí không có `player_id` để
giữ. Hình dạng cuối cùng của nghĩa vụ xoá vẫn thuộc
[Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14).

## 6. Dấu thời gian làm thô tới ngày UTC

`observed_on` MUST là ngày UTC. Giờ, phút, giây MUST NOT được lưu.

Lý do là chống tái định danh, không phải tiết kiệm chỗ. Một timestamp chính xác
tới giây, cộng với `terminal_status` và `final_score`, gần như xác định duy nhất
một Match; khi đó pseudonym ở §5 nối lại được với Match history hoặc với security
log — thứ mà [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12)
giữ 30 ngày kèm timestamp. Làm thô tới ngày giữ nguyên mọi phân tích mà §1 cần,
vì cả sáu đại lượng đều là đại lượng tích luỹ, đồng thời biến phép ghép 1-1 thành
việc không còn tầm thường.

Việc truy ngược một Match cụ thể là việc của anti-cheat evidence, đã có chủ, có
tập dữ liệu riêng và retention riêng.

## 7. Độ khó Puzzle: đúng một đặc trưng, và vì sao chỉ một

`puzzle_difficulty_class` MUST là một hàm toàn phần từ pool secret vào một tập
nhãn hữu hạn, thoả ba bất biến:

1. tính được offline từ luật sampler, không cần biết secret của một Match cụ thể;
2. không mang `puzzle_id` và không cho phép suy ra nó;
3. mỗi nhãn MUST chứa ít nhất **172** secret.

Ở `digitcode-balance-telemetry/1.0.0`, class dùng đúng **một** đặc trưng:

> `symmetric_family` — secret có thuộc họ đối xứng cột hay không.

[Định lượng độ công bằng và khả năng giải của Puzzle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6)
chứng minh EXACT rằng 465.120 secret gộp thành 465.034 lớp, trong đó 86 lớp cỡ 2
— tức **172** secret — là một họ đối xứng duy nhất, không phân biệt được kể cả
khi biết toàn bộ clue. Nhãn nhỏ nhất vì thế có đúng 172 phần tử, đạt bất biến 3
với dấu bằng.

Hai đặc trưng đã bị loại, có lý do:

- **Số Clue tối thiểu để xác định secret.** Không dùng được vì không tính được:
  khoảng adaptive vẫn hở ở `[10, 16]` và
  [`findings.md`](../2026-08-24-clue-bounds/findings.md) nói rõ đóng nó cần một
  cây quyết định tối ưu chưa ai dựng. Một đặc trưng chưa tính được không thể là
  trường bắt buộc.
- **Trọng số sampler.** Không dùng vì không liên quan:
  [Định lượng độ công bằng và khả năng giải của Puzzle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6)
  đo được sampler lệch 9/7 nhưng **độ khó thì không lệch**. Đưa nó vào class là
  phân lớp theo một trục đã được chứng minh là không mang thông tin độ khó.

Độ khó thực tế không nằm ở class — nó được đo **hậu nghiệm** từ chính các trường
12–16 gộp theo class. Class chỉ tồn tại để tách nhóm bệnh lý ra khỏi phần còn
lại. Mở rộng taxonomy MUST tạo contract version mới, không sửa tại chỗ.

**Hệ quả phải nói trước: trên pool Ranked, class là hằng số.** Nhãn dương của
`symmetric_family` đúng bằng 172 mã mà R-P-10 đã loại khỏi pool Ranked, nên mọi
fact có `puzzle_pool = RANKED_RESTRICTED` đều mang cùng một nhãn. Đó không phải
khuyết tật — nhóm bệnh lý đã bị loại khỏi Ranked bằng luật, nên không còn gì để
phân biệt ở đó; class chỉ biến thiên trong Practice, nơi nhãn dương có tần suất
kỳ vọng `172 / 465.120`, tức khoảng 0,037%. Vì vậy `puzzle_difficulty_class`
MUST NOT được dùng như trục phân tích độ khó của Ranked; ở Ranked, độ khó đọc từ
các trường 12–16 gộp theo band. Một taxonomy có sức phân biệt trên pool Ranked
là việc của contract version sau, và nó cần một đặc trưng chưa tính được hôm nay.

Rò rỉ secret không xảy ra qua đường này: fact chỉ tồn tại **sau** khi Match
finalized, thời điểm mà R-O-03 đã công bố secret cho chính hai phía, và fact
không mang `puzzle_id` nên không nối được một class với một Match đang chạy.

## 8. Aggregation: partition, band, và status

Aggregate MUST là một phép tính **xác định** trên tập Telemetry Fact, tính **khi
đọc**. MUST NOT có bản materialize, snapshot định kỳ, hay scheduled job nào mà
tính đúng đắn của aggregate phụ thuộc vào.

Lý do: [Nghiên cứu cơ chế scheduled job zero-cost cho Vercel Hobby + Supabase Free](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27)
kết luận không cơ chế zero-cost nào được vendor tuyên bố là đủ đảm bảo — Vercel
Cron trên Hobby bị chặn cứng ở một lần mỗi ngày, còn `pg_cron` không được tuyên
bố chống pause. Telemetry không nằm trên đường sống của Match nên `pg_cron` không
bị cấm ở đây, nhưng một aggregate có thể đứng im mà không ai biết là rủi ro không
cần mua: ở quy mô MVP, aggregate chỉ được đọc khi review hiệu chuẩn.

**Partition.** Status MUST được tính riêng cho từng cặp `(ruleset_id,
profile_id)`. Gộp ngang hai profile hoặc hai ruleset vào cùng một band là bị
CẤM — nó mâu thuẫn trực tiếp với Rating Generation.

**Band.** Một Match đóng góp đúng một quan sát vào đúng một band; band là hàm của
`pre_match_rating_snapshot` của phía Player, theo đúng định nghĩa 11 band của
[Chốt hàm hiệu chuẩn Ranked Rating thành Score mục tiêu](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30)
§9: rộng 100 Rating, tâm tại `500, 600, ..., 1500`, band 500 nhận mọi Rating
`< 550`, các band giữa là `[tâm - 50, tâm + 50)`, band 1500 nhận mọi Rating
`>= 1450`. Snapshot vẫn MUST được ghi ở độ chính xác đầy đủ (trường 17) để tính
lại được nếu định nghĩa band đổi ở một profile version sau.

Đây là cách artifact này đọc cụm "group theo … pre-Match Ranked Rating snapshot"
của §9: snapshot là **giá trị chọn band**, không phải một đơn vị thống kê riêng.
Cách đọc kia — gộp từng giá trị snapshot rồi bình quân lên band — làm một giá trị
rating có 1 Match nặng bằng giá trị có 50 Match, và Wilson không còn áp được lên
một tỷ lệ bình quân.

**Đại lượng.** Dataset là các Ranked Match giữa Player và Bot Opponent đã
finalized. Mọi Ranked Match finalized đều rating-eligible
([Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
§7: "There is no void branch reachable from gameplay"), nên aggregation MUST NOT
dựng thêm một nhánh loại trừ nào.

```text
decisive share = Player wins / (Player wins + Bot Opponent wins)
```

Draw MUST báo riêng, không nằm trong mẫu số. Status MUST theo đúng ba nhãn của
issue 30 §9 — `VALIDATED` khi toàn Wilson 95% interval hai phía nằm trong
`40%..60%`; `OUT_OF_TOLERANCE` khi toàn interval nằm dưới 40% hoặc trên 60%;
`INSUFFICIENT_EVIDENCE` khi chưa có decisive Match và trong mọi trường hợp còn
lại. Artifact này MUST NOT sửa ngưỡng, nhãn, hay mốc 94 decisive Match.

**Band biên.** Miền calibrated là `500..1500`, nhưng band 500 nhận mọi Rating
`< 550` và band 1500 nhận mọi Rating `>= 1450`, nên hai band này trộn quan sát
ngoài miền vào quan sát trong miền. Aggregate của band 500 và band 1500 MUST báo
kèm `out_of_domain_count`, đếm từ `rating_domain_flag`.

Artifact này MUST NOT loại quan sát ngoài miền khỏi band, MUST NOT đổi định nghĩa
band, và MUST NOT đổi status — cả ba đều là tài sản của issue 30, vốn đã chốt
"không auto-tune profile đã publish; correction phải tạo profile version mới qua
review". Câu hỏi thật mà việc báo này phơi ra — status của một band biên có được
phép kích hoạt profile version mới hay không — được graduate thành
[Chốt phản ứng khi band biên của live balance validation rơi vào OUT_OF_TOLERANCE](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/45).

## 9. Retention: một bất biến, không phải một con số

Thoả thuận retention, thứ tự xoá và schema vật lý thuộc
[Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14).
Artifact này MUST NOT đặt số ngày.

Nó gửi sang đúng một bất biến:

> Telemetry Fact MUST NOT bị xoá, làm mờ, hay tổng hợp mất mát trong khi cặp
> `(ruleset_id, profile_id)` của nó vẫn là Rating Generation hiện hành.

Lý do: `VALIDATED` đòi **94** decisive Match trong **một** band dưới **cùng** một
Generation. Một thoả thuận retention ngắn bình thường sẽ khiến các band thưa
không bao giờ tích đủ, và `VALIDATED` thành điều kiện bất khả thi vĩnh viễn — đúng
loại bẫy mà [Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17)
§5 đã phải gỡ một lần khi bác điều kiện "ít nhất một band `VALIDATED` trước Open
Beta". Bất biến này **có** thu hẹp không gian lựa chọn của chủ schema, và thu hẹp
có chủ ý: nó loại mọi thoả thuận xoá hay tổng hợp mất mát chạm vào fact của
Generation đang sống, kể cả một chu kỳ quét đồng nhất kiểu 30 ngày. Cái nó không
làm là ấn định một con số — sàn neo vào vòng đời của Generation, nên chủ schema
vẫn chọn tự do thời hạn, thứ tự xoá và hình dạng lưu trữ cho mọi thứ còn lại.

## 10. Telemetry không nối vào bất kỳ đường ra quyết định tự động nào

- Balance Telemetry MUST là nội bộ. Không endpoint, không màn hình, không mục
  lịch sử nào cho Player đọc nó.
- Aggregate MUST NOT là input của gameplay, của Matchmaking Queue, của Ranked
  Rating hay Rating Settlement, của Skill Estimate, hoặc của việc chọn Bot
  Calibration Profile cho một Match.
- Không cơ chế nào được tự động đổi profile dựa trên status. Chuỗi phản ứng đã
  chốt là: người đọc aggregate → review → profile version mới.

Điều kiện thứ hai và thứ ba là cách giữ "không auto-tune" của issue 30 §9 bằng
ràng buộc chứ không bằng thiện chí. Điều kiện thứ nhất giữ cho
[Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17)
§7.2 tuyên bố B8 — cấm nói Bot Opponent được chứng minh cân bằng — không thể bị
vi phạm qua đường telemetry. Nếu sau này muốn hiển thị bất cứ thứ gì ra Player,
đó là việc của chủ UX và chủ public wording, không phải của contract này.

## 11. Acceptance invariants

Một implementation tuân thủ `digitcode-balance-telemetry/1.0.0` MUST thoả:

1. Mỗi Match finalized sinh đúng hai Telemetry Fact; finalization chạy lại không
   sinh thêm fact nào.
2. Không Telemetry Fact nào chứa bất kỳ mục nào trong danh sách cấm ở §4.
3. Không tồn tại phép nối nào, trong schema hay trong truy vấn, ghép hai fact của
   cùng một Match, hoặc ghép một fact với Match history, anti-cheat evidence hay
   security log.
4. `observed_on` không mang thông tin nhỏ hơn một ngày.
5. `subject_pseudonym` của cùng một Player khác nhau giữa hai Rating Generation.
6. Mọi nhãn của `puzzle_difficulty_class` chứa ít nhất 172 secret.
7. Status của một band tính lại từ tập fact luôn cho cùng kết quả, không phụ
   thuộc thời điểm chạy hay sự tồn tại của một job.
8. Không cặp `(ruleset_id, profile_id)` nào bị gộp chung khi tính status.
9. Aggregate của band 500 và band 1500 luôn kèm `out_of_domain_count`; aggregate
   của mọi band luôn kèm `distinct_subject_count` và số Draw.
10. Không đường mã nào đọc aggregate trong luồng gameplay, matchmaking, rating,
    hay chọn profile.

## 12. Artifact này không quyết định

| Chủ đề | Chủ |
| --- | --- |
| Schema vật lý, index, retention, quyền đọc, xoá dữ liệu, privacy policy | [Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| Nội dung Bot Calibration Profile, định nghĩa band, ngưỡng tolerance, mốc 94 | [Chốt hàm hiệu chuẩn Ranked Rating thành Score mục tiêu](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30) |
| Validation status nào cho phép launch; public wording về cân bằng | [Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17) |
| Anti-cheat evidence, security log, ngưỡng quota 40%/50%, log leakage | [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) |
| Observability, alerting, quota monitoring, release criteria | [Chốt quality gate, zero-cost operations và release criteria](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16) |
| Presentation và câu chữ hiển thị cho Player | [Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| Transaction, transport và index implementation | [Chọn kiến trúc web và managed services](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3) |
| Phản ứng với status của band biên | [Chốt phản ứng khi band biên của live balance validation rơi vào OUT_OF_TOLERANCE](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/45) |
| Production implementation | ngoài phạm vi map |

## 13. Canonical sources

- [`CONTEXT.md`](../../../CONTEXT.md): **Balance Telemetry**, **Rating
  Generation**, **Ranked Match**, **Practice Match**, **Bot Opponent**, **Bot
  Calibration Profile**, **Skill Estimate**, **Score**, **Bot Score**, **Solve
  Time**, **Ruleset**.
- [`game-spec.md`](../2026-08-23-issue-9-game-spec/game-spec.md): R-I-02, R-I-03,
  R-P-14, R-B-03, R-C-15, R-V-07 đến R-V-09, R-BOT-07, R-O-03 — bí mật, đáp án
  Clue, ghi chú nháp, Strike, terminal status, công bố sau Match.
- [`bot-calibration-profile.md`](../2026-08-31-issue-30-bot-calibration/bot-calibration-profile.md)
  §9: decisive share, 11 band, ba validation status, mốc 94 decisive Match, và
  việc giao event/storage/privacy/production aggregation cho ticket này.
- [`elo-and-result-integrity.md`](../2026-09-13-issue-15-elo-policy/elo-and-result-integrity.md):
  §7 ma trận outcome và "không có nhánh void"; §8 Rating Generation; §13 giao
  event và aggregate đo decisive share theo band cho ticket này.
- [`launch-posture.md`](../2026-09-15-issue-17-launch-posture/launch-posture.md):
  §5 cửa balance validation và hệ quả của `OUT_OF_TOLERANCE`; §7.2 tuyên bố bị
  cấm B8.
- [`findings.md`](../2026-08-22-issue-6-puzzle-fairness/findings.md): 465.120
  secret, 465.034 lớp, 86 lớp cỡ 2 tức 172 secret trong một họ đối xứng cột,
  sampler lệch 9/7 nhưng độ khó không lệch.
- [`findings.md`](../2026-08-24-clue-bounds/findings.md): khoảng adaptive
  `[10, 16]` vẫn hở, chưa có cây quyết định tối ưu.
- [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12):
  danh sách cấm của operational log; security log 30 ngày tách khỏi telemetry;
  anti-cheat evidence và retention của nó; không thu IP/device fingerprint.
- [Chốt Match lifecycle, reconnect và concurrency semantics](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4):
  finalization atomic và idempotent; chi phí của lưu lượng theo từng hành động.
- [Nghiên cứu cơ chế scheduled job zero-cost cho Vercel Hobby + Supabase Free](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27):
  giới hạn của Vercel Cron trên Hobby và của `pg_cron`.
- [Chốt identity, profile và invite-room lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2):
  tombstone giữ `player_id`; tên thật lộ trong Match là rò rỉ PII.
