# Launch Posture cho Production MVP

Posture ID: **`digitcode-launch-posture/1.0.0`**
Ticket: [Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)

Đây là artifact planning chốt **posture phát hành** của Production MVP: nhãn vận
hành, ranh giới thương mại, cách mở cửa, những gì được và không được nói với
Player, mặt support, và điều kiện nâng cấp trả phí. Nó không phải production
implementation, không thay đổi 95 luật của `digitcode-ruleset/1.0.0`, và không
tạo release criteria mới ngoài ba gate ở §9.

## 1. Nhãn vận hành

Production MVP được phát hành dưới đúng một posture, gọi là **Live Beta**:

- chi phí định kỳ **bằng 0**;
- **không** cam kết availability;
- **phi thương mại** hoàn toàn.

Ràng buộc zero-cost của destination được giữ nguyên; destination **không** bị vẽ
lại. [Nghiên cứu kiến trúc zero-cost tương thích Vercel](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8)
kết luận "không có tổ hợp managed free-tier nào chứng minh được production-grade
vô điều kiện dưới toàn bộ ràng buộc", và cho phép topology Vercel Hobby +
Supabase Free + Brevo Free SMTP "chỉ dưới nhãn vận hành **non-commercial live
beta, zero-cost, no SLA**". Artifact này nhận đúng điều kiện đó làm posture.

Hệ quả bắt buộc: không tài liệu, trang, thông báo hay mô tả store nào của MVP
được gọi bản phát hành này là production-grade, stable, generally available,
hay bất kỳ từ nào hàm ý mức bảo đảm vận hành. Xem danh sách cấm ở §7.

Ba hướng nới ràng buộc mà research nêu — custom domain + paid email baseline,
fixed paid hosting/database baseline, hoặc bỏ magic link chỉ giữ Google OAuth —
**không** được dùng trong Live Beta. Chúng chỉ vào cuộc qua §8.

## 2. Ranh giới phi thương mại

Vercel Hobby giới hạn **non-commercial personal use** ([issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8)).
Vi phạm không tạo hoá đơn — nó đặt cả project vào rủi ro bị thu hồi. Vì vendor
không định nghĩa chi tiết "commercial", posture này cắt ở mức không còn rìa mờ:

MVP **MUST NOT** có bất kỳ dòng tiền hay hoạt động quảng bá thu lợi nào, gồm và
không giới hạn ở:

- thanh toán, mua bán trong game, vật phẩm trả phí, gói đăng ký;
- quảng cáo dưới mọi hình thức, kể cả house ad;
- donation, tip, "buy me a coffee", gây quỹ;
- sponsor, logo tài trợ, nội dung được trả tiền;
- affiliate link, referral thưởng tiền;
- bán, cho thuê hoặc chia sẻ dữ liệu Player cho bên thứ ba vì lợi ích thương mại.

Không có ngoại lệ "thụ động". Một link donation không đổi lấy quyền lợi trong
game vẫn bị cấm, vì gate ở §9.1 yêu cầu **xác nhận** tính hợp lệ, và không thể
xác nhận một vùng vendor không định nghĩa.

Xuất hiện ý định thu lợi là **trigger nâng cấp** theo §8, không phải một ngoại lệ
của §2.

## 3. Hai stage mở cửa

Mở cửa có đúng hai stage, theo thứ tự, không rút gọn:

| Stage | Ai vào được | Điều kiện để rời stage |
| --- | --- | --- |
| **Canary** | invite-only | gate canary của [Chốt quality gate, zero-cost operations và release criteria](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16) đạt |
| **Open Beta** | đăng ký tự do, không giới hạn số Player | — |

Canary là bắt buộc vì [issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8)
ghi "Vercel cấm synthetic load testing ngoài Enterprise; capacity phải ramp bằng
invite-only canary, không được tuyên bố đã chứng minh". Không có đường đo capacity
nào khác ở chi phí 0, nên không có đường bỏ qua stage này.

Open Beta **MUST NOT** giới hạn số Player Identity bằng invite, whitelist hay cap
tuyệt đối. Phanh duy nhất là admission control theo quota mà
[Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12)
đã chốt: cảnh báo ở **40%**, **chặn admission Match mới ở 50%**, mở lại khi xuống
dưới **40%** projected 30-day usage.

