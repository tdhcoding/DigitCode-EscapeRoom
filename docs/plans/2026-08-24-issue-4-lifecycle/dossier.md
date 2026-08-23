# Dossier — Chốt Match lifecycle, reconnect và concurrency semantics

Ticket: [Chốt Match lifecycle, reconnect và concurrency semantics](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)
Branch: `feat/issue-4-lifecycle-prep`
Soạn: bước AFK đầu phiên 2026-08-24 (phiên có người ngồi cùng).

## Tài liệu này là gì

Đây là **phần AFK của một ticket `wayfinder:grilling`**: gom hết ràng buộc đã có,
dựng cây quyết định, và soạn sẵn câu hỏi round-1 kèm khuyến nghị — để buổi
grilling bắt đầu ở câu hỏi thật chứ không ở phần tra cứu. Cùng khuôn với
[dossier của #2](https://github.com/tdhcoding/DigitCode-EscapeRoom/blob/main/docs/plans/2026-08-24-issue-2-identity/dossier.md).

Nó **không quyết định gì**. Mọi mục ở phần C là câu hỏi để người dùng trả lời;
khuyến nghị chỉ là khuyến nghị, có thể bác toàn bộ. Theo `wayfinder`, ticket HITL
không được agent tự trả lời thay.

Ba phần bắt buộc: **(A)** ràng buộc đã có, **(B)** design tree, **(C)** câu hỏi
round-1. Thêm **(D)** dữ kiện đã tra sẵn, **(E)** để dành round-2, **(F)** ranh
giới với ticket khác.

**Một dòng đáng đọc trước hết.** Cụm từ "**Match bắt đầu**" xuất hiện đúng hai
lần trong toàn bộ ruleset (R-S-02 và bảng R-T-01), cụm "**tạo Match**" đúng một
lần (R-P-13), và "**Match start**" đúng một lần (R-V-06). Không chỗ nào định
nghĩa chúng. Ba luật nặng nhất của lifecycle — đồng hồ chạy từ đâu, `ACTIVE` vào
lúc nào, Puzzle sinh lúc nào — cùng treo lên hai từ chưa có nghĩa. Đó là câu hỏi
số một của ticket này, và mọi câu còn lại đều hạ nguồn của nó.

---

## A. Những quyết định đã có, và chúng ràng buộc #4 như thế nào

Mỗi dòng ghi **nguồn → ràng buộc cụ thể lên #4**. Không tóm tắt lại nguồn; chỉ
lấy phần cắt vào ticket này.

### A.1 Sáu thứ [#2](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2) CỐ Ý đẩy sang #4

Đây là phần nặng nhất của mục A. #2 không bỏ sót sáu mục này — nó treo chúng lại
và ghi rõ là của #4.

| # | #2 để lại gì | Ràng buộc cụ thể lên #4 |
| --- | --- | --- |
| 1 | **Hai mốc "tạo Match" và "Match bắt đầu"** chưa được định nghĩa, nhưng #2 đã treo hai quyết định lên chúng: mã invite **chết vĩnh viễn khi Match bắt đầu** (Q7 sau tinh chỉnh ở Q9), và mode phải cố định **trước khi Puzzle sinh** — mà R-P-13 sinh Puzzle lúc **tạo Match**. | #4 MUST định nghĩa cả hai mốc. Nếu hai mốc **lệch nhau**, tồn tại một cửa sổ **mã còn sống trong khi Puzzle đã sinh**. Cửa sổ đó phải hoặc bị đóng bằng thiết kế, hoặc được chứng minh là vô hại — không được để ngỏ. → **C-Q1** |
| 2 | **Quyền huỷ room của owner phải tắt đúng thời điểm Match bắt đầu** (R-T-08). #2 gọi đây là "chỗ dễ vi phạm spec nhất của cả ticket đó": nút "đóng room" phải **biến mất** đúng lúc Match khởi động, và "room ownership" **không** phải quyền admin trên một Match đang chạy. | Ranh giới quyền của owner là **hàm của mốc start** ở mục 1. Chốt mốc start là chốt luôn dòng này. Không có ngoại lệ cho người vận hành. → **C-Q1**, **C-Q11** |
| 3 | **Rời room SAU khi Match bắt đầu** — R-T-07: **không phải** forfeit, đồng hồ chạy tới `EXPIRED`. #2 chỉ chốt ca **trước** khi Match bắt đầu (ghế mở lại, mã sống lại tới hết TTL gốc, không gia hạn). | #4 nhận nguyên ca **sau** start. Hệ quả trực tiếp: **không có disconnect grace**, và UI **không được** có nút "rời trận" trông như một lối thoát mềm cạnh Forfeit. → **C-Q3**, **C-Q11** |
| 4 | **Self-join bị cấm cứng (Q9.2) phải sống sót qua reconnect và multi-tab.** Cùng `player_id` không được giữ hai ghế **kể cả khác thiết bị**. | Bất biến này là **của #2**, #4 chỉ được giữ chứ không được nới. Nó nói ghế gắn với `player_id`, **không** gắn với session/tab/thiết bị — nên chính sách multi-tab của #4 là câu hỏi về **UX và ngân sách connection**, không phải về tính đúng đắn của ghế. → **C-Q4** |
| 5 | **"Match chưa terminal" là mẫu số của cap 1 room + 1 Match.** R-T-11 nói một Player terminal **không** kết thúc Match; #2 chốt là Player đã `SOLVED` mà đối thủ chưa xong thì **VẪN** tính là đang bận (đó là lý do #2 tách hai ô thay vì gộp một). | Cap của #2 chỉ có nghĩa nếu **có ai đó thực sự đẩy Match sang terminal**. Nếu một Match bị bỏ rơi mà không cơ chế nào finalize nó, cap của #2 biến thành **khoá tài khoản vô thời hạn**. Đây là chỗ #4 nợ #2 một câu trả lời, không phải ngược lại. → **C-Q7**, **C-Q8** |
| 6 | **Session lifetime và multi-device.** Gate #9 của #8 đặt JWT expiry **600 giây** và bắt **rotate topic khi revoke membership**. Refresh-token policy, "đăng xuất mọi thiết bị", multi-tab takeover — **chưa ai chốt**. | 600 giây là **đầu vào cứng** (gate của #8, đổi thì phải quay lại HITL của #8). Nhưng 600 giây < deadline 900 giây của một Match ⇒ **mọi Match đều đi qua ít nhất một lần refresh token**. Refresh hỏng giữa trận là sự cố **gameplay**, không chỉ sự cố auth. → **C-Q13**, **C-Q14** |

### A.2 Từ ruleset `digitcode-ruleset/1.0.0` ([#9](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9), CLOSED)

Mục 12 của game-spec liệt kê **đầu vào cứng** mà #4 MUST nhận nguyên trạng:
R-P-14 và R-I-02, R-S-04 và R-T-07, R-T-11, R-K-04.

| Luật | Ràng buộc lên #4 |
| --- | --- |
| **R-S-02** Mỗi Match có **một** Match Clock duy nhất, **wall-clock**, chạy từ lúc Match bắt đầu. Mọi thời hạn đọc từ đồng hồ này. | Một nguồn thời gian, không phải hai. Client **không** có đồng hồ có thẩm quyền. Mọi deadline (900 s), mọi khoá (10 s), mọi hao mòn (60 s) đều là hàm của **một** mốc `started_at`. → **C-Q6** |
| **R-S-03** **Không có Pause.** | Đóng cứng nhánh "tạm dừng khi mất kết nối". Không hỏi. |
| **R-S-04** Mất kết nối **MUST NOT** dừng Match Clock. | Đóng cứng nhánh "disconnect grace period" trong chính đề bài của #4. Cụm "disconnect grace" trong tiêu đề ticket là **di sản của lúc charting**, không phải một nhánh còn mở. |
| **R-S-05** Hao mòn 1 Score mỗi 60 s, **dừng ngay** khi Player vào terminal; Score đóng băng làm bản ghi. | Score là **hàm của thời gian** chứ không phải một biến được tick. Nó buộc #4 chọn giữa "lưu Score" và "suy ra Score" — và suy ra là cách duy nhất không cần timer chạy nền. → **C-Q6** |
| **R-S-06** Deadline **15 phút** (900 s) áp cho **cả hai** Player. | Một deadline chung, không phải hai đồng hồ cá nhân. |
| **R-V-04** Verify **không tốn Score** và **MUST NOT bị giới hạn số lần**. | Verify là command **không giới hạn** ở tầng luật chơi. Trần duy nhất là rate limit của hạ tầng (#8: 20 command/phút/actor). Đây là lý do trần invocation xấu nhất của một Match do **rate limit** đặt, không phải do luật chơi đặt (xem D.1). |
| **R-V-05** Verify trên bàn cờ **không giải mã được** bị từ chối tường minh: không Strike, không mất Score, **không đổi state**. | Một command hợp lệ nhưng **không đổi state**. Idempotency key và `version` của #4 phải xử lý được loại này mà không tạo version mới giả. → **C-Q9** |
| **R-V-08** Strike 1: −10 Score và **khoá Verify 10 giây Match Clock**; khoá chỉ khoá Verify. **R-V-09** Strike 2 → `ELIMINATED` ngay. | Khoá 10 s là một `locked_until` đọc từ Match Clock, không phải một timer client. → **C-Q6** |
| **R-T-01/02** Bốn terminal state **absorbing**; sau terminal, **mọi hành động đổi state** bị từ chối, không ngoại lệ; truy cập **chỉ-đọc** Clue đã mua vẫn mở (R-C-15). | Terminal là một **hàng rào ở tầng command**, phải kiểm tra **dưới lock**, không phải ở UI. Và nó **không** cắt kết nối: người đã terminal vẫn cần đọc. → **C-Q9** |
| **R-T-05** Cả hai `SOLVED` → Score cao hơn thắng; hoà Score → **Solve Time sớm hơn**; hoà cả hai → Draw. | Solve Time là **mili giây từ Match start**, do server ghi. Độ phân giải và nguồn của con số đó là quyết định của #4. → **C-Q6** |
| **R-T-06** Forfeit là hành động **chủ động, tường minh**, và là **thua** bất kể đối thủ đang ở đâu. | Forfeit là **đường thoát duy nhất**. Mọi lối ra khác phải rơi vào R-T-07. → **C-Q11** |
| **R-T-07** Mất kết nối rồi không quay lại **không phải** bỏ cuộc: đồng hồ chạy tiếp tới deadline rồi `EXPIRED`. **MUST NOT** cố phân biệt rage-quit với rớt mạng. | Đóng cứng nhánh "finalize sớm khi đối thủ chắc chắn đã bỏ đi". Người đã Solve ở phút 3 **phải** chờ tới phút 15 nếu đối thủ biến mất. Không được lách. → **C-Q8** |
| **R-T-08** Match đang chạy **MUST NOT** bị huỷ, reset hay sinh lại Puzzle bởi **bất kỳ ai** — kể cả người vận hành. | Xem A.1 mục 2. Ràng buộc này bắt đầu có hiệu lực **đúng tại mốc start**, nên định nghĩa mốc start chính là định nghĩa phạm vi của R-T-08. |
| **R-T-11** **Match kết thúc** khi **cả hai** Player terminal. Chỉ khi đó mới đánh giá R-T-05, mới lộ thông tin theo R-O-02, mới phát `puzzle_id` theo R-P-14. | Định nghĩa chính xác của "finalization". Một Player terminal sớm **không** kết thúc Match. → **C-Q8** |
| **R-P-13** Một Match có **đúng một** Puzzle, **sinh lúc tạo Match**, dùng chung cho cả hai Player. | Mốc "tạo Match" là mốc sinh Puzzle. Ghép với A.1 mục 1: mode phải cố định trước mốc này, và #2 đã chốt mode cố định **lúc tạo room**. → **C-Q1** |
| **R-P-14** Puzzle giữ server-side, lưu bền cùng Match; client nhận `puzzle_id` **mờ** và **chỉ sau khi Match kết thúc**. **R-I-02** Mã bí mật **không rời server** khi Match còn chạy, **không ghi log**, phát **một lần duy nhất** trong kết quả cuối. | Một Puzzle đã sinh mà chưa dùng **không lộ gì**. Đây là dữ kiện quyết định cho câu hỏi "cửa sổ giữa hai mốc có nguy hiểm không" ở C-Q1. |
| **R-I-01** Server **authoritative** cho toàn bộ Score, Strike, Clue, state và đồng hồ. | Không có optimistic authority ở client. Client được **render** đồng hồ, không được **quyết định** nó. |
| **R-O-01** Trong lúc Match chạy, một Player **MUST chỉ thấy** về đối thủ: **trạng thái kết nối** (online/offline) và Match Clock chung. **R-O-02** Score, số Clue, Player Board, và **việc đối thủ đã Solve hay chưa** **MUST NOT** lộ trước R-T-11. | Đọc theo nghĩa **trần quyền** (whitelist): hiện *ít hơn* là hợp lệ, hiện *nhiều hơn* thì không. Cách đọc này là **một diễn giải**, không phải điều spec nói thẳng — C-Q5 đưa nó ra hỏi chứ không tự chốt. |
| **R-K-01** Mọi Match **MUST** ghi bền `ruleset_id` mà nó được chơi dưới đó. | `ruleset_id` được đóng dấu tại mốc **tạo Match**, cùng transaction với Puzzle. → **C-Q1** |

### A.3 Từ [#8 — kiến trúc zero-cost](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8) (CLOSED)

#8 đã trả lời trước một phần lớn của #4 ở tầng **cơ chế**. Những dòng dưới đây là
**đã có**, #4 không hỏi lại — nó chỉ được xây tiếp lên.

| #8 xác lập | Ràng buộc lên #4 |
| --- | --- |
| PostgreSQL là **authority duy nhất**. Vercel API là **control point, không phải trust boundary**; mọi guardrail phải enforce lại trong PostgreSQL vì publishable key là public. | Mọi luật lifecycle của #4 phải phát biểu được như một **điều kiện kiểm tra trong transaction**, không phải như một luật ở tầng route. |
| Pipeline 10 bước cho một command: reject JWT hỏng → lookup `(actor_id, command_id)` **trước limiter** → token bucket → membership fail-fast → insert dedup row → per-Match limiter → `SELECT … FOR UPDATE` **theo cùng thứ tự user ID ở mọi code path** → kiểm lại membership/phase/terminal/lockout/`expected_version`/`deadline_at` bằng **database time** → tính toán server-side → ghi kết quả + Elo cùng transaction → tăng `version`, ghi notification row, commit. | Đây là **khung có sẵn** của #4. Việc còn lại là điền: **danh sách command**, **phạm vi của `expected_version`**, và **những precondition nào tồn tại** ở mỗi phase. → **C-Q9** |
| `commands` unique theo `(actor_id, command_id)`, lưu canonical hash của `match_id`/action/payload/`expected_version`; replay cùng hash trả **cùng result** kể cả khi bucket đã cạn; cùng ID khác hash bị **reject**. | Idempotency **đã được chốt về cơ chế**. #4 chốt **ai sinh `command_id`** và **nó sống bao lâu**. → **C-Q9** |
| `rating_settlements.match_id` **unique**; Practice Match **không có** settlement row. | Finalization idempotent là hệ quả của một unique constraint, không phải của một lock. Elo **không thể** chạy hai lần. → **C-Q8** |
| **"Không có server timer tick mỗi giây. Deadline được kiểm tra khi command/snapshot/finalization chạy."** | **Ràng buộc nặng nhất của cả ticket này.** Không có tiến trình nào đánh thức một Match. `EXPIRED` là một trạng thái **được quan sát**, không phải một sự kiện **được phát**. Nếu cả hai Player biến mất ở phút 2, **không gì** đẩy Match sang terminal. → **C-Q7** |
| `deadline_at` và `locked_until` là **server timestamps**; UI chỉ render countdown từ timestamp trả về. | Xác nhận thiết kế "suy ra thay vì tick" ở C-Q6, và đóng nhánh "client gửi timestamp". |
| `matches.version` **chỉ tăng**; stale command bị reject hoặc trả snapshot mới. | Version tồn tại rồi; #4 chốt nó là **per-Match** hay **per-Player**. → **C-Q9** |
| Realtime event **chỉ là invalidation/hint**. Mất event, event lặp, reconnect đều được sửa bằng `GET snapshot` + version. | **Reconnect handshake đã được chốt về hình dạng**: connect → snapshot → version. #4 không thiết kế lại; nó chốt **khi nào** client phải snapshot. → **C-Q5** |
| Gate #9: **JWT expiry 600 giây**. Realtime **cache quyền** tới khi client gửi JWT mới hoặc token hết hạn. Khi membership đổi, transaction **rotate một channel epoch không đoán được**; membership helper kiểm **cả membership lẫn epoch**. Client cũ phải bị disconnect/re-evaluate **trong 10 phút**. | 600 s là **đầu vào cứng**. Ghép với deadline 900 s: **mọi Match đều đi qua ít nhất một lần refresh**. → **C-Q13** |
| Gate #9 (cùng dòng): test rằng **Realtime client KHÔNG thể `INSERT`/broadcast/Presence**. | **Supabase Presence bị tắt bởi thiết kế bảo mật.** Nên "online/offline" của R-O-01 **không** lấy được miễn phí từ Realtime — nó phải mua bằng invocation hoặc suy ra từ dấu vết có sẵn. → **C-Q5** |
| Guardrail khởi điểm: **20 command/phút/actor** (burst 5), **40 command/phút/Match**, payload ≤ 8 KiB. Chỉ đổi sau local test + HITL. | Trần invocation xấu nhất của một Match do **rate limit** đặt (xem D.1), không phải luật chơi. |
| **Vercel tính MỌI invocation**, kể cả request lỗi và bot traffic. Hobby **pause** khi vượt, không có overage. | Rate limit ở tầng DB **không tiết kiệm invocation** — invocation đã xảy ra trước khi limiter chạy. Thứ duy nhất tiết kiệm được invocation là **không gọi**. Vì thế "client có polling không" là một quyết định **ngân sách**, không chỉ là một quyết định kỹ thuật. → **C-Q6** |
| Supabase Free: **200 peak connections**, 100 messages/giây, 100 channel joins/giây. Broadcast tính **1 message gửi + 1 cho mỗi subscriber** (một event tới hai player ≈ **3 units**). Internal budget: ≤ 1 triệu Realtime messages/tháng, ≤ 50 msg/s, ≤ 50% mỗi quota. | Ngân sách connection là thứ định giá chính sách multi-tab. Xem D.1. → **C-Q4** |
| Trần vận hành: canary **5 Match đồng thời**, tối đa **25** sau 7 ngày quan sát + HITL. | Mọi phép tính capacity của #4 lấy **25 Match đồng thời** làm trần, không phải 100. |
| Fail-closed: Vercel pause ⇒ **toàn bộ API ngừng**, "Match hiện tại cũng thất bại". Zero-cost stack **không bảo đảm** Match sống qua hard-stop. | Có một class sự cố mà #4 **không** thiết kế thoát ra được. #4 chỉ được chọn hành vi khi quay lại: recover bằng snapshot, và đồng hồ đã chạy suốt. → **C-Q7** |

### A.4 Từ [#10 — toàn vẹn Elo](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10) (CLOSED)

| #10 xác lập | Ràng buộc lên #4 |
| --- | --- |
| Elo zero-sum cần **một transfer duy nhất**, **atomic và idempotent**. | Finalization của #4 là nơi transfer xảy ra. Nó phải nằm **trong cùng transaction** với việc ghi kết quả (#8 bước 9), và được bảo vệ bằng unique settlement row. → **C-Q8** |
| §5.3 **Elo ordering** — thứ tự settle giữa nhiều Match ảnh hưởng rating. #2 đã **xoá bài toán này khỏi MVP** bằng cap 1 Match chưa terminal. | Cap của #2 chỉ giữ được tính chất đó nếu Match được finalize **đáng tin cậy**. Một Match treo vô hạn không chỉ khoá tài khoản — nó mở lại bài toán ordering mà #2 tưởng đã đóng. → **C-Q7** |
| §7.2 **reversal không tương đương replay**. | Không có "huỷ kết quả rồi tính lại" như một cơ chế lifecycle. Nếu finalize sai thì đó là bài toán **correction** của #15, không phải rollback của #4. |

### A.5 Từ [#2 — identity, profile và invite-room lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2) (CLOSED), ngoài sáu mục ở A.1

| #2 chốt | Ràng buộc lên #4 |
| --- | --- |
| **Cap cứng: 1 room đang mở + 1 Match chưa terminal**, hai ô **tách biệt**. | Hai bất biến phải được enforce **dưới điều kiện đua**, không phải bằng check-then-insert. → **C-Q10** |
| **Mode chốt lúc TẠO ROOM, in vào invite, BẤT BIẾN.** Người nhận thấy mode **trước khi** join. | Room **đã** mang mode trước khi Match tồn tại. Ghép với R-P-13, đây là dữ kiện làm cho phương án "Match sinh muộn" khả thi mà không vi phạm gì. → **C-Q1** |
| **Invite TTL 30 phút** = đúng **hai lần** deadline Match. Mã **single-use**, bị *giữ* khi ghế thứ hai được nhận, chỉ **chết vĩnh viễn khi Match bắt đầu**; rời trước đó ⇒ mã sống lại tới hết **TTL gốc**, không gia hạn. Mã đã chết **không bao giờ** tái dùng. | TTL 30 phút là **giới hạn tự nhiên** cho toàn bộ phase phòng chờ. #4 chỉ cần quyết định room có chết cùng lúc với mã hay không. → **C-Q3** |
| **Owner huỷ/sinh lại được CHỈ khi chưa ai vào.** | Có **ba** vùng quyền, không phải hai: (1) chưa ai vào — huỷ được; (2) đã đủ hai người, chưa start — #2 không nói; (3) đã start — R-T-08 cấm tuyệt đối. Vùng (2) là của #4. → **C-Q3** |
| **Rematch = Match record MỚI với Puzzle MỚI, trong cùng room**, cần **cả hai** đồng ý; mã đã tiêu **không** sống lại; cap chỉ áp cho room Ranked (khởi điểm 5). | Room **sống lâu hơn** một Match. Đây là bằng chứng mạnh nhất rằng Room và Match là **hai thực thể**, không phải một. → **C-Q1**, **C-Q12** |
| **Quy tắc thông điệp lỗi:** thông điệp giàu thông tin **chỉ** trả sau khi đã xác thực. | Áp cho mọi lỗi lifecycle của #4: reconnect vào Match không thuộc về mình, join room đã đầy, command sau terminal. |
| **Zero email ngoài auth.** Không có kênh nào chủ động chạm tới người được mời; không báo được "đối thủ đã vào room" khi người dùng ở tab khác. | Mọi tín hiệu lifecycle là **in-app**. Người dùng đóng tab thì không nhận được gì. Đây là lý do phase phòng chờ cần một TTL rõ ràng thay vì chờ vô hạn. → **C-Q3** |

### A.6 Từ [#25 — mô hình đối thủ của Ranked Match](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25) (OPEN, frontier)

#25 **chưa được chốt** và #4 **không** được giả định kết quả của nó. Nhưng #25
ràng buộc #4 theo hai chiều, và cả hai đều cần đọc trước khi chốt bất cứ thứ gì
dính Ranked:

- **#25 có thể vẽ lại destination của map.** Nhánh (4) — đối thủ máy — mâu thuẫn
  với định nghĩa Match trong `CONTEXT.md` ("đúng hai Player", Player là "người đã
  xác thực"). Nếu người chủ map chọn nhánh đó thì một phần lifecycle của #4 bị vô
  hiệu (không còn phòng chờ hai người, không còn ready hai chiều). ⇒ **#4 nên
  chốt lifecycle theo mô hình hai người thật**, và ghi rõ phần nào sẽ phải viết
  lại nếu #25 đi nhánh (4). Không chờ #25.
- **#25 dữ kiện 3**: chia sẻ Clue giữa hai account **không** cho thêm Elo, vì
  `K=32` không xét margin. Nên #4 **không** được biện minh cho bất kỳ luật
  lifecycle nào bằng lý do "chống chia sẻ Clue" — luật đó sẽ đắt mà không mua
  được gì.

### A.7 Từ `CONTEXT.md` (19 thuật ngữ, gốc repo)

| Thuật ngữ đã có | Ràng buộc lên #4 |
| --- | --- |
| **Match**: "A **real-time** head-to-head contest in which **exactly two** Players **independently** solve the **same** Puzzle". _Avoid_: Game, **room**, session. | `CONTEXT.md` **cấm** dùng "room" như từ đồng nghĩa của Match. Nhưng nó **chưa định nghĩa** Room như một thuật ngữ riêng — nên hiện tại repo có một từ bị cấm mà không có từ thay thế. #4 phải sửa việc này. |
| **Match Clock**: "running from **Match start**… **It never pauses**." | `CONTEXT.md` cũng dùng "Match start" mà không định nghĩa. Cùng lỗ hổng với ruleset. |
| **Player State**: "The **private**, evolving board, clues, score, and guesses belonging to **one** Player in a Match." | Đơn vị của `version`/snapshot có thể là Player State chứ không nhất thiết là Match. → **C-Q9** |
| **Forfeit**: "A Player's **explicit** surrender." | Xác nhận: không có lối thoát ngầm. |

**Từ vựng #2 để lại cần thêm** (chưa làm được ở phiên #2 vì bản `CONTEXT.md`
đích còn nằm trong PR chưa merge — nay đã merge, chỉ còn **một** bản):
**Room**, **Invite Code**, **Room Owner**, **Rematch**, **Player Tag**.

**#4 sẽ sinh thêm** ứng viên: **Match Start**, **Match Creation**, **Seat**,
**Session** (hoặc **Connection**), **Finalization**, **Command**. → **C-Q1** và
**C-Q9** quyết định từ nào thật sự cần vào glossary.

### A.8 Từ Out of scope của map

- **Public matchmaking, spectator, chat** — không có đường vào Match nào ngoài
  invite. #4 không thiết kế hàng đợi.
- **Full replay, admin dashboard** — **không có công cụ vận hành** để sửa một
  Match hỏng bằng tay. Ghép với R-T-08 (kể cả người vận hành cũng không được can
  thiệp): mọi ca biên lifecycle phải **tự thoát được**, vì không ai đến cứu.
- **Rating decay, season, leaderboard** — Elo chỉ được đọc ở lịch sử cá nhân,
  nên một Match finalize muộn **không** làm sai bảng xếp hạng nào. Đây là lý do
  "finalize muộn" có thể chấp nhận được ở MVP, và cần nói rõ ra khi chốt C-Q7.

---

## B. Design tree của #4

Nhánh có dấu ✱ là nhánh **đã bị đóng** bởi ràng buộc ở phần A — ghi kèm lý do để
thấy vì sao không hỏi.

```text
#4 Match lifecycle, reconnect, concurrency
│
├── B1  TOPOLOGY — Room và Match là gì với nhau
│   ├── B1.1  Một record hay hai record riêng                        → C-Q1
│   │         ├─ Một: room CHÍNH LÀ match row
│   │         └─ Hai: Room sống lâu hơn Match (#2 rematch ép hướng này)
│   ├── B1.2  Mốc "tạo Match" = mốc sinh Puzzle (R-P-13)             → C-Q1
│   ├── B1.3  Mốc "Match bắt đầu" = t=0 của Clock, mã chết,
│   │         R-T-08 bắt đầu có hiệu lực                             → C-Q1
│   ├── B1.4  Hai mốc trùng nhau hay lệch nhau                       → C-Q1
│   └── B1.5  ✱ Owner huỷ Match đang chạy — R-T-08 cấm tuyệt đối
│
├── B2  PHASE PHÒNG CHỜ (sau join, trước start)
│   ├── B2.1  Có ready-up không; một chiều hay hai chiều             → C-Q2
│   ├── B2.2  Có countdown không, dài bao nhiêu, huỷ được không      → C-Q2
│   ├── B2.3  Room sống bao lâu nếu không ai start                   → C-Q3
│   ├── B2.4  Mất kết nối ở phòng chờ ≠ rời phòng chờ?               → C-Q3
│   ├── B2.5  Owner huỷ khi đã đủ hai người, chưa start              → C-Q3
│   └── B2.6  ✱ Chốt mode ở ready-up — #2 Q8 đã đóng: mode chốt lúc tạo room
│
├── B3  GHẾ, KẾT NỐI, PRESENCE
│   ├── B3.1  ✱ Ghế gắn với player_id — #2 Q9.2 đã đóng
│   ├── B3.2  Nhiều tab / nhiều thiết bị: takeover, cùng tồn tại,
│   │         hay từ chối                                            → C-Q4
│   ├── B3.3  Reconnect handshake                                    → C-Q5
│   ├── B3.4  "online/offline" của đối thủ tính bằng gì, giá bao nhiêu → C-Q5
│   └── B3.5  ✱ Disconnect grace period — R-S-03/04 + R-T-07 đã đóng
│
├── B4  ĐỒNG HỒ, HAO MÒN, DEADLINE
│   ├── B4.1  Nguồn thời gian và nơi deadline được đánh giá          → C-Q6
│   ├── B4.2  Score/lockout: lưu hay suy ra                          → C-Q6
│   ├── B4.3  Độ phân giải Solve Time và luật phá hoà                → C-Q6
│   ├── B4.4  Client có polling định kỳ không (ngân sách invocation) → C-Q6
│   └── B4.5  ✱ Pause / dừng đồng hồ — R-S-03/R-S-04 đã đóng
│
├── B5  TERMINAL VÀ FINALIZATION
│   ├── B5.1  Ai đẩy một Match bị bỏ rơi sang EXPIRED, trong bao lâu → C-Q7
│   ├── B5.2  Ràng buộc "quan sát được trong X" là bao nhiêu         → C-Q7
│   ├── B5.3  Finalization: trigger, atomicity, idempotency          → C-Q8
│   ├── B5.4  Hệ quả của finalize muộn lên cap của #2                → C-Q7
│   └── B5.5  ✱ Finalize sớm khi đối thủ "chắc chắn đã bỏ đi" —
│             R-T-07 cấm phân biệt rage-quit với rớt mạng
│
├── B6  COMMAND SEMANTICS
│   ├── B6.1  Danh sách command đầy đủ, và phase nào cho phép gì     → C-Q9
│   ├── B6.2  Ai sinh command_id, sống bao lâu, dedup theo gì        → C-Q9
│   ├── B6.3  expected_version: per-Match hay per-Player State       → C-Q9
│   ├── B6.4  Command không đổi state (R-V-05, R-C-13) có tăng version? → C-Q9
│   └── B6.5  ✱ Con số rate limit — #12
│
├── B7  CONCURRENCY
│   ├── B7.1  Enforce cap 1 room + 1 Match dưới điều kiện đua        → C-Q10
│   ├── B7.2  Đua ghế cuối cùng khi hai người cùng nhập mã           → C-Q10
│   ├── B7.3  Đua start: cả hai bấm Ready cùng lúc                   → C-Q10
│   ├── B7.4  Đua VERIFY đồng thời của hai Player                    → C-Q10
│   └── B7.5  ✱ Thứ tự lock theo user ID — #8 đã chốt
│
├── B8  ĐƯỜNG RA
│   ├── B8.1  Có nút "rời trận" sau start không                      → C-Q11
│   ├── B8.2  Forfeit: xác nhận, idempotent, khả dụng ở phase nào    → C-Q11
│   ├── B8.3  Đóng room ở phase nào thì còn hợp lệ                   → C-Q11
│   └── B8.4  ✱ Forfeit là thua — R-T-06 đã đóng
│
├── B9  REMATCH LIFECYCLE
│   ├── B9.1  Ai đề nghị, đề nghị sống bao lâu, huỷ được không       → C-Q12
│   ├── B9.2  Room ở trạng thái gì giữa hai Match                    → C-Q12
│   ├── B9.3  Rematch có đi lại phase ready/countdown không          → C-Q12
│   └── B9.4  ✱ Cần cả hai đồng ý, Puzzle mới, cap 5 cho Ranked — #2 Q11
│
└── B10 SESSION VÀ MULTI-DEVICE
    ├── B10.1  Refresh-token policy, rotation, reuse detection       → C-Q13
    ├── B10.2  Token hết hạn giữa Match (600 s < 900 s)              → C-Q13
    ├── B10.3  "Đăng xuất mọi thiết bị" nghĩa là gì, trong bao lâu   → C-Q14
    ├── B10.4  Revoke membership → rotate channel epoch: khi nào xảy ra → C-Q14
    └── B10.5  ✱ JWT expiry 600 s — gate #9 của #8, đầu vào cứng
```

**Thứ tự phụ thuộc trong round-1.** Q1 (topology + hai mốc) chi phối **gần như
tất cả**: Q2, Q3, Q6, Q7, Q8, Q11, Q12. Q4 (multi-tab) chi phối Q5 (presence) và
Q14 (đăng xuất mọi thiết bị). Q6 (đồng hồ) chi phối Q7 (EXPIRED) và Q8
(finalization). Q9 (command) chi phối Q10 (concurrency). Vì thế round-1 đi theo
đúng thứ tự **Q1 → Q14**.

---

## C. Câu hỏi grilling round-1

Mỗi câu: **câu hỏi** → **khuyến nghị** → **vì sao** → **ai tiêu thụ câu trả lời**.

Người dùng đã yêu cầu **hỏi từng câu một** và chờ trả lời rồi mới sang câu tiếp.
Danh sách này là bản in sẵn để đọc trước, **không** phải để trả lời hàng loạt.

Tôi **không** trả lời câu nào trong số này.

---

### Q1 — Room và Match là một record hay hai? Và chính xác lúc nào Match được "tạo", lúc nào Match "bắt đầu"?

Ruleset dùng "tạo Match" (R-P-13, sinh Puzzle) và "Match bắt đầu" (R-S-02 đồng hồ
chạy; R-T-01 vào `ACTIVE`) mà **không định nghĩa cả hai**. #2 lại treo hai quyết
định lên chúng: mã invite **chết vĩnh viễn khi Match bắt đầu**, và mode phải cố
định **trước khi Puzzle sinh**. Ba phương án:

- **(a) Một record.** Room *là* Match row. Puzzle sinh lúc tạo room. "Bắt đầu" là
  một lần đổi cột `started_at`.
- **(b) Hai record, Match sinh MUỘN.** Room là thực thể riêng, mang mode và mã.
  Match row + Puzzle + `ruleset_id` được **INSERT trong đúng transaction làm
  Match bắt đầu**. Hai mốc **trùng nhau tuyệt đối**.
- **(c) Hai record, Match sinh SỚM.** Match row tạo lúc ghế thứ hai được nhận;
  "bắt đầu" muộn hơn (sau ready). Hai mốc **lệch nhau**.

➡️ **Khuyến nghị: (b).**

**Vì sao.** Ba lý do độc lập.

1. **Nó xoá cửa sổ mà #2 cảnh báo, thay vì quản lý cửa sổ đó.** Ở (b), "tạo
   Match" và "Match bắt đầu" là **cùng một transaction**, nên không tồn tại
   khoảnh khắc nào mã còn sống mà Puzzle đã sinh. Ở (a) và (c) cửa sổ đó có thật
   và phải được lý luận về độ an toàn ở mọi ticket sau. Cần nói thẳng: cửa sổ ấy
   **có lẽ vô hại** — R-P-14 và R-I-02 giữ Puzzle server-side và mã bí mật không
   rời server, nên một Puzzle chưa dùng không lộ gì. Nhưng "vô hại" là một lập
   luận phải **bảo trì**; "không tồn tại" thì không.
2. **#2 đã ép hướng này rồi mà chưa gọi tên.** Rematch là "Match record MỚI với
   Puzzle MỚI, trong **cùng room**" — nghĩa là **một Room ứng với N Match**. Đó
   là quan hệ 1-N, và (a) không biểu diễn được nó. Cap của #2 cũng đếm hai ô
   **tách biệt** ("1 room đang mở" và "1 Match chưa terminal") — hai ô tách biệt
   thì cần hai bảng để đếm.
3. **Nó làm R-T-08 có một ranh giới sắc.** "Match đang chạy MUST NOT bị huỷ" trở
   thành "**Match row tồn tại ⇒ không ai được xoá nó**". Không cần phân biệt
   trạng thái trong cùng một bảng, không cần một cột `phase` mà một bug có thể
   đọc sai. Đây chính là chỗ #2 gọi là "dễ vi phạm spec nhất", và (b) biến nó từ
   một luật cần nhớ thành một luật do schema giữ.

**Đánh đổi phải nói ra.** (b) cần **hai** bảng và một transaction start làm nhiều
việc (INSERT Match, sinh Puzzle, đóng dấu `ruleset_id`, giết mã, khoá cap). Đó là
transaction phức tạp nhất của hệ thống, và nó chạy **đúng một lần** mỗi Match.
Ngược lại (a) đơn giản hơn về schema nhưng dời độ phức tạp sang **mọi truy vấn
khác**, vì mỗi truy vấn phải hỏi "row này đang ở phase nào".

**Ai tiêu thụ:** #14 (schema — đây là quyết định đầu vào lớn nhất), #12 (bề mặt
tấn công của phase), #13 (số màn hình), #3 (transaction boundary), `CONTEXT.md`.

---

### Q2 — Có phase ready-up không? Một chiều hay hai chiều? Có countdown không?

#2 đã bỏ ready-up khỏi việc **chọn mode** (mode chốt lúc tạo room). Câu còn lại
là ready-up có tồn tại vì **lý do khác** không. Ba phương án: (a) không có —
Match bắt đầu ngay khi ghế thứ hai được nhận; (b) **ready hai chiều** — cả hai
bấm sẵn sàng, người bấm sau kích hoạt start; (c) ready một chiều — owner bấm bắt
đầu.

➡️ **Khuyến nghị: (b), ready hai chiều, và countdown ngắn 3 giây không huỷ được.**

**Vì sao.** Sau mốc start, R-T-08 khoá cứng và R-T-06 nói **đường ra duy nhất là
Forfeit — một trận thua**. Ở room Ranked, đó là Elo thật. Bắt đầu một trận đấu có
hậu quả không thể rút lại mà **không hỏi** người vừa mới bấm vào một link là sai
về mặt đồng thuận. #2 đã dùng đúng lập luận này cho rematch ("owner không được
lôi người kia vào một trận ảnh hưởng Elo lần nữa mà không hỏi") — nếu rematch cần
hai chiều thì Match đầu tiên cũng vậy. (c) tái tạo đúng vấn đề mà #2 đã bác.

Countdown 3 giây **không** phải để đổi ý — nó để hai client kịp đồng bộ trước khi
đồng hồ chạy, vì R-S-04 nói đồng hồ **không dừng** dù ai chưa sẵn sàng. Cho huỷ
countdown thì tạo ra một trạng thái đua ngay sát mốc quan trọng nhất của hệ thống
mà không mua được gì.

**Ai tiêu thụ:** #13 (màn phòng chờ và countdown), #12 (phase nào nhận command
gì), #14.

