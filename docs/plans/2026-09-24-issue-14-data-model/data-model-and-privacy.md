# Data Model, Match History và quyền riêng tư cho Production MVP

Contract ID: **`digitcode-data-model/1.0.0`**
Ruleset ID: **`digitcode-ruleset/1.0.0`**
Ticket: [Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)

Decision: HITL grilling with the map owner on 2026-09-24.

Đây là artifact planning chốt **mô hình dữ liệu logic** của Production MVP: dữ
liệu nào tồn tại, cái gì là state và cái gì là event, mỗi thứ sống bao lâu, ai
được đọc gì, xoá tài khoản làm gì với lịch sử, và vì sao result cùng Ranked
Rating audit được mà không lộ Puzzle đang chơi. Nó chốt entity logic và ràng
buộc, không chốt DDL, kiểu cột hay index vật lý. Nó không đổi 95 luật của
`digitcode-ruleset/1.0.0`, không đổi công thức rating, và không mở lại quyết định
nào của các ticket đã đóng.

## 1. Những gì artifact này kế thừa, không quyết định lại

- [Chốt identity, profile và invite-room lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2):
  xoá tài khoản là tombstone, xoá PII và giữ `player_id`, rating ledger và Match
  record; từ chối xoá khi còn Match chưa terminal; không hoàn ngược transfer nào.
  Invite Code dùng một lần, không bao giờ tái dùng.
- [Chốt Match lifecycle, reconnect và concurrency semantics](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4):
  Room và Match là hai entity; Match sinh ở Match Start; Score suy ra, đóng băng
  một lần khi terminal; `version` tính theo Player State; `command_id` do client
  sinh; finalization atomic, idempotent và là hàm thuần; mọi bất biến
  concurrency do PostgreSQL giữ.
- [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12):
  PostgreSQL là authority; Puzzle secret không ai đọc trong vận hành thường ngày;
  operational log không chứa secret, đáp án Clue, Player State hay PII; security
  log 30 ngày; command dedup tới 24 giờ sau terminal; anti-cheat chỉ dùng pair,
  outcome, duration, Forfeit và account age, không thu IP hay device fingerprint.
