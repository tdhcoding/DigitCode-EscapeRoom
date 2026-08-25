# Dossier — Chốt mô hình đối thủ của Ranked Match

Ticket: [Chốt mô hình đối thủ của Ranked Match](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)
Branch: `feat/issue-25-opponent-prep`
Soạn: phiên AFK 2026-08-24 (không có người ngồi cùng).

> **KẾT CỤC — đọc trước khi trích bất cứ dòng nào từ phần (C).**
> Buổi grilling ngày 2026-08-25 đã **bác phần lớn khuyến nghị** của tài liệu này.
> Người chủ map chọn vẽ lại destination: **Ranked rời khỏi Room và chỉ đến từ một
> hàng đợi, với Bot Opponent làm đường lui.** Cụ thể, C-Q6 chọn *có đối thủ máy*
> (dossier khuyến nghị *không*), C-Q1 không chọn nhánh nào trong hai nhánh dossier
> đưa ra, C-Q3 **không chấp nhận** rủi ro tự đấu (dossier khuyến nghị chấp nhận),
> và C-Q8 kết luận cap 5 đã **chết** cùng với room Ranked.
>
> Phần **(A)** ràng buộc kế thừa và phần **(D)** dữ kiện đã tra vẫn **đúng và đã
> được dùng suốt buổi** — chỉ phần **(C)** khuyến nghị là hết hiệu lực.
> Quyết định thật nằm ở **resolution comment của
> [#25](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25)**.

## Tài liệu này là gì

Đây là **phần AFK của một ticket `wayfinder:grilling`**: gom hết ràng buộc đã có,
dựng cây quyết định, và soạn sẵn câu hỏi round-1 kèm khuyến nghị — để buổi
grilling bắt đầu ở câu hỏi thật chứ không ở phần tra cứu. Cùng khuôn với
[dossier của #4](https://github.com/tdhcoding/DigitCode-EscapeRoom/blob/main/docs/plans/2026-08-24-issue-4-lifecycle/dossier.md)
và [dossier của #2](https://github.com/tdhcoding/DigitCode-EscapeRoom/blob/main/docs/plans/2026-08-24-issue-2-identity/dossier.md).

Nó **không quyết định gì**. Mọi mục ở phần C là câu hỏi để người dùng trả lời;
khuyến nghị chỉ là khuyến nghị, có thể bác toàn bộ. Theo `wayfinder`, ticket HITL
không được agent tự trả lời thay — và với ticket này còn một lý do mạnh hơn: một
trong bốn nhánh là **hành vi vẽ lại destination của map**, tức quyết định của
người chủ map, không phải của phiên làm việc.

Ba phần bắt buộc: **(A)** ràng buộc đã có, **(B)** design tree, **(C)** câu hỏi
round-1. Thêm **(D)** dữ kiện đã tra sẵn, **(E)** để dành round-2, **(F)** ranh
giới với ticket khác.

**Một dòng đáng đọc trước hết.** #2 chốt "cap rematch cho room Ranked, khởi điểm
**5**" với lý do ghi thẳng là "để **không tạo ra một đường rematch vô hạn**". Nhưng
control mà [#10](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10) §4.3
thực sự mô tả là "cap số rated Match cho mỗi **unordered pair** trong một
**window**" — **cap theo cặp**, không phải cap theo room. Và
[#4](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4) Q12 vừa chốt
rằng room chết 10 phút sau Match và **owner đóng sớm được bất cứ lúc nào room
không còn Match chưa terminal**. Ghép ba dòng đó lại: cùng một cặp account chỉ cần
**đóng room rồi mở room mới** là được thêm 6 trận nữa. Và chi phí biên thật của
việc đó là **đúng một command** (`CLOSE_ROOM`) — vì `CREATE_ROOM` + `JOIN_ROOM`
chỉ thay chỗ cho `PROPOSE_REMATCH` + `ACCEPT_REMATCH` mà một rematch vốn đã tốn.
Trên 869 trận, cả cái cap tốn thêm **2,4%** số command. Cap 5 là **ma sát**,
không phải **chặn trên** — nó không bao giờ là thứ #2 nghĩ nó là. Xem D.3.

---

## A. Những quyết định đã có, và chúng ràng buộc #25 như thế nào

Mỗi dòng ghi **nguồn → ràng buộc cụ thể lên #25**. Không tóm tắt lại nguồn; chỉ
lấy phần cắt vào ticket này.

### A.1 Sáu dữ kiện đã xác lập trong body #25 — NHẬN NGUYÊN TRẠNG

Body của #25 đã chốt sáu dữ kiện. Chúng **không được tính lại** trong phiên
grilling; việc của phần A này chỉ là nói rõ mỗi dữ kiện **khoá** nhánh nào.

| # | Dữ kiện | Nó khoá gì ở #25 |
| --- | --- | --- |
| 1 | **Hai account tự đấu là lỗ hổng thật, và Q10 của #2 không chặn.** #10 xác nhận zero-sum **không** ngăn boosting — nó chỉ chuyển điểm. Điều kiện Ranked của #2 chỉ **tăng giá** mỗi donor. | Câu hỏi của #25 **không** phải "có lỗ hổng không" (đã biết là có) mà là "**mô hình đối thủ chịu được tới mức nào**, và ta chấp nhận mức nào". → **C-Q1**, **C-Q3** |
| 2 | **Điều kiện "≥1 Practice Match" gần như không tăng chi phí Sybil.** `N` donor chỉ cần ghép với nhau: `N/2` trận, mỗi trận ~15 giây. Giá trị thật là **onboarding**. | #25 **MUST NOT** thừa kế điều kiện đó như một biện pháp bảo mật, và **MUST NOT** đề xuất "thêm một điều kiện onboarding nữa" như một control chống Sybil. → **C-Q5** |
| 3 | **Chia sẻ Clue giữa hai account KHÔNG cho thêm Elo.** R-P-13 cho cả hai cùng một Puzzle nên đọc mã cho nhau là khả thi; nhưng `K=32` **không xét margin** nên transfer chỉ phụ thuộc hai rating. Forfeit cho winner **đúng cùng lượng Elo** như Solve, và nhanh hơn. ⇒ vấn đề **Score**, không phải **Elo**. **Chỉ** thành vấn đề Elo nếu #15 thêm một số hạng margin. | Hai hệ quả. (i) #25 **MUST NOT** biện minh cho một mô hình đối thủ bằng lý do "chống chia sẻ Clue" — nó không mua được gì ở tầng Elo. (ii) Dữ kiện này có **tiền đề** (`K=32`, không margin); nếu #15 định thêm margin thì tiền đề mất và dòng này **phải đọc lại**. → **C-Q7** |
| 4 | **Nhánh (3) ghép random đụng scope và đụng thực tế.** Map xếp public matchmaking **out of scope**, và pool người chơi **rỗng** lúc launch. | Nhánh (3) đóng bằng **hai** lý do độc lập — cả hai đều không phải "chưa làm kịp". Nếu người chủ map muốn mở lại, đó là hành vi **scoping**, không phải một bước trên đường đi. → **B1.3** (✱) |
| 5 | **Nhánh (4) đối thủ máy là hành vi vẽ lại destination.** `CONTEXT.md` định nghĩa Match là contest giữa **đúng hai Player**, Player là **người đã xác thực**; destination nói Player **mời nhau**. | Dossier này **PHÂN TÍCH** nhánh (4) và nói rõ nó vô hiệu hoá phần nào của #2 và #4 (xem D.5), nhưng **KHÔNG chọn nó**, **không sửa destination**, **không sửa `CONTEXT.md`** theo nó. Chọn nhánh (4) là quyết định của **người chủ map**. → **C-Q6** |
| 6 | **Nhánh (2) khả thi nhưng là research mới.** Cần một thang độ khó cho từng Puzzle. #6 có mốc dùng được: tập clue **cố định** tốn đúng **22 Clue**, adaptive cần **[10, 16]**, sampler **không** làm lệch độ khó. | Phần A.6 dưới đây trả lời "khả thi tới đâu" bằng con số, và nói rõ **thiếu gì**. → **C-Q1**, **A.6** |

### A.2 Từ [#2 — identity, profile và invite-room lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2) (CLOSED)

12 quyết định. Bảng dưới chỉ lấy phần cắt vào #25.

| #2 chốt | Ràng buộc lên #25 |
| --- | --- |
| **Q10 — điều kiện Ranked: (i) có identity Google **VÀ** (ii) đã hoàn tất ≥ 1 Practice Match** ("hoàn tất" = terminal bất kỳ **trừ** `FORFEITED`). #2 ghi thẳng: (ii) **gần như không tăng chi phí Sybil**; hàng rào Sybil thật chỉ là **(i)**; giá trị thật của (ii) là **onboarding**. #10 nói thẳng "magic-link/Google auth **không chứng minh** một người-một-account". | Đây là **toàn bộ** hàng rào định danh mà #25 được kế thừa, và nó chặn đúng **một** thứ: chi phí tạo mỗi donor = **một account Google**. #25 **MUST NOT** đọc (ii) như một biện pháp bảo mật, và **MUST NOT** thừa kế nó như bằng chứng rằng Sybil đã được xử lý. Xem D.1 cho giá thật của một donor. → **C-Q5** |
| **Q11.4 — cap số rematch CHỈ áp cho room Ranked; room Practice không giới hạn. Giá trị khởi điểm 5.** Lý do: #10 §4.1/§4.3 — nhiều ván cùng một cặp **không tăng** connectivity của pool. "Việc của #2 chỉ là **không tạo ra một đường rematch vô hạn**"; con số cuối thuộc #15. | **Cap này là cap theo ROOM, không phải theo CẶP** — và #10 §4.3 mô tả control theo **cặp trong một window**. Với #4 Q12 (room chết sau 10 phút, owner đóng sớm được), mở room mới là **ba command**. ⇒ cap 5 **không** đóng đường bơm Elo; nó chỉ thêm ma sát. Đây là chỗ #25 phải nói thẳng cho #15, nếu không #15 sẽ thừa kế con số 5 **mà mất tiền đề của nó**. Xem D.3. → **C-Q8** |
| **Q5 — cap cứng 1 room đang mở + 1 Match chưa terminal mỗi account, hai ô tách biệt.** | Đây là **control chống farm hiệu quả nhất đang có**, và nó tồn tại vì lý do khác hẳn: nó **serialize** việc farm. Người bơm Elo chỉ chạy được **một trận một lúc**, không song song hoá được. Đó là thứ biến "869 trận" ở D.1 thành nhiều giờ đồng hồ thật. #25 **không được nới** ô cap này. |
| **Q8 — mode chốt lúc TẠO ROOM, in vào invite, BẤT BIẾN.** Không đủ điều kiện Ranked ⇒ **từ chối rõ ràng**, không âm thầm hạ xuống Practice. | Mọi control mà #25 chọn phải **phát biểu được tại thời điểm tạo room hoặc tại Match Start**, không được là "trận này tự hạ xuống Practice ở giữa chừng". Nhánh "Match vượt cap tự thành Practice" của #10 §4.3 **va thẳng** vào Q8 này. → **C-Q8** |
| **Q9.2 — self-join CẤM CỨNG**, cùng `player_id` không giữ hai ghế kể cả khác thiết bị. | Chặn đúng **một** kịch bản: một account tự đấu với chính nó. Nó **không** chạm tới kịch bản của #25 (một **người**, hai **account**). Khoảng cách giữa hai câu đó chính là toàn bộ ticket này. |
| **Q1 — Ranked yêu cầu Google; magic link chỉ Practice.** | Nếu #25 muốn tăng chi phí Sybil thì đòn bẩy **duy nhất** đang có nằm ở đây, và nó đã được kéo hết cỡ. Mọi đòn bẩy khác (tuổi account, số điện thoại) đã bị #2 bác có lý do — #25 nên đọc lý do trước khi đề xuất lại. → **C-Q5** |
| **Q12 — zero email ngoài auth.** | Không có kênh nào chủ động chạm tới người chơi ⇒ **không có** cơ chế cảnh báo/khiếu nại ngoài in-app. Bất kỳ control nào cần "báo cho người dùng biết họ bị flag" đều **không có đường** ở MVP. → **C-Q3** |
| **Quy tắc thông điệp lỗi:** thông điệp giàu thông tin **chỉ** trả sau khi đã xác thực. | Nếu #25 chọn một control từ chối Match (ví dụ cap theo cặp), thông điệp từ chối phải tuân quy tắc này — và nó **cũng** là một oracle: "cặp này đã chạm cap" là thông tin. → **C-Q8** |

### A.3 Từ [#4 — Match lifecycle, reconnect và concurrency](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4) (CLOSED 2026-08-24)

#4 vừa chốt 15 thứ. Bảy trong số đó cắt thẳng vào #25.

| #4 chốt | Ràng buộc lên #25 |
| --- | --- |
| **Match Start là MỘT mốc duy nhất.** "Tạo Match" = "Match bắt đầu" = **một transaction** do `READY` thứ hai kích hoạt: INSERT Match row, sinh Puzzle, đóng dấu `ruleset_id`, giết Invite Code, chiếm ô cap, khoá R-T-08. | **Mọi control của #25 phải chạy TRƯỚC hoặc TRONG transaction đó**, dưới lock room row — vì sau khi commit thì R-T-08 cấm huỷ. Không tồn tại chỗ nào để "xem lại sau rồi vô hiệu Match". Một control kiểu "phát hiện rồi huỷ trận" là **bất khả thi về kiến trúc**, không phải đắt. → **C-Q3**, **C-Q8** |
| **Mọi bất biến do partial unique index giữ, không do logic giữ** — vì Vercel API là control point, **không phải trust boundary** (publishable key là public, có người gọi thẳng Data API). | Một cap **theo cặp trong một window** **KHÔNG** biểu diễn được bằng unique index — nó là một `COUNT(*)` trên một khoảng thời gian. Nên control đó phải là một **truy vấn dưới lock trong transaction start**, tức một loại bảo vệ **yếu hơn** mọi bất biến khác của hệ thống. Phải nói thẳng chi phí đó khi chọn. → **C-Q8** |
| **Cap 1 room + 1 Match chưa terminal giữ bằng partial unique index** trên `(owner_id)` và `(player_id)`. | Farm bị **serialize hoàn toàn**: một Match chưa terminal mỗi account. Ghép với D.1: đường 869 trận là **tuần tự**, không rút ngắn bằng song song. |
| **`EXPIRED` là trạng thái ĐƯỢC QUAN SÁT**, không tiến trình nền; admission tự dọn. **Đánh đổi đã chấp nhận: một Match bỏ rơi có thể nằm `ACTIVE` hàng tuần.** | Hai hệ quả cho #25. (i) Nếu control là một `COUNT` trên **Match đã settle**, người farm chỉ cần **bỏ dở** vài trận để làm mẫu số sai; đếm trên **Match row** (mọi trạng thái) thì không. (ii) Không có tiến trình nền nào ⇒ **không có** đường chạy job phát hiện collusion theo lịch. Xem [#27](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27) cho phần này. → **C-Q3** |
| **Multi-tab và multi-device CÙNG TỒN TẠI trên một ghế**; server **không phân biệt được** hai tab của cùng actor; chỉ báo "đang điều khiển" là trang trí phía client. | Kịch bản của #25 **rẻ hơn** người ta tưởng: một người điều khiển hai account **trong cùng một trình duyệt, hai tab**, không cần thiết bị thứ hai, không cần cửa sổ ẩn danh. #4 biến multi-tab thành ca **thường ngày** có chủ ý — nên nó cũng làm self-play thành ca **thoải mái**. Đây là leo thang có thật của mối đe doạ, và nó đến từ một quyết định đúng ở #4. → **C-Q1**, **C-Q3** |
| **Q3.3 — owner đóng được room khi đã đủ hai người nhưng chưa start**, và #4 ghi kèm một dòng gửi thẳng #15/#25: *"ở room Ranked, owner **nhìn thấy tag đối thủ** rồi mới quyết định đóng hay chơi. Nếu #15 cho hiện rating trong phòng chờ thì đó thành 'chọn đối thủ có lợi'."* | **Opponent shopping đã tồn tại ở mức tag**, trước cả khi ai bàn tới việc hiện rating. #25 phải chốt xem đó có phải điều chấp nhận được dưới mô hình đối thủ đã chọn hay không, và phải giao ràng buộc rõ cho #15. → **C-Q4** |
| **Q12 — room sống thêm 10 phút sau khi Match kết thúc; owner đóng sớm được bất cứ lúc nào room không còn Match chưa terminal.** Rematch **đi lại đầy đủ** ready + countdown. | Đây là mảnh ghép làm cap-5-theo-room mất hiệu lực: **đóng room, mở room mới**. Không cần chờ 10 phút. Xem D.3. → **C-Q8** |
| **Q11 — sau start, đường ra duy nhất là `FORFEIT`**; không có nút rời trận. | Với người farm, `FORFEIT` **là công cụ**, không phải hình phạt: nó cho winner **đúng cùng lượng Elo** như Solve (R-T-05.3) trong **vài giây** thay vì 15 phút. Toàn bộ kinh tế của D.1 dựa trên dòng này. |

### A.4 Từ [#10 — nghiên cứu tính toàn vẹn Elo](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10) (CLOSED)

**Đây là nguồn gốc của mọi lập luận Elo trên map này.** Bốn mục được ticket #25
gọi tên đích danh, cộng hai mục nền.

| #10 xác lập | Ràng buộc lên #25 |
| --- | --- |
| **§4.1 (MATH)** Expected score chỉ dùng `R_A − R_B`. Trong graph mà node là Player và edge là rated Match, **dữ liệu trong một connected component không chứa bằng chứng** để đặt component đó cao/thấp hơn một component không có edge nối chéo. Baseline chung ép mean về `1000` là **prior/policy**, không phải so sánh quan sát được. | Đây là ràng buộc **nặng nhất** lên nhánh (1). Pool invite-only là một **tập các component nhỏ, rời rạc**. Nên một rating Ranked ở MVP **không** là một tuyên bố so sánh được toàn cục — nó chỉ so sánh được **bên trong** component. Nếu sản phẩm định trình bày nó như một thang chung thì đó là một tuyên bố **model không đỡ được**. → **C-Q2** |
| **§4.1 (MATH)** Nhiều game chân thực cùng một cặp **vẫn cung cấp evidence** về chênh lệch trong cặp, nhưng **không tăng connectivity** của pool. ⇒ "repeated opponent" **không tự nó là abuse**, đặc biệt trong population nhỏ. | Cấm/cap gặp lại **đánh vào người dùng thật trước tiên** — ở một pool invite-only, chơi lại với đúng người bạn của mình là **ca thường ngày**, không phải ca biên. Bất kỳ cap theo cặp nào cũng phải trả lời "false-positive budget là bao nhiêu". → **C-Q8** |
| **§4.2 (FACT + MATH)** Lichess định nghĩa boosting/sandbagging và **hạn chế multiple accounts** — đó là policy first-party, **không phải theorem Elo**. Từ `1000/1000`, `K=32`, 10 win dàn xếp liên tiếp ⇒ `1110.47/889.53`: tổng vẫn `2000`, đã chuyển `110.47` điểm. Transfer giảm dần nhưng **không bằng 0**. Donor cố tình thua rồi **inactive/đóng account** làm mean của **active subset** và rating recipient tăng. **Nhiều donor mới tránh phần lớn hiệu ứng diminishing.** | Ba dòng này là toàn bộ kinh tế của D.1, và đã được **tính lại độc lập** ở đó (`1110.473/889.527` — khớp). Dòng cuối là dòng quan trọng nhất: nó nói **cap theo cặp đẩy kẻ tấn công sang Sybil**, tức đổi một tấn công **tự giới hạn** lấy một tấn công **không tự giới hạn**. Xem D.1 bảng 2. → **C-Q3**, **C-Q8** |
| **§4.3 (CHOICE)** "Invite-only **không loại bỏ** collusion; nó cho Player **quyền chọn opponent**, nên cần chốt control và **false-positive budget**. **Không có nguồn nào ở đây chứng minh một ngưỡng lặp cụ thể là tối ưu.**" Bảng 8 control ứng viên kèm chi phí. Các signal có thể giữ: tỷ trọng Match theo pair, chuỗi outcome một chiều, duration bất thường, tỷ lệ forfeit/timeout, account age, opponent diversity, graph donor→recipient. IP/device fingerprint **vượt phạm vi** và cần quyết định privacy riêng. | Bảng đó là **menu** của C-Q3, và câu "không nguồn nào chứng minh ngưỡng tối ưu" nghĩa là **mọi con số ở #25 đều là policy, không phải kết quả**. Danh sách signal là thứ #25 **phải** giao cho #14 nếu muốn giữ đường phát hiện về sau — vì retention là quyết định **khó đảo**. → **C-Q3** |
| **§5.3 (MATH)** Hai update Elo **không commutative**. #2 đã xoá bài toán ordering khỏi MVP bằng cap 1 Match chưa terminal. Ledger phải lưu order đã dùng để rebuild được. | #25 **không được** chọn một mô hình đối thủ làm sống lại bài toán này. Cụ thể: bất kỳ nhánh nào cho một account có **nhiều hơn một** Match Ranked chưa terminal (ví dụ đấu nhiều đối thủ máy song song ở nhánh 4) sẽ mở lại §5.3. → **C-Q6** |
| **§1.3, §3** Zero-sum là một **tính chất được chứng minh** của transfer `+T/−T`, và nó **mất** dưới nhiều lựa chọn provisional (bảng §3.2: "per-player K cao cho provisional" ⇒ không tự giữ zero-sum). | Nhánh (2) — rating theo performance cá nhân — **bỏ hẳn** transfer, nên §1.3 không còn áp dụng và toàn bộ phân tích của #10 phải **viết lại**. Đó là chi phí thật của nhánh (2), lớn hơn "cần một thang độ khó". → **C-Q1** |

### A.5 Từ ruleset `digitcode-ruleset/1.0.0` ([#9](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9), CLOSED)

| Luật | Ràng buộc lên #25 |
| --- | --- |
| **R-T-08** Match đang chạy **MUST NOT** bị huỷ, reset hay sinh lại Puzzle bởi **bất kỳ ai** — kể cả người vận hành. | **Bất kỳ nhánh nào cũng phải giữ.** Hệ quả trực tiếp: không có control nào của #25 được thực hiện bằng cách **huỷ một Match đang chạy**. Ghép với #4 (Match Start là một transaction): control **phải** ở admission, hoặc không ở đâu cả. |
| **R-K-04** Hai Match chỉ **so sánh được** về mặt luật chơi nếu **cùng `ruleset_id`**. Spec **không** quyết định Elo xử lý ra sao khi ruleset đổi — đó là **đầu vào cứng cho #15**. | **Bất kỳ nhánh nào cũng phải giữ.** Hệ quả sắc nhất: nhánh (2) cần một **thang độ khó**, mà thang đó là một tham số của luật chơi ⇒ đưa nó vào là **bump ruleset** (R-K-01) ⇒ Match trước và sau **không so sánh được**. Hôm nay chi phí ≈ 0 (chưa Match nào chơi thật); về sau thì không. → **C-Q1** |
| **R-P-16** Ngoài R-P-10, Ranked **MUST NOT** có thêm **bất kỳ ngưỡng độ khó nào**. Lý do spec ghi: #6 đo được độ khó **gần như đồng đều** — **trung vị 12, p99 15, worst case 16** lần mua — và một ngưỡng như vậy cần **cây quyết định tối ưu** mà khoảng `[8, 16]` chưa đóng. "Đây là **từ chối có chủ ý**, không phải thiếu sót." | Luật này **không** cấm nhánh (2) (nó cấm một *ngưỡng lọc Puzzle*, không cấm một *thang dùng để chấm điểm*), nhưng nó cấm **bằng đúng lý do** mà nhánh (2) sẽ vấp phải: **không có cây tối ưu**, nên "độ khó" hiện chỉ là **độ khó theo một chiến lược bot cụ thể**. Xem A.6. → **C-Q1** |
| **R-K-01 / R-K-02** Ruleset có tên và version; **đổi bất kỳ giá trị nào ở bảng R-K-02 là bump version**. Bảng `1.0.0` có 8 tham số — **không** tham số nào là thang độ khó hay tham số Elo. | Elo **không nằm trong ruleset**. Nên `K`, margin, provisional, cap là **policy của #15**, không phải luật chơi — và đổi chúng **không** bump ruleset, **không** phá R-K-04. Ngược lại, một **thang độ khó** thì lại là luật chơi. Ranh giới này quyết định nhánh (2) đắt tới đâu. → **C-Q1**, **C-Q7** |
| **R-T-05.3** Không ai `SOLVED`, đúng một `FORFEITED` → **Player còn lại thắng**. **R-T-04** `FORFEITED` xếp **dưới cùng**. **R-T-06** Forfeit là **thua** bất kể đối thủ ở đâu. | Đây là **cơ chế farm rẻ nhất**: donor bấm Forfeit ngay sau Match Start, recipient thắng đủ Elo trong vài giây. Ba luật này tồn tại để bịt đường **né thua**, và chúng làm đúng việc đó — nhưng chúng cũng làm đường **dâng thắng** rẻ đi. Đó là đánh đổi đã có, #25 không đảo được. Xem D.1. |
| **R-V-08 / R-V-09** Strike 1: −10 Score và khoá Verify **10 giây**; Strike 2 → `ELIMINATED` ngay. | Nguồn của con số "~15 giây mỗi trận" ở dữ kiện 2 của #25: một donor tự loại mình cần **2 Wrong Guess** cách nhau **10 giây**. Với đường Forfeit thì còn nhanh hơn. Xem D.1. |
| **R-P-09 / R-P-10** Practice rút từ **465.120**; Ranked rút từ **464.948** (loại 172 mã thuộc 86 cặp collision). **R-P-13** một Match đúng một Puzzle, sinh lúc tạo Match, **dùng chung** cho cả hai Player. | R-P-13 là nguồn của dữ kiện 3 (chia sẻ Clue khả thi). R-P-10 là **ngưỡng eligibility duy nhất** mà Ranked được phép có — R-P-16 cấm thêm cái thứ hai. |
| **R-S-12** Trần **17 lần mua Clue**. **R-S-11** Hao mòn 60 giây được chọn để trần 17 phủ worst case **16** với **đúng một lần mua dư**. | Biên **1 lần mua**. Nếu nhánh (2) đổi cách chấm điểm cá nhân thì phải kiểm lại biên này chứ không được giả định nó còn nguyên. |

### A.6 Từ [#6](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6) + `docs/plans/2026-08-24-clue-bounds/findings.md` — **nhánh (2) khả thi tới đâu**

Dữ kiện 6 của #25 nói nhánh (2) "khả thi nhưng là research mới". Đây là câu trả
lời cụ thể cho "tới đâu", và **cái gì còn thiếu**.

**Cái đã có, và nó tốt hơn tưởng tượng.**

Phân phối độ khó theo greedy minimax, đo trên **toàn bộ 465.120** secret (#6 §5.2,
histogram nguyên văn) — mọi thống kê dưới đây **tính lại trong phiên này** từ
histogram đó, không chép:

```text
độ sâu :   5    6     7      8      9     10     11      12     13     14     15    16
secret :  15  296  2216  10070  28279  57337  89102  106811  95226  57281  17633  854
```

| Đại lượng | Giá trị | Ghi chú |
| --- | --- | --- |
| Trung bình | **11,837** lần mua | #6 ghi 11,84 (uniform) và 11,83 (sampler thật) — khớp |
| Độ lệch chuẩn | **1,662** lần mua | = **8,3 điểm Score** (giá Clue 5) |
| Trung vị | 12 | khớp R-P-16 |
| p99 | 15 | khớp R-P-16 |
| Miền `[10, 14]` | **87,24%** số Puzzle | |
| Miền `[11, 13]` | **62,59%** số Puzzle | |
| Toàn miền `[5, 16]` | 55 điểm Score | nhưng chỉ **12,76%** nằm ngoài `[10, 14]` |
| Hai đuôi (`≤ 8` và `≥ 15`) | **6,68%** | 2,71% + 3,97% |

⇒ **Thang độ khó tồn tại, và nó rẻ để sản xuất.** Một lượt dựng cây đầy đủ gán
độ sâu cho **mọi** secret; `bounds_adaptive_search.py sweep` chạy **128 lượt trong
~21 phút**, tức **~10 giây một lượt**. Bảng tra `secret → độ sâu` là **465.120
dòng ≈ 454 KB** — vặt so với mọi ngân sách của map. Nhánh (2) **không** cần tính
runtime, và **không** cần một ticket research để biết điều đó.

**Cái còn thiếu — và đây mới là phần đắt.**

1. **Thang đó không có thẩm quyền.** Nhãn của chặn trên 16 là **HEURISTIC**. Quét
   128 cấu hình greedy: **30 lượt** cho worst case 16, **88 lượt** cho 17, **10
   lượt** cho 18. Đổi luật phá hoà thì **cả thang dịch chuyển**. Nên "độ khó của
   Puzzle X" hôm nay nghĩa là "độ sâu của X **dưới một chiến lược bot cụ thể mà
   không tài liệu nào chốt**". Đó chính là lý do R-P-16 từ chối đặt ngưỡng.
2. **Chưa ai đo phương sai phía NGƯỜI CHƠI.** Chuẩn hoá theo độ khó chỉ đáng làm
   nếu phương sai do Puzzle **đáng kể so với** phương sai do người chơi. Ta biết
   vế đầu (**sd = 8,3 điểm** trên thang 100) và **không biết gì** về vế sau — map
   ghi rõ ở *Not yet specified* rằng cách đo telemetry cân bằng game **chưa được
   chốt**, và không có người chơi nào để đo. **Không research nào đóng được khoảng
   này trước launch.** Đây là ràng buộc **thời gian**, không phải ràng buộc nỗ lực.
3. **Nhánh (2) bỏ zero-sum.** #10 §1.3 chứng minh zero-sum cho transfer `+T/−T`.
   Rating theo performance cá nhân **không có** transfer, nên §1.3, §4.1, §4.2,
   §5.3 — bốn mục nền của map — **không còn áp dụng**, và phải có phân tích thay
   thế. Đó là research mới thật sự, không phải cái thang độ khó.
4. **Đưa thang vào là bump ruleset.** Thang độ khó là tham số luật chơi (R-K-01) ⇒
   R-K-04 ⇒ Match trước/sau **không so sánh được**.

### A.7 Từ `CONTEXT.md` (26 thuật ngữ, gốc repo — bản trên `main` từ `e9f2cdf`)

| Thuật ngữ đã có | Ràng buộc lên #25 |
| --- | --- |
| **Match**: "A real-time head-to-head contest in which **exactly two Players** independently solve the same Puzzle and are ranked by their performance." | Nhánh (4) đối thủ máy **mâu thuẫn trực tiếp** với dòng này. Không phải "chưa hỗ trợ" — **mâu thuẫn**. |
| **Player**: "An **authenticated person** who participates in a Match." | Đối thủ máy **không phải Player**: nó không phải người, không xác thực được. Nhánh (4) buộc phải hoặc (i) sửa định nghĩa Player, hoặc (ii) tạo một khái niệm thứ ba và nói rõ nó **không** vào Match. Cả hai đều là **hành vi vẽ lại mô hình miền**, tức việc của người chủ map. → **C-Q6** |
| **Ranked Match**: "A Match whose **final result changes both Players' Elo ratings**." | Nhánh (2) làm câu này **sai**: dưới rating theo performance cá nhân, thứ đổi rating **không phải** *result* của Match mà là **màn trình diễn của từng người**. Chọn nhánh (2) ⇒ phải viết lại định nghĩa này. → **C-Q1**, **C-Q9** |
| **Score**: "_Avoid_: Points, **Elo**, **rating**" | **Lỗ hổng từ vựng, cùng dạng với lỗ hổng Room mà #4 tìm ra:** glossary **cấm** dùng "Elo"/"rating" làm từ đồng nghĩa của Score, nhưng **chưa bao giờ định nghĩa** Elo Rating là gì. Repo lại có một từ bị cấm mà không có từ thay thế. #25 là ticket đầu tiên mà thiếu sót này gây phiền thật, vì cả bốn nhánh đều là câu hỏi "**rating đo cái gì**". → **C-Q9** |
| **Practice Match**: "same game rules … except unrestricted pool, and **does not change either Player's Elo rating**." | Nếu nhánh (4) được đặt **chỉ trong Practice**, định nghĩa này vẫn đúng nguyên văn — nhưng **Match** thì vẫn nói "exactly two Players". Nên "đối thủ máy chỉ ở Practice" **vẫn** là sửa mô hình miền, chỉ nhẹ hơn. → **C-Q6** |

### A.8 Từ Out of scope của map #1

Bảy mục, và **năm** trong số đó cắt vào #25:

- **Public matchmaking** — đóng nhánh (3) ở tầng scope (dữ kiện 4 của #25).
- **Leaderboard** — **không có bề mặt công khai nào** để một rating bị bơm được
  trưng ra. Đây là dữ kiện quyết định của C-Q4: phần thưởng của boosting ở MVP
  gần bằng **không**, và nó là lý do mạnh nhất để chấp nhận nhánh (1).
- **Spectator, chat** — không có kênh quan sát/tố giác nào ngoài in-app.
- **Season, rating decay** — rating **không tự trôi về trung bình**, nên một
  rating bị bơm **ở lại vĩnh viễn**. Chiều ngược của gạch đầu dòng trên: phần
  thưởng thấp, nhưng **thiệt hại thì lâu dài**.
- **Moderation platform** — **không có** công cụ vận hành để xử lý một ca
  collusion sau khi phát hiện. Mọi control ở nhánh "phát hiện rồi xử lý" của #10
  §4.3 đều **không có người tiêu thụ** ở MVP. → **C-Q3**

---

## B. Design tree của #25

Nhánh có dấu ✱ là nhánh **đã bị đóng** bởi ràng buộc ở phần A — ghi kèm lý do để
thấy vì sao không hỏi.

```text
#25 Mô hình đối thủ của Ranked Match
│
├── B1  MÔ HÌNH ĐỐI THỦ — bốn nhánh của ticket
│   ├── B1.1  (1) Giữ invite head-to-head như #2 đã chốt          → C-Q1
│   │         ├─ chấp nhận rủi ro tự đấu, ghi thành thật
│   │         └─ chấp nhận + thêm control cấu trúc                → C-Q3, C-Q8
│   ├── B1.2  (2) Rating theo performance cá nhân                 → C-Q1
│   │         ├─ cần thang độ khó       — CÓ, rẻ, nhưng HEURISTIC (A.6)
│   │         ├─ cần phương sai người chơi — KHÔNG CÓ, và không đo
│   │         │  được trước launch (A.6.2)
│   │         ├─ bỏ zero-sum ⇒ #10 §1.3/§4.1/§4.2/§5.3 phải viết lại
│   │         └─ bump ruleset (R-K-01) ⇒ R-K-04 cắt lịch sử
│   ├── B1.3  ✱ (3) Ghép random / public matchmaking — map xếp OUT
│   │         OF SCOPE, và pool rỗng lúc launch (dữ kiện 4)
│   ├── B1.4  (4) Đối thủ máy — HÀNH VI SCOPING, KHÔNG PHẢI MỘT BƯỚC
│   │         ├─ mâu thuẫn CONTEXT.md "exactly two Players" (A.7)
│   │         ├─ mâu thuẫn destination "Player mời nhau"
│   │         ├─ vô hiệu hoá phần nào của #2 và #4               → D.5
│   │         └─ QUYẾT ĐỊNH CỦA NGƯỜI CHỦ MAP                    → C-Q6
│   └── B1.5  Lai: giữ (1) cho Ranked, đặt (4) ngoài Ranked      → C-Q6
│
├── B2  RATING ĐANG ĐO CÁI GÌ — ngữ nghĩa, không phải cơ chế
│   ├── B2.1  Tuyên bố về chênh lệch kỹ năng giữa hai người       → C-Q2
│   ├── B2.2  Tuyên bố về mức trình diễn của một account          → C-Q2
│   ├── B2.3  Phạm vi so sánh: trong component hay toàn cục
│   │         (#10 §4.1 nói model KHÔNG đỡ được toàn cục)         → C-Q2
│   └── B2.4  ✱ Giá trị K, baseline 1000 — Notes map + #15
│
├── B3  MỨC CHẤP NHẬN RỦI RO TỰ ĐẤU
│   ├── B3.1  Chấp nhận + ghi thành thật, không control mới       → C-Q3
│   ├── B3.2  Control cấu trúc (cap theo cặp, giảm K theo lần gặp) → C-Q3, C-Q8
│   ├── B3.3  Phát hiện sau + correction                          → C-Q3
│   │         └─ ✱ không có moderation platform (out of scope),
│   │            không có tiến trình nền (#4 Q7)
│   ├── B3.4  Giữ signal để phát hiện VỀ SAU (quyết định retention) → C-Q3
│   └── B3.5  ✱ IP/device fingerprint — #10 §4.3 nói vượt phạm vi,
│             cần quyết định privacy riêng (#14)
│
├── B4  PHẦN THƯỞNG CỦA BOOSTING — rating hiện ở đâu
│   ├── B4.1  Chỉ trong lịch sử cá nhân                           → C-Q4
│   ├── B4.2  Hiện trong phòng chờ trước khi start                → C-Q4
│   │         └─ #4 Q3.3 cảnh báo: thành "chọn đối thủ có lợi"
│   ├── B4.3  ✱ Leaderboard công khai — out of scope
│   └── B4.4  ✱ Cơ chế hiển thị cụ thể — #15 và #13
│
├── B5  ĐIỀU KIỆN VÀO RANKED
│   ├── B5.1  Giữ nguyên (i) Google + (ii) ≥1 Practice            → C-Q5
│   ├── B5.2  Thêm điều kiện mới (tuổi account, diversity…)       → C-Q5
│   │         └─ ✱ tuổi account, số điện thoại — #2 Q10 đã bác có lý do
│   └── B5.3  ✱ Bỏ (ii) — #2 giữ nó vì lý do onboarding, không phải bảo mật
│
├── B6  RÀNG BUỘC #25 GIAO CHO #15
│   ├── B6.1  Số hạng margin: có được thêm không, với điều kiện gì → C-Q7
│   ├── B6.2  Cap rematch: theo room hay theo cặp, cửa sổ nào      → C-Q8
│   ├── B6.3  Provisional: có cần không dưới mô hình đã chọn       → E
│   └── B6.4  ✱ Draw settlement, correction, ledger — thuần #15
│
└── B7  MÔ HÌNH MIỀN
    ├── B7.1  "Elo Rating" cần vào CONTEXT.md không               → C-Q9
    ├── B7.2  "Ranked Match" có phải viết lại không (nhánh 2)      → C-Q9
    └── B7.3  ✱ Sửa "Match"/"Player" theo nhánh (4) — CHỈ khi
              người chủ map chọn nhánh (4) trước
```

**Thứ tự phụ thuộc trong round-1.** **Q1** (chọn nhánh) chi phối gần như tất cả:
Q2, Q3, Q5, Q7, Q8, Q9. **Q6** (nhánh 4) đứng riêng vì nó là câu hỏi **scoping**,
và nếu câu trả lời là "có" thì Q1 phải hỏi lại. **Q2** (rating đo gì) chi phối Q4
(hiện ở đâu). **Q3** (mức chấp nhận) chi phối Q8 (cap). Vì thế round-1 nên đi
**Q6 → Q1 → Q2 → Q3 → Q4 → Q5 → Q7 → Q8 → Q9** — hỏi câu scoping **trước**, để
không phải đi lại.

---

## C. Câu hỏi grilling round-1

Mỗi câu: **câu hỏi** → **khuyến nghị** → **vì sao** → **ai tiêu thụ câu trả lời**.

Theo tiền lệ của #2 và #4, hỏi **từng câu một** và chờ trả lời rồi mới sang câu
tiếp. Danh sách này là bản in sẵn để đọc trước, **không** phải để trả lời hàng loạt.

**Tôi KHÔNG trả lời câu nào trong số này.** Khuyến nghị là khuyến nghị.

---

### Q6 — HỎI TRƯỚC. Đối thủ máy: có vẽ lại destination của map không?

*(Đánh số theo cây B, nhưng hỏi trước tiên — xem "thứ tự phụ thuộc" ở cuối phần B.)*

`CONTEXT.md` định nghĩa **Match** là contest giữa **đúng hai Player**, và
**Player** là **người đã xác thực**. Destination của map nói Player **mời nhau**
vào Match 1v1. Đối thủ máy không phải Player. Nên đây **không** phải câu hỏi
"có làm tính năng đó không" mà là câu hỏi "**destination có đổi không**" — và
theo `wayfinder`, ruling scope là việc của người chủ map, không phải của một
phiên làm việc.

Ba hình dạng có thể, chi phí rất khác nhau:

- **(a) Không.** Destination giữ nguyên. Đối thủ máy nằm ngoài effort này; nếu
  muốn thì mở một effort mới sau.
- **(b) Chỉ trong Practice**, như một chế độ luyện tập **không phải Match**.
  `CONTEXT.md` phải sinh một khái niệm thứ ba (ví dụ *Solo Run*) và nói rõ nó
  **không** là Match, **không** vào lịch sử đấu, **không** chạm Elo.
- **(c) Có, kể cả Ranked.** Destination phải sửa, `CONTEXT.md` phải sửa hai thuật
  ngữ nền, và một phần của #2 và #4 mất hiệu lực (danh sách chính xác ở **D.5**).

➡️ **Khuyến nghị: (a) ở effort này** — và nếu thèm nhánh (4) thì là **(b)**, không
bao giờ **(c)** trong cùng một map.

**Vì sao.** Ba lý do độc lập.

1. **(c) không giải được bài toán mà #25 tồn tại để giải.** Câu hỏi của ticket là
   "mô hình đối thủ chịu được **hai account tự đấu** tới mức nào". Đối thủ máy
   không loại bỏ kịch bản đó — nó **thêm một** nguồn Elo. Nếu bot cho Elo thì
   người ta farm bot; nếu bot **không** cho Elo thì Ranked vẫn phải là người-đấu-
   người và ta vẫn đứng nguyên chỗ cũ. Nhánh (4) **né** câu hỏi chứ không trả lời.
2. **Giá của (c) đã đo được và nó lớn** — xem **D.5**: nó vô hiệu hoá phần
   ready-hai-chiều và ghế-hai-người của #4, phần đối xứng-đồng-thuận của #2, và
   mở lại bài toán ordering của #10 §5.3 nếu một người đấu nhiều bot song song.
3. **(b) rẻ và không vướng gì** — Practice **đã** không chạm Elo (`CONTEXT.md`),
   nên một chế độ luyện tập với bot không phá bất biến nào. Nó vẫn là hành vi
   scoping, nhưng là loại **cộng thêm**, không phải loại **viết lại**.

**Cạm bẫy phải nói ra.** (b) nghe rất rẻ, nhưng nó **vẫn** kéo `CONTEXT.md`: nếu
gọi nó là "Practice Match" thì định nghĩa **Match** ("exactly two Players") sai
ngay; nếu gọi tên khác thì phải định nghĩa tên đó. Không có đường "cứ làm rồi
tính" mà không đụng mô hình miền.

**Ai tiêu thụ:** map #1 (destination + Out of scope), `CONTEXT.md`, và — nếu chọn
(c) — **#2 và #4 phải mở lại một phần**, xem D.5.

---

### Q1 — Ranked Match dùng mô hình đối thủ nào?

Đây là câu hỏi của ticket. Bốn nhánh, nhưng chỉ **hai** thực sự còn mở sau phần A:
(3) đã đóng bằng scope **và** thực tế (dữ kiện 4), (4) chuyển thành Q6.

- **(1) Giữ invite head-to-head** như #2 đã chốt, và chấp nhận rủi ro tự đấu ở
  một mức được ghi rõ.
- **(2) Rating theo performance cá nhân**, cần một thang độ khó cho từng Puzzle.

➡️ **Khuyến nghị: (1).**

**Vì sao.** Bốn lý do độc lập, xếp theo sức nặng.

1. **(2) thiếu một dữ kiện mà không research nào lấy được trước launch.** Chuẩn
   hoá theo độ khó chỉ đáng làm nếu phương sai do Puzzle **đáng kể so với** phương
   sai do người chơi. Ta biết vế đầu: **sd = 1,66 lần mua = 8,3 điểm** trên thang
   100, và **87,24%** Puzzle nằm gọn trong `[10, 14]` (A.6, tính lại từ histogram
   của #6). Vế sau **không tồn tại** — chưa có người chơi nào, và map ghi rõ
   telemetry cân bằng game còn nằm ở *Not yet specified*. Chọn (2) hôm nay là
   **mua một cơ chế để sửa một độ lệch chưa ai đo**.
2. **(2) đắt hơn nhiều so với "cần một thang độ khó".** Thang đó thực ra **rẻ**:
   một lượt dựng cây ~10 giây gán độ sâu cho cả 465.120 secret, bảng tra ~454 KB
   (A.6). Cái đắt là ba thứ khác: nhãn của thang là **HEURISTIC** và **dịch chuyển
   theo luật phá hoà** (30/128 cấu hình cho 16, 88/128 cho 17, 10/128 cho 18); đưa
   thang vào ruleset là **bump version** ⇒ **R-K-04** cắt lịch sử; và bỏ transfer
   thì **#10 §1.3, §4.1, §4.2, §5.3 không còn áp dụng** — bốn mục nền của map phải
   viết lại. Đó mới là research thật sự.
3. **Phần thưởng của boosting ở MVP gần bằng không.** Leaderboard, spectator,
   season đều **out of scope**; rating chỉ đọc ở **lịch sử cá nhân** (#4 Q7).
   Một rating bị bơm không được trưng ra đâu cả. Đây là lý do mạnh nhất để (1)
   chịu được — và nó **phụ thuộc C-Q4**: nếu rating hiện trong phòng chờ thì lập
   luận này yếu đi đáng kể.
4. **(1) là thứ #2 và #4 đã xây quanh.** Chọn (1) là **không** mở lại gì; chọn
   (2) mở lại định nghĩa **Ranked Match** trong `CONTEXT.md` (A.7) và toàn bộ
   phân tích Elo. Ở một map mà nửa dưới đang chờ đúng ticket này, chi phí mở lại
   là chi phí thật.

**Đánh đổi phải nói ra, và nó không nhỏ.** Chọn (1) là **chấp nhận** rằng hai
account do một người điều khiển có thể chuyển Elo cho nhau, rằng #4 vừa làm việc
đó **thoải mái hơn** (multi-tab là ca thường ngày — A.3), và rằng ở D.1 một người
kiên nhẫn tới 1500 điểm trong **111 trận với 23 donor**, hoặc **869 trận với một
donor duy nhất**. Không control nào ở MVP chặn được điều đó; cùng lắm là làm nó
chậm hơn. Câu C-Q3 hỏi ta chấp nhận mức nào, chứ không hỏi ta chặn kiểu gì.

**Ai tiêu thụ:** **#15** (đây là đầu vào lớn nhất của nó — "Elo đang đo cái gì"),
#14 (signal nào phải giữ), #12 (threat acceptance), `CONTEXT.md`, map #1.

---

### Q2 — Rating Ranked là tuyên bố về cái gì, và so sánh được trong phạm vi nào?

#10 §4.1 nói một câu mà cả map chưa ai đối diện: trong graph mà node là Player và
edge là rated Match, **dữ liệu trong một connected component không chứa bằng
chứng** để đặt component đó cao/thấp hơn một component không nối chéo. Baseline
1000 chỉ là **prior/policy**. Mà pool invite-only ở MVP **chính là** một tập
component nhỏ, phần lớn rời rạc: bạn bè mời nhau.

Ba cách phát biểu:

- **(a) Rating là tuyên bố toàn cục** — "1350 mạnh hơn 1200" bất kể hai người có
  đường nối nào.
- **(b) Rating là tuyên bố trong phạm vi những người bạn thực sự đã đấu** (và
  những người họ đã đấu), và sản phẩm **nói thẳng** điều đó.
- **(c) Rating là một con số cá nhân**, không tuyên bố gì, chỉ để nhìn lịch sử
  của chính mình.

➡️ **Khuyến nghị: (b).**

**Vì sao.** (a) là một tuyên bố mà **model không đỡ được** — #10 §4.1 nói thẳng,
và nó không phải ý kiến mà là tính chất của Bradley-Terry trên graph rời rạc.
Phát biểu (a) rồi sau này thêm matchmaking để "sửa" là làm ngược: tuyên bố trước,
bằng chứng sau. (c) thì vứt đi phần có thật: **bên trong** một component, rating
**đúng là** evidence về chênh lệch (§4.1, câu thứ hai), và đó chính là thứ hai
người bạn muốn biết. (b) giữ đúng phần model đỡ được và không hứa phần nó không
đỡ được — và nó là câu **rẻ nhất** để nói, vì không có leaderboard nào để mâu
thuẫn với nó.

**Nó cũng đổi cách đọc C-Q3.** Dưới (b), "bơm Elo" làm hỏng một tuyên bố **hẹp**,
nên thiệt hại thật sự nhỏ hơn ta tưởng. Dưới (a), cùng hành vi đó làm hỏng một
tuyên bố **rộng**, và khi đó control cấu trúc đáng giá hơn nhiều.

**Ai tiêu thụ:** #15 (policy), **#17** (đây là một phần của launch posture — nói
gì với người chơi), #13 (chữ trên màn hình), `CONTEXT.md` (C-Q9).

---

### Q3 — Mức chấp nhận rủi ro tự đấu: chấp nhận, chặn cấu trúc, hay phát hiện sau?

#10 §4.3 đưa 8 control ứng viên và nói thẳng: **"không có nguồn nào chứng minh
một ngưỡng lặp cụ thể là tối ưu"**. Nên mọi con số ở đây là **policy**, không
phải kết quả. Bốn tư thế:

- **(a) Chấp nhận và ghi thành thật.** Không control mới ngoài những gì #2 đã có.
- **(b) Chấp nhận + một control cấu trúc** (cap theo cặp trong một window, hoặc
  giảm K theo số lần gặp).
- **(c) Phát hiện sau + correction.**
- **(d) Chấp nhận bây giờ, nhưng **giữ signal** để phát hiện về sau.**

➡️ **Khuyến nghị: (a) + (d).** Cụ thể: không thêm control chặn nào ở MVP, nhưng
**chốt ngay** danh sách signal phải lưu, và giao nó cho #14 như một ràng buộc
retention.

**Vì sao.**

1. **(c) không có người tiêu thụ.** Moderation platform **out of scope**;
   #4 chốt **không có tiến trình nền** nào (`EXPIRED` là trạng thái được quan
   sát); #2 chốt **zero email**, nên không có kênh nào báo cho người bị flag.
   Một cơ chế phát hiện mà không có ai xử lý và không có cách thông báo là chi
   phí thuần.
2. **(b) có một tác dụng phụ ngược dấu, và #10 §4.2 đã cảnh báo:** "**nhiều donor
   mới tránh phần lớn hiệu ứng diminishing**". D.1 đo được: farm **một** donor
   tới 1500 cần **869 trận**; đổi donor mỗi 5 trận chỉ cần **111 trận với 23
   donor**. Cap theo cặp **đẩy** kẻ tấn công từ đường tự-giới-hạn sang đường
   **không** tự giới hạn — trừ khi chi phí một donor mới (một account Google) đủ
   cao, mà #2 Q10 đã nói là **không**. Control này có thể làm mọi thứ **tệ hơn**.
3. **(b) còn đánh vào người dùng thật trước.** #10 §4.1: chơi lại nhiều lần cùng
   một cặp **không tự nó là abuse**, và ở pool invite-only thì đó là **ca thường
   ngày**. False-positive budget ở đây gần như chắc chắn âm.
4. **(d) là phần thực sự khó đảo.** Không lưu signal hôm nay thì **vĩnh viễn**
   không phân tích được giai đoạn đầu. Lưu thì tốn một dòng schema. Bất đối xứng
   rõ ràng. #10 §4.3 đã liệt kê sẵn: tỷ trọng Match theo pair, chuỗi outcome một
   chiều, duration bất thường, tỷ lệ forfeit/timeout, account age, opponent
   diversity, graph donor→recipient. **IP/device fingerprint thì KHÔNG** — §4.3
   nói rõ nó vượt phạm vi và cần một quyết định privacy riêng (#14).

**Ràng buộc kiến trúc mà mọi lựa chọn phải qua:** #4 chốt Match Start là **một
transaction duy nhất** và R-T-08 cấm huỷ Match sau đó. Nên control **chặn** chỉ
tồn tại được ở **admission**; không có "phát hiện rồi huỷ trận". Và #4 chốt mọi
bất biến phải do **constraint** giữ vì Vercel API không phải trust boundary — mà
cap-theo-cặp-trong-window **không** biểu diễn được bằng unique index (nó là một
`COUNT` trên khoảng thời gian), nên nó sẽ là loại bảo vệ **yếu hơn** mọi bất biến
khác của hệ thống. Đó là chi phí thật của (b), ngoài chi phí ở lý do 2 và 3.

**Ai tiêu thụ:** **#12** (threat acceptance — đây là đầu vào trực tiếp), **#14**
(retention của signal, quyết định khó đảo), #15 (con số cuối nếu chọn (b)),
#17 (nói gì công khai).

---

### Q4 — Rating hiện ở đâu, và #25 có đặt ràng buộc lên #15 về việc đó không?

**Cơ chế hiển thị rating thuộc #15** — #4 đã ghi rõ như vậy. Câu này **không**
định lấn sân; nó hỏi #25 có muốn **giao một ràng buộc** cho #15 hay không, vì
câu trả lời làm đổi sức nặng của C-Q1 lý do 3 và của C-Q3.

Ba mức phơi bày:

- **(a) Chỉ trong lịch sử cá nhân.** Không ai thấy rating của ai.
- **(b) Hiện trong phòng chờ**, trước khi bấm Ready.
- **(c) Một bề mặt công khai nào đó.** — ✱ đã đóng: leaderboard **out of scope**.

➡️ **Khuyến nghị: #25 giao cho #15 một ràng buộc dạng "nếu-thì", không chốt thay:**
*nếu #15 chọn (b) thì lập luận "phần thưởng boosting ≈ 0" của #25 mất hiệu lực và
#15 phải bù bằng một control khác.*

**Vì sao.** #4 Q3.3 đã dựng sẵn cái bẫy và ghi lại: owner **đóng được room khi đã
đủ hai người nhưng chưa start**, nên ở room Ranked owner **nhìn thấy tag đối thủ
rồi mới quyết định chơi hay không**. Thêm rating vào màn đó là biến một quyền
lifecycle vô hại thành **bộ lọc chọn đối thủ có lợi** — và nó rẻ: mở room, xem
rating, đóng, mở lại. #4 nói đúng rằng đây **không** phải lý do bác quyền đóng
room (người join vốn đã có quyền tương đương), nhưng nó **là** lý do #25 phải
giao ràng buộc thay vì im lặng.

Chiều ngược cũng phải nói: **(a) làm người chơi mù**. Không thấy rating đối thủ
thì không biết trận này có đáng không — mà đó lại chính là điều làm Elo có ý
nghĩa với người chơi. Đây là đánh đổi thật, không phải lựa chọn hiển nhiên.

**Ai tiêu thụ:** **#15** (nó sở hữu quyết định), #13 (màn phòng chờ), #17.

---

### Q5 — Điều kiện vào Ranked có đổi không?

#2 Q10 chốt: **(i) có identity Google** và **(ii) đã hoàn tất ≥ 1 Practice Match**
(terminal bất kỳ trừ `FORFEITED`). #2 ghi thẳng rằng **(ii) gần như không tăng chi
phí Sybil** và giá trị thật của nó là **onboarding**. Câu hỏi: #25 có đổi gì
không?

- **(a) Giữ nguyên, không thêm gì.**
- **(b) Thêm một điều kiện** (tuổi account, số Practice, opponent diversity…).
- **(c) Bỏ (ii).**

➡️ **Khuyến nghị: (a).**

**Vì sao.** #2 đã bác **tuổi account** ("trong beta invite-only, friction thời
gian đánh vào người dùng thật nặng hơn kẻ tấn công — kẻ tấn công chỉ cần chờ") và
**số điện thoại** (PII mới, SMS quota không có trong stack zero-cost, thêm một
trục privacy cho #14). Cả hai lý do vẫn nguyên giá trị. **Opponent diversity** thì
#10 §4.3 cảnh báo trực tiếp: nó "có thể khiến user hợp pháp provisional rất lâu"
— ở một pool mà thành phần điển hình là hai người bạn, đó gần như là chắc chắn.
Nâng số Practice từ 1 lên `N` chỉ nhân chi phí donor với `N × 15 giây` (dữ kiện 2
của #25) — vô nghĩa trước một người chấp nhận bỏ ra 30 phút.

⇒ Không có đòn bẩy nào ở đây chưa được kéo. Hàng rào Sybil thật là **(i)**, và giá
của nó là **một account Google mỗi donor** — D.1 định lượng: tới 1500 điểm cần
**23** account Google theo đường nhanh nhất.

**Cạm bẫy phải tránh:** đừng giữ (ii) rồi **ghi vào tài liệu như một biện pháp
chống Sybil**. #2 đã nói rõ nó không phải. Giữ nó **vì onboarding** thì đúng; giữ
nó vì bảo mật thì là thừa kế một tiền đề sai — đúng cái bẫy đã xuất hiện bốn lần
trên map này.

**Ai tiêu thụ:** #12, #15 (provisional), #13 (màn onboarding).

---

### Q7 — #25 có cấm #15 thêm số hạng margin vào Elo không?

Dữ kiện 3 của #25 nói: chia sẻ Clue **không** cho thêm Elo — nhưng câu đó có
**tiền đề**: `K=32` **không xét margin**. Nếu #15 thêm một số hạng margin (ví dụ
"thắng cách biệt 40 Score thì transfer nhiều hơn") thì **Score đổi được transfer**,
và lỗ chia sẻ Clue **biến thành lỗ Elo**. Ticket #25 đã ghi: *"nếu #15 định thêm
margin thì phải quay lại đọc dòng này"*.

- **(a) Cấm margin** ở ruleset/policy.
- **(b) Không cấm, nhưng ghi một ràng buộc có điều kiện** cho #15.
- **(c) Im lặng**, để #15 tự tìm ra.

➡️ **Khuyến nghị: (b).**

**Vì sao.** (a) là lấn sân: margin là **policy Elo**, và R-K-02 cho thấy Elo
**không nằm trong ruleset** (bảng 8 tham số configurable không có tham số Elo
nào) — nên nó thuộc #15 một cách rõ ràng. (c) là chính xác cái bẫy mà map này đã
vấp **bốn lần**: bê một con số/kết luận sang ticket sau **mà bỏ mất tiền đề của
nó**. Dữ kiện 3 rất dễ bị đọc thành "chia sẻ Clue vô hại" — nó **không** vô hại;
nó vô hại **dưới một điều kiện cụ thể**.

Câu ràng buộc nên đọc được như một mệnh đề kiểm chứng được, ví dụ: *"Nếu chính
sách Elo đưa vào bất kỳ số hạng nào phụ thuộc Score hoặc Solve Time, thì R-P-13
(hai Player cùng một Puzzle) trở thành một bề mặt chuyển giá trị giữa hai account,
và #15 MUST xử lý nó trong cùng quyết định."*

**Ai tiêu thụ:** **#15** (trực tiếp), #12 (nếu margin vào thì bề mặt threat đổi).

---

### Q8 — Cap rematch: giữ "5 mỗi room", hay đổi sang cap theo cặp trong một cửa sổ?

**Đây là câu mà dossier này tồn tại để bắt.** #2 Q11.4 chốt cap **5 cho room
Ranked**, và ghi lý do là "**không tạo ra một đường rematch vô hạn**". Nhưng:

- Control mà #10 §4.3 mô tả là *"cap số rated Match cho mỗi **unordered pair**
  trong một **window**"* — **theo cặp**, không theo room.
- #4 Q12 chốt room chết **10 phút** sau Match, và **owner đóng sớm được** bất cứ
  lúc nào room không còn Match chưa terminal.
- ⇒ cùng một cặp account chỉ cần **đóng room, mở room mới** là có thêm 6 trận.
  Giá danh nghĩa ba command (`CLOSE_ROOM`, `CREATE_ROOM`, `JOIN_ROOM`), nhưng
  **chi phí biên thật là một** — hai command kia thay chỗ cho
  `PROPOSE_REMATCH` + `ACCEPT_REMATCH` của một rematch. Trên 869 trận: **+2,4%**.

**Cap 5 là ma sát, không phải chặn trên.** Xem D.3 cho phép tính đầy đủ.

Bốn hướng:

- **(a) Giữ nguyên "5 mỗi room"**, và **sửa lý do** trong tài liệu: nó là ma sát
  UX, không phải chặn Elo.
- **(b) Đổi sang cap theo cặp trong một window** (ví dụ `N` Ranked Match mỗi cặp
  mỗi 24 giờ).
- **(c) Bỏ cap hẳn** và dựa vào diminishing returns của chính Elo.
- **(d) Giảm K theo số lần gặp** (#10 §4.3, dòng "vẫn dùng cùng `+T/−T`").

➡️ **Khuyến nghị: (a), và giao con số cho #15 kèm ghi chú rằng nó KHÔNG phải một
chặn trên.** Nếu người chủ map muốn một chặn trên thật thì là **(d)**, không phải
(b).

**Vì sao.**

1. **(b) đắt về kiến trúc hơn vẻ ngoài.** #4 chốt mọi bất biến do **partial unique
   index** giữ, vì Vercel API **không phải trust boundary**. Cap theo cặp trong
   window **không** là một unique index — nó là `COUNT(*)` trên một khoảng thời
   gian, chạy dưới lock trong transaction Match Start. Đó là **loại bảo vệ yếu
   nhất** trong toàn hệ thống, cho một control mà #10 nói **không có ngưỡng tối
   ưu nào được chứng minh**.
2. **(b) đẩy kẻ tấn công sang Sybil** — #10 §4.2, và D.1 đo được: cap theo cặp làm
   đường "một donor" chậm lại, nhưng đường "23 donor" thì **nhanh hơn 7,8 lần**
   và cap không chạm tới nó. Trao đổi sai chiều.
3. **(b) đánh vào ca thường ngày.** Hai người bạn đấu nhau 20 trận một tối là
   **chính xác** hành vi mà sản phẩm này muốn có, và #10 §4.1 nói nó **không tự
   nó là abuse**.
4. **(d) là control duy nhất trong bảng §4.3 vừa giữ zero-sum vừa giảm lợi ích
   farm** mà **không** từ chối trận nào — nên nó không có false positive theo
   nghĩa "người dùng thật bị chặn". Giá của nó (#10 ghi): rating phụ thuộc
   **pair history**, formula phức tạp hơn, và version hoá khó hơn.
5. **(c) không đủ**: D.1 cho thấy diminishing returns **có thật nhưng chậm** —
   869 trận vẫn tới 1500 với **một** donor duy nhất.

**Bẫy đọc số phải nói ra.** Con số **5** của #2 hợp lệ **cho mục đích của #2** —
không tạo một nút "rematch" bấm mãi không hết trong một room. Nó **chưa bao giờ**
là một chặn trên Elo, và #15 sẽ thừa kế nó **kèm lý do sai** nếu #25 không sửa
dòng đó ở đây.

**Ai tiêu thụ:** **#15** (sở hữu con số cuối), #14 (nếu (b): phải đếm trên Match
row chứ **không** trên settlement — vì #4 cho phép Match bỏ rơi nằm `ACTIVE` hàng
tuần, nên đếm settlement sẽ **đếm thiếu**), #12.

---

### Q9 — `CONTEXT.md` có thiếu thuật ngữ nào mà #25 buộc phải thêm không?

Hai phát hiện từ phần A.7:

1. **`CONTEXT.md` cấm dùng "Elo"/"rating" làm từ đồng nghĩa của Score
   (`Score._Avoid_`), nhưng chưa bao giờ định nghĩa Elo Rating.** Đây **đúng dạng**
   lỗ hổng mà #4 đã tìm ra với Room: repo có một từ **bị cấm** mà không có từ
   **thay thế**. #25 là ticket đầu tiên mà nó gây phiền thật, vì cả bốn nhánh đều
   là câu hỏi "rating đo cái gì".
2. **Định nghĩa `Ranked Match` hiện tại** — *"A Match whose final **result**
   changes both Players' Elo ratings"* — **chỉ đúng dưới nhánh (1)**. Dưới nhánh
   (2), thứ đổi rating không phải *result* mà là màn trình diễn của từng người.

➡️ **Khuyến nghị: thêm một thuật ngữ — `Elo Rating` — và câu chữ của nó lấy thẳng
từ câu trả lời C-Q2** (phạm vi so sánh). Sửa `Ranked Match` **chỉ khi** C-Q1 chọn
(2). **Không** đụng `Match` và `Player` trừ khi C-Q6 chọn (c).

**Vì sao.** Thuật ngữ chỉ nên vào glossary khi nó đã có nghĩa chốt được — và
`Elo Rating` sẽ có nghĩa đó ngay sau C-Q2. Ngược lại, sửa `Match`/`Player` là
hành vi **theo sau** một quyết định scoping, không phải một bước độc lập; làm
trước là tự cho phép mình cái quyền mà Q6 nói là của người chủ map.

**Ai tiêu thụ:** `CONTEXT.md`, #15, #14, #13.

---

## D. Dữ kiện đã tra sẵn

Mọi con số ở đây **tự tính lại trong phiên này**, không chép từ ticket trước.
Nơi nào khớp với nguồn thì ghi rõ là đã đối chiếu.

### D.1 Kinh tế của việc bơm Elo — chi phí thật của một điểm rating

Đầu vào: baseline **1000**, **K=32**, không margin (Notes map #1);
`E_A = 1/(1 + 10^((R_B−R_A)/400))`, `R_A' = R_A + K(1 − E_A)`.

**Bảng 1 — farm MỘT donor duy nhất, A luôn thắng:**

| Sau `n` trận | Rating A | Rating donor | Transfer trận đó |
| ---: | ---: | ---: | ---: |
| 1 | 1016,000 | 984,000 | 16,000 |
| 5 | 1066,831 | 933,169 | 11,030 |
| **10** | **1110,473** | **889,527** | 7,489 |
| 20 | 1165,435 | 834,565 | 4,330 |
| 40 | 1226,095 | 773,905 | 2,260 |

Dòng `n=10` khớp **chính xác** #10 §4.2 (`1110.4725/889.5275`, chuyển `110.47`
điểm) — đã đối chiếu, không chép.

**Bảng 2 — chi phí tới rating 1500 theo ba chiến lược:**

| Chiến lược | Số trận | Số donor (account Google) |
| --- | ---: | ---: |
| Một donor duy nhất | **869** | 1 |
| Donor mới mỗi 5 trận | **111** | **23** |
| Donor mới mỗi trận | 106 | 106 |

⇒ **Đổi donor hiệu quả gấp ~7,8 lần** so với farm một donor. Đây chính là câu
#10 §4.2 nói bằng lời ("nhiều donor mới tránh phần lớn hiệu ứng diminishing"),
nay có số. **Hệ quả cho C-Q8:** một cap theo cặp làm cột 1 chậm lại và **không
chạm** cột 2 — nó đẩy kẻ tấn công sang đúng đường tệ hơn.

**Chi phí thời gian và hạ tầng của một trận farm.** Đường rẻ nhất là donor
`FORFEIT` ngay sau Match Start (R-T-05.3 cho winner **đúng cùng lượng Elo** như
Solve — dữ kiện 3 của #25). **Nhưng `FORFEIT` của donor một mình KHÔNG kết thúc
Match**: R-T-11 đòi **cả hai** Player terminal. Nên người bơm cũng phải tự đưa
mình vào terminal, và đường nhanh nhất là **hai `VERIFY` sai** → `ELIMINATED`
(R-V-08 khoá 10 giây giữa hai lần — đây chính là nguồn của con số "~15 giây mỗi
trận" ở dữ kiện 2 của #25). `FORFEITED` xếp **dưới** `ELIMINATED` (R-T-04) nên
người bơm vẫn thắng theo R-T-05.3.

Command của một trận, **đúng bảy**, cho cả trận đầu lẫn rematch (finalization là
**hệ quả**, không phải command — #4 Q8):

```text
trận đầu trong room : CREATE_ROOM, JOIN_ROOM, READY x2, FORFEIT, VERIFY x2   = 7
rematch             : PROPOSE_REMATCH, ACCEPT_REMATCH, READY x2, FORFEIT, VERIFY x2 = 7
mỗi lần thay room   : + CLOSE_ROOM                                            = 1

869 trận (một donor, cap 5 => 6 trận/room => 145 room)
    = 869 x 7 + 145 = 6.228 command = 1,25% ngân sách 500.000 invocation
111 trận (23 donor => 23 room, cộng 11 trận Practice cho eligibility của donor)
    = 111 x 7 + 22 + 77  ≈   876 command = 0,18% ngân sách
ở 15 giây/trận: 869 trận ≈ 3,6 giờ  |  111 trận ≈ 28 phút
```

**Ba kết luận đáng nói ra:**

1. **Ngân sách zero-cost KHÔNG chặn được việc farm.** Toàn bộ chiến dịch tốn
   **1,25%** ngân sách invocation — và đó là đường **đắt nhất** trong hai đường;
   đường 23 donor chỉ tốn **0,18%**. Đừng nhầm ràng buộc chi phí thành một control.
2. **Rate limit của #8 cũng không chặn.** 20 command/phút/actor: người bơm phát
   **4** command mỗi trận (`CREATE_ROOM`/`PROPOSE_REMATCH`, `READY`, `VERIFY` ×2)
   ⇒ trần **5 trận/phút**; donor phát 3 ⇒ trần 6,7 trận/phút. Biên mỏng hơn vẻ
   ngoài, nhưng vẫn **xa trên** tốc độ một người thật bấm được, nên kết luận
   không đổi.
3. **Thứ thật sự làm chậm là cap của #2**: 1 room + 1 Match chưa terminal, giữ
   bằng **partial unique index** (#4 Q10). Nó **serialize** hoàn toàn: một trận
   một lúc, không song song hoá được. Con số 3,6 giờ ở trên **là nhờ nó**. Đây là
   control chống-farm hiệu quả nhất đang có, và nó tồn tại vì một lý do khác hẳn.

### D.2 Phân phối độ khó Puzzle — nền của nhánh (2)

Nguồn histogram: #6 §5.2 (greedy minimax, câu mở đầu `Q3:B`, chạy trên toàn bộ
465.120 secret). Thống kê dưới đây **tính lại từ histogram**, không chép.

| Đại lượng | Giá trị |
| --- | --- |
| N | 465.120 |
| Trung bình | **11,837** lần mua (#6 ghi 11,84 — khớp) |
| **Độ lệch chuẩn** | **1,662** lần mua = **8,3 điểm Score** |
| Trung vị / p99 / worst | 12 / 15 / 16 (khớp R-P-16) |
| `[10, 14]` | **87,24%** |
| `[11, 13]` | **62,59%** |
| `≤ 8` | 2,71% |
| `≥ 15` | 3,97% |

Chi phí sản xuất thang: một lượt dựng cây ≈ **10 giây**
(`bounds_adaptive_search.py sweep` = 128 lượt/~21 phút), bảng tra 465.120 dòng
≈ **454 KB**. Nhãn: **HEURISTIC** — 30/128 cấu hình greedy cho worst case 16,
88/128 cho 17, 10/128 cho 18 (`clue-bounds/findings.md` §2.4). Cây tối ưu vẫn
nằm đâu đó trong **`[10, 16]`**.

### D.3 Cap rematch: theo ROOM ≠ theo CẶP

```text
#2 Q11.4     : cap 5,  đơn vị = ROOM Ranked,  lý do ghi = "không tạo đường rematch vô hạn"
#10 §4.3     : control  = "cap số rated Match cho mỗi UNORDERED PAIR trong một WINDOW"
#4  Q12      : room chết 10 phút sau Match; owner ĐÓNG SỚM ĐƯỢC khi room không còn
               Match chưa terminal
#2  Q7.4     : mã đã chết không tái dùng  ->  room mới cần mã mới, KHÔNG cản gì
#2  Q5       : 1 room đang mở mỗi account ->  phải đóng trước khi mở, KHÔNG cản gì

=> reset cap: CLOSE_ROOM + CREATE_ROOM + JOIN_ROOM, không chờ 10 phút
   nhưng CREATE_ROOM + JOIN_ROOM chỉ THAY CHỖ cho PROPOSE_REMATCH + ACCEPT_REMATCH
   mà một rematch vốn đã tốn  ->  chi phí biên thật chỉ là 1 CLOSE_ROOM
=> cap 5 theo room  ->  ma sát,  KHÔNG phải chặn trên
```

Định lượng, dùng đúng con số của D.1. "Cap 5 rematch" nghĩa là **6 trận mỗi room**
(một trận đầu + 5 rematch). Với 869 trận: **145 chu kỳ room** ⇒ **+145 `CLOSE_ROOM`**
trên nền 6.083 command, tức **+2,4%**. Chi phí biên của cả cái cap là **hai phần
trăm**, và không tốn giây nào.

Đây là con số nói lên tất cả: cap 5 không nâng giá đủ để đổi hành vi của bất kỳ
ai.

**Đây là bẫy "bê con số mà bỏ mất tiền đề", lần thứ năm trên map này.** Con số 5
đúng cho mục đích của #2. Nó **không** là chặn trên Elo, và #15 sẽ thừa kế nó kèm
lý do sai nếu #25 im lặng.

### D.4 Vị trí #25 trên đồ thị phụ thuộc — ĐÃ TRA LẠI TỪ TRACKER

Đọc bằng `gh api …/dependencies/blocked_by` và `…/blocking`, ngày 2026-08-24, sau
khi #4 đóng và sau khi wire #27:

```text
#25 blocked_by = 0   (frontier)
#25 blocking   = #15

chuỗi:  #25 -> #15 -> #14 -> {#3, #13}
        #13 -> #16 ;  #3 -> {#11, #7, #16} ;  #11 -> {#7, #16} ;  #7 -> #16

#15 blocked_by: #10 (closed), #4 (closed), #25 (OPEN)  -> #25 là blocker DUY NHẤT còn lại
#14 blocked_by: #2 (closed),  #4 (closed), #15 (OPEN)  -> #15 là blocker DUY NHẤT còn lại
```

⇒ **#25 chặn bắc cầu 7 ticket**: #15, #14, #3, #13, #11, #7, #16 — tức **mọi
ticket mở còn lại trừ #12, #17, #27**.

So sánh **cùng đơn vị bắc cầu** (không so bắc cầu với trực tiếp): #12, #17 và #27
mỗi cái chặn bắc cầu **4** ticket — tất cả đều đi qua #3 rồi toả ra #11, #7, #16.
Nên khoảng cách là **7 so với 4**, không phải "7 so với 1". Kết luận nút cổ chai
không đổi, nhưng đừng trích con số mà bỏ mất đơn vị của nó.

**#25 là nút cổ chai thật của nửa dưới map**, và đóng nó là hành động mở khoá lớn
nhất còn lại.

### D.5 Nhánh (4) vô hiệu hoá chính xác cái gì — PHÂN TÍCH, KHÔNG PHẢI ĐỀ XUẤT

Nếu người chủ map chọn nhánh (4) ở dạng **(c) có, kể cả Ranked**, đây là giá đã
biết của câu C-Q6.

**Đọc cho đúng: nhánh (4c) không XOÁ #2 và #4 — nó CHẺ ĐÔI chúng.** Nếu Ranked
đấu bot được **thêm vào bên cạnh** Ranked đấu người, mọi luật của #2 và #4 vẫn
đúng nguyên trên **đường người-đấu-người**. Cái phát sinh là: mỗi quyết định
lifecycle cần **một biến thể thứ hai** cho đường bot, và những quyết định **dựa
trên tính đối xứng giữa hai người** thì **không có** biến thể bot hiển nhiên —
phải nghĩ lại từ đầu chứ không phải chỉnh tham số. Bảng dưới đánh dấu đúng những
chỗ đó.

**Từ `CONTEXT.md`** — hai thuật ngữ nền phải viết lại: **Match** ("exactly two
Players"), **Player** ("an authenticated person"). Kéo theo **Ranked Match**,
**Seat** ("one of a Room's two places, held by a Player").

**Từ [#2](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2):**

| #2 chốt | Trên ĐƯỜNG BOT thì sao |
| --- | --- |
| Invite Code, TTL 30 phút, single-use, entropy 6 ký tự | **Không** — không có ai để mời |
| Q9 năm ca biên khi join (self-join, người thứ ba, mã sai) | **Không** — không có join |
| Q11 rematch cần **cả hai** đồng ý; cap 5 cho room Ranked | **Không** — bot luôn đồng ý; cap mất nghĩa |
| Q5 cap 1 room + 1 Match chưa terminal | **Một phần** — vẫn cần, nhưng lý do (fail closed trước quota) đổi |
| Q10 điều kiện Ranked (Google + ≥1 Practice) | **Một phần** — (ii) mất nghĩa nếu bot là đường vào Ranked |

**Từ [#4](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4):**

| #4 chốt | Trên ĐƯỜNG BOT thì sao |
| --- | --- |
| Q2 ready **hai chiều**; `READY` thứ hai kích hoạt start | **Không** — chỉ còn một người bấm |
| Q2b `started_at = commit + 3 giây` để **hai trình duyệt** bắt nhịp | **Không** — chỉ còn một trình duyệt |
| Q3 mất kết nối ở phòng chờ không nhả ghế; owner đóng room | **Không** — không có phòng chờ hai người |
| Q5 "hoạt động gần đây" của đối thủ | **Không** — bot luôn hoạt động |
| Q7/Q8 finalization khi **cả hai** terminal (R-T-11) | **Phải định nghĩa lại** — bot terminal lúc nào? |
| Q12 rematch cả hai đề nghị được | **Không** |
| Q4 multi-tab / multi-device trên một ghế | **Còn nguyên** — vẫn áp cho người thật |
| Q1, Q6, Q9, Q10, Q11, Q13, Q14 | **Còn nguyên** |

**Từ [#10](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10):** nếu bot
có rating thì bot là một node trong graph, và §4.1 nói **connectivity** là thứ
làm rating so sánh được — một bot đấu với tất cả mọi người sẽ là **hub nối toàn
bộ pool**, tức nó **giải** bài toán component rời rạc của C-Q2. Đó là lợi ích
thật, và là lý do duy nhất nhánh (4) hấp dẫn về mặt Elo. Nhưng §5.3 mở lại nếu một
người đấu **nhiều bot song song** — trừ khi cap 1 Match chưa terminal của #2 được
giữ nguyên cho cả bot.

**Đếm được, không ước lượng.** #4 chốt **15** quyết định (Q1–Q14 cộng Q2b). Bảng
trên phân loại đủ cả 15: **bảy** cần một biến thể riêng cho đường bot (Q2, Q2b,
Q3, Q5, Q7, Q8, Q12) và **tám** đứng nguyên (Q1, Q4, Q6, Q9, Q10, Q11, Q13, Q14).
Phía #2, **năm** quyết định cần xét lại.

Trong bảy cái phải làm lại, **bốn** cái — ready hai chiều (Q2), mốc đồng bộ 3 giây
(Q2b), rematch cần cả hai đồng ý (Q12, và #2 Q11), và finalization khi **cả hai**
terminal (Q8 / R-T-11) — **dựa thẳng vào việc có hai con người**. Chúng không có
biến thể bot mà chỉ có một thiết kế mới.

Đó là **hai ticket đã đóng** phải mở lại một phần. Theo `wayfinder`, việc đó không
phải "resolve thêm một ticket" mà là **vẽ lại một phần map đã đi qua** — và một
thuật ngữ nền của `CONTEXT.md` (**Match**, **Player**) đổi nghĩa theo.

---

## E. Để dành round-2

Những câu này **phụ thuộc câu trả lời round-1**:

1. **Con số cụ thể của control cấu trúc** — chỉ phát sinh nếu C-Q3 chọn (b) hoặc
   C-Q8 chọn (b)/(d). Con số cuối thuộc #15 dù thế nào.
2. **Provisional có cần không dưới mô hình đã chọn** — #10 §3.2 liệt kê 6 option
   và ba trong số đó **phá zero-sum**. Chỉ hỏi được sau C-Q1 và C-Q2.
3. **Danh sách signal chính xác phải lưu** — phụ thuộc C-Q3(d); hình dạng bảng
   thuộc #14.
4. **Câu chữ chính xác của định nghĩa `Elo Rating`** — phụ thuộc C-Q2.
5. **Nếu C-Q6 chọn (b)**: khái niệm thứ ba tên là gì, nó vào lịch sử đấu không,
   nó dùng pool Puzzle nào (R-P-09 hay R-P-10).
6. **Ticket research cho nhánh (2)** — chỉ phát sinh nếu C-Q1 chọn (2). Xem ghi
   chú ở cuối A.6: phần đắt **không** phải thang độ khó (rẻ, ~10 giây), mà là
   (i) phương sai phía người chơi — **không đo được trước launch** — và (ii) viết
   lại #10 §1.3/§4.1/§4.2/§5.3 khi bỏ zero-sum.

## F. #25 KHÔNG quyết định

| Vấn đề | Thuộc ticket |
| --- | --- |
| Con số cuối của mọi cap, `K`, provisional, draw settlement, correction, rating ledger, **và có hiện rating trong phòng chờ không** | [#15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| Schema, retention của signal collusion, PII, quyết định privacy về IP/device fingerprint | [#14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| Rate limit cụ thể, CAPTCHA, ban/appeal, threat model đầy đủ của Sybil | [#12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) |
| Nói gì với người chơi về mức bảo đảm của rating, nhãn beta | [#17](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17) |
| Màn phòng chờ, cách hiển thị tag/rating, UX của thông điệp từ chối | [#13](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| Cơ chế lưu/tính rating, transaction boundary | [#3](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3), [#14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| **Destination của map có đổi không** (nhánh 4) | **Người chủ map** — không ticket nào sở hữu việc này |

---

## Nguồn

- Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)
- [#25](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25) — body, sáu dữ kiện đã xác lập
- [#2 resolution comment](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2#issuecomment-5388396390) — 12 quyết định identity/invite
- [#4 resolution comment](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4#issuecomment-5388852395) — 15 quyết định lifecycle
- [#10](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10) + `docs/research/2026-08-22-elo-integrity.md` — §1.3, §3.2, §4.1, §4.2, §4.3, §5.3
- [#9](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9): `docs/plans/2026-08-23-issue-9-game-spec/game-spec.md` — R-T-04/05/06/08, R-K-01/02/04, R-P-09/10/13/16, R-S-11/12, R-V-08/09
- [#6](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6): `docs/plans/2026-08-22-issue-6-puzzle-fairness/findings.md` §5.2 + `docs/plans/2026-08-24-clue-bounds/findings.md` §2.4, §5
- [#8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8) + `docs/research/2026-08-22-zero-cost-vercel-architecture.md` — ngân sách invocation, rate limit
- `CONTEXT.md` (26 thuật ngữ, `e9f2cdf` trên `main`)
- `docs/plans/2026-08-24-issue-4-lifecycle/dossier.md` và `docs/plans/2026-08-24-issue-2-identity/dossier.md` — khuôn của tài liệu này
