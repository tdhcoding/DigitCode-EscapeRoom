# Supabase MAU cho phiên ẩn danh

- Ngày khảo sát và truy cập nguồn: 2026-08-25
- Ticket: [#33 - Nghiên cứu cách Supabase tính MAU cho phiên ẩn danh](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/33)
- Map liên quan: [#1 - DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)
- Phạm vi: Supabase-hosted Auth trên Free Plan; anonymous sign-in, refresh, tạo lại phiên trình duyệt, link Google, quan sát usage, xóa/cleanup user và tác động được tài liệu hóa lên MAU. Báo cáo chỉ dùng tài liệu chính thức Supabase hiện hành và đối chiếu các quyết định trong repo; không chọn product, privacy, retention hoặc architecture policy.
- Tính thời điểm: pricing, quota và hành vi vendor dưới đây là snapshot tại ngày truy cập.

## Research acceptance

Câu hỏi của ticket được trả lời đến đúng giới hạn tài liệu chính thức:

- Supabase **không tài liệu hóa trực tiếp** anonymous sign-in có tính MAU hay không. Việc anonymous sign-in tạo một user, còn MAU đếm distinct user sign in hoặc refresh token, tạo một suy luận mạnh rằng có tính; báo cáo không nâng suy luận đó thành vendor guarantee. [Anonymous Sign-Ins](https://supabase.com/docs/guides/auth/auth-anonymous), [Monthly Active Users](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users)
- Free Plan công bố 50.000 MAU included và không có giá over-usage; vượt quota liên tục dẫn tới notification, grace period rồi có thể bị service restriction. Vendor không công bố một pre-restriction margin, grace-period duration hoặc restriction order đủ để chứng minh một automation có thể chặn trước restriction. [Pricing](https://supabase.com/pricing), [Billing FAQ - Fair Use Policy](https://supabase.com/docs/guides/platform/billing-faq#fair-use-policy)
- Automatic cleanup anonymous user hiện **không có**. Supabase đưa một câu SQL xóa thủ công user ẩn danh cũ hơn 30 ngày làm ví dụ, nhưng không nói thao tác xóa user làm giảm MAU đã ghi nhận trong billing cycle hiện tại. [Anonymous Sign-Ins - Automatic cleanup](https://supabase.com/docs/guides/auth/auth-anonymous#automatic-cleanup)
- Dashboard cho xem MAU theo organization, chọn project và time period; tài liệu không công bố breakdown anonymous/permanent hoặc freshness/latency guarantee của metric. [Monthly Active Users - View usage](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users#view-usage)

Đây là acceptance của **research artifact**, không phải kết luận Supabase phù hợp hay không phù hợp với destination.

## Bối cảnh repo được đối chiếu

- [#25 resolution Q14](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25#issuecomment-5408934507) chốt Player chưa đăng ký dùng phiên ẩn danh có user id, không dùng IP, và dự kiến link sang Google để Skill Estimate đi theo user. Cùng resolution, bảng **#25 KHÔNG quyết định** giao schema/retention, lịch sử, PII và privacy cho #14; "ẩn số MAU của user ẩn danh" được để lại cho ticket mới. Báo cáo này chỉ kiểm tra premise vendor, không lấp các quyết định đó.
- [#8 resolution](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8#issuecomment-5379815241) và [`docs/research/2026-08-22-zero-cost-vercel-architecture.md`](./2026-08-22-zero-cost-vercel-architecture.md) coi Supabase Free trong dedicated organization là phương án live-beta có điều kiện, ghi quota 50.000 MAU, Fair Use grace/restriction và yêu cầu fail closed. Findings hiện tại xác nhận quota và database-size risk của anonymous user, nhưng vendor vẫn không nối anonymous sign-in với MAU accounting bằng một tuyên bố trực tiếp.
- [Map #1 Destination/Notes](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1) hiện yêu cầu chơi được khi chưa lập nick, giữ identity khi link provider, và recurring cost bằng 0 với quota exhaustion fail closed. Báo cáo không thay đổi destination hoặc Notes.

## Documented

### Ma trận câu trả lời

Trong bảng này, `Yes`/`No` trả lời đúng mệnh đề ở cột đầu; `Not documented` nghĩa là các nguồn Supabase đã khảo sát không công bố hành vi đó.

| Câu hỏi | Kết quả | Điều Supabase thực sự tài liệu hóa |
| --- | --- | --- |
| Anonymous user có tính vào MAU khi `signInAnonymously()` không? | **Not documented** | **Supabase does not document this as of 2026-08-25.** `signInAnonymously()` "creates an anonymous user"; MAU là distinct user "who log in or refresh their token" trong billing cycle. Ghép hai định nghĩa tạo một suy luận mạnh, nhưng không phải tuyên bố accounting riêng cho anonymous. [Anonymous Sign-Ins](https://supabase.com/docs/guides/auth/auth-anonymous), [MAU - What you are charged for](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users#what-you-are-charged-for) |
| Sign-in hoặc token refresh có kích hoạt MAU không? | **Yes** | Cả log in và refresh token đều nằm trong định nghĩa; mỗi unique user chỉ tính một lần trong cycle dù authenticate nhiều lần. [MAU - What you are charged for](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users#what-you-are-charged-for) |
| Sau khi mất anonymous browser session, gọi anonymous sign-in để tạo lại ảnh hưởng MAU thế nào? | **Not documented** | **Supabase does not document this as of 2026-08-25.** Anonymous user cũ không truy cập lại được sau sign-out, clear browsing data hoặc dùng thiết bị khác, và mỗi lời gọi anonymous sign-in tạo một user. Docs không nối ca tạo lại này với MAU ledger. [Anonymous Sign-Ins](https://supabase.com/docs/guides/auth/auth-anonymous), [MAU](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users) |
| Có thể link Google vào anonymous user hiện tại không? | **Yes** | Manual linking phải được bật; `linkIdentity({ provider: 'google' })` link OAuth identity "to the user" đang đăng nhập. [Anonymous Sign-Ins - Link an OAuth identity](https://supabase.com/docs/guides/auth/auth-anonymous#link-an-oauth-identity), [Identity Linking](https://supabase.com/docs/guides/auth/auth-identity-linking#manual-linking-beta) |
| Link Google vào anonymous user ảnh hưởng MAU accounting thế nào? | **Not documented** | **Supabase does not document this as of 2026-08-25.** Docs nói identity được link vào user hiện tại, nhưng không mô tả MAU ledger khi anonymous user được chuyển đổi hoặc link provider. [Identity Linking](https://supabase.com/docs/guides/auth/auth-identity-linking#manual-linking-beta), [MAU](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users) |
| Có thể xóa thủ công anonymous Auth user không? | **Yes** | Supabase đưa SQL xóa anonymous users và cho phép xóa Auth user qua API hoặc Dashboard. Xóa row mặc định cascade session và vô hiệu refresh token; access JWT đã phát vẫn valid tới expiry. [Anonymous Sign-Ins - Automatic cleanup](https://supabase.com/docs/guides/auth/auth-anonymous#automatic-cleanup), [User Management - Deleting users](https://supabase.com/docs/guides/auth/managing-user-data#deleting-users) |
| Xóa riêng anonymous user có giảm MAU đã ghi trong cycle hiện tại không? | **Not documented** | **Supabase does not document this as of 2026-08-25.** Billing FAQ chỉ nói pause/delete **project** không xóa usage đã phát sinh; không nói delete một Auth user. [Billing FAQ - Fair Use Policy](https://supabase.com/docs/guides/platform/billing-faq#fair-use-policy), [User Management - Deleting users](https://supabase.com/docs/guides/auth/managing-user-data#deleting-users) |
| Dashboard có breakdown MAU anonymous so với permanent/provider không? | **Not documented** | **Supabase does not document this as of 2026-08-25.** Trang MAU chỉ công bố aggregate cho selected time period, all projects mặc định và project dropdown. [MAU - View usage](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users#view-usage) |
| Metric MAU có freshness/update latency guarantee không? | **Not documented** | **Supabase does not document this as of 2026-08-25.** Pricing nói usage page có thể được xem "at any time" và upcoming invoice "updates as you go", nhưng không đặt refresh interval, lag bound hoặc SLO. [Pricing - How can I track my usage?](https://supabase.com/pricing) |
| Supabase có automatic cleanup anonymous users không? | **No** | Trang anonymous ghi "Automatic cleanup of anonymous users is currently not available" và đưa SQL delete thủ công làm ví dụ. [Anonymous Sign-Ins - Automatic cleanup](https://supabase.com/docs/guides/auth/auth-anonymous#automatic-cleanup) |

### Chuỗi accounting và ambiguity cần giữ nguyên

Ba phát biểu vendor cùng tồn tại:

1. Pricing ghi **Anonymous Sign-ins: Included** trên cả Free, Pro, Team và Enterprise. Đây là availability/feature inclusion. [Pricing - Auth](https://supabase.com/pricing)
2. Pricing ghi **Total Users: Unlimited**, nhưng ghi **MAUs: 50,000 included** trên Free. Vendor trình bày chúng thành hai dòng metric riêng nhưng không định nghĩa chi tiết hơn nhãn `Total Users`. [Pricing - Auth](https://supabase.com/pricing)
3. Trang MAU định nghĩa billable usage là distinct user log in hoặc refresh, còn trang anonymous nói anonymous sign-in tạo user và user đó "behaves like a permanent user" trừ khả năng truy cập lại sau khi mất session. [MAU](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users), [Anonymous Sign-Ins](https://supabase.com/docs/guides/auth/auth-anonymous)

Vì vậy, "Anonymous Sign-ins: Included" không tài liệu hóa một exemption khỏi MAU. Đồng thời, Supabase không đặt một câu explicit cạnh pricing rằng anonymous user được đưa vào MAU. Báo cáo giữ nguyên ambiguity về cách diễn đạt của vendor và chỉ áp đúng các định nghĩa đã công bố; không tự diễn giải `Included` thành "unlimited anonymous MAU".

### Năm đại lượng không được trộn

| Đại lượng | Nghĩa được tài liệu hóa | Free Plan hiện hành |
| --- | --- | --- |
| **Feature included** | Quyền dùng Anonymous Sign-ins trên plan; không phải đơn vị usage. | Included. [Pricing - Auth](https://supabase.com/pricing) |
| **Total Users** | Pricing liệt kê `Total Users` thành một dòng riêng với `MAUs`; các docs đã khảo sát không định nghĩa chi tiết hơn nhãn này. Việc coi nó là total user records là cách đọc, không phải định nghĩa vendor được trích. | Unlimited. [Pricing - Auth](https://supabase.com/pricing) |
| **MAU** | Số distinct users sign in hoặc refresh token trong billing cycle; mỗi user tối đa một count/cycle, count reset đầu cycle. | 50.000 included; over-usage hiển thị `-` trên Free. [MAU - Pricing](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users#pricing) |
| **Database size** | Dữ liệu PostgreSQL; anonymous users được lưu trong database và vendor cảnh báo abuse có thể làm database size tăng mạnh. Đây không phải Supabase file Storage. | 500 MB database size/project; file Storage là quota riêng 1 GB. [Pricing - Database and Storage](https://supabase.com/pricing), [Anonymous Sign-Ins - Abuse prevention](https://supabase.com/docs/guides/auth/auth-anonymous#abuse-prevention-and-rate-limits) |
| **Endpoint rate limit** | Vendor trực tiếp ghi anonymous sign-in endpoint `/auth/v1/signup` được limited by IP. Việc tách endpoint limit khỏi MAU quota là phân loại của báo cáo; vendor không nói rate limit này deduplicate người hoặc MAU giữa browser/device. | 30 requests/IP/hour, burst tối đa 30; có thể cấu hình trong Auth rate limits. [Production Checklist - Auth rate limits](https://supabase.com/docs/guides/deployment/going-into-prod#auth-rate-limits), [Anonymous Sign-Ins - Abuse prevention](https://supabase.com/docs/guides/auth/auth-anonymous#abuse-prevention-and-rate-limits) |

### Usage có thể quan sát và Fair Use

- Organization usage page hiển thị MAU cho tất cả projects mặc định, cho phép chọn một project và time period khác. Upcoming invoice trên billing page cập nhật trong quá trình sử dụng. [MAU - View usage](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users#view-usage), [Pricing - How can I track my usage?](https://supabase.com/pricing)
- Free quota là 50.000 MAU/cycle; count reset đầu billing cycle. Free không có MAU over-usage price trong bảng MAU. [MAU - Pricing](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users#pricing)
- Khi Free vượt quota, Supabase gửi notification và cho grace period; nếu tiếp tục vượt, restriction có thể gồm pause projects, database read-only, cấm launch/transfer project hoặc API trả `402`, thường áp trên toàn organization. Suspected abuse có thể bị restrict không báo trước. [Billing FAQ - Fair Use Policy](https://supabase.com/docs/guides/platform/billing-faq#fair-use-policy)
- Grace period không được công bố độ dài. Sau khi đã dùng grace period, lần vượt tiếp theo có thể bị restrict không có grace period mới cho tới khi warning tự clear sau nhiều billing cycles dưới quota. [Billing FAQ - grace period](https://supabase.com/docs/guides/platform/billing-faq#what-is-a-grace-period-and-does-it-reset-after-usage-drops)
- Pause/delete project dừng usage mới nhưng không xóa usage đã phát sinh trong cycle; restriction do quota được gỡ khi quota refill đầu cycle, có thể có short delay. [Billing FAQ - removing restrictions](https://supabase.com/docs/guides/platform/billing-faq#how-can-i-remove-restrictions-applied-from-the-fair-use-policy)

### Deletion và cleanup

- Automatic cleanup anonymous user không có. SQL mẫu xóa `auth.users` có `is_anonymous = true` và `created_at` cũ hơn 30 ngày chỉ là cơ chế manual được minh họa; **30 ngày là literal trong ví dụ vendor, không phải retention recommendation được báo cáo này chọn**. [Anonymous Sign-Ins - Automatic cleanup](https://supabase.com/docs/guides/auth/auth-anonymous#automatic-cleanup)
- Supabase cho phép xóa Auth user trực tiếp hoặc qua Dashboard. Xóa bằng `auth.admin.deleteUser()` mặc định xóa row, cascade sessions và làm refresh token không mint được access token mới; access JWT đã phát hành vẫn valid tới expiry. [User Management - Deleting users](https://supabase.com/docs/guides/auth/managing-user-data#deleting-users)
- Supabase không nối tài liệu deletion/cleanup Auth với MAU ledger. Do đó không thể tuyên bố cleanup trước cuối cycle sẽ lấy lại MAU quota.

## Not documented

Các câu sau vẫn là unknown sau khi đọc bảy trang trong **Nguồn Supabase chính thức** và tìm trong đó các cụm `anonymous`, `MAU`, `monthly active`, `billing`, `delete`, `cleanup`, `link`, `usage`, `freshness` và `latency`:

- Anonymous sign-in có được đưa vào MAU accounting hay không: **Supabase does not document this as of 2026-08-25.**
- Tạo anonymous user mới sau khi mất browser session ảnh hưởng MAU ledger thế nào: **Supabase does not document this as of 2026-08-25.**
- Link Google vào anonymous user hiện tại ảnh hưởng MAU ledger thế nào: **Supabase does not document this as of 2026-08-25.**
- Anonymous/permanent/provider MAU breakdown trong Dashboard hoặc API: **Supabase does not document this as of 2026-08-25.**
- Freshness, refresh cadence, maximum lag hoặc SLO của MAU usage metric/upcoming invoice: **Supabase does not document this as of 2026-08-25.**
- Delete một Auth user có trừ distinct-user MAU đã ghi trong billing cycle hiện tại hay không: **Supabase does not document this as of 2026-08-25.**
- Thời lượng grace period, pre-restriction margin và thứ tự resource bị restrict khi vượt Free MAU: **Supabase does not document this as of 2026-08-25.**
- Một API chính thức để lấy live per-user MAU ledger hoặc anonymous-only MAU count: **Supabase does not document this as of 2026-08-25.**

Không dùng community post, blog không phải docs chính thức hoặc support guess để lấp các khoảng trống này.

## Implications/constraints for later decisions

Các dòng dưới đây là đầu vào/ràng buộc cho ticket sau, không phải quyết định:

- Mô hình Player dùng phiên ẩn danh của #25 tạo Auth user thật. Suy luận vận hành an toàn là anonymous user có thể tiêu MAU và một browser/device mất session có thể tạo thêm distinct usage, nhưng Supabase không tài liệu hóa accounting riêng cho hai ca này. Endpoint IP rate limit cũng không được tài liệu hóa như một cơ chế deduplicate MAU giữa browser/device.
- Vendor trực tiếp nói manual linking gắn Google identity "to the user" đang đăng nhập. Điều đó hỗ trợ premise identity của #25, nhưng không tự bảo đảm Skill Estimate đi theo: continuity của application data còn phụ thuộc cách DigitCode neo dữ liệu. Tác động lên MAU accounting vẫn chưa được tài liệu hóa. Conflict với một existing account cần application handling; Supabase nêu rõ conflict resolution phụ thuộc application requirements. [Anonymous Sign-Ins - Resolving identity conflicts](https://supabase.com/docs/guides/auth/auth-anonymous#resolving-identity-conflicts)
- `Total Users: Unlimited` không loại rủi ro capacity: anonymous records vẫn dùng database và Free database size là 500 MB/project. MAU, database growth và endpoint abuse là ba constraint riêng mà các ticket sau phải quyết định cách quan sát và kiểm soát.
- Dashboard aggregate có thể dùng để đối soát organization/project usage, nhưng tài liệu không đủ để dùng nó như hard real-time admission control trước restriction. Không có freshness bound, grace duration hoặc guaranteed warning trong suspected-abuse case.
- Dedicated Free organization từ #8 vẫn là một isolation constraint có cơ sở: plan/quota và Fair Use được áp theo organization, còn usage page mặc định tổng hợp mọi project. Findings này không quyết định có tiếp tục topology đó hay không.
- Manual deletion có thể là một primitive kỹ thuật cho retention policy sau này, nhưng vendor example 30 ngày không chọn retention cho DigitCode, và deletion không được chứng minh là công cụ lấy lại MAU trong current cycle.
- Free MAU over-usage không có đơn giá, nhưng "recurring cost bằng 0" và "không service restriction" là hai thuộc tính khác nhau. Tài liệu nói Fair Use restriction **có thể** áp dụng khi tiếp tục vượt Free quota; nó không bảo đảm một hard-stop tức thời, loại restriction cụ thể hoặc ngưỡng admission chính xác.

## Nguồn Supabase chính thức

- [Manage Monthly Active Users usage](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users)
- [Anonymous Sign-Ins](https://supabase.com/docs/guides/auth/auth-anonymous)
- [Supabase Pricing](https://supabase.com/pricing)
- [Billing FAQ - Fair Use Policy](https://supabase.com/docs/guides/platform/billing-faq#fair-use-policy)
- [Production Checklist - Auth rate limits](https://supabase.com/docs/guides/deployment/going-into-prod#auth-rate-limits)
- [Identity Linking](https://supabase.com/docs/guides/auth/auth-identity-linking)
- [User Management](https://supabase.com/docs/guides/auth/managing-user-data)