Lý do không dùng cap theo đầu người: cap ấy không tương quan với thứ thực sự bị
giới hạn. Quota Vercel Hobby đếm invocation — "1.000.000 invocation/tháng", và
"Counts regardless of request success or failure" ([issue 27](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27)).
Một Player chơi liên tục tốn gấp nhiều lần một Player đã đăng ký rồi bỏ, nên cap
đầu người vừa chặn oan vừa không chặn đúng. Thêm nữa, Matchmaking Queue chỉ ghép
được người với người khi có đủ người cùng lúc; giữ invite-only suốt MVP sẽ làm
Queue hầu như luôn ghép Bot Opponent, làm rỗng chính tính năng mà
[Chốt mô hình đối thủ của Ranked Match](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25)
đưa vào destination.

Admission đóng là một **trạng thái vận hành bình thường** của Live Beta, không
phải sự cố. Nó phải được nói trước ở §7, không được để Player phát hiện bằng cách
bị từ chối.

## 4. Availability: không cam kết con số nào

MVP **MUST NOT** công bố bất kỳ con số availability, uptime, SLA, SLO, RTO hay
thời gian khôi phục nào cho Player.

Dữ kiện bắt buộc posture này:

- Supabase Free "có thể bị pause sau bảy ngày low activity"; restore là "thủ công
  — ba bước bấm nút trong Dashboard, **không có SLO restore**, cửa sổ restore **1
  năm**" ([issue 27](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27)).
- Danh sách chống pause chính thức chỉ có hai việc, **cả hai đều đến từ ngoài**:
  mở Dashboard, hoặc có request thật từ ứng dụng đã kết nối. Không có ngưỡng định
  lượng nào được vendor nêu ([issue 27](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27)).
- `pg_cron` nằm trong một vòng lặp đóng: "nó chỉ hoạt động trong đúng những khoảng
  thời gian mà hệ thống vốn đã khoẻ mạnh nhờ có người dùng thật"
  ([issue 27](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27)). Cơ
  chế tự cứu không cứu được lúc cần cứu.
- Vendor **không tuyên bố gì** về việc `pg_cron` có chạy khi project đã pause
  ([issue 27](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27)).
- "Free stack không có SLA/automatic backup" ([issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8)).

Vì thời gian **phát hiện** sự cố không có bảo đảm nào, mọi con số dạng "khôi phục
trong N giờ kể từ khi phát hiện" đều không đo được từ phía Player. Gate 10 của
research đặt mục tiêu "operator restore <= 30 phút", nhưng đó là số đo trong một
drill có chủ đích trên disposable project — nó là release criteria của
[issue 16](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16), **không**
phải lời hứa với Player, và MUST NOT được trình bày như một lời hứa.

Im lặng cũng bị cấm. Một web app không nói gì sẽ được Player giả định là luôn
online — đúng cái bẫy mà
[Chốt mức bảo đảm khi Player mất quyền truy cập](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34)
§5 đã cấm khi nó buộc phải nói thẳng rằng không có đường khôi phục. Nên posture là:
**nói thật, không kèm số** — xem fact F5 và F6 ở §7.

## 5. Cửa balance validation

[Chốt hàm hiệu chuẩn Ranked Rating thành Score mục tiêu](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30)
§9 giao cho ticket này việc quyết định validation status nào cho phép launch.

**Launch được phép khi toàn bộ 11 band ở `INSUFFICIENT_EVIDENCE`.**

Lý do là số học, không phải khoan nhượng. Status `VALIDATED` của một band đòi
Wilson 95% interval hai phía của decisive share nằm trọn trong `40%..60%`; ở
observed split đúng 50/50, **94** decisive Match là mẫu nhỏ nhất đạt được điều
đó, cho interval `[40,0927%, 59,9073%]` — `92` Match cho `[39,9898%, 60,0102%]`
và trượt. Trước launch, số Ranked Match giữa Player và Bot Opponent bằng **0**,
nên mọi band đều `INSUFFICIENT_EVIDENCE` và không band nào có thể là `VALIDATED`.
Đòi `VALIDATED` để launch là đòi một điều kiện chỉ có thể thoả sau launch.