- [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
  §10–§11: Rating Settlement trong transaction finalization, idempotency key là
  `match_id`; Rating Ledger strictly append-only với sáu nhóm trường tối thiểu;
  correction là event mới và không đảo kết quả Match; Generation cũ lưu kèm nhãn,
  không xoá, không mang sang.
- [Chốt Match lifecycle cho đường Matchmaking Queue](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/31):
  Queue Entry có đúng ba trạng thái terminal; Match Start đóng dấu Ruleset,
  Bot Calibration Profile và snapshot rating; Bot Opponent hành động theo một lịch
  deterministic và chỉ đổi Bot Score qua action ledger.
- [Chốt mức bảo đảm khi Player mất quyền truy cập](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34):
  mất quyền truy cập không xoá dữ liệu đã lưu và không đảo kết quả hay settlement.
- [Chốt telemetry tối thiểu để kiểm chứng cân bằng gameplay](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/35)
  §9: Telemetry Fact MUST NOT bị xoá, làm mờ hay tổng hợp mất mát khi Rating
  Generation của nó còn hiện hành.

## 2. Ba lớp của một Match

Một Match để lại ba loại dữ liệu, mỗi loại một mục đích và một vòng đời.

| Lớp | Là gì | Sống bao lâu |
| --- | --- | --- |
| **Match record** | Bản ghi kết quả đóng băng lúc finalization | Vĩnh viễn |
| **Match Timeline** | Chuỗi hành động được chấp nhận của cả hai phía | 90 ngày sau finalization |
| **State trong Match** | Player State và Bot State hiện hành, có `version` | 90 ngày sau finalization |

**State trong Match** là nguồn authoritative khi Match đang chạy. Mỗi command
được chấp nhận và làm đổi state MUST append **đúng một** event vào Match Timeline
ngay trong cùng transaction với thay đổi state. Command bị từ chối hoặc no-op
(R-V-05, R-C-13) MUST NOT tạo event. Với Bot Opponent, action ledger của
[Chốt Match lifecycle cho đường Matchmaking Queue](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/31)
§7 chính là phần timeline của phía bot.

**Match record** được finalization ghi, trong cùng transaction làm phía thứ hai
terminal. Nó mang đủ tập R-O-03: secret, hai terminal state, hai Score hoặc Score
cùng Bot Score cuối, các Solve Time có tồn tại, và outcome.

**Vì sao không event-sourced.** Timeline hết hạn sau 90 ngày còn kết quả thì vĩnh
viễn. Nếu timeline là nguồn sự thật duy nhất, sau 90 ngày không dựng lại được kết
quả nữa. Ba lớp tách nhau để lớp nặng có thể hết hạn mà lớp cần giữ không mất gì.

**Player Board trong timeline.** Allowlist command của
[Chốt Match lifecycle, reconnect và concurrency semantics](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4)
không có command ghi board, nên Player Board chỉ tới server cùng Verify. Timeline
vì vậy chứa board của **mỗi lần Verify được chấp nhận**, không chứa từng lần vẽ.
Ghi chú nháp không bao giờ có mặt (R-B-03).

**Mốc tính hạn** của mọi thứ "sau finalization" là thời điểm commit của
finalization, không phải `deadline_at`. Một Match chưa finalize thì chưa có mốc,
nên timeline và state của nó không thể hết hạn trước khi kết quả tồn tại.

## 3. Entity logic và vòng đời

| Entity | Nội dung chính | Hết hạn |
| --- | --- | --- |
| Player Identity | `player_id`, `created_at`, thuộc tính bền "đã từng link Google" (issue 15 §6), display name, lịch sử tên, Player Tag, `tombstoned_at` | Vĩnh viễn; PII bị xoá ở tombstone (§8) |
| Linked Identity | Provider link, email | Nằm ở auth của vendor; xoá ở tombstone |
| Room | Owner, mode, trạng thái, mốc thời gian | Vĩnh viễn |
| Invite Code registry | Mọi mã từng phát, kèm Room | Vĩnh viễn |
| Queue Entry | Player, trạng thái, `bot_eligible_at`, `expires_at` | 24 giờ sau khi vào trạng thái terminal |
| Match record | §2, cộng các giá trị đóng dấu ở Match Start: `ruleset_id`, `profile_id`, snapshot rating, Generation, `started_at`, `deadline_at`; `room_id` hoặc `null`; `puzzle_id` mờ | Vĩnh viễn |
| Puzzle secret | Secret và seed lịch bot (§4) | 90 ngày sau finalization |
| Player State, Bot State | State hiện hành, `version`, mốc hoạt động gần đây | 90 ngày sau finalization |
| Match Timeline event | §2 | 90 ngày sau finalization |
| Command dedup | `command_id`, response đã trả | 24 giờ sau terminal (issue 12) |
| Ranked Rating | Theo cặp (Player Identity, Rating Generation) | Vĩnh viễn |
| Rating Ledger event | Sáu nhóm trường của issue 15 §11 | Vĩnh viễn |
| Skill Estimate log | §9 | Vĩnh viễn |
| Telemetry Fact | 20 trường của issue 35 §3 | Sàn issue 35 §9, rồi 90 ngày sau khi Generation hết hiện hành |
| Case file | §6 | Muộn hơn giữa 90 ngày và 30 ngày (§6) |
| Enforcement record | §6 | Chừng nào Player Identity còn tồn tại |
| Security log | Issue 12 | 30 ngày |

**Mốc hoạt động gần đây** là một trường của Player State, được command và
snapshot cập nhật. Nó hết hạn cùng Player State và MUST NOT trở thành log truy
cập. MVP không có bảng session riêng: refresh token, rotation và logout-all do
auth của vendor giữ. Nơi duy nhất ghi sự kiện auth là security log của issue 12.

**Invite Code registry** giữ vĩnh viễn để luật "không bao giờ tái dùng" của issue 2
là một constraint, không phải một kiểm tra trong code. Mã đã chết không mở được gì
nên không còn là bí mật. Hash cũng vô ích, vì không gian 10⁹ brute-force được
ngay. Khi mã còn sống, mọi rào của issue 12 vẫn áp dụng: không có trong URL, log,
analytics hay referrer.

**Rating Generation cũ** MUST được lưu kèm nhãn Generation. Không xoá, không mang
sang ([Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
§8).

## 4. Puzzle secret và seed của Bot Opponent

R-P-14 giao hình dạng bản ghi Puzzle cho ticket này.

- Secret MUST nằm trong một entity riêng, khoá theo `match_id`. Entity này MUST
  NOT cấp quyền nào cho role mà client dùng được. Chỉ các hàm server đọc nó:
  trả lời Clue, chấm Verify, chấm Bot Submission, dựng lịch bot và finalization.
- Rào này là **cấu trúc**. Nó không phụ thuộc việc viết đúng một policy từng dòng
  trên Match record, vì publishable key là public và ai cũng gọi thẳng Data API
  được.
- Finalization MUST chép secret vào Match record trong chính transaction đó. "Lộ
  secret" và "kết quả tồn tại" vì vậy là cùng một sự kiện, đúng lý do issue 4 gộp
  finalization vào một transaction: R-I-02 cho phép phát secret đúng một lần, sau
  R-T-11.
- `puzzle_id` MUST là một giá trị ngẫu nhiên, không phải chỉ số của mã trong pool,
  để không suy ra được secret từ nó.
- Lịch hành động của Bot Opponent MUST được lưu dưới dạng **input**: `profile_id`
  và snapshot rating nằm trên Match record; seed ngẫu nhiên nằm cạnh secret. MUST
  NOT lưu bản lịch tính sẵn. Biết lịch là biết bot sắp Solve lúc nào, điều mà
  R-O-02 và R-BOT-10 cấm. Khi đã có secret và seed, toàn bộ lịch tính lại được,
  nên audit không cần bản tính sẵn.
- Break-glass access vào entity này MUST có lý do và có audit (issue 12).

## 5. Retention: hai tầng, và cái gì được hy sinh

Không cơ chế zero-cost nào được vendor bảo đảm đủ để một hành vi phụ thuộc vào nó
([Nghiên cứu cơ chế scheduled job zero-cost cho Vercel Hobby + Supabase Free](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27)).
Retention vì vậy dùng đúng mẫu mà issue 4 và issue 31 dùng cho `EXPIRED`:
correctness nằm trên đường đọc, sweep chỉ là tối ưu.

1. **Hết hạn truy cập là bảo đảm cứng.** Mỗi hàng có hạn MUST mang mốc hết hạn
   của chính nó. Mọi đường đọc MUST lọc theo mốc đó, nên hàng quá hạn không đọc
   được nữa dù vẫn còn trên đĩa.
2. **Xoá vật lý là best-effort.** `pg_cron` hoặc quét kèm các đường ghi sẵn có
   được phép làm việc này. Không có hạn trễ nào được hứa, và không hành vi sản
   phẩm nào được phụ thuộc vào việc xoá vật lý đã chạy hay chưa. Theo dõi độ trễ
   xoá thuộc
   [Chốt quality gate, zero-cost operations và release criteria](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16).

**Áp lực quota.** Các lớp vĩnh viễn chỉ tăng mà không giảm, trong khi Postgres của
Supabase Free có 500 MB mỗi project. Khi áp lực quota buộc phải chọn:

- Match Timeline (kéo theo state trong Match) là lớp **duy nhất** operator được
  rút ngắn dưới 90 ngày. Việc rút MUST là một quyết định có ghi lại, MUST NOT tự
  động, và MUST NOT chạm Match nào mà một case file còn mở đang trỏ tới.
- Match record, Rating Ledger, Skill Estimate log, enforcement record và Telemetry
  Fact của Generation hiện hành MUST NOT bị cắt. Hết đường thì admission đóng, đúng
  luật fail closed của map.

Vì vậy 90 ngày là chính sách nội bộ, không phải lời hứa công khai. Điều đó khớp với
tuyên bố bị cấm B4 của
[Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17)
§7.2: không hứa một thời hạn lưu trữ cụ thể.

## 6. Anti-cheat evidence: case file và enforcement record

Tập dữ liệu anti-cheat của issue 12 (pair, outcome, duration, Forfeit, account age)
đều nằm sẵn trên Match record, Rating Ledger và Player Identity, tức là trên các
lớp vĩnh viễn mà issue 2 và issue 15 đã chốt. Nếu hiểu "anti-cheat evidence" là
chính các dữ liệu đó, mốc 90/30 của issue 12 hoặc vô nghĩa, hoặc đụng hai quyết định
đã đóng. Artifact này đọc nó như sau:

- **Case file** là evidence. Nó gồm flag, tham chiếu tới các `match_id` liên quan
  và ghi chú của reviewer. Nó MUST NOT chép dữ liệu Match. Nó hết hạn ở thời điểm
  muộn hơn giữa **90 ngày** sau finalization của Match mới nhất mà nó tham chiếu
  và **30 ngày** sau khi case đóng. Case còn mở thì không hết hạn.
- **Enforcement record** ghi một vi phạm đã xác nhận: `player_id`, case ID,
  reason category, thời điểm xác nhận, bậc nấc, restriction từ/đến, kết quả
  appeal. Nó MUST append-only; appeal thành công là một record mới. Nó MUST NOT
  chứa PII, dữ liệu Match hay ghi chú reviewer. Nó sống chừng nào Player Identity
  còn tồn tại, kể cả sau tombstone, vì nấc 7 ngày → 30 ngày → vô thời hạn của
  issue 12 cần biết đây là vi phạm thứ mấy.

Cách đọc này không nới tập dữ liệu của issue 12, không thêm IP hay fingerprint,
và không sửa issue 2 hay issue 15.

**Signal collusion.** Các signal mà
[Chốt mô hình đối thủ của Ranked Match](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25)
yêu cầu giữ (tỷ trọng Match theo cặp, chuỗi outcome một chiều, duration bất thường,
tỷ lệ Forfeit/timeout, account age, opponent diversity, graph donor→recipient) đều
suy ra được từ lớp vĩnh viễn. MUST NOT có kho signal riêng hay bản materialize:
signal được tính khi đọc. Ticket này chỉ bảo đảm bốn thứ tồn tại vĩnh viễn: cặp
Player của Match, outcome, terminal state (kể cả `FORFEITED`), `started_at` cùng
thời điểm finalization, và `created_at` của Player Identity. `created_at` không
phải PII và sống qua tombstone.

## 7. Ai được đọc gì

Không ai ngoài những người tham gia đọc được bất cứ thứ gì về một Match. Public
profile, spectator, leaderboard và admin dashboard đều nằm ngoài phạm vi của map.

| Dữ liệu | Player tham gia | Player khác | Operator được chỉ định |
| --- | --- | --- | --- |
| State trong Match của chính mình | Trong lúc chơi | Không | Break-glass có audit |
| State trong Match của Opponent | Không trước R-T-11 (R-O-02, R-BOT-10) | Không | Break-glass có audit |
| Match record | Sau R-T-11 | Không | Có |
| Match Timeline, cả hai phía | Sau R-T-11, tới khi hết hạn | Không | Có, qua case file |
| Puzzle secret, seed | Chỉ qua Match record, sau R-T-11 | Không | Break-glass có audit |
| Rating Ledger event mình tham gia | Sau R-T-11, kể cả snapshot rating của Opponent | Không | Có |
| Actor và reason của correction | Chỉ reason category | Không | Có |
| Skill Estimate log | Không | Không | Có |
| Queue Entry của chính mình | Có (issue 31 §8) | Không | Có |
| Case file | Không | Không | Có |
| Enforcement record của chính mình | Reason category, case ID, restriction | Không | Có |
| Telemetry Fact | Không (issue 35 §10) | Không | Có |
| Security log | Không | Không | Có (issue 12) |

- **Timeline của cả hai phía.** R-O-03 giao cho ticket này câu hỏi "Clue nào
  Opponent đã mua". Sau R-T-11, mỗi phía đọc được **toàn bộ** Match Timeline của
  cả hai phía, gồm Clue, board lúc Verify, Strike và terminal. Lúc đó secret đã
  công bố nên không còn gì để lộ, và issue 12 cũng định nghĩa replay là timeline
  "của cả hai phía". Với Match đấu bot, Player đọc được timeline của Bot Opponent,
  đúng tinh thần R-BOT-11 và Q13 của issue 25.
- **Snapshot rating của Opponent.** Ranked Rating là con số public (`CONTEXT.md`),
  nên Player đọc được snapshot của Opponent trong ledger event, nhưng chỉ sau
  R-T-11, vì R-O-01 giới hạn những gì thấy được trong lúc chơi. Ticket này chỉ
  chốt **quyền** đọc. Việc có vẽ con số đó lên màn hình hay không thuộc
  [Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13).
- **Skill Estimate** không bao giờ hiển thị cho Player (`CONTEXT.md`), nên log của
  nó chỉ operator đọc được.
- Mọi quyền trong bảng MUST được PostgreSQL kiểm lại. Client không được tự khai
  `player_id` (issue 12).

## 8. Tombstone và identity ẩn danh

Issue 2 đã chốt phần lõi của tombstone. Artifact này điền bốn chỗ còn thiếu:

1. **Player Tag** bị xoá cùng display name và lịch sử tên. Lịch sử của Opponent chỉ
   hiện "Người chơi đã xoá". Tag không phải PII, nhưng người quen nhận ra
   "#4821 đã xoá" là ai.
2. **Phần timeline của người bị xoá** không bị đụng tới và tự hết hạn sau 90 ngày.
   Nó không chứa PII, và Opponent có quyền xem replay theo §7.
3. **Ranked Rating và Skill Estimate** được giữ, vì ledger phải reconcile được với
   rating đã materialize. Chúng không còn đường đọc nào, vì một tài khoản tạo lại
   là một Player Identity mới.
4. **Auth user của vendor** bị xoá hẳn, vì đó là nơi chứa email và provider link.
   Player Identity của mình thì được giữ.

Tombstone không đụng tới enforcement record (§6) và `created_at` (§6).

**Identity ẩn danh** không hết hạn chỉ vì không hoạt động. Nó được giữ như mọi
Player Identity khác và chỉ bị tombstone khi chính Player yêu cầu xoá. Cho nó hết
hạn sẽ thêm một đường mất quyền truy cập mới, không đảo ngược được, vào ma trận
của
[Chốt mức bảo đảm khi Player mất quyền truy cập](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34)
§3, trong khi lợi ích dung lượng là nhỏ: hàng Player rất nhẹ, còn Match record của
họ vẫn vĩnh viễn. Dung lượng của chúng do issue 16 theo dõi như mọi quota khác.

## 9. Rating Ledger và Skill Estimate log

Rating Ledger giữ đúng định nghĩa của `CONTEXT.md` và issue 15 §11: mọi Rating
Settlement và mọi correction, không gì khác.

Skill Estimate quyết định trực tiếp Ranked Rating mở đầu (`Ranked Rating := Skill
Estimate`, issue 15 §5), nhưng ledger không ghi nó. Không có gì giải thích được
một opening rating cụ thể. Vì vậy:

- Mỗi lần Skill Estimate đổi MUST append một event vào **Skill Estimate log**, tách
  khỏi Rating Ledger. Event gồm `match_id`, Rating Generation, giá trị trước,
  `K_seed`, delta, giá trị sau, và thời điểm commit.
- Log này MUST append-only và vĩnh viễn.
- Seed của Ranked Rating trong một Generation là giá trị cuối cùng của log trong
  Generation đó. Nhờ vậy phép reconciliation của issue 15 §11 ("seed cộng tổng
  applied delta") có một điểm neo kiểm chứng được.
- Event MUST được ghi trong cùng transaction finalization với Practice Match đấu
  bot đã tạo ra nó.

## 10. Match History

**Match History** là những gì một Player đọc lại được về các Match mình đã chơi:
Match record vĩnh viễn, cộng Match Timeline khi nó còn hạn.

- **Đọc Match History là đường finalization thứ tư.** Trước khi trả danh sách, nếu
  Match chưa finalize duy nhất của actor đã quá `deadline_at` thì đường đọc MUST
  gọi đúng hàm finalization mà ba đường của issue 4 đang dùng. Constraint "một
  Match chưa finalize cho mỗi Player Identity" bảo đảm việc này tốn tối đa một
  transaction. Đây là bổ sung, không đổi bất biến nào của issue 4: hàm vẫn là
  một, và kết quả vẫn là hàm thuần của `started_at`, các command đã ghi và
  `clock_timestamp()`.
- Nhờ vậy Match History không bao giờ hiện cho chính người xem một Match "đã hết
  giờ nhưng chưa có kết quả". Match còn trong hạn hiện là đang diễn ra, không kèm
  thông tin nào mà R-O-02 cấm.
- Match đấu bot MUST hiện rõ là đấu Bot Opponent, không có Player Tag giả (issue 25
  Q13). Nó vào Match History như mọi Match khác.
- Match History MUST NOT được dựng từ Balance Telemetry, và ngược lại (issue 35 §2,
  §4).

## 11. Ràng buộc mà PostgreSQL MUST giữ

Mỗi dòng dưới đây MUST là một ràng buộc mà database không thể vi phạm, không phải
một kiểm tra ở tầng ứng dụng. Cách biểu diễn cụ thể (index, exclusion, trigger hay
khoá tuần tự) thuộc
[Chọn kiến trúc web và managed services](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3).

1. Tối đa **một** Match chưa finalize cho mỗi Player Identity, chung cho Room,
   Matchmaking Queue và Match đấu bot (issue 4 Q10, issue 15 §10).
2. Tối đa một Room đang mở cho mỗi Room Owner, và tối đa một Match chưa terminal
   cho mỗi Room (issue 4 Q10).
3. Tối đa một Queue Entry còn hiệu lực cho mỗi Player, và không bao giờ đồng thời
   có Queue Entry còn hiệu lực cùng một Match chưa finalize (issue 31 §11).
4. Tối đa một Rating Ledger event khởi đầu cho mỗi `match_id`; correction có khoá
   idempotency và constraint riêng (issue 15 §10–§11).
5. Finalization ghi kết quả đúng một lần cho mỗi Match và sinh đúng hai Telemetry
   Fact; chạy lại không ghi thêm gì (issue 4 Q8, issue 35 §2).
6. Mỗi Invite Code từng phát là duy nhất trên toàn registry, vĩnh viễn.
7. `command_id` là duy nhất trong phạm vi dedup của actor (issue 4 Q9).
8. Một command được chấp nhận và làm đổi state sinh đúng một Match Timeline event.
9. Rating Ledger, Skill Estimate log, enforcement record và Telemetry Fact không có
   đường update hay delete nào.

## 12. Acceptance invariants

Một implementation tuân thủ `digitcode-data-model/1.0.0` MUST thoả:

1. Không role nào mà client dùng được đọc được Puzzle secret hay seed của bot khi
   Match chưa finalize.
2. Secret xuất hiện trong Match record đúng khi, và chỉ khi, Match đã finalize.
3. Không đường đọc nào trả về một hàng đã quá mốc hết hạn của chính nó, bất kể hàng
   đó đã bị xoá vật lý hay chưa.
4. Sau khi Match Timeline hết hạn, Match record vẫn trả đủ tập R-O-03.
5. Rating hiện hành trong một Generation bằng giá trị cuối của Skill Estimate log
   cộng tổng applied delta trong Rating Ledger; mọi sai lệch phát hiện được bằng
   một truy vấn.
6. Tombstone không xoá hay sửa bất kỳ Match record, Rating Ledger event, Skill
   Estimate log event hay enforcement record nào.
7. Sau tombstone, không bề mặt nào hiện display name, lịch sử tên, Player Tag hay
   email của người đó.
8. Case file còn mở không bao giờ hết hạn, và Match mà nó trỏ tới không bị rút ngắn
   timeline.
9. Case file không chứa bản sao dữ liệu Match; enforcement record không chứa PII.
10. Đọc Match History không bao giờ trả một Match đã quá `deadline_at` mà chưa có
    kết quả của chính người đọc.
11. Không bề mặt nào của Player hiện Skill Estimate hay log của nó.
12. Không có entity session nào của riêng hệ thống; không có IP, device fingerprint
    hay user-agent trong bất kỳ entity nào ở §3.

## 13. Artifact này không quyết định

| Chủ đề | Chủ |
| --- | --- |
| DDL, kiểu cột, index vật lý, cách biểu diễn ràng buộc §11, transaction và transport, notification row cho Realtime | [Chọn kiến trúc web và managed services](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3) |
| Cách trình bày Match History và replay, có vẽ rating của Opponent không, câu chữ "Người chơi đã xoá" | [Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| Ngưỡng cảnh báo quota, theo dõi độ trễ xoá vật lý, release criteria | [Chốt quality gate, zero-cost operations và release criteria](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16) |
| Rà soát pháp lý của nghĩa vụ xoá dữ liệu và privacy notice; issue 2 giao nghĩa vụ xoá cho cả ticket này lẫn issue 7, hình dạng xoá chốt ở §8 | [Chốt license và attribution policy](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/7) |
| Public wording về lưu trữ | [Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17) |
| Tập dữ liệu anti-cheat, nấc phạt, security log | [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) |
| Công thức rating, Generation, correction policy | [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| Nội dung Telemetry Fact và aggregate | [Chốt telemetry tối thiểu để kiểm chứng cân bằng gameplay](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/35) |
| Production implementation | ngoài phạm vi map |

## 14. Canonical sources

- [`CONTEXT.md`](../../../CONTEXT.md): **Player Identity**, **Linked Identity**,
  **Tombstone**, **Match**, **Match History**, **Match Timeline**, **Player
  State**, **Bot State**, **Rating Ledger**, **Rating Generation**, **Skill
  Estimate**, **Ranked Rating**, **Balance Telemetry**, **Room**, **Invite Code**,
  **Queue Entry**.
- [`game-spec.md`](../2026-08-23-issue-9-game-spec/game-spec.md): R-P-14, R-I-01,
  R-I-02, R-I-03, R-B-03, R-C-13, R-C-15, R-V-05, R-T-11, R-O-01, R-O-02, R-O-03,
  R-BOT-10, R-BOT-11.
- [Chốt identity, profile và invite-room lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2):
  tombstone, cap, vòng đời Invite Code.
- [Chốt Match lifecycle, reconnect và concurrency semantics](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4):
  topology Room/Match, Score suy ra, allowlist command, ba đường finalization,
  ràng buộc concurrency, Match bỏ rơi nằm `ACTIVE` hàng tuần.
- [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12):
  secret, log, security log 30 ngày, dedup 24 giờ, replay nhẹ, tập dữ liệu
  anti-cheat, nấc phạt, mốc 90/30.
- [`elo-and-result-integrity.md`](../2026-09-13-issue-15-elo-policy/elo-and-result-integrity.md):
  §5 Skill Estimate, §8 Rating Generation, §10 settlement, §11 Rating Ledger.
- [`dossier.md`](../2026-08-24-issue-25-opponent/dossier.md) và
  [Chốt mô hình đối thủ của Ranked Match](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25):
  danh sách signal collusion, luôn nói rõ đấu bot, identity ẩn danh.
- [`matchmaking-queue-lifecycle.md`](../2026-09-03-issue-31-matchmaking-lifecycle/matchmaking-queue-lifecycle.md):
  §3 Queue Entry, §6 Match Start, §7 lịch bot, §8 quyền đọc trong Queue, §11.
- [`access-loss-guarantees.md`](../2026-09-04-issue-34-access-loss/access-loss-guarantees.md):
  §3 ma trận mất quyền truy cập.
- [`balance-telemetry.md`](../2026-09-22-issue-35-balance-telemetry/balance-telemetry.md):
  §2, §4, §9, §10.
- [`launch-posture.md`](../2026-09-15-issue-17-launch-posture/launch-posture.md):
  §7.2 tuyên bố bị cấm B4.
- [Nghiên cứu cơ chế scheduled job zero-cost cho Vercel Hobby + Supabase Free](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27):
  không scheduler zero-cost nào được vendor bảo đảm.
- [Nghiên cứu cách Supabase tính MAU cho phiên ẩn danh](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/33):
  anonymous user là auth user thật, không có automatic cleanup.
- [`zero-cost-vercel-architecture.md`](../../research/2026-08-22-zero-cost-vercel-architecture.md):
  Postgres 500 MB mỗi project trên Supabase Free.
