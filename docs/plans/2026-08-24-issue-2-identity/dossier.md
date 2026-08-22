# Dossier — Chốt identity, profile và invite-room lifecycle

Ticket: [Chốt identity, profile và invite-room lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)
Branch: `feat/issue-2-identity-prep`
Soạn: phiên đêm 2026-08-24, không giám sát.

## Tài liệu này là gì

Đây là **phần AFK của một ticket `wayfinder:grilling`**: gom hết dữ kiện đã có,
dựng cây quyết định, và soạn sẵn câu hỏi round-1 kèm khuyến nghị — để buổi
grilling bắt đầu ở câu hỏi thật chứ không ở phần tra cứu.

Nó **không quyết định gì**. Mọi mục ở phần C là câu hỏi để người dùng trả lời;
khuyến nghị chỉ là khuyến nghị, có thể bác toàn bộ. Theo `wayfinder`, ticket
HITL không được agent tự trả lời thay.

Ba phần theo yêu cầu: **(A)** ràng buộc đã có, **(B)** design tree, **(C)** câu
hỏi round-1. Thêm **(D)** dữ kiện đã tra sẵn (đỡ phải hỏi), **(E)** câu để dành
round-2, **(F)** ranh giới với ticket khác.

Vị trí của #2 trên map: `blocked_by = 0`, và nó **chặn trực tiếp ba ticket** —
[#4 Match lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4),
[#12 threat model](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12),
[#14 data model](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14).
Gián tiếp, qua #4 và #14, nó nằm trên đường tới #15, #13, #3, #11, #7, #16.
Trên map hiện tại chỉ có #2 và #17 là frontier, nên đây là ticket đòn bẩy cao
nhất còn lại.

---

## A. Những quyết định đã có, và chúng ràng buộc #2 như thế nào

Mỗi dòng ghi **nguồn → ràng buộc cụ thể lên #2**. Không tóm tắt lại nguồn; chỉ
lấy phần cắt vào ticket này.

### A.1 Từ Notes của map #1 (standing decisions)

| Notes nói | Ràng buộc lên #2 |
| --- | --- |
| "Auth mục tiêu: Google OAuth + email magic link" | Hai provider là **mục tiêu**, không phải kết luận. #2 phải chốt provider nào bật ở launch, và bật với điều kiện gì (xem A.2). |
| "Match được tạo bằng invite link/mã ngắn; chưa có public matchmaking" | Đường vào Match **duy nhất** là invite. Không có lobby, không hàng đợi. Mọi câu hỏi entry đều quy về vòng đời một invite. |
| "Ranked Match cập nhật Elo; Practice Match không" | Mode là thuộc tính của **Match**, và #2 phải chốt nó được chọn ở đâu trong vòng đời room (B7). |
| "Elo khởi điểm 1000, K=32, không xét margin" | Không ràng buộc trực tiếp, nhưng khoá con số baseline mà câu hỏi Sybil (C-Q10) dựa vào: mỗi account mới là **1000 điểm donor mới** (#10 §4.2). |
| "Web là sản phẩm mới trong cùng repo; Qt/ESP32 giữ làm tham chiếu" | Không có identity nào kế thừa từ native. Native không có account — #2 thiết kế từ số 0, không phải migration. |
| "UX tiếng Việt, responsive desktop/mobile, WCAG 2.2 AA" | Mã invite phải **gõ được trên bàn phím mobile** và đọc được qua giọng nói/tin nhắn — chi phối bảng chữ cái của mã (C-Q6). |
| "Dùng URL `*.vercel.app` trong MVP" | Không có custom domain → không authenticate được sender domain → chính là gốc của launch risk magic link (A.2). Cũng loại Clerk khỏi bàn cân. |

### A.2 Từ [#8 — Nghiên cứu kiến trúc zero-cost tương thích Vercel](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8) (CLOSED)

Đây là nguồn ràng buộc **nặng nhất** lên #2, vì nó biến "auth" từ lựa chọn sản
phẩm thành bài toán ngân sách.

| #8 xác lập | Ràng buộc lên #2 |
| --- | --- |
| Stack đề xuất: Vercel Hobby `sin1` + Supabase Free `ap-southeast-1` + Brevo Free SMTP, dưới nhãn **non-commercial live beta, no SLA** | Auth chạy trên **Supabase Auth**. Google OAuth có sẵn ở Free; magic link cần custom SMTP. #2 không được chốt provider nào nằm ngoài khả năng của Supabase Auth. |
| Supabase mặc định **không gửi được magic link công khai** (SMTP mặc định chỉ gửi tới member của project, 2 email/giờ) | Magic link **bắt buộc** đi qua Brevo. Không có đường "cứ bật lên là chạy". |
| Brevo Free: **300 sends/ngày**, tối đa 1.000 email queued sau đó không deliver | Toàn bộ email của sản phẩm — auth **và** bất cứ thứ gì khác — chia nhau 300/ngày. Đây là lý do C-Q12 tồn tại. |
| Gate #3 của #8: hạ provider-side OTP limit xuống **6/giờ toàn project**, bật CAPTCHA, "với bảy recipient khác nhau trong cùng giờ, request thứ bảy phải bị `429`" | **Ràng buộc cứng nhất của cả ticket.** 6 magic link/giờ là trần cho *toàn bộ nền tảng*, không phải mỗi user. Xem D.2 để thấy nó gãy ở đâu. |
| Gate #4 của #8: 10 magic link/provider tới Gmail/Outlook/Yahoo trong ≥2 ngày, 10/10 tới trước khi link hết hạn, ≥9/10 vào inbox trong 2 phút, **spam là fail** | Magic link là **launch gate chưa vượt qua**, không phải tính năng đã có. #2 phải chốt hành vi khi gate này trượt. |
| Brevo không authenticate được domain free (Gmail/Yahoo); `From` có thể bị thay bằng `t-sender-sib.com` | Ngay cả khi gate #4 đậu, sender vẫn không có reputation. Nếu #2 dựa vào email cho luồng critical (invite, khôi phục account) thì rủi ro không nằm trong tay dự án. |
| Gate #5: Site URL/redirect phải là **exact path** cho `*.vercel.app`, không wildcard production; phải test `redirectTo` bịa, link hết hạn, link replay | Redirect sau khi đăng nhập — đặc biệt luồng "nhận invite khi chưa đăng nhập rồi quay lại đúng room" (C-Q9) — phải nằm trong allowlist tĩnh. Không được nhét mã room vào `redirectTo` tuỳ ý. |
| Launch cap: invite-only canary **5 active Matches**, đo 7 ngày, HITL mới nâng, **tối đa 25** | Trần đồng thời của cả hệ thống. Mọi quota per-account (C-Q5) phải fail-closed **trước** trần này chứ không phải sau. |
| Vercel Hobby: **1 triệu function invocations/tháng**, pause chứ không overage; mọi invocation đều tính kể cả request lỗi và bot | Enumeration mã invite không chỉ là vấn đề bảo mật — nó **đốt quota** và có thể pause deployment. Entropy của mã (C-Q6) vì thế là quyết định vận hành, không chỉ threat model. |
| Vercel Hobby giới hạn **non-commercial personal use** | Không có tier trả phí, không mua vật phẩm, không cái gì gắn tiền vào account. Cắt luôn một nhánh của cây profile. |
| Supabase Free: 50.000 MAU, 500 MB database/project, project có thể pause sau ~7 ngày ít hoạt động, **không có automatic backup** | MAU không phải chặn. Nhưng "không backup" nghĩa là account là dữ liệu **có thể mất** — ảnh hưởng cách hứa hẹn với người dùng về profile và lịch sử (C-Q4). |
| Gate #9: JWT expiry **600 giây**; revoke membership phải rotate topic ngay | Session ngắn ⇒ refresh thường xuyên. Điều này *không* tiêu thêm magic link (refresh token khác OTP), nhưng nó chi phối câu hỏi session ở E.1. |

### A.3 Từ [#10 — Nghiên cứu tính toàn vẹn Elo cho Match mời riêng](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10) (CLOSED)

#10 cố ý **không chọn policy**; nó giao lại 12 decision inputs. Đúng **một**
trong 12 thuộc về #2:

> **Input 8 — Identity/Sybil:** điều kiện account được chơi Ranked và mức
> friction chấp nhận được trong invite-only MVP.

Những dữ kiện của #10 ràng buộc #2:

| #10 xác lập | Ràng buộc lên #2 |
| --- | --- |
| Zero-sum **không** ngăn boosting; collusion chỉ chuyển điểm. 10 ván dàn xếp từ `1000/1000`, `K=32` → `~1110,47 / ~889,53` | Ranked eligibility là hàng rào **đầu tiên và rẻ nhất**; mọi hàng rào sau (cap cặp lặp, giảm K) đều là #15 và đều đắt hơn. |
| Account mới ở baseline `1000` là **nguồn donor mới**; donor thua rồi biến mất làm rating của nhóm active trông bị inflation | "Ai được chơi Ranked" và "xoá account nghĩa là gì" là **cùng một câu hỏi** nhìn từ hai đầu. C-Q4 và C-Q10 phải trả lời nhất quán. |
| "magic-link/Google auth **không chứng minh** một người-một-account" | Đừng bán Google OAuth như giải pháp Sybil. Nó chỉ **tăng giá** của một account mới, không chặn. Khuyến nghị ở C-Q10 nói rõ điều này. |
| Elo phụ thuộc thứ tự; cần total order bền vững cho rating events | Không ràng buộc #2 trực tiếp — nhưng nghĩa là #2 **không được** thiết kế bất cứ thứ gì cho phép hai Match của cùng một Player chạy song song mà không có thứ tự (⇒ khuyến nghị per-account cap ở C-Q5). |
| Audit ledger append-only; reversal **không** tương đương replay | Xoá account **không thể** rút các Elo transfer đã xảy ra. Ràng buộc trực tiếp lên C-Q4. |
| Invite-only cho Player quyền **chọn đối thủ**, nên cần chốt control + false-positive budget | Cây invite của #2 chính là cái tạo ra quyền đó. Mỗi lựa chọn ở B4/B5 đều mở/đóng bề mặt cho #15. |

### A.4 Từ [#5 — Nghiên cứu nghĩa vụ license cho bản web public](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/5) (CLOSED)

Ràng buộc nhẹ nhưng có thật:

- Repo **chưa có `LICENSE`**; #7 mới là ticket chốt. #2 không được tạo ra nghĩa
  vụ license mới — cụ thể: **không bundle font/icon/avatar pack** cho profile
  nếu chưa có provenance. Avatar do người dùng upload thì kéo theo cả
  provenance lẫn moderation, mà moderation đã **out of scope** trên map.
- Nhãn vận hành non-commercial (A.2) + "không public profile" (A.5) ⇒ profile
  là dữ liệu **nội bộ trận đấu**, không phải trang giới thiệu.

### A.5 Từ Out of scope của map #1

Bốn dòng cắt thẳng vào #2 — chúng **thu hẹp** cây quyết định:

- **Public matchmaking, leaderboard, spectator, chat** → không có đường vào nào
  ngoài invite; không có người thứ ba trong room; không có kênh chữ giữa hai
  người chơi.
- **Public profile** → profile chỉ phục vụ: đối thủ nhận ra bạn, và lịch sử đấu
  đọc được. Không URL profile công khai.
- **Moderation platform** → tên hiển thị **không** được đặt vào vị trí cần
  kiểm duyệt liên tục. Đây là lý do chính của khuyến nghị C-Q3.
- **Custom domain** → xem A.2, gốc của toàn bộ vấn đề magic link.

### A.6 Từ [#9 — game specification `digitcode-ruleset/1.0.0`](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9) (CLOSED)

Mục 12 của `game-spec.md` liệt kê **đầu vào cứng** mà mọi ticket sau MUST nhận
nguyên trạng. Những luật cắt vào #2:

| Luật | Ràng buộc lên #2 |
| --- | --- |
| **R-P-09 / R-P-10** — Practice rút từ **465.120** mã; Ranked rút từ **464.948** (loại 172 mã thuộc 86 cặp collision) | Mode **thay đổi pool sinh Puzzle**. Nó không phải một cái cờ hiển thị — nó phải cố định **trước** khi Puzzle được sinh. |
| **R-P-13** — một Match có đúng một Puzzle, **sinh lúc tạo Match** | ⇒ Mode phải chốt xong trước thời điểm đó. #2 chốt *ở đâu trong vòng đời room*; #4 chốt *chính xác lúc nào Match được tạo*. |
| **R-P-14 / R-I-02** — mã bí mật không rời server tới hết Match; client chỉ nhận `puzzle_id` mờ, và chỉ sau khi Match kết thúc | Invite link/mã **MUST NOT** mang bất kỳ thứ gì suy ra được từ Puzzle. Mã invite phải độc lập hoàn toàn với `puzzle_id`. |
| **R-T-08** — Match đang chạy MUST NOT bị huỷ, reset hay sinh lại Puzzle bởi **bất kỳ ai**, kể cả người vận hành | "Room ownership" **không** bao gồm quyền kết thúc Match. Owner của room ≠ admin của Match. Ràng buộc trực tiếp lên B5 và C-Q7. |
| **R-T-06** — Forfeit là hành động chủ động và là **thua** | Đường thoát duy nhất khỏi Match đang chạy. ⇒ "xoá account giữa Match" không thể là một đường thoát thứ hai (C-Q4). |
| **R-T-07** — mất kết nối rồi không quay lại là `EXPIRED`, **không** phải forfeit; MUST NOT cố phân biệt rage-quit với rớt mạng | #2 không được thiết kế bất cứ tín hiệu identity nào (đăng xuất, đóng tab, xoá account) mang nghĩa "bỏ cuộc". |
| **R-T-11** — Match kết thúc khi **cả hai** Player terminal | Một Player rời đi không giải phóng room. Ảnh hưởng cách đếm "active Match" cho quota per-account (C-Q5). |
| **R-K-01 / R-K-04** — mọi Match ghi bền `ruleset_id`; chỉ Match cùng `ruleset_id` mới so sánh được | Mỗi rematch là một **Match record riêng**, không phải một lượt chơi lại trong cùng record (C-Q11). |
| **R-S-06** — deadline Match **15 phút** | Cho một con số thật để đặt TTL invite và định nghĩa "active Match" (D.3). |
| `CONTEXT.md`: **Player** = "An authenticated person who participates in a Match" | Glossary đã chốt: **không có guest**. Không thể chơi khi chưa đăng nhập, kể cả Practice. Đây là ràng buộc đã có, không phải câu hỏi mở. |
| `CONTEXT.md`: **Practice Match** = cùng luật, rút từ **unrestricted pool**, không đổi Elo | Practice không phải "Ranked tắt Elo" — nó khác cả pool. Củng cố kết luận ở R-P-09. |

---

## B. Design tree của #2

Cây dưới đây là **toàn bộ bề mặt quyết định** của ticket. Nhánh có dấu ✱ là nhánh
đã bị ràng buộc ở phần A đóng lại một phần — ghi kèm để thấy vì sao không hỏi.

```text
#2 Identity, profile, invite-room lifecycle
│
├── B1  IDENTITY — ai là Player
│   ├── B1.1  Provider nào bật ở launch                          → C-Q1
│   │         ├─ Google OAuth (Supabase Free có sẵn)
│   │         ├─ Email magic link (Brevo, 6/giờ, gate #4 chưa đậu)
│   │         └─ ✱ Clerk / Firebase / Resend — #8 đã loại (không có custom domain)
│   ├── B1.2  Một account nhiều provider? Merge theo email?      → C-Q2
│   ├── B1.3  ✱ Guest / chơi không đăng nhập — CONTEXT.md đã đóng: Player là "authenticated person"
│   └── B1.4  Session lifetime, multi-device                     → E.1 (round 2)
│
├── B2  ACCOUNT LIFECYCLE
│   ├── B2.1  Tạo account: implicit lúc đăng nhập lần đầu, hay có bước onboarding?  → gộp vào C-Q3
│   ├── B2.2  Link thêm provider vào account đã có               → C-Q2
│   ├── B2.3  Xoá account: nghĩa là gì với Match đang chạy / lịch sử / Elo → C-Q4
│   └── B2.4  ✱ Đổi email chính — hệ quả của C-Q2, để round 2
│
├── B3  PROFILE
│   ├── B3.1  Display name: nguồn (tự nhập / lấy từ provider)    → C-Q3
│   ├── B3.2  Unique hay không; cơ chế phân biệt trùng tên       → C-Q3
│   ├── B3.3  Tần suất đổi tên; giữ lịch sử tên                  → C-Q3
│   ├── B3.4  ✱ Avatar — A.4 (license/provenance) + moderation out of scope
│   └── B3.5  ✱ Trang profile công khai — out of scope trên map
│
├── B4  ROOM CREATION & INVITE ARTIFACT
│   ├── B4.1  Ai được tạo room; bao nhiêu room/Match đồng thời mỗi account → C-Q5
│   ├── B4.2  Hình dạng invite: link dài / mã ngắn gõ tay / cả hai        → C-Q6
│   ├── B4.3  Entropy và bảng chữ cái của mã                              → C-Q6
│   └── B4.4  Invite được gửi qua kênh nào (in-app email? chỉ copy?)      → C-Q12
│
├── B5  INVITE LIFECYCLE
│   ├── B5.1  Single-use hay reusable                            → C-Q7
│   ├── B5.2  TTL                                                → C-Q7
│   ├── B5.3  Owner revoke / regenerate                          → C-Q7
│   ├── B5.4  Tái sử dụng mã sau khi chết                        → C-Q7
│   └── B5.5  ✱ Owner huỷ Match đang chạy — R-T-08 cấm tuyệt đối
│
├── B6  JOIN & EDGE CASES
│   ├── B6.1  Chưa đăng nhập mà mở link → luồng quay lại đúng room  → C-Q9
│   ├── B6.2  Self-join (cùng account giữ cả hai ghế)               → C-Q9
│   ├── B6.3  Người thứ ba khi room đã đủ 2                         → C-Q9
│   ├── B6.4  Rời room trước khi Match bắt đầu → ghế mở lại?        → C-Q9
│   ├── B6.5  Mã sai / mã chết → thông điệp lỗi lộ gì               → C-Q9
│   └── B6.6  ✱ Reconnect sau khi Match đã bắt đầu — thuộc #4
│
├── B7  MODE SELECTION (Ranked / Practice)
│   ├── B7.1  Chốt ở đâu trong vòng đời: tạo room / ready-up / hai bên đồng ý  → C-Q8
│   ├── B7.2  Người nhận có thấy mode trước khi join không                     → C-Q8
│   └── B7.3  Điều kiện account được chơi Ranked (Sybil friction)              → C-Q10
│
├── B8  REMATCH
│   ├── B8.1  Cùng room hay room mới; mã invite có sống lại không  → C-Q11
│   ├── B8.2  Cần cả hai đồng ý hay owner quyết                    → C-Q11
│   ├── B8.3  Giới hạn số rematch trong một room                   → C-Q11
│   └── B8.4  ✱ Cap số Ranked Match giữa cùng một cặp — thuộc #15
│
└── B9  LAUNCH POSTURE CỦA EMAIL   (giao thoa với #17)
    ├── B9.1  Hành vi nếu gate #4 của #8 trượt                    → C-Q1
    ├── B9.2  Có gửi email nào ngoài auth không                   → C-Q12
    └── B9.3  ✱ Nhãn non-commercial beta công bố ra sao — thuộc #17
```

**Thứ tự phụ thuộc trong round-1.** Q1 (provider) chi phối Q2, Q10, Q12. Q6
(hình dạng mã) chi phối Q7 (vòng đời) và Q9 (thông điệp lỗi). Q8 (mode chốt ở
đâu) chi phối Q11 (rematch). Vì thế round-1 nên đi theo đúng thứ tự Q1 → Q12.

---

## C. Câu hỏi grilling round-1

Mỗi câu: **câu hỏi** → **khuyến nghị của tôi** → **vì sao** → **ai tiêu thụ câu
trả lời**. Theo `grilling`, đúng ra phải hỏi từng câu một và chờ trả lời; danh
sách này là bản in sẵn để người dùng đọc trước hoặc trả lời thẳng trên GitHub.

Tôi **không** trả lời câu nào trong số này.

---

### Q1 — Provider auth nào bật ở launch, và điều gì xảy ra nếu email không đến?

Notes chốt mục tiêu "Google OAuth + email magic link". #8 lại biến magic link
thành launch gate chưa vượt qua. Ba đường: (a) Google-only ở launch, magic link
để sau; (b) bật cả hai, magic link mang nhãn beta; (c) bật cả hai nhưng
**Ranked yêu cầu Google**, magic link chơi được Practice.

**Khuyến nghị: (c).**

**Vì sao.** Đây là câu duy nhất trong round-1 mà một con số đã có sẵn quyết định
gần hết. Gate #3 của #8 bắt hạ OTP limit xuống **6/giờ cho toàn project** — nghĩa
là **6 lần đăng nhập bằng email mỗi giờ cho toàn bộ nền tảng**, không phải mỗi
user. Ở trần canary 5 Match đồng thời (10 Player) thì còn chịu được; ở trần 25
Match (**50 Player**) thì một đợt onboarding bằng email là bất khả thi — người
thứ 7 trong giờ nhận `429`. Mà luồng invite **vốn dĩ bùng theo cụm**: gửi link
cho bạn và mong bạn đăng nhập trong vài phút.

Google OAuth không đụng trần đó, có sẵn ở Supabase Free, và cho một email đã
verified — thứ mà C-Q10 cần. Giữ magic link **bật** vẫn có giá trị thật: nó là
đường dự phòng cho người không có/không muốn dùng Google, và nó cho dự án cơ hội
chạy gate #4 (10 email × 3 provider × 2 ngày) trên traffic thật thay vì phải
chặn launch chờ nó.

Nhánh (c) cũng khiến việc gate #4 **trượt** không còn là sự cố launch: magic
link tụt xuống Practice-only, sản phẩm vẫn chạy.

**Ai tiêu thụ:** #12 (bề mặt auth), #14 (identity columns), #17 (launch posture),
#3 (chọn service).

---

### Q2 — Một account có link được nhiều provider không, và có bao giờ auto-merge theo email không?

Nếu bật cả Google và magic link, một người có thể xuất hiện dưới hai identity với
cùng địa chỉ email.

**Khuyến nghị: cho link nhiều provider, nhưng chỉ từ bên trong một phiên đã đăng
nhập, và không bao giờ auto-merge lúc đăng nhập.**

**Vì sao.** Auto-merge-theo-email là lỗ chiếm tài khoản kinh điển: nếu một
provider trả về email chưa verified, người đăng nhập bằng provider đó nhận luôn
account của người kia. Supabase có tuỳ chọn identity linking, và nó phải được
chốt **tường minh** chứ không để mặc định. Đường an toàn: hai identity khác
provider mặc định là **hai account riêng**; muốn gộp thì đăng nhập vào account
đích rồi mới link.

Chi phí: một người có thể vô tình tạo hai account và mang hai rating. Với #10
input 8 (Sybil) thì đó là nhiễu, nhưng **kém nguy hiểm hơn nhiều** so với một
đường chiếm tài khoản. Nếu bạn chọn Q1 = (a) Google-only thì câu này gần như
biến mất, và đó là một điểm cộng nữa cho việc chốt Q1 trước.

**Ai tiêu thụ:** #12, #14.

---

### Q3 — Display name lấy từ đâu, có phải unique không, đổi được bao nhiêu lần?

Đối thủ phải nhận ra bạn, và lịch sử đấu phải đọc được — nhưng public profile đã
out of scope và moderation platform cũng vậy.

**Khuyến nghị: bắt buộc tự nhập một lần lúc onboarding (không im lặng lấy tên
Google); KHÔNG yêu cầu unique; kèm một `player_tag` ngắn bất biến để phân biệt
người trùng tên; cho đổi tên tối đa 1 lần/30 ngày và giữ lịch sử tên.**

**Vì sao.** Unique display name kéo theo namespace, tranh chấp tên, hàng đợi
reservation, và — quan trọng nhất — một bề mặt cần **kiểm duyệt liên tục**, mà
map đã xếp moderation platform ra ngoài scope. Tag bất biến giải quyết đúng vấn
đề thật (phân biệt hai người trùng tên trong lịch sử đấu) mà không tạo namespace.

Không im lặng lấy tên Google vì tên thật lộ ra trong một trò chơi đấu 1v1 là rò
rỉ PII mà người dùng không chủ động đồng ý; #14 sẽ phải dọn.

Giữ lịch sử tên vì #15 và #12 sau này cần đọc lịch sử đấu mà không bị đổi tên
làm mất dấu — và vì với `K=32` thì đổi tên là một cách rẻ để tránh bị nhận diện
sau khi sandbagging.

Giới hạn 1 lần/30 ngày là con số **tôi đề xuất, không có nguồn** — nếu bạn thấy
quá chặt cho một beta invite-only thì cứ nới; điều cần chốt là *có* giới hạn.

**Ai tiêu thụ:** #14 (schema + privacy), #13 (UX hiển thị đối thủ).

---

### Q4 — "Xoá account" nghĩa chính xác là gì?

Ba tình huống phải trả lời cùng lúc: đang có Match chạy dở; lịch sử đấu đã có;
Elo đã transfer cho người khác.

**Khuyến nghị: tombstone, không xoá vật lý.**
- **Từ chối** xoá khi Player còn Match chưa terminal. Bắt Forfeit trước.
- Sau khi xoá: xoá PII (email, identity link, tên hiển thị hiện tại), **giữ**
  `player_id`, rating ledger và Match record, hiển thị là "Người chơi đã xoá".
- **Không** hoàn ngược bất kỳ Elo transfer nào.
- Không cho tạo lại account trên cùng email mà thừa kế rating cũ.

**Vì sao.** #10 §7.2 nói rõ reversal **không** tương đương replay: rút một vế của
một transfer zero-sum sẽ làm mọi expected score sau đó sai, và không rebuild được
từ ledger. #10 §4.2 còn cho thấy chính việc donor "thua rồi biến mất" là cơ chế
inflation — nên xoá rating của người rời đi vừa sai kỹ thuật vừa **là** lỗ hổng.

Từ chối xoá giữa Match là hệ quả trực tiếp của R-T-08 (không ai được huỷ Match
đang chạy) và R-T-06 (Forfeit là đường thoát duy nhất). Nếu xoá account kết thúc
được Match thì nó thành đường thoát thứ hai — và là đường **né thua**, vì đối thủ
đang chờ ở R-T-11.

Cần lưu ý ngược lại: đây là ràng buộc kỹ thuật, không phải kết luận pháp lý.
Nghĩa vụ xoá dữ liệu (nếu có) thuộc #14/#7 — #2 chỉ chốt **ngữ nghĩa người dùng
thấy**.

**Ai tiêu thụ:** #14 (privacy + retention), #15 (ledger), #7.

---

### Q5 — Ai được tạo room, và mỗi account được mở bao nhiêu room/Match cùng lúc?

**Khuyến nghị: mọi account đã đăng nhập đều tạo được room; giới hạn cứng
**1 room đang mở + 1 Match chưa terminal** mỗi account.**

**Vì sao.** Ba lý do độc lập cùng chỉ về một chỗ:

1. **Quota.** #8 đặt trần canary 5 Match đồng thời (nâng tối đa 25). Trần đó là
   của *hệ thống*; nếu không có cap per-account thì một account đủ để dùng hết.
   Cap per-account là cách rẻ nhất để fail closed **trước** khi chạm quota
   vendor, mà #8 yêu cầu là "ngừng Match mới, giữ reserve cho Match đang chạy".
2. **Elo ordering.** #10 §5.3: Elo phụ thuộc thứ tự, và hai Match khác nhau cùng
   chạm một Player cần một serial order. Cấm một Player có hai Match chạy song
   song thì bài toán đó biến mất khỏi MVP — đây là món quà cho #15, gần như miễn
   phí ở quy mô invite-only.
3. **Luật chơi.** R-S-02 cho mỗi Match một Match Clock wall-clock **không dừng**
   (R-S-03, R-S-04). Chơi hai Match song song nghĩa là ít nhất một Match đang tự
   hao mòn Score trong lúc người chơi nhìn chỗ khác. Cho phép điều đó là biến
   một luật chơi thành cái bẫy.

"1 room + 1 Match" chứ không phải "1 tổng cộng": người vừa chơi xong nên mở được
room mới trong lúc Match cũ còn chờ đối thủ vào terminal (R-T-11 — một người
terminal **không** kết thúc Match).

**Ai tiêu thụ:** #4 (lifecycle), #12 (abuse), #16 (quota gate), #17.

---

### Q6 — Invite là link dài, mã ngắn gõ tay, hay cả hai? Và mã dài bao nhiêu?

**Khuyến nghị: cả hai, cùng một mã 6 ký tự Crockford base32; link chỉ là mã nhúng
trong URL. Mã sinh ngẫu nhiên bằng CSPRNG, có unique constraint ở DB và retry khi
đụng.**

**Vì sao — bằng số (tự tính, xem D.1).** Với 32 ký tự và trần 25 room sống đồng
thời:

| Độ dài | Không gian | Số lần đoán mù trung bình để trúng 1 room |
| --- | --- | --- |
| 4 | 1.048.576 | **41.943** |
| 5 | 33.554.432 | 1.342.177 |
| **6** | **1.073.741.824** | **42.949.673** |
| 8 | 1,0995 × 10¹² | 4,4 × 10¹⁰ |

Mốc so sánh không phải "bao nhiêu thì an toàn" mà là **ngân sách Vercel Hobby: 1
triệu invocation/tháng**, và #8 nói rõ mọi invocation đều tính kể cả request lỗi
và bot. Mã 4 ký tự cần ~42.000 lần đoán — **4% ngân sách tháng** là đủ chiếm một
room của người khác. Mã 6 ký tự cần ~43 triệu lần đoán, tức **43 lần toàn bộ ngân
sách tháng**; kẻ tấn công sẽ làm deployment pause (self-DoS) trước khi trúng.

6 ký tự cũng là ngưỡng gõ tay còn dễ chịu trên mobile — Notes yêu cầu
responsive/touch và WCAG 2.2 AA. Crockford base32 bỏ `I`, `L`, `O`, `U`: hết nhầm
`0`/`O` và `1`/`I` khi đọc qua điện thoại, và bỏ `U` để giảm khả năng sinh ra từ
tục ngẫu nhiên — có ích khi không có moderation.

Unique constraint + retry chứ không phải "xác suất đủ nhỏ": với 6 ký tự, **10.000
mã từng phát ra đã có 4,55% khả năng trùng ít nhất một lần**. Đó là chuyện chắc
chắn xảy ra, không phải rủi ro xa vời — nhưng nó vô hại nếu DB từ chối và sinh
lại.

**Ai tiêu thụ:** #12 (enumeration, rate limit), #13 (UX nhập mã), #14 (schema).

---

### Q7 — Vòng đời invite: dùng một lần hay nhiều lần? Sống bao lâu? Owner huỷ được không? Mã có được tái dùng?

**Khuyến nghị: single-use (chết ngay khi ghế thứ hai được nhận); TTL 30 phút;
owner huỷ/sinh lại được khi chưa ai vào; mã đã chết KHÔNG BAO GIỜ tái sử dụng.**

**Vì sao.** TTL 30 phút = **hai lần deadline Match** (R-S-06 chốt 15 phút). Nó
đủ dài cho "gửi link, chờ bạn mở app", và đủ ngắn để số mã sống đồng thời luôn
nhỏ — mà chính con số đó là mẫu số trong bảng ở Q6. TTL dài làm bảng đó xấu đi
tuyến tính.

Single-use vì reusable link là một invite **vĩnh viễn đúng**: ai có nó cũng vào
được mọi Match sau này của owner. Trong một hệ invite-only đang cố chống collusion
(#10 §4.3), một cái link truyền tay được là đúng thứ không nên có.

Không tái dùng mã vì một link cũ trong lịch sử chat **không bao giờ** được trỏ
vào Match của người khác — kể cả nhiều tháng sau. Không gian 10⁹ đủ để không bao
giờ cần tái dùng.

Owner huỷ được — nhưng chỉ **trước khi Match bắt đầu**. Sau đó R-T-08 cấm tuyệt
đối, và "room ownership" không được biến thành quyền admin trên một Match đang
chạy. Đây là chỗ dễ vô tình vi phạm spec nhất trong cả ticket.

**Ai tiêu thụ:** #4, #12, #14.

---

### Q8 — Ranked hay Practice được chốt ở đâu trong vòng đời room?

**Khuyến nghị: chốt lúc **tạo room**, in vào invite, bất biến sau đó; người nhận
thấy mode **trước** khi bấm join.**

**Vì sao.** Đây không phải lựa chọn UX — nó bị luật ép. R-P-09/R-P-10 cho Ranked
và Practice **hai pool khác nhau** (464.948 vs 465.120), và R-P-13 sinh Puzzle
**lúc tạo Match**. Nên mode phải cố định trước thời điểm đó. Chốt lúc tạo room là
điểm sớm nhất và đơn giản nhất; chốt lúc ready-up thì phải định nghĩa "ai đổi
được, đổi tới lúc nào" và mở ra một race ngay sát thời điểm sinh Puzzle — đúng
loại việc #4 sẽ phải dọn.

Người nhận phải thấy trước vì Ranked **thay đổi rating của họ**. Cho ai đó vào
một trận đấu ảnh hưởng Elo mà không nói trước là sai; và với #10 §4.3, "UX phải
báo policy vào lúc nào" là một câu hỏi đã được nêu sẵn.

Hệ quả cần chốt kèm: nếu người nhận **không đủ điều kiện Ranked** (Q10), invite
Ranked phải từ chối họ một cách rõ ràng — chứ không âm thầm hạ xuống Practice.

**Ai tiêu thụ:** #4 (thời điểm tạo Match), #13 (UX), #15.

---

### Q9 — Bốn ca biên khi join: chưa đăng nhập, tự join chính mình, người thứ ba, và mã sai

**Khuyến nghị:**
- **Chưa đăng nhập:** giữ mã ở phía client, đẩy qua auth, quay lại đúng room.
  Redirect URI là **path tĩnh** đã allowlist (gate #5 của #8) — mã room đi theo
  state/lưu trữ client, **không** nhét vào `redirectTo`.
- **Self-join:** cấm cứng. Cùng `player_id` không được giữ hai ghế, kể cả tab
  khác hay thiết bị khác.
- **Người thứ ba khi đã đủ 2:** từ chối, và trả **đúng cùng một lỗi** như mã sai.
- **Mã sai / hết hạn / đã dùng:** một thông điệp duy nhất, không phân biệt.
- **Rời trước khi Match bắt đầu:** ghế mở lại, invite sống lại tới hết TTL. Sau
  khi Match bắt đầu thì thuộc #4 (R-T-07: rời đi không phải forfeit).

**Vì sao.** Self-join tạo một Match mà cả hai vế là cùng một Player: Elo
self-transfer, và với R-T-11 thì Match chỉ kết thúc khi cả hai terminal — nghĩa
là một người có thể tự khoá mình. Đây là bug rẻ nhất để chặn ngay ở #2 và đắt
nhất để dọn ở #15.

Một thông điệp lỗi duy nhất cho mọi ca hỏng vì phân biệt "mã này tồn tại nhưng đã
đầy" với "mã này không tồn tại" biến endpoint join thành **oracle enumeration**:
nó thu hẹp không gian 10⁹ xuống tập mã đang sống. #12 sẽ phải chốt rate limit,
nhưng #2 quyết định endpoint có rò rỉ hay không ngay từ đầu.

Không nhét mã vào `redirectTo` vì gate #5 của #8 bắt test "crafted `redirectTo`"
và cấm wildcard ở production.

**Ai tiêu thụ:** #12 (chính), #4, #13.

---

### Q10 — Account mới cần gì trước khi được chơi Ranked?

Đây đúng là **decision input 8** mà #10 giao lại: "điều kiện account được chơi
Ranked và mức friction chấp nhận được trong invite-only MVP".

**Khuyến nghị: cần (i) identity Google đã verified và (ii) đã hoàn tất ≥ 1
Practice Match. KHÔNG yêu cầu tuổi account, KHÔNG yêu cầu số điện thoại.**

**Vì sao.** #10 nói thẳng: "magic-link/Google auth **không chứng minh** một
người-một-account". Nên đừng đặt kỳ vọng sai — hàng rào này không chặn Sybil, nó
chỉ **tăng giá** mỗi donor mới. Với K=32, một chuỗi 10 ván dàn xếp chuyển
~110 điểm; nếu mỗi donor phải có một Google account riêng **và** chơi hết một
Practice Match 15 phút, chi phí mỗi donor tăng đáng kể mà người dùng thật gần như
không thấy gì (họ vốn sẽ chơi thử một ván).

"≥1 Practice" còn có tác dụng phụ tốt: nó bảo đảm không ai gặp Ranked Match đầu
tiên mà chưa từng thấy luật — có ý nghĩa với ruleset 84 luật của #9.

Không yêu cầu tuổi account vì trong beta invite-only, người được mời hôm nay muốn
chơi hôm nay; friction thời gian đánh vào người dùng thật nặng hơn đánh vào kẻ
tấn công (kẻ tấn công chỉ cần chờ).

Không dùng số điện thoại vì nó là PII mới, tốn SMS quota (không có trong stack
zero-cost), và kéo theo cả một trục privacy cho #14.

**Đây là CHOICE, không phải FACT** — #10 nói rõ không nguồn nào chứng minh một
ngưỡng cụ thể là tối ưu. Cần bạn chốt.

**Ai tiêu thụ:** #15 (chính), #12, #14.

---

### Q11 — Rematch hoạt động ra sao?

**Khuyến nghị: rematch tạo một **Match record mới với Puzzle mới** trong **cùng
room**; cần **cả hai** bấm đồng ý; mã invite đã tiêu **không** sống lại; giới hạn
số rematch trong một room (đề xuất 5).**

**Vì sao.** R-T-08 cấm reset Match và R-P-13 buộc mỗi Match đúng một Puzzle — nên
rematch **phải** là record mới, không thể là "chơi lại" trong record cũ. R-K-01
bắt mỗi Match ghi `ruleset_id` riêng; điều đó chỉ đúng nếu mỗi rematch là một
Match thật.

Cần cả hai đồng ý vì owner của room không có quyền lôi người kia vào một trận
Ranked nữa (xem Q8: mode bất biến, nên rematch của room Ranked cũng là Ranked).

Mã invite không sống lại vì nó đã single-use (Q7) và vì mã sống lại thì bảng
entropy ở Q6 mất mẫu số ổn định.

Giới hạn số rematch: con số 5 là **tôi đề xuất, không có nguồn**. Lý do có giới
hạn thì có nguồn: #10 §4.1 chỉ ra nhiều ván cùng một cặp **không tăng
connectivity** của pool, và §4.3 liệt kê "cap số rated Match cho mỗi cặp trong
một window" là một control ứng viên. Policy cap thật thuộc **#15**; #2 chỉ cần
**không** tạo ra một đường rematch vô hạn khiến #15 phải đi dọn ngược.

**Ai tiêu thụ:** #15 (chính), #4, #14.

---

### Q12 — Sản phẩm có gửi email nào ngoài auth không? Cụ thể: có gửi invite qua email trong app không?

**Khuyến nghị: KHÔNG. Zero email ngoài auth. Invite chỉ chia sẻ ngoài luồng —
copy link/mã rồi tự gửi qua Messenger/Zalo/bất cứ đâu.**

**Vì sao.** Brevo Free là **300 sends/ngày dùng chung cho mọi loại email**. Đó là
cùng một cái ví trả cho magic link. Mỗi email invite gửi đi là một magic link ít
đi. Và vì #8 đã hạ OTP xuống 6/giờ (144/ngày) để bảo vệ deliverability, việc đổ
thêm mail transactional từ cùng một sender **chưa authenticate domain** đúng là
thứ làm hỏng chính cái đang cố bảo vệ.

Còn một lý do phi ngân sách: gửi email tới địa chỉ do người dùng nhập là một bề
mặt spam do người lạ điều khiển, trên một sender không có domain riêng. Đó là
cách nhanh nhất để đốt reputation của một account Brevo mới.

Ngoài luồng cũng hợp với thực tế người dùng ở đây: người mời và người được mời
gần như chắc chắn đã có một kênh chat sẵn.

**Ai tiêu thụ:** #17 (launch posture), #16 (quota gate), #13 (UX chia sẻ).

---

## D. Dữ kiện đã tra sẵn

Phần này để trong buổi grilling không phải dừng lại tra cứu. Mọi con số ở đây
**tôi tự tính lại**, không chép từ ticket trước.

### D.1 Entropy của mã invite

Alphabet Crockford base32 (32 ký tự, bỏ `I` `L` `O` `U`).

Đoán mù, `L` = số mã sống đồng thời, `N` = 32^k:

| k | N | L=5: số lần đoán TB | L=25: số lần đoán TB |
| --- | --- | --- | --- |
| 4 | 1.048.576 | 209.715 | 41.943 |
| 5 | 33.554.432 | 6.710.886 | 1.342.177 |
| 6 | 1.073.741.824 | 214.748.365 | 42.949.673 |
| 7 | 34.359.738.368 | 6.871.947.674 | 1.374.389.535 |
| 8 | 1.099.511.627.776 | 219.902.325.555 | 43.980.465.111 |

Va chạm sinh mã (birthday, `T` = tổng số mã từng phát ra):

| k | T=1.000 | T=10.000 | T=100.000 |
| --- | --- | --- | --- |
| 4 | 37,90% | ~100% | ~100% |
| 5 | 1,48% | 77,46% | ~100% |
| 6 | 0,05% | **4,55%** | 99,05% |
| 8 | ~0% | 0,0045% | 0,45% |

⇒ ở mọi độ dài thực tế, **unique constraint + retry là bắt buộc**, không phải tuỳ chọn.

### D.2 Ngân sách email — chỗ nó gãy

- Brevo Free: **300 sends/ngày** (mọi loại email), sau đó tối đa 1.000 giữ trong
  queue rồi **không deliver**.
- Supabase Auth mặc định 30 OTP/giờ toàn project; **#8 gate #3 bắt hạ xuống
  6/giờ** ⇒ trần 144/ngày.
- Trần vận hành của #8: canary **5 Match** đồng thời → tối đa **25** sau 7 ngày
  quan sát + HITL.

Ráp lại: 25 Match = **50 Player**. Nếu cohort đó đăng nhập bằng magic link, họ
cần 50 email — trong khi trần là **6/giờ**. Người thứ 7 trong bất kỳ giờ nào
nhận `429`. Onboarding theo cụm (đúng bản chất của invite) là ca gãy, không phải
ca hiếm.

Chặn thật vì thế **không phải** 300/ngày của Brevo — nó là **6/giờ** do chính #8
áp đặt. Đây là dữ kiện nền của C-Q1 và C-Q12.

### D.3 Con số từ luật chơi mà #2 dùng tới

Đã tính lại độc lập từ R-S-01/05/06 và R-C-12, khớp với R-S-12 của spec:

```text
100 Score, 5/Clue, −1 mỗi 60 giây, deadline 900 giây
  hao mòn tối đa   : 15
  còn cho Clue     : 85  ->  17 lần mua  (spec R-S-12: 17)  ✓
ở chu kỳ 30 giây   : hao mòn 30, còn 70 ->  14 lần mua      ✓
32 Clue × 5 = 160 > 100 -> không bao giờ mua hết (R-S-10)   ✓
```

Với #2 chỉ có **deadline 15 phút** là dùng trực tiếp (đặt TTL invite ở Q7, và
định nghĩa "Match đang chạy" ở Q5). Phần còn lại ghi ở đây để buổi grilling khỏi
phải mở lại spec.

### D.4 Vị trí #2 trên đồ thị phụ thuộc

```text
#2 ──> #4 ──> #12
   ├─> #12    #15 ──> #14
   └─> #14 ──> #3 ──> #7, #11, #16
            └> #13
```
`blocked_by` hiện tại: #2 = 0, #17 = 0 (hai frontier duy nhất); #4 = 1 (chỉ chờ
#2); #12 = 2; #14 = 3; #15 = 1; #3 = 3; #13 = 1; #11 = 1; #7 = 2; #16 = 6.

---

## E. Để dành round-2

Những câu này **phụ thuộc câu trả lời round-1**, hỏi bây giờ là hỏi sớm:

1. **Session lifetime và multi-device.** #8 gate #9 đặt JWT expiry 600 giây và
   bắt rotate topic khi revoke membership. Nhưng refresh-token policy, "đăng
   xuất mọi thiết bị", và multi-tab đều dính vào #4 (takeover) và #12 (threat
   model). Chỉ hỏi sau khi Q1 chốt provider.
2. **Đổi email chính** — chỉ có nghĩa nếu Q2 cho phép nhiều provider.
3. **Người chơi bị chặn/ban** — cần #12 chốt threat model trước.
4. **Hiển thị rating ở đâu trong room/profile** — cần #15.
5. **Thông báo (notification) khi đối thủ vào room** — cần Q12; nếu zero email
   thì chỉ còn in-app, và in-app thì dính realtime topology của #3.
6. **Khôi phục account khi mất cả Google lẫn email** — phụ thuộc Q1/Q2, và với
   "Supabase Free không có automatic backup" thì cần một câu trả lời thành thật
   thay vì một quy trình.

## F. #2 KHÔNG quyết định (đúng theo mục 12 của game-spec)

| Vấn đề | Thuộc ticket |
| --- | --- |
| Reconnect handshake, multi-tab takeover, idempotency, thứ tự lệnh, thời điểm chính xác Match được tạo | [#4](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4) |
| Rate limit cụ thể, CAPTCHA placement, chống enumeration, ban/appeal | [#12](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12) |
| Schema, retention, PII, quyền riêng tư của lịch sử đấu | [#14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| Provisional, cap cặp lặp, correction, draw settlement | [#15](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| Chọn service thật (Supabase vs khác) | [#3](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3) |
| Nhãn beta công bố ra sao, tiêu chí launch | [#17](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17) |
| UX cụ thể của màn onboarding/room | [#13](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| LICENSE và attribution | [#7](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/7) |

---

## Nguồn

- Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1) — Notes, Decisions so far, Out of scope
- [#8 resolution comment](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8) + `docs/research/2026-08-22-zero-cost-vercel-architecture.md` @ `4d71e18` (branch `research/vercel-zero-cost`)
- [#10 resolution comment](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/10) + `docs/research/2026-08-22-elo-integrity.md` @ `7e27ec0` (branch `research/elo-integrity`)
- [#5 resolution comment](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/5) + `docs/research/2026-08-22-public-web-licensing.md` @ `9470f63` (branch `research/web-license`)
- [#9](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9): `docs/plans/2026-08-23-issue-9-game-spec/game-spec.md` mục 12 + `CONTEXT.md` @ `dcf434f` (branch `feat/competitive-game-spec`)