---

### Q3 — Phòng chờ sống bao lâu, và mất kết nối ở phòng chờ có phải là rời đi không?

#2 chốt ca **rời tường minh** trước start (ghế mở lại, mã sống lại tới hết TTL
gốc). Còn ba lỗ: (i) **mất kết nối** ở phòng chờ có được coi là rời đi không;
(ii) room sống bao lâu nếu **không ai** bấm ready; (iii) owner có được đóng room
khi **đã đủ hai người nhưng chưa start** không — #2 chỉ cho huỷ "khi **chưa ai**
vào".

➡️ **Khuyến nghị:**
**(i) Không.** Mất kết nối ở phòng chờ **không** nhả ghế; chỉ hành động **rời
tường minh** mới nhả. **(ii)** Room hết hạn cùng lúc với mã: **30 phút kể từ lúc
tạo room**, không gia hạn; hết hạn mà chưa start thì room tự đóng và nhả ô cap.
**(iii) Có** — owner được đóng room ở vùng "đã đủ hai người, chưa start", và việc
đó **không** phải huỷ Match vì chưa có Match nào tồn tại (theo Q1(b)).

**Vì sao.** (i) là **cùng một lập luận với R-T-07, áp sớm hơn một phase**: không
phân biệt được rớt mạng với bỏ đi, nên đừng cố phân biệt. Nếu mất kết nối tự nhả
ghế thì một người đi tàu điện ngầm mất chỗ, còn mã thì đã bị *giữ* nên bạn của họ
không vào thay được — kết quả tệ hơn hẳn việc chờ.