Cũng vì thế, đòi "ít nhất một band `VALIDATED` trước khi mở Open Beta" là chặn
Open Beta vô thời hạn: canary chỉ cần "ít nhất 100 normal user commands"
([issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8) gate 11),
xa dưới 94 decisive Match trong **một** band đơn lẻ.

**`OUT_OF_TOLERANCE` không đóng Ranked Match.** Nó kích hoạt một Bot Calibration
Profile version mới, đúng phản ứng mà [issue 30](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30)
§9 đã chốt ("Không auto-tune profile đã publish; correction phải tạo profile
version mới qua review").

Hai lý do không đóng Ranked:

1. [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
   §7 chốt "Every finalized Ranked Match is rating-eligible. There is no void
   branch reachable from gameplay". Một trạng thái "Ranked tạm đóng" sẽ cần
   semantics mới cho Queue Entry đang chờ và Match đang chạy — thuộc quyền
   [Chốt Match lifecycle cho đường Matchmaking Queue](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/31),
   không phải ticket này.
2. Profile version mới **đã** là một hình thức tạm dừng, ở mức từng Player.

Hệ quả sắc, nêu thẳng để không thành ngạc nhiên: profile version mới đổi
`profile_id`, nên theo [issue 15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
§8 nó mở một **Rating Generation** mới, và "Ranked eligibility lapses until the
new measurement is complete". Mỗi Player phải đo lại **5** Practice Match đấu Bot
Opponent với `K_seed = 128`, re-seed từ Ranked Rating cuối của Generation cũ
(không phải từ 1000). Vậy "không đóng Ranked" nghĩa là hệ thống không có công tắc
đóng Ranked toàn cục, **không** nghĩa là Player chơi Ranked liên tục không gián
đoạn: từng Player vẫn mất eligibility cho tới khi đo lại xong. Điều này MUST được
nói trước ở §7 (fact F8).

## 6. Mặt support

MVP mở đúng **một** kênh liên hệ công khai, phạm vi hẹp.

Kênh này nhận **duy nhất** một loại việc: **appeal một sanction**. Nó tồn tại vì
[issue 12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) đã chốt
mọi Player phải có "một đường appeal riêng tư để con người review thủ công", và
sanction phải kèm reason category + case ID.

Kênh này **MUST** tuyên bố tường minh những việc nó không làm:

| Không làm được | Vì đã chốt ở |
| --- | --- |
| Khôi phục Player Identity đã mất quyền truy cập | [issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34) §5, §7 |
| Chuyển, gộp hoặc thay thế Player Identity bằng identity proof thủ công | [issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34) §7 |
| Khôi phục dữ liệu bằng database restore | [issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34) §7 |
| Đảo kết quả một Match đã finalized | [issue 15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) §11 |
| Hứa thời gian trả lời | posture này |

Ranh giới quan trọng nhất: **có** người xử lý appeal sanction, **không** có người
khôi phục identity. Một nhãn "Liên hệ / Hỗ trợ" chung sẽ bị đọc thành "có support
tức là cứu được tài khoản" — đúng điều [issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34)
§5 cấm: "It MUST NOT imply that contacting support can restore access". Vì thế
kênh MUST được đặt tên và mô tả theo phạm vi của nó, không đặt tên chung chung, và
MUST đi kèm bảng từ chối ở trên. Câu chữ cuối cùng thuộc
[Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13).

MVP **MUST NOT** mở kênh thứ hai cho "lỗi kỹ thuật". Một operator duy nhất không
duy trì được hai mặt, và kênh kỹ thuật là chính cái cửa Player sẽ dùng để xin lại
tài khoản, làm vỡ ranh giới vừa dựng.

Bản thân correction do anti-cheat sinh ra vẫn đi đường đã chốt ở
[issue 12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) — "con
người review trước mọi Ranked Rating correction hoặc ban" — và correction chỉ điều
chỉnh rating, "never reverses a Match result"
([issue 15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) §11).

## 7. Public notice: fact bắt buộc và tuyên bố bị cấm

MVP **MUST** có một trang notice công khai duy nhất, truy cập được **không** cần
đăng nhập, là launch gate §9.3. Trang này là vật thể kiểm tra được của posture.

Artifact này chốt **nội dung bắt buộc** và **giới hạn diễn đạt**. Nó **không**
chốt câu chữ tiếng Việt, không chốt vị trí hiển thị inline, không chốt thiết kế —
những phần đó thuộc [issue 13](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13),
đúng như [issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34)
§5 phân định.

### 7.1 Fact bắt buộc

Trang notice MUST nói đủ tám fact sau. Diễn đạt tự do, nội dung thì không.

| ID | Fact |
| --- | --- |
| F1 | Đây là **Live Beta** phi thương mại, không phải bản phát hành có bảo đảm vận hành. |
| F2 | Dịch vụ **không** cam kết availability; nó có thể dừng **nhiều ngày**, và việc khôi phục là **thủ công**. |
| F3 | Dịch vụ **không** có backup tự động do nhà cung cấp bảo đảm. |
| F4 | Khi lượng dùng chạm ngưỡng nội bộ, hệ thống **ngừng nhận Match mới** cho tới khi hạ xuống; đây là hành vi thiết kế, không phải lỗi. |
| F5 | Không có đường khôi phục Player Identity đã mất, và **không** có operator hay support nào làm được việc đó. |
| F6 | Liên kết một Linked Identity là **cách phòng ngừa**, không phải lời hứa khôi phục. |
| F7 | Kênh liên hệ duy nhất chỉ nhận appeal sanction; phạm vi và giới hạn của nó theo bảng ở §6. |
| F8 | Khi Rating Generation đổi, Ranked Rating cũ được **lưu trữ kèm nhãn Generation** và Player phải đo lại trước khi chơi Ranked tiếp; rating giữa hai Generation **không** so sánh được. |

F5 và F6 là diễn đạt ở mức launch của đúng những điều
[issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34) §5 đã bắt
buộc; artifact này không thêm bảo đảm nào, cũng không nới bảo đảm nào. F8 là hệ
quả của §5 cộng [issue 15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15)
§8.

### 7.2 Tuyên bố bị cấm

Trang notice, và mọi surface công khai khác của MVP, **MUST NOT** chứa:

| ID | Bị cấm | Vì |
| --- | --- | --- |
| B1 | "production-grade", "stable", "generally available", hay từ tương đương | [issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8): không được gọi là production-grade |
| B2 | Bất kỳ con số uptime, SLA, SLO, RTO, hay thời gian khôi phục | §4 |
| B3 | Ngụ ý rằng liên hệ support có thể lấy lại quyền truy cập | [issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34) §5 |
| B4 | Hứa dữ liệu được giữ vĩnh viễn, hoặc hứa một thời hạn lưu trữ cụ thể | [issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34) §3; retention thuộc [issue 14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| B5 | Hứa email magic link tới ngay hoặc tới chắc chắn | [issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34) §7; deliverability là launch gate của [issue 16](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16) |
| B6 | Tuyên bố capacity đã được kiểm chứng, hoặc số Player đồng thời chịu được | [issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8): "không được tuyên bố đã chứng minh" |
| B7 | Tuyên bố hệ thống ngăn được gian lận, external solver, hay thông đồng ngoài luồng | [issue 12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12): những điều này tường minh **không** được hứa |
| B8 | Tuyên bố Bot Opponent được chứng minh cân bằng, bất bại, hay rating hội tụ về trình độ thật | [issue 30](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30) §7, §9; ở launch mọi band là `INSUFFICIENT_EVIDENCE` |
| B9 | Bất kỳ lời mời thanh toán, donation, sponsor hay quảng cáo | §2 |
| B10 | So sánh Ranked Rating giữa hai Rating Generation | [issue 15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) §8 invariant 10 |

## 8. Trigger nâng cấp trả phí

Mặc định: **không** account nào có payment method, và **không** có đường
auto-upgrade hay paid-overage nào — đây là gate §9.2, giữ đúng tính chất
"pause thay vì phát sinh overage" của Vercel Hobby
([issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8)).

Posture này cam kết trước **một** ngưỡng. Chạm ngưỡng là nâng cấp, không phải mở
một cuộc thảo luận:

> **Trigger:** tổng số ngày mà admission Match mới ở trạng thái **đóng** đạt
> **>= 14 ngày** trong một **cửa sổ trượt 90 ngày**.

Ba lựa chọn thiết kế cần nói rõ lý do:

**Vì sao đo nhu cầu bị từ chối, không đo % quota.** Ngưỡng **50%** projected
30-day usage đã được [issue 12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12)
gán cho một phản ứng khác: chặn admission. Nếu trigger nâng cấp cũng đặt ở 50%
thì cùng một sự kiện kích hoạt hai phản ứng ngược nhau — một bên ngừng nhận
người, một bên chi tiền — và artifact tự mâu thuẫn ngay khi publish. Đo trạng thái
admission đóng nằm **sau** ngưỡng 50%, nên không chồng lệnh.

**Vì sao không đo ở một mốc quota cao hơn, ví dụ 80%.** Vì admission đã đóng ở
50%, usage rất khó bò tới 80%; trigger ấy gần như không bao giờ bắn, tức một luật
chết.

**Vì sao không đo bằng số lần bị pause.** Pause đến từ **ít** hoạt động
([issue 27](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27): pause
sau bảy ngày low activity). Trả tiền để chống pause là trả tiền đúng lúc game đang
vắng — sai hướng kinh tế.

**Vì sao là cửa sổ trượt, không phải chu kỳ 30 ngày.** Cửa sổ trượt không bị lách
bằng cách các đợt đóng rơi đúng hai bên biên chu kỳ billing, và nó bắt được kịch
bản thật nhất: free tier liên tục thiếu một chút, đóng vài ngày mỗi tuần, mãi mãi.

**Nguồn tiền.** Nâng cấp là **chi từ tiền của chủ dự án**, không phải từ doanh thu
game. §2 cấm mọi dòng tiền và §2 không có ngoại lệ nào được §8 mở ra. Trigger này
MUST NOT được đọc thành "đã tới lúc kiếm tiền": nếu MVP muốn có doanh thu thì
Vercel Hobby non-commercial personal use không còn hợp lệ, và đó là một quyết định
posture khác, phải quay lại HITL.

**Điều gì được nâng cấp.** Trigger chỉ nói *phải* nâng cấp, không chọn sẵn hướng.
Ba hướng hợp lệ là ba hướng research đã nêu: custom domain + paid email baseline;
fixed paid hosting/database baseline; hoặc bỏ email magic link chỉ giữ Google
OAuth. Research cảnh báo thẳng "Không nên đổi sang nhiều free vendor hơn để che một
ràng buộc chưa khả thi", nên thêm vendor free thứ tư **không** phải một hướng hợp
lệ. Chọn hướng nào là quyết định HITL tại thời điểm trigger bắn, và nó nới ràng
buộc zero-cost của destination — tức phải đi qua việc vẽ lại destination, không
phải qua artifact này.

**Ai đo.** Tín hiệu là trạng thái admission, đã tồn tại nhờ
[issue 12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12). Việc đo,
ghi và báo động thuộc [issue 16](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16);
artifact này chỉ đặt ngưỡng.

## 9. Launch gate thuộc ticket này

Ticket này nhận đúng **ba** gate — những gate mà không ticket nào khác sở hữu
được. Research của [issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8)
nêu 14 launch gate; gate 3 đến 14 là **release criteria** và thuộc
[issue 16](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16). Artifact
này **trỏ tới** chúng và MUST NOT chép lại danh sách, để không tạo bản sao thứ hai
của một danh sách sẽ đổi.

1. **Xác nhận non-commercial.** Xác nhận mục đích sử dụng thực tế vẫn hợp lệ với
   Vercel Hobby non-commercial personal-use restriction, và §2 được tuân thủ trên
   mọi surface. (research gate 1)
2. **Xác nhận không có đường chi tiền.** Xác nhận không account nào có payment
   method và không có auto-upgrade hay paid-overage path nào.
   (research gate 2)
3. **Trang notice tồn tại và đúng.** Trang notice công khai ở §7 truy cập được
   không cần đăng nhập, chứa đủ tám fact F1–F8, và không chứa bất kỳ tuyên bố
   B1–B10 nào. (mới, thuộc ticket này)

Gate nào thất bại thì quay lại HITL, không thêm workaround ngầm — giữ đúng nguyên
tắc của [issue 8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8).

## 10. Artifact này không quyết định

| Vấn đề | Ticket owner |
| --- | --- |
| Release criteria, quality gate, quota monitoring, backup/recovery drill, migration/rollback (research gate 3–14) | [Chốt quality gate, zero-cost operations và release criteria](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/16) |
| Câu chữ tiếng Việt, vị trí hiển thị, thiết kế của notice và mọi disclosure inline | [Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| License áp dụng, notices, attribution, branding phải đổi trước public deployment | [Chốt license và attribution policy](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/7) |
| Kiến trúc, managed services, transaction boundary, realtime transport, region | [Chọn kiến trúc web và managed services](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3) |
| Schema, Match history, retention, xoá dữ liệu, privacy | [Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| Event và aggregate để đo decisive share theo band | [Chốt telemetry tối thiểu để kiểm chứng cân bằng gameplay](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/35) |
| Semantics của Queue Entry và Match đang chạy khi cấu hình đổi | [Chốt Match lifecycle cho đường Matchmaking Queue](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/31) |
| Rating eligibility, settlement, saturation, Rating Generation | [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| Nội dung Bot Calibration Profile và ngưỡng tolerance | [Chốt hàm hiệu chuẩn Ranked Rating thành Score mục tiêu](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30) |
| Triển khai Production MVP | ngoài scope của map |

Đặc biệt: artifact này **không** tạo, nới hay thu hẹp bất kỳ bảo đảm nào với
Player. Mọi bảo đảm và mọi từ chối bảo đảm đã được
[issue 34](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34),
[issue 12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) và
[issue 15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) chốt;
ticket này chỉ quyết định chúng được **công bố** thế nào.

## 11. Canonical sources

- [`CONTEXT.md`](../../../CONTEXT.md): **Live Beta**, **Production MVP**,
  **Player Identity**, **Linked Identity**, **Rating Generation**,
  **Ranked Match**, **Bot Opponent**.
- [Nghiên cứu kiến trúc zero-cost tương thích Vercel](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8):
  nhãn non-commercial live beta / zero-cost / no SLA; non-commercial personal use;
  pause thay vì overage; cấm synthetic load testing; không SLA/automatic backup;
  14 launch gate và ba hướng nới ràng buộc.
- [Nghiên cứu cơ chế scheduled job zero-cost cho Vercel Hobby + Supabase Free](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27):
  1.000.000 invocation/tháng; invocation lỗi vẫn tính; pause sau bảy ngày low
  activity; restore thủ công không SLO, cửa sổ 1 năm; vòng lặp đóng của `pg_cron`.
- [Nghiên cứu cách Supabase tính MAU cho phiên ẩn danh](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/33):
  50.000 MAU mỗi billing cycle; Fair Use restriction không công bố duration,
  margin hay order, nên không đủ cho hard real-time admission control.
- [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12):
  ngưỡng quota 40% / 50% / 40%; appeal riêng tư có người review; sanction kèm
  reason category và case ID; những điều tường minh không được hứa.
- [Chốt mức bảo đảm khi Player mất quyền truy cập](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34):
  disclosure bắt buộc; không có đường khôi phục thủ công; phân định câu chữ cho
  [issue 13](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) và
  nhãn beta cho ticket này.
- [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15):
  §7 không có nhánh void; §8 Rating Generation và re-seed; §11 correction không đảo
  kết quả; §13 public wording và support posture thuộc ticket này.
- [Chốt hàm hiệu chuẩn Ranked Rating thành Score mục tiêu](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/30):
  §9 ba validation status, 11 band, 94 decisive Match, và việc giao cửa launch cho
  ticket này.
- [Nghiên cứu nghĩa vụ license cho bản web public](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/5):
  repo chưa có `LICENSE`; SBOM/notices, asset provenance và trademark review là
  việc phải làm trước khi phát hành.