(ii) chọn 30 phút vì đó là **con số duy nhất đã có**, và #2 đã dựng cả bảng
entropy quanh nó ("TTL chính là mẫu số `L`"). Thêm một hằng số thứ hai cho room
là thêm một thứ phải giải thích mà không mua được gì. Và nó có ràng buộc thật:
**zero email** (#2 Q12) nghĩa là không có cách nào gọi người được mời quay lại —
nên chờ vô hạn chỉ tạo ra room ma giữ ô cap của owner.

(iii) là hệ quả sạch của Q1(b): trước mốc start **không có Match**, nên R-T-08
chưa có gì để bảo vệ. Đây đúng là "chỗ dễ vi phạm spec nhất" mà #2 chỉ ra, và
cách an toàn nhất để không vi phạm là làm cho ranh giới trùng khít với ranh giới
tồn tại của một hàng trong bảng.

**Ai tiêu thụ:** #13, #14, #12.

---

### Q4 — Cùng một `player_id` mở nhiều tab hoặc nhiều thiết bị thì sao?

#2 Q9.2 đã cấm cứng **hai ghế** cho cùng `player_id`. Còn lại là **một ghế, nhiều
client**. Ba phương án: (a) **takeover cứng** — kết nối mới đá kết nối cũ ra, tab
cũ thành chỉ-đọc; (b) **cùng tồn tại** — mọi tab đều gửi command được, server là
trọng tài; (c) **từ chối** — kết nối thứ hai bị chặn.

➡️ **Khuyến nghị: (b), cùng tồn tại — nhưng client mới nhất được đánh dấu "đang
điều khiển" ở UI, thuần trang trí.**

**Vì sao.** Ba dữ kiện.

1. **Tính đúng đắn đã được mua ở chỗ khác rồi.** Server authoritative (R-I-01),
   idempotency theo `(actor_id, command_id)`, `version` đơn điệu tăng, và mọi
   precondition kiểm dưới lock (#8). Hai tab của cùng một người **không** tạo ra
   một lớp lỗi mới — chúng chỉ là hai client của một actor. Takeover cứng lại
   **thêm** state phải đồng bộ và một chế độ hỏng mới ("tab nào đang sống").
2. **Ngân sách connection chịu được.** Trần vận hành là 25 Match đồng thời = 50
   socket; Supabase Free cho **200**. Dư 150, tức **trung bình 3 tab phụ mỗi
   người chơi** trước khi chạm trần (xem D.1).
3. **Rủi ro thật thì nhỏ và tự chịu.** Ca xấu nhất là hai tab cùng bấm Verify với
   hai bàn cờ khác nhau → hai Strike → `ELIMINATED`. Đó là hành vi của chính
   người chơi, không phải lỗ hổng, và R-V-08 đã có khoá 10 giây giữa hai Strike
   nên nó không xảy ra do tai nạn double-click.

**Đánh đổi.** Người dùng có thể tự làm mình rối khi hai tab hiển thị lệch nhau.
Chỉ báo "đang điều khiển" ở UI là cách rẻ nhất giảm chuyện đó mà không đưa thêm
một cơ chế server nào.

**Ai tiêu thụ:** #12 (session theft, một tab bị chiếm), #13 (chỉ báo), #3
(connection budget).

---

### Q5 — Reconnect handshake, và "online/offline" của đối thủ lấy ở đâu?

**Reconnect gần như đã được chốt** ở #8: mọi khôi phục đi qua `GET snapshot` +
`version`; Realtime event chỉ là gợi ý invalidation. Câu thật nằm ở nửa sau.
R-O-01 cho phép Player thấy **trạng thái kết nối** của đối thủ, nhưng gate #9 của
#8 **cấm client dùng Presence** của Supabase. Nên online/offline **không** lấy
được miễn phí. Bốn phương án:

- **(a) Không hiển thị gì** về kết nối của đối thủ. Đọc R-O-01 như một **trần
  quyền** (được thấy *tối đa* chừng đó), không phải một nghĩa vụ.
- **(b) "Hoạt động gần đây"** suy ra **miễn phí** từ timestamp command/snapshot
  gần nhất — và **gọi đúng tên nó** ở UI, không gọi là online.
- **(c) Presence thật** bằng heartbeat RPC theo chu kỳ, trả bằng invocation.
- **(d) Xin nới gate #9** để bật Presence dạng khoá chặt.

➡️ **Khuyến nghị: (b).**

**Vì sao.** Giá của (c) là con số đáng nhìn thẳng. Toàn bộ **lối chơi** của một
Match tốn khoảng **44 invocation** (2 người × ~22 command, xem D.1). Heartbeat
5 giây tốn **360**/Match — gấp **8,2 lần** toàn bộ phần còn lại, chỉ để vẽ một
chấm màu. Ngay ở chu kỳ 30 giây nó vẫn tốn 60/Match, tức **1,4 lần**. Trên Hobby,
vượt quota là **deployment pause**, không phải hoá đơn — nên đây là ngân sách
thật, không phải tối ưu sớm.

(d) đắt hơn nhiều so với vẻ ngoài: #8 nói rõ gate trượt thì **quay lại HITL**,
nên nó mở lại một quyết định kiến trúc đã đóng để đổi lấy một chỉ báo UI.

(a) hợp lệ về mặt luật nhưng tệ về mặt sản phẩm, vì R-T-07 tạo ra đúng cái tình
huống người chơi cần biết nhất: đối thủ đã biến mất và bạn phải ngồi tới phút 15.

(b) miễn phí, trung thực, và **đúng chính xác** thứ hệ thống thật sự biết. Nó
cũng tránh một lời hứa sai: với kiến trúc không tick, "online" **không** phải thứ
server quan sát được — nó chỉ suy ra được.

**Cần chỉ ra một chỗ khó chịu của (b):** người chơi ngồi suy nghĩ 3 phút không
gửi command nào sẽ hiện là "không hoạt động" dù họ đang chăm chú. Nhãn phải chịu
được điều đó — đó là lý do phải gọi là "hoạt động gần đây" chứ không phải
"offline".

**Ai tiêu thụ:** #13 (nhãn và ngưỡng), #3 (realtime topology), #12, #14.

---

### Q6 — Đồng hồ: nguồn thời gian ở đâu, deadline đánh giá ở đâu, Score lưu hay suy ra?

R-S-02 nói **một** đồng hồ wall-clock; #8 nói **không có server tick** và
`deadline_at`/`locked_until` là server timestamp. Còn ba chỗ hở: (i) deadline
được đánh giá bằng **đồng hồ nào** — thời điểm request tới Vercel, hay
`clock_timestamp()` của PostgreSQL lúc lấy lock; (ii) Score/Strike-lockout được
**lưu** rồi cập nhật, hay **suy ra** từ `started_at`; (iii) client có **poll**
định kỳ không.

➡️ **Khuyến nghị:**
**(i)** `clock_timestamp()` của PostgreSQL **lúc lấy lock**, một nguồn duy nhất.
**(ii)** Score = **suy ra**: `100 − 5×(số Clue) − 10×(số Strike) − ⌊t/60⌋`, chặn
sàn 0, với `t = min(now, thời điểm Player đó vào terminal) − started_at`; đóng
băng thành giá trị lưu **đúng một lần** khi Player vào terminal (R-S-05 gọi đó là
"bản ghi"). `locked_until` cũng là timestamp, không phải bộ đếm.
**(iii)** **Không polling định kỳ.** Client tự vẽ đồng hồ từ `started_at` và
`deadline_at` server trả về; chỉ gọi server khi: gửi command, nhận Realtime hint,
reconnect, và **đúng một lần** tại deadline.

**Vì sao.** (i): hai đồng hồ nghĩa là hai câu trả lời cho "trận đã hết chưa", và
R-T-05 phân định thắng thua bằng **Solve Time tới mili giây**. Đánh đổi có thật:
một request chậm có thể lỡ deadline dù người chơi bấm kịp. Chấp nhận nó, vì lựa
chọn còn lại là tin timestamp do client hoặc edge cung cấp — mà #8 đã cấm.

(ii) là cách **duy nhất** thoả mãn "không có server tick" mà vẫn đúng R-S-05.
Nếu Score được lưu và cập nhật, phải có ai đó chạy trừ dần mỗi 60 giây; không có
ai cả. Suy ra cũng làm hao mòn **tự dừng** ở terminal, đúng nguyên văn R-S-05, mà
không cần một hành động dừng.

(iii) là quyết định **ngân sách**, không phải kỹ thuật: mọi invocation đều tính,
kể cả request lỗi. Poll 5 giây trong 15 phút = 180 lần/người, gấp bốn lần toàn bộ
lối chơi. Đồng hồ là thứ client tính được **hoàn toàn chính xác** từ hai
timestamp — không có lý do nào để hỏi lại server.

**Hệ quả cần chốt cùng:** vì client vẽ đồng hồ cục bộ, đồng hồ máy người dùng
lệch sẽ hiện sai. Khuyến nghị: lấy độ lệch **một lần** lúc vào Match (so
`started_at` với thời điểm nhận) rồi bù, thay vì tin đồng hồ máy.

**Ai tiêu thụ:** #3 (timer model — #4 chốt ngữ nghĩa, #3 chốt cơ chế), #14, #13,
#12.

---

### Q7 — Cả hai Player biến mất ở phút 2. Ai đẩy Match sang `EXPIRED`, và trong bao lâu?

**Đây là câu khó nhất của ticket.** #8 chốt "không có server timer tick; deadline
được kiểm khi command/snapshot/finalization chạy". Nghĩa là `EXPIRED` là trạng
thái **được quan sát**, không phải sự kiện **được phát**. Nếu không ai đọc, Match
nằm nguyên `ACTIVE` **vô thời hạn** — và cap "1 Match chưa terminal" của #2 khoá
**cả hai** tài khoản. Bốn phương án:

- **(a) Lười thuần tuý + tự chữa.** Không có tiến trình nền. Nhưng **chính đường
  admission tự dọn**: trước khi kiểm cap, transaction finalize mọi Match quá hạn
  của actor đó. Người quay lại chơi tiếp **tự mở khoá cho chính mình**.
- **(b) Quét theo lịch trong PostgreSQL** (`pg_cron` hoặc tương đương) mỗi vài
  phút.
- **(c) Quét bằng Vercel Cron.**
- **(d) Bỏ cap của #2** để bài toán biến mất.

➡️ **Khuyến nghị: (a) làm nền, và ghi (b) như một cải tiến CÓ ĐIỀU KIỆN — điều
kiện là ai đó xác minh được `pg_cron` chạy zero-cost trên Supabase Free.**

**Vì sao (a) là nền.** Nó **không thêm một phụ thuộc hạ tầng nào**, và nó chữa
đúng người bị đau: tài khoản bị khoá chỉ khoá cho tới lần tiếp theo chủ nó muốn
chơi — và chính lần đó mở khoá. Ai không quay lại thì không bị ảnh hưởng bởi ô
cap của mình. Bốn dữ kiện làm cho "finalize muộn" chịu được ở MVP: leaderboard và
rating decay **out of scope** (không bảng xếp hạng nào sai); #2 cap **1 Match**
nên không có bài toán Elo ordering (#10 §5.3) để hỏng; settlement idempotent theo
unique `match_id` nên finalize lúc nào cũng ra cùng kết quả; và Elo chỉ đọc ở
lịch sử cá nhân.

**Vì sao (b) chỉ là "có điều kiện".** Tôi **đã tra và không tìm thấy**: nghiên
cứu #8 — tài liệu zero-cost duy nhất của repo — **không hề nhắc tới** cron,
scheduled job hay `pg_cron` ở bất kỳ đâu (đã grep toàn bộ `docs/research/` và
`docs/plans/`). Vercel Hobby cũng có giới hạn riêng về cron mà #8 không khảo sát.
Vì thế: đề xuất (b) như một sự thật là **thừa kế một tiền đề không có nguồn** —
đúng cái bẫy đã xuất hiện ba lần trên map này. Nếu người dùng muốn (b) làm nền,
việc đúng là **mở một ticket research** trước, không phải chốt bừa.

**(d) thì bác.** Cap của #2 mua ba thứ (fail-closed trước quota vendor, xoá Elo
ordering, và giữ R-S-02 khỏi thành bẫy khi chơi hai trận song song). Bỏ nó để
tránh một ca biên là đổi ngược.

**Câu hỏi con phải chốt cùng:** ràng buộc quan sát được. Khuyến nghị: **"một Match
quá deadline MUST được finalize trước khi bất kỳ Player nào của nó bắt đầu Match
tiếp theo"** — một ràng buộc **nhân quả**, kiểm chứng được bằng test, thay vì một
ràng buộc thời gian ("trong vòng 5 phút") mà kiến trúc không tick **không thể**
hứa.

**Ai tiêu thụ:** #14 (schema + sweep), #15 (khi nào Elo settle), #3 (timer/job
model), #12, #17.

---

### Q8 — Finalization: ai kích hoạt, và chuyện gì xảy ra nếu hai bên cùng kích hoạt?

R-T-11: Match kết thúc khi **cả hai** terminal — chỉ khi đó mới đánh giá R-T-05,
mới lộ R-O-02, mới phát `puzzle_id` (R-P-14). Câu: finalization là một **bước
riêng** hay **hệ quả** của transaction làm Player thứ hai terminal? Và nó gồm
những gì?

➡️ **Khuyến nghị: finalization là một hệ quả TRONG CÙNG transaction làm Player
thứ hai vào terminal, không phải một bước riêng.** Cùng transaction đó: tính
outcome (R-T-05), ghi kết quả bền, INSERT settlement row Elo nếu Ranked, tăng
`version`, ghi notification row. Bảo vệ bằng **unique `rating_settlements.match_id`**
(đã có ở #8). Kích hoạt từ **ba** đường và cả ba đi vào **cùng một hàm**: command
của Player, snapshot đọc thấy đã quá deadline, và bước tự chữa ở admission (Q7).

**Vì sao.** Tách finalization thành bước riêng tạo ra một cửa sổ mà Match "đã
xong nhưng chưa chốt" — và R-O-02 dựa vào R-T-11 để quyết định **khi nào được lộ
mã bí mật**. Một cửa sổ như thế là chỗ để rò rỉ. Gộp vào một transaction thì
"Match kết thúc" và "kết quả tồn tại" là **cùng một sự kiện**, đúng nguyên văn
R-T-11.

Ba đường kích hoạt cùng một hàm là điều kiện để (a) của Q7 an toàn: dù ai chạm
vào trước, kết quả giống hệt nhau, vì nó là hàm thuần của `started_at`, các
command đã ghi, và `clock_timestamp()`.

**Ca biên cần chốt trong câu này:** hai Player cùng Verify đúng trong vài mili
giây. Cả hai transaction đều thấy "cả hai terminal". Khuyến nghị: thứ tự lock cố
định theo user ID (#8 đã chốt) làm chúng nối tiếp; transaction sau thấy settlement
row đã tồn tại và **trả lại kết quả đã có** thay vì tính lại. Đây chính là gate #8
mục 8 ("concurrent VERIFY, deadline race, duplicate finalization") — #4 chỉ đặt
ngữ nghĩa cho nó.

**Ai tiêu thụ:** #15 (settle Elo), #14, #12, #3.

---

### Q9 — Danh sách command đầy đủ, và `expected_version` là của Match hay của Player State?

#8 đã dựng pipeline nhưng để trống ba ô: **command nào tồn tại**, **ai sinh
`command_id`**, và **`version` thuộc về ai**.

➡️ **Khuyến nghị.**
Danh sách command **đóng** (allowlist, R-I-04 bắt whitelist chính xác):
`CREATE_ROOM`, `CLOSE_ROOM`, `JOIN_ROOM`, `LEAVE_ROOM`, `READY`, `UNREADY`,
`BUY_CLUE`, `VERIFY`, `FORFEIT`, `PROPOSE_REMATCH`, `ACCEPT_REMATCH`. Đọc đi qua
`GET_SNAPSHOT`, **không** phải command. **Không** có `START_MATCH` — start là
**hệ quả** của `READY` thứ hai (Q2), không phải một lệnh gọi được.
`command_id` do **client sinh** (UUIDv4), một id cho mỗi **ý định** của người
dùng, giữ nguyên qua mọi lần retry, sống bằng đời của Match.
`version` là **per-Player State**, không phải per-Match.

**Vì sao `version` per-Player State.** Player State theo `CONTEXT.md` là "the
**private**, evolving board, clues, score, and guesses belonging to **one**
Player". Hành động của đối thủ **không thể** làm command của bạn thành không hợp
lệ — R-O-02 còn cấm bạn biết chúng. Nếu `version` là per-Match thì mỗi lần đối
thủ mua Clue, `expected_version` của bạn thành cũ và command hợp lệ bị từ chối
oan; client sẽ phải re-snapshot liên tục, tức **đốt invocation vì một xung đột
không có thật**. Per-Player State thì `expected_version` chỉ bắt đúng thứ nó nên
bắt: hai tab của **chính bạn** dẫm lên nhau (Q4).

Match vẫn giữ `version` **riêng** cho invalidation ở tầng Realtime (#8 đã có) —
hai con số cho hai mục đích khác nhau, và cần gọi tên khác nhau để không lẫn.

**Vì sao không có `START_MATCH`.** Một lệnh start gọi được là một bề mặt để đua và
để gọi hai lần; start như một hệ quả của `READY` thứ hai thì bị serialize sẵn bởi
lock trên room.

**Ca biên phải chốt cùng:** command **hợp lệ nhưng không đổi state** — Verify
trên bàn cờ không giải mã được (R-V-05) và mua lại Clue đã có (R-C-13), cả hai
"từ chối tường minh và miễn phí". Khuyến nghị: **không** tăng `version`, **không**
ghi notification row, nhưng **có** ghi dedup row để retry trả về cùng câu trả lời.
Tăng version cho một no-op sẽ bắt cả hai client re-snapshot mà không có gì mới.

**Ai tiêu thụ:** #14 (bảng `commands`), #12 (bề mặt tấn công), #3, #13.

---

### Q10 — Bốn điều kiện đua. Enforce bằng constraint hay bằng kiểm-rồi-ghi?

Bốn ca: (i) hai tab cùng bấm tạo room → hai room, vỡ cap của #2; (ii) hai người
cùng nhập một mã cho **ghế cuối**; (iii) cả hai bấm `READY` cùng lúc → hai Match;
(iv) hai `PROPOSE_REMATCH`/`ACCEPT_REMATCH` cùng lúc → hai Match trong một room.

➡️ **Khuyến nghị: mỗi bất biến được giữ bởi một CONSTRAINT của cơ sở dữ liệu,
không phải bởi một đoạn logic.**

- (i) **partial unique index** trên `(owner_id)` với điều kiện room đang mở; và
  trên `(player_id)` với điều kiện Match chưa terminal. Vi phạm cap thành một lỗi
  unique, không phải một nhánh `if` ai đó quên.
- (ii) `SELECT … FOR UPDATE` trên **room row** trước khi nhận ghế; người thua trả
  lỗi "người thứ ba" của #2 Q9.3.
- (iii) và (iv) cùng khuôn: **partial unique index trên `(room_id)` với điều kiện
  Match chưa terminal**, cộng lock room row. Transaction thứ hai thấy Match đã
  tồn tại và trả **cùng** Match đó — thành công idempotent, không phải lỗi.

**Vì sao.** #8 nói thẳng Vercel API là control point **chứ không phải trust
boundary**: publishable key là public nên có người gọi thẳng Data API, bỏ qua mọi
kiểm tra ở route. Bất biến chỉ sống nếu PostgreSQL **không thể** biểu diễn trạng
thái vi phạm. Kiểm-rồi-ghi dưới `READ COMMITTED` không chặn được hai transaction
song song cùng thấy "chưa có room nào".

**Đánh đổi.** Nhiều partial unique index có nghĩa là một số thao tác hợp lệ trả
về lỗi unique và phải được **dịch** thành thông điệp người đọc được — và theo quy
tắc của #2, thông điệp giàu thông tin chỉ trả **sau khi đã xác thực**.

**Ai tiêu thụ:** #14 (index thật), #12, #3.

---

### Q11 — Sau khi Match bắt đầu, người chơi có những đường ra nào?

R-T-06: Forfeit là hành động chủ động, tường minh, và là **thua**. R-T-07: mất
kết nối rồi không quay lại **không phải** forfeit — đồng hồ chạy tới `EXPIRED`.
Câu: UI có nút "rời trận" không, và Forfeit cần xác nhận thế nào?

➡️ **Khuyến nghị: sau mốc start, đúng MỘT hành động rời đi tồn tại — `FORFEIT`,
có bước xác nhận, và ở room Ranked thì hộp xác nhận nói thẳng là sẽ mất Elo.
KHÔNG có nút "rời trận"/"về trang chủ" nào rời khỏi Match.** Đóng tab được, và
đóng tab **không** phải forfeit (R-T-07) — nó là mất kết nối, đồng hồ chạy tiếp.
Đường quay lại là mở lại link Match.

**Vì sao.** Một nút "rời trận" đứng cạnh "bỏ cuộc" **buộc** hệ thống phải trả lời
"rời thì khác bỏ cuộc chỗ nào" — và câu trả lời duy nhất đúng luật là "không khác
gì đóng tab", tức là một nút không làm gì cả. Tệ hơn: người chơi sẽ đọc nó như một
lối thoát an toàn khỏi một trận đang thua, đúng cái mà R-T-04 xếp `FORFEITED`
dưới cùng để bịt.

**Đánh đổi thẳng thắn:** người chơi bị kẹt trong một trận đã thua chắc **không**
có cách rút ngắn nào ngoài Forfeit (một trận thua ghi sổ) hoặc chờ tới phút 15.
Đó là hệ quả cố ý của R-T-06 + R-T-07, không phải thiếu sót của #4.

**Ai tiêu thụ:** #13 (nút và hộp thoại), #12, #15.

---

### Q12 — Rematch: ai đề nghị, đề nghị sống bao lâu, và room ở trạng thái gì giữa hai Match?

#2 đã chốt: Match record mới, Puzzle mới, cùng room, cần **cả hai** đồng ý, mã đã
tiêu không sống lại, cap chỉ áp cho room Ranked (khởi điểm 5). Còn ba lỗ: đề nghị
rematch **hết hạn** khi nào; **ai** đề nghị được; và room sống bao lâu sau khi
Match kết thúc.

➡️ **Khuyến nghị:** **cả hai** Player đề nghị được (không chỉ owner — đối xứng với
việc cần cả hai đồng ý). Đề nghị hết hạn theo **room**, không có TTL riêng. Room
sống thêm **một khoảng cố định sau khi Match kết thúc** — khuyến nghị **10 phút**
— rồi tự đóng và nhả ô cap. Rematch **đi lại đúng phase ready/countdown** của Q2.

**Vì sao 10 phút, và tại sao KHÔNG dùng lại 30 phút.** 30 phút là TTL của **mã
invite**, và #2 buộc nó vào một phép tính entropy cụ thể ("TTL chính là mẫu số
`L`"). Sau khi Match bắt đầu, mã **đã chết vĩnh viễn** — nên room hậu-Match
**không** còn là bề mặt tấn công của mã nữa, và nó không có lý do gì phải thừa kế
con số của bài toán kia. Đây đúng là cái bẫy mà handoff cảnh báo: **bê con số mà
bỏ mất tiền đề của nó**. 10 phút chỉ cần đủ dài để hai người xem kết quả và quyết
định, và mỗi phút thừa là một phút ô cap của cả hai bị giữ.

**Vì sao rematch đi lại ready/countdown:** vì nó tạo một Match **mới** với Elo
thật, và lập luận đồng thuận ở Q2 áp y nguyên.

**Ai tiêu thụ:** #13, #14, #15 (cap thật), #12.

---

### Q13 — Refresh token, và token hết hạn giữa Match

Gate #9 của #8 đặt **JWT expiry 600 giây** — đầu vào cứng. Deadline Match là
**900 giây**. ⇒ **Mọi Match đều đi qua ít nhất một lần refresh token.** Refresh
hỏng giữa trận là sự cố **gameplay**: đồng hồ vẫn chạy (R-S-04), và không quay
lại được thì `EXPIRED` (R-T-07). Câu: refresh policy là gì, và client làm gì khi
refresh hỏng?

➡️ **Khuyến nghị:** giữ **rotation bật** và **reuse detection bật** (mặc định của
Supabase); **không** đặt inactivity timeout, **không** đặt absolute session
time-box ở MVP. Client refresh **chủ động ở ~50% TTL (khoảng 300 giây)**, không
đợi hết hạn, và **MUST gọi lại `setAuth` cho Realtime** sau mỗi lần refresh — vì
#8 nói Realtime **cache quyền** tới khi client gửi JWT mới. Refresh hỏng ⇒ UI vào
trạng thái **"đang kết nối lại" chặn thao tác**, hiện rõ rằng **đồng hồ vẫn đang
chạy**, và thử lại — **không** âm thầm nuốt command.

**Vì sao không time-box.** Luồng invite **bùng theo cụm** và **zero email** nghĩa
là không có cách nào mời ai đó đăng nhập lại. Một session hết hạn giữa lúc bạn
đang chờ đối thủ là friction đánh vào người dùng thật; giá trị bảo mật của nó
thuộc #12 và cần một threat model, không phải một con số đặt sẵn ở #4.

**Vì sao refresh sớm ở 300 giây.** Refresh **đúng lúc** hết hạn nghĩa là mọi lỗi
mạng thoáng qua đều thành mất phiên giữa trận. Ở 50% TTL còn nguyên 300 giây để
thử lại — và 300 giây là **một phần ba** trận đấu, đủ rộng cho nhiều lần thử.

**Ai tiêu thụ:** #12 (session policy), #3 (client auth), #13 (trạng thái UI), #17.

---

### Q14 — "Đăng xuất mọi thiết bị" nghĩa là gì, và nó tương tác thế nào với một Match đang chạy?

Gate #9 bắt: khi **revoke membership**, transaction phải **rotate một channel
epoch không đoán được**, và client cũ phải bị disconnect/re-evaluate **trong 10
phút**. Nhưng "đăng xuất mọi thiết bị" cho *tài khoản* thì chưa ai chốt. Với JWT
600 giây, access token đã phát **vẫn dùng được tới 600 giây** sau khi refresh
token bị thu hồi.

➡️ **Khuyến nghị: có tính năng "đăng xuất mọi thiết bị", và mô tả nó ĐÚNG như
nó là: thu hồi mọi refresh token ngay lập tức; các phiên đang mở ngừng hoạt động
trong vòng tối đa 10 phút.** Không hứa "ngay lập tức". Và: **đăng xuất mọi thiết
bị KHÔNG kết thúc Match đang chạy, KHÔNG phải forfeit** — nó rơi vào R-T-07,
đồng hồ chạy tới `EXPIRED`.

**Vì sao đây không phải chi tiết kỹ thuật.** Nếu "đăng xuất mọi thiết bị" kết
thúc được Match thì nó thành **đường thoát thứ hai** khỏi một trận đang thua —
đúng lỗ hổng mà #2 đã bịt cho "xoá account" ("nếu xoá account kết thúc được Match
thì nó thành đường thoát thứ hai, và là đường né thua"). Cùng lập luận, cùng kết
luận. Đây là chỗ #4 phải nhất quán với #2 chứ không được nghĩ lại từ đầu.

**Cần chốt kèm:** cửa sổ 600 giây là **có thật và không xoá được** ở kiến trúc
này. Với một tài khoản bị chiếm, kẻ tấn công còn tối đa 10 phút. Nếu người dùng
thấy mức bảo đảm đó không đủ thì đó là đầu vào cho #12, và có thể cho #8.

**Ai tiêu thụ:** #12, #14 (bảng session), #3, #17.

---

## D. Dữ kiện đã tra sẵn

Mọi con số ở đây **tự tính lại trong phiên này**, không chép từ ticket trước.

### D.1 Ngân sách invocation, message và connection của một Match

Đầu vào: deadline **900 giây** (R-S-06); trần vận hành **25 Match đồng thời**
(#8); internal budget **≤ 50% mỗi quota** (#8) ⇒ **500.000** invocation/tháng của
1 triệu Hobby; **≤ 1 triệu** Realtime message/tháng; **200** peak connection;
broadcast tính **1 + 1/subscriber = 3 units** cho một event tới hai người.

Lối chơi của một Match (chặn trên hợp lý, không phải trần lý thuyết):

```text
mỗi Player: 17 lần mua Clue (trần R-S-12) + 3 Verify + READY + FORFEIT/finalize
          ≈ 22 command
một Match  ≈ 44 invocation, ≈ 44 event x 3 = 132 message units
=> ≈ 11.400 Match/tháng theo invocation; ≈ 7.500 theo message
```

Heartbeat presence (chỉ để trả lời R-O-01), 2 Player × toàn bộ 900 giây:

| Chu kỳ | invocation/Match | so với TOÀN BỘ lối chơi | Match/tháng ở 50% budget |
| --- | --- | --- | --- |
| 5 s | 360 | **8,2×** | 1.388 |
| 10 s | 180 | 4,1× | 2.777 |
| 15 s | 120 | 2,7× | 4.166 |
| 30 s | 60 | 1,4× | 8.333 |
| 60 s | 30 | 0,7× | 16.666 |

⇒ presence bằng heartbeat **đắt hơn toàn bộ trò chơi** ở mọi chu kỳ dưới 45 giây.
Đây là dữ kiện nền của **C-Q5**.

Connection:

```text
25 Match đồng thời x 2 socket = 50 / 200 peak  ->  dư 150
=> trung bình 3 tab phụ mỗi Player trước khi chạm trần
```

⇒ multi-tab **chịu được** ở trần vận hành hiện tại. Dữ kiện nền của **C-Q4**.

Trần xấu nhất do **rate limit** (không phải luật chơi) đặt: R-V-04 nói Verify
**không giới hạn số lần**, nên trần thật của một Player là guardrail 20
command/phút của #8 → `20 × 15 × 2 = 600` invocation/Match, tức ~833 Match/tháng.
Và vì Vercel **tính cả request bị từ chối**, rate limit ở tầng DB **không** tiết
kiệm invocation — nó chỉ tiết kiệm công của database. Dữ kiện nền của **C-Q6(iii)**.

### D.2 Các con số đồng hồ, tính lại từ luật

```text
100 Score, 5/Clue, -1 mỗi 60 giây, deadline 900 giây
  hao mòn tối đa tới deadline : 900/60 = 15
  còn lại cho Clue            : 85 -> 17 lần mua   (khớp R-S-12)
  khoá Verify sau Strike 1    : 10 giây Match Clock (R-V-08)
  TTL invite                  : 1800 giây = đúng 2x deadline (#2 Q7.2)
  JWT expiry                  : 600 giây  = 0,67x deadline (#8 gate #9)
```

Dòng cuối là dòng #4 phải để ý: **600 < 900**, nên **mọi** Match đều đi qua ít
nhất một lần refresh token. → **C-Q13**.

### D.3 Vị trí #4 trên đồ thị phụ thuộc — ĐÃ TRA LẠI TỪ TRACKER

Cạnh blocking thật, đọc bằng `gh api …/dependencies/blocked_by` (không suy từ
handoff):

```text
#4 chặn trực tiếp:  #12,  #14,  #15
#4 KHÔNG chặn #13 — #13 bị chặn bởi #14 (nên chỉ chịu ảnh hưởng gián tiếp)
#15 bị chặn bởi #4 VÀ #25    ->  đóng #4 chưa mở khoá #15
#14 bị chặn bởi #4 VÀ #15    ->  đóng #4 chưa mở khoá #14
```

`blocked_by` hiện tại: #4 = 0 (đã claim), #17 = 0, #25 = 0; #12 = 1 (chỉ chờ #4);
#13 = 1; #14 = 2; #15 = 2; #11 = 1; #3 = 3; #7 = 2; #16 = 6.

**Frontier sau khi đóng #4** (mở, `blocked_by = 0`, chưa ai claim): **#12, #17,
#25** — tăng đúng **một** ticket so với {#17, #25} hiện nay.

Ghi rõ vì bản giao việc của phiên này nói #4 chặn "#12, #13, #14" và nói frontier
sẽ "nở ra đáng kể". Tracker nói khác: #4 chặn **#12, #14, #15**, và frontier nở
thêm **đúng một** ticket, vì #14 và #15 mỗi cái còn một blocker khác. **#12** là
toàn bộ phần thưởng trực tiếp của việc đóng #4.

---

## E. Để dành round-2

Những câu này **phụ thuộc câu trả lời round-1**:

1. **Hình dạng chính xác của snapshot payload** — phụ thuộc Q9 (`version` thuộc
   về ai) và Q1 (một hay hai record). Nội dung field là của #14.
2. **Ngưỡng và nhãn của "hoạt động gần đây"** — chỉ có nghĩa nếu Q5 chọn (b).
3. **Có cần ticket research về `pg_cron`/scheduled job zero-cost không** — chỉ
   phát sinh nếu Q7 muốn (b) làm nền thay vì cải tiến có điều kiện.
4. **Hành vi khi Vercel deployment pause giữa Match** — #8 nói thẳng là Match
   hiện tại cũng chết và stack **không bảo đảm** sống sót. Câu còn lại là người
   chơi **thấy gì** và Match đó **kết thúc thế nào**, dính #17 (launch posture).
5. **Trạng thái Match hiển thị ở lịch sử khi finalize muộn** — phụ thuộc Q7 và
   thuộc #14.
6. **Có cần khái niệm "Session" trong `CONTEXT.md` không** — phụ thuộc Q4 và Q14.

## F. #4 KHÔNG quyết định

| Vấn đề | Thuộc ticket |
| --- | --- |
| Con số rate limit, CAPTCHA, ban/appeal, threat model của session theft | [#12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) |
| Schema thật, index thật, retention, PII, hình dạng bản ghi lịch sử | [#14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| Elo: draw settlement, provisional, correction, cap rematch cuối cùng | [#15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| **Cơ chế** timer/scheduled job, realtime transport, chọn service | [#3](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3) — #4 chỉ chốt **ngữ nghĩa** |
| UX của phòng chờ, countdown, chỉ báo kết nối, hộp xác nhận Forfeit | [#13](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| Mô hình đối thủ của Ranked (có giữ invite head-to-head không) | [#25](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25) |
| Nhãn beta, tiêu chí launch, mức bảo đảm công bố ra ngoài | [#17](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17) |

---

## Nguồn

- Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)
- [#2 resolution comment](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2#issuecomment-5388396390) — 12 quyết định identity/invite mà #4 kế thừa
- [#9](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9): `docs/plans/2026-08-23-issue-9-game-spec/game-spec.md` — R-T-*, R-S-02/03/04/05/06, R-P-13/14, R-V-04/05/08/09, R-O-01/02, R-I-01/02, mục 12
- [#8 resolution](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8) + `docs/research/2026-08-22-zero-cost-vercel-architecture.md` — kiến trúc authority, 14 launch gate, quota envelope
- [#10 resolution](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10) + `docs/research/2026-08-22-elo-integrity.md` — settlement atomic/idempotent, §5.3 ordering, §7.2 reversal
- [#25](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25) — mô hình đối thủ, 6 dữ kiện đã xác lập
- `CONTEXT.md` (19 thuật ngữ, gốc repo)
- `docs/plans/2026-08-24-issue-2-identity/dossier.md` — khuôn của tài liệu này
