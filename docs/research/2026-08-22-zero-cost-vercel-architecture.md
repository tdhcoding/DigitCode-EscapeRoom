# Kiến trúc zero-cost tương thích Vercel cho DigitCode Web Multiplayer

- Ngày khảo sát: 2026-08-22
- Ticket: [#8 - Nghiên cứu kiến trúc zero-cost tương thích Vercel](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8)
- Phạm vi: Production MVP 1v1, frontend và web API trên Vercel, Google OAuth + email magic link, PostgreSQL, realtime server-authoritative, URL `*.vercel.app`, không recurring charge hoặc automatic overage.
- Tính thời điểm: quota và điều khoản dưới đây là snapshot tại ngày khảo sát; phải kiểm tra lại trước khi launch.

## Kết luận điều hành

Không có tổ hợp managed free-tier nào có thể được chứng minh là **production-grade vô điều kiện** dưới toàn bộ ràng buộc hiện tại. Ba chặn chính là:

1. Vercel Hobby chỉ dành cho non-commercial personal use và sẽ pause khi vượt included usage. Nó phù hợp một live beta cá nhân/phi thương mại, không phải nền tảng production thương mại. [Vercel Hobby](https://vercel.com/docs/plans/hobby)
2. Supabase Auth mặc định không thể gửi magic link công khai: SMTP mặc định chỉ gửi tới địa chỉ thành viên project, hiện giới hạn 2 email/giờ và không dành cho production. [Supabase custom SMTP](https://supabase.com/docs/guides/auth/auth-smtp)
3. Brevo Free là một relay khả dụng trong khảo sát vì có SMTP transactional, không cần thẻ và cho xác minh một sender riêng lẻ khi chưa sở hữu domain; tuy nhiên domain không được authenticate làm giảm deliverability, có thể làm Brevo thay địa chỉ `From`, và không tạo ra bảo đảm production. [Brevo plans](https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans), [sender verification](https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email)

Phương án ít rủi ro nhất để tiếp tục dưới dạng **live beta có điều kiện** là:

- Vercel Hobby chạy Next.js và API tại `sin1`.
- Supabase Free tại `ap-southeast-1` cung cấp Auth, PostgreSQL và Realtime.
- PostgreSQL transaction là authority duy nhất; Realtime chỉ fan-out state đã commit.
- Google OAuth chạy qua Supabase Auth; magic link dùng Supabase Auth với Brevo Free SMTP.
- Client không được quyền ghi trực tiếp game state hoặc tự quyết timer, score, winner hay Elo.

Phương án này giữ Match và Elo trong một consistency boundary, ít dịch vụ và ít failure mode hơn Neon + Ably hoặc Durable Objects + PostgreSQL. Nó chỉ được launch nếu human-in-the-loop chấp nhận các caveat phi thương mại, không SLA/backup, project pause và email không có authenticated domain. Nếu "Production MVP" đòi hỏi SLA, commercial use hoặc email deliverability có uy tín, cần nới ít nhất một ràng buộc về paid baseline/custom domain.

## Tiêu chí đánh giá

Trong báo cáo này:

- **Zero-cost** nghĩa là tài khoản vẫn ở free plan và không có đường tự động tạo paid overage.
- **Fail closed về chi phí** nghĩa là dịch vụ từ chối, giới hạn hoặc pause thay vì tự động tính phí.
- **Fail closed về game** nghĩa là khi authority hoặc durable store không xác nhận transaction, command thất bại; client không được tiếp tục bằng state tự suy đoán.
- "Có region Singapore" không đồng nghĩa latency Việt Nam đã được chứng minh. Không có vendor nào trong khảo sát công bố benchmark đại diện cho mạng người dùng Việt Nam.

## Các giới hạn quyết định kiến trúc

| Dịch vụ | Free-tier hiện hành | Sleep, region và độ bền | Khi vượt quota | Thẻ/overage | Kết luận |
| --- | --- | --- | --- | --- | --- |
| **Vercel Hobby** | 4 active CPU-hours/tháng, 360 GB-hours provisioned memory, 1 triệu Function invocations, 1 triệu Edge Requests và Function tối đa 300 giây. Fair-use guidelines còn nêu mức điển hình 100 GB Fast Data Transfer và 10 GB Fast Origin Transfer/tháng. [Hobby](https://vercel.com/docs/plans/hobby), [Function pricing](https://vercel.com/docs/functions/usage-and-pricing), [fair use](https://vercel.com/docs/limits/fair-use-guidelines#typical-monthly-usage-guidelines) | Một Function region; có thể chọn Singapore `sin1`. Fluid compute pre-warm và bytecode cache để giảm cold-start impact, nhưng first request chưa có cache và không có latency SLO. [Function regions](https://vercel.com/docs/functions/configuring-functions/region), [Fluid compute](https://vercel.com/docs/fluid-compute#bytecode-caching) | Hobby deployment bị pause khi vượt included usage; trong đa số trường hợp feature chỉ dùng lại sau 30 ngày. Không có on-demand overage cho Hobby. [plans](https://vercel.com/docs/plans#what-happens-when-i-reach-100-usage), [Hobby cycle](https://vercel.com/docs/plans/hobby#hobby-billing-cycle) | Free, nhưng tài liệu hiện hành không tuyên bố rõ "không cần thẻ" cho Hobby. Việc nâng Pro mới yêu cầu card details. | Fail closed về chi phí, nhưng thời điểm/grace trước pause không được đặc tả. Chỉ hợp lệ nếu dự án vẫn là non-commercial personal use. |
| **Supabase Free** | 2 active projects; 50.000 MAU, 5 GB egress, 1 GB Storage, 2 triệu Realtime messages/tháng và 200 peak connections được cộng dồn theo organization; PostgreSQL 500 MB là per project. Nano có 60 max database connections và 200 max pooler clients. [pricing](https://supabase.com/pricing), [billing scope](https://supabase.com/docs/guides/platform/billing-on-supabase#variable-usage-fees-and-quotas), [compute limits](https://supabase.com/docs/guides/platform/compute-and-disk#postgres-replication-slots-wal-senders-and-connections) | Có exact AWS Singapore `ap-southeast-1`. Free project có thể bị pause sau một tuần inactivity; không có automatic backups hoặc uptime SLA. [regions](https://supabase.com/docs/guides/platform/regions), [pricing](https://supabase.com/pricing) | Free nhận cảnh báo và grace period; nếu tiếp tục vượt, restriction có thể là pause, database read-only hoặc API `402`. Restriction được gỡ khi quota refill. [Billing FAQ](https://supabase.com/docs/guides/platform/billing-faq#fair-use-policy) | Free không có giá overage; tài liệu billing không hứa rõ signup Free không cần thẻ. | Fit tốt nhất về consistency và region, nhưng restriction không xảy ra chính xác ngay tại byte/message vượt ngưỡng và không có SLA. |
| **Neon Free** | 100 CU-hours/project/tháng, 0,5 GB continuous storage/project, 5 GB public egress/tháng, tối đa 2 CU. [plans](https://neon.com/docs/introduction/plans) | Scale-to-zero bắt buộc sau 5 phút không có active query. Có AWS Singapore `aws-ap-southeast-1`; region cố định sau khi tạo project. [plans](https://neon.com/docs/introduction/plans#scale-to-zero), [regions](https://neon.com/docs/introduction/regions) | Hết CU-hours hoặc egress làm compute suspend tới kỳ sau/nâng cấp; write làm tăng storage sẽ fail khi quá 0,5 GB. Dữ liệu không bị xóa. [Free limits](https://neon.com/docs/introduction/plans#faqs) | Neon tuyên bố Free permanent và no credit card. [pricing](https://neon.com/pricing) | Fail closed rõ và Postgres tốt, nhưng cần auth + realtime riêng; cold wake và nhiều consistency boundary hơn Supabase. |
| **Cloudflare Workers + Durable Objects Free** | Workers: 100.000 requests/ngày, 10 ms CPU/request, 128 MB/isolate. SQLite DO: 100.000 requests/ngày, 13.000 GB-s/ngày, 5 triệu rows read/ngày, 100.000 rows written/ngày, 5 GB total storage. [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), [DO pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/) | WebSocket Hibernation giữ socket nhưng cho phép object rời memory; in-memory state phải được phục hồi từ storage. `apac-se` chỉ là best-effort hint, không bảo đảm Singapore. [WebSocket Hibernation](https://developers.cloudflare.com/durable-objects/best-practices/websockets/), [data location](https://developers.cloudflare.com/durable-objects/reference/data-location/) | Free-tier operation thuộc loại quota đã cạn sẽ fail với error; daily quota reset 00:00 UTC. Workers route có thể cấu hình fail closed để trả Error 1027. | Tài liệu không tuyên bố rõ no-card cho Workers/DO Free. Không có paid overage khi vẫn ở Free. | Bằng chứng fail-closed mạnh nhất, nhưng thêm authority ngoài Vercel, không pin Singapore và tạo bài toán đồng bộ DO/Postgres. |
| **Ably Free** | 6 triệu messages/tháng, 250.000/giờ, 500/giây, 200 concurrent connections và 200 concurrent channels. [limits](https://ably.com/docs/platform/pricing/limits) | Có global edge/Singapore infrastructure nhưng Free không chọn hoặc bảo đảm nơi xử lý; geo restriction là Enterprise concern. [network](https://ably.com/network), [architecture](https://ably.com/docs/platform/architecture/edge-network) | Count limits chặn resource vượt ngưỡng; rate limits có thể reject hoặc probabilistic suppression. Nhiều quota có buffer không công bố. [exceeding limits](https://ably.com/docs/platform/pricing/limits#exceeding-a-limit) | Free không cần thẻ và không hết hạn. [pricing FAQ](https://ably.com/docs/platform/pricing/faqs) | Dùng tốt làm fan-out, không được dùng làm authority. Không đáp ứng deterministic fail-closed cho monthly message limit. |
| **Pusher Channels Sandbox** | 200.000 messages/ngày và 100 concurrent connections. [pricing](https://pusher.com/channels/pricing/) | App chọn được public cluster `ap1` đặt tại Singapore. [clusters](https://pusher.com/docs/channels/miscellaneous/clusters/) | Chạm hard event limit thì server publish trả `403`; chạm connection limit thì client mới bị từ chối. Cửa sổ ngày là 00:00-23:59 UTC. [limit behavior](https://docs.bird.com/pusher/channels/channels/limits/what-happens-when-i-hit-my-channels-plan-limits), [limit period](https://docs.bird.com/pusher/channels/channels/limits/over-what-time-period-are-my-channels-limits-counted) | Pricing gọi Sandbox là Free nhưng tài liệu không cam kết rõ no-card. | Quota behavior và Singapore rõ hơn Ably, nhưng chỉ tối đa danh nghĩa 50 Match 1v1 đồng thời và vẫn cần auth + DB riêng. |
| **Brevo Free** | 300 email sends/ngày, transactional email/SMTP, no time limit. [plans](https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans) | Free không công bố uptime SLA. Sender chưa authenticate domain có thể xác minh bằng mã 6 số gửi tới chính địa chỉ sender. [sender verification](https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email) | Sau 300 sends, tối đa 1.000 email thêm được giữ trong retry queue; email sau đó không được deliver. Unused sends không rollover. [Free limits](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan) | Free forever, no credit card required. | Một cầu nối magic-link khả dụng với ràng buộc no-domain/no-card, nhưng queue làm failure không hoàn toàn tức thời và unauthenticated domain là rủi ro launch. |

## Vercel WebSocket: thông tin cũ đã hết hiệu lực

Vercel Functions hiện có thể serve WebSocket bằng Fluid compute; thông tin cũ cho rằng Vercel hoàn toàn không hỗ trợ WebSocket không còn đúng. Tuy nhiên capability này vẫn không phù hợp làm authority chính cho Match:

- WebSocket đang được công bố dưới dạng Public Beta; trang docs ghi `Permissions Required: WebSockets` nhưng không tuyên bố cụ thể quyền này có trên mọi Hobby account. [WebSocket docs](https://vercel.com/docs/functions/websockets), [Public Beta announcement](https://vercel.com/changelog/websocket-support-is-now-in-public-beta)
- Socket đóng khi Function đạt max duration. Hobby có maximum 300 giây, nên một Match đủ 15 phút phải chịu ít nhất hai lần reconnect theo thiết kế. [WebSocket lifecycle](https://vercel.com/docs/functions/websockets#handle-disconnections-and-reconnects), [Function limits](https://vercel.com/docs/functions/limitations#max-duration)
- Reconnect có thể tới Function instance khác; presence, room, counter và durable state phải nằm ở external store. [persistent state](https://vercel.com/docs/functions/websockets#manage-persistent-state)
- Next.js chưa có stable native upgrade API; Vercel hướng dẫn dùng `experimental_upgradeWebSocket()`. [Next.js WebSocket](https://vercel.com/docs/functions/websockets#nextjs)
- Vercel không công bố WebSocket-specific concurrency, message-rate hoặc message-size limit. Socket vẫn dùng Function, transfer và provisioned-memory quotas chung. [limits and pricing](https://vercel.com/docs/functions/websockets#limits-and-pricing)

Vì vậy Vercel WebSocket chỉ nên là transport có thể thay thế. Nếu mọi command vẫn phải transaction vào PostgreSQL và reconnect vẫn phải nạp snapshot, managed Realtime đã cung cấp đúng vai trò với ít beta risk hơn.

## Auth và email magic link

| Phương án | Google OAuth | Magic link | Domain/thẻ | Kết luận |
| --- | --- | --- | --- | --- |
| **Supabase Auth + Brevo SMTP** | Social OAuth có trong Free. [Supabase pricing](https://supabase.com/pricing) | Supabase hỗ trợ passwordless email khi cấu hình custom SMTP; Brevo có transactional SMTP 300 sends/ngày. [Supabase SMTP](https://supabase.com/docs/guides/auth/auth-smtp), [Brevo plans](https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans) | Brevo no-card và có thể verify sender email riêng lẻ; domain authentication vẫn được khuyến nghị/yêu cầu để đáp ứng chuẩn Gmail/Yahoo. | **Chọn có điều kiện.** Phải test deliverability, bật CAPTCHA tại Supabase Auth và rate-limit app trước launch. |
| **Firebase Auth Spark** | Có Google sign-in; backend có thể verify ID token. [Google sign-in](https://firebase.google.com/docs/auth/web/google-signin), [verify ID tokens](https://firebase.google.com/docs/auth/admin/verify-id-tokens) | Spark chỉ có 5 email-link sign-in emails/ngày. [Auth limits](https://firebase.google.com/docs/auth/limits) | Nâng quota gắn với billed tier/billing instrument. | Loại: 5/ngày không đủ cho public MVP. |
| **Clerk Hobby** | Có social connections và magic links; 50.000 MRU/app, no card. [pricing](https://clerk.com/pricing) | Managed email link có sẵn. | Production instance yêu cầu domain sở hữu, quyền thêm DNS record và OAuth credentials riêng. [production deployment](https://clerk.com/docs/guides/development/deployment/production) | Loại khi MVP chỉ có `*.vercel.app`. |
| **Resend Free làm SMTP** | Không phải auth provider. | 3.000 email/tháng, 100/ngày, không Free overage. [pricing](https://resend.com/pricing) | Bắt buộc add và verify ít nhất một domain sở hữu. [verified domains](https://resend.com/docs/dashboard/domains/introduction) | Loại vì không có custom domain. |
| **Neon Auth** | Managed Better Auth có OAuth. | Auth vẫn Beta; production checklist yêu cầu custom SMTP cho verification email. [Neon Auth production checklist](https://neon.com/docs/auth/production-checklist) | Không giải quyết sender domain; còn thêm beta dependency. | Không chọn cho Production MVP hiện tại. |

Brevo không biến email từ free public domain thành một sender có reputation production. Brevo nêu rõ free domains như Gmail/Yahoo không thể authenticate; sender có thể bị thay bằng địa chỉ thuộc `t-sender-sib.com`. Do đó magic link phải được xem là **launch gate**, không phải một fact đã giải quyết hoàn toàn. [Brevo sender requirements](https://help.brevo.com/hc/en-us/articles/14925263522578-Comply-with-Gmail-Yahoo-and-Microsoft-s-requirements-for-email-senders)

## So sánh topology

### A. Vercel + Supabase tích hợp

```text
Browser
  | HTTPS command + Supabase user JWT
  v
Next.js/Vercel API (sin1)
  | publishable key + same user JWT
  v
Supabase Data API/RPC -> PostgreSQL (ap-southeast-1)
  | committed, sanitized event
  v
Supabase private Realtime channel ----> Browser

Supabase Auth ----SMTP----> Brevo Free ----> magic-link recipient
```

Đánh giá:

- **Correctness:** tốt nhất vì Match, command deduplication, final result và hai Elo update cùng một PostgreSQL transaction.
- **Security:** Vercel chuyển tiếp user JWT qua Data API bằng publishable key, nên request được map sang role `authenticated` và có `auth.uid()` thay vì vào bằng `service_role`. Data API chỉ expose narrowly-granted `security invoker` wrappers; owner-privileged implementations nằm trong non-exposed schema. Private Realtime chỉ có `SELECT` policy để client nhận Broadcast theo membership; không có client `INSERT` policy trong MVP. [API keys and Auth](https://supabase.com/docs/guides/api/api-keys#interaction-with-supabase-auth), [securing the Data API](https://supabase.com/docs/guides/database/hardening-data-api), [security definer placement](https://supabase.com/docs/guides/database/postgres/row-level-security#use-security-definer-functions), [Realtime Authorization](https://supabase.com/docs/guides/realtime/authorization)
- **Realtime:** Supabase khuyến nghị Broadcast thay Postgres Changes cho scalability/security. Trigger `realtime.broadcast_changes()` phát cả `NEW`/`OLD`, nên chỉ được gắn vào notification table chỉ chứa `match_id`, committed `version` và event type, không gắn vào bảng puzzle/PlayerState. [database changes](https://supabase.com/docs/guides/realtime/subscribing-to-database-changes)
- **Region:** Vercel Function và Supabase đều chọn chính xác Singapore; điều này giảm khoảng cách giữa API và DB nhưng chưa chứng minh latency từ Việt Nam.
- **Failure mode:** mất Realtime không làm mất authority; client reconnect rồi tải snapshot theo version. Mất DB làm command fail closed.
- **Lock-in:** trung bình. PostgreSQL schema/transaction portable; Supabase Auth, Realtime RLS và helper functions là phần proprietary.
- **Operational risk:** project pause, không automatic backup, không SLA, quota restriction có grace period và Brevo deliverability.

**Kết luận:** topology được khuyến nghị nếu chấp nhận live beta có điều kiện.

### B. Vercel + Neon PostgreSQL + Ably hoặc Pusher

Đánh giá:

- Neon cung cấp Postgres Singapore, no-card và hành vi hết compute/egress/storage rõ hơn Supabase.
- Ably cung cấp no-card nhưng không pin Singapore và không hard-stop phần lớn quota ngay đúng ngưỡng; Pusher có Singapore/hard reject rõ hơn nhưng no-card chưa được tài liệu xác nhận.
- Stack vẫn cần auth provider và email relay thứ tư/thứ năm.
- PostgreSQL commit và realtime publish không cùng transaction. Cần transactional outbox, publisher retry và client snapshot recovery; Vercel Hobby không tự cung cấp một durable continuously-running outbox worker.
- Scale-to-zero sau 5 phút làm query đầu tiên chịu wake path; session-scoped state như temporary tables, prepared statements, advisory locks và `LISTEN/NOTIFY` không được dùng làm durable coordination. [Neon compute lifecycle](https://neon.com/docs/introduction/compute-lifecycle#session-context-considerations)

**Kết luận:** không chọn cho MVP. Nó không tăng correctness nhưng tăng số vendor, token bridge, outbox machinery và failure mode.

### C. PostgreSQL ledger + Cloudflare Durable Object theo Match

Đánh giá:

- Một Durable Object có thể serialize command cho một Match và giữ WebSocket bằng Hibernation; đây là runtime realtime mạnh nhất trong các free option.
- Nếu DO là authority còn Postgres là ledger, không có atomic transaction xuyên DO storage và PostgreSQL. Crash ở giữa tạo split-brain hoặc settlement thiếu.
- Nếu PostgreSQL vẫn là authority và DO chỉ serialize/cache/fan-out, mọi command vẫn phải round-trip DB; lợi ích so với topology A không bù complexity.
- `apac-se` chỉ là location hint best-effort, không phải exact Singapore placement.
- Workers/DO endpoint còn đưa custom backend ra ngoài Vercel, lệch khỏi quyết định "web APIs chạy trên Vercel" nếu không được HITL miễn trừ.
- Lock-in cao vì DO identity, storage transaction, alarm và Hibernation API là Cloudflare-specific.

**Kết luận:** không chọn cho MVP. Chỉ cân nhắc lại nếu requirement tương lai cần room process lâu sống hơn và cho phép backend ngoài Vercel/paid migration path.

### D. Vercel native WebSocket + durable PostgreSQL

Đánh giá:

- Có thể prototype nhờ Public Beta, nhưng mỗi full Match cần reconnect do 300-second duration.
- In-memory room không durable và không dùng được qua reconnect/deployment/multiple instances.
- External store/pubsub vẫn bắt buộc, nên phương án không loại được managed realtime dependency.
- WebSocket entitlement trên Hobby và các socket-specific limits chưa được official docs xác nhận.

**Kết luận:** giữ làm đối chứng/prototype, không đưa vào Production MVP.

## Kiến trúc authority được khuyến nghị

PostgreSQL phải là nơi duy nhất quyết định state. Đường truy cập được chọn cho MVP là **user-scoped Supabase Data API/RPC**, không phải direct PostgreSQL connection và không phải secret/`service_role` request:

- Browser gửi Supabase user JWT cùng command tới Vercel API.
- Vercel dùng publishable key và chuyển tiếp chính user JWT khi gọi `security invoker` command wrapper trong dedicated exposed API schema.
- Wrapper gọi exact-signature `security definer` implementation trong non-exposed internal schema. Private implementation lấy actor bằng `auth.uid()`, không nhận `user_id` từ command, tự kiểm tra membership rồi chạy toàn bộ transaction.
- Snapshot đi qua một exposed invoker wrapper khác; private implementation dùng cùng JWT, tự kiểm tra membership và chỉ project public Match state cùng PlayerState của caller.
- Browser giữ user JWT cho private Realtime channel; Realtime RLS kiểm tra membership khi join.

Game tables, owner-privileged implementations và Realtime-membership helper nằm trong non-exposed internal schema; dedicated exposed API schema chỉ chứa invoker wrappers. Revoke default table/function privileges. Role `authenticated` chỉ nhận các grant sau: `EXECUTE` exact wrapper signatures; internal-schema `USAGE`; `EXECUTE` exact private implementation/helper signatures; không có table privileges. Vì internal schema không nằm trong Data API Exposed schemas, client không thể gọi private definer bằng RPC URL. Realtime RLS chỉ cho `SELECT`/receive trên topic hợp lệ; không grant `INSERT`/client broadcast hoặc Presence trong MVP. [securing the Data API](https://supabase.com/docs/guides/database/hardening-data-api), [security definer placement](https://supabase.com/docs/guides/database/postgres/row-level-security#use-security-definer-functions), [Realtime authorization](https://supabase.com/docs/guides/realtime/authorization#broadcast)

Mỗi private `security definer` function phải tự enforce row filtering và được review như một security boundary, đặt `search_path = ''`, schema-qualify mọi object và reject khi `auth.uid()` null. Không function `security definer` nào được nằm trong exposed schema. [function security and privileges](https://supabase.com/docs/guides/database/functions#security-definer-vs-invoker), [Supabase RLS warning](https://supabase.com/docs/guides/database/postgres/row-level-security#use-security-definer-functions)

Publishable key không phải secret, nên caller có thể bỏ qua Vercel và gọi RPC trực tiếp. Do đó Vercel API là control point chứ không phải trust boundary: authentication, membership, payload/rate limits, phase/version, idempotency và admission limits bắt buộc được enforce lại trong PostgreSQL. Secret key authorize `service_role` và có thể bypass RLS khi request không mang user access token, vì vậy secret/`service_role` không được dùng trên player command hoặc snapshot path. [Supabase API keys](https://supabase.com/docs/guides/api/api-keys), [RLS bypass](https://supabase.com/docs/guides/database/postgres/row-level-security#bypassing-row-level-security)

Mỗi command transaction cần thực hiện theo một đường duy nhất:

1. Data API reject JWT không hợp lệ/hết hạn; private function lấy actor từ `auth.uid()` trước mọi thao tác khác và reject null actor, action ngoài allowlist hoặc serialized payload lớn hơn guardrail ban đầu 8 KiB.
2. Lookup `(actor_id, command_id)` trước limiter. Replay đã commit với cùng canonical hash trả actor-scoped result kể cả khi bucket đã cạn; cùng ID nhưng khác Match/action/payload/version bị reject.
3. Với command mới, áp database token bucket trên row riêng của actor trước khi chạm Match. Guardrail ban đầu là 20 commands/phút/actor, burst 5; chỉ đổi sau local test và HITL review.
4. Kiểm tra membership không lock để fail fast. Chỉ member mới được chạm per-Match limiter hoặc contested Match rows; membership phải được kiểm tra lại sau khi lock.
5. Insert `(actor_id, command_id, canonical_request_hash)` vào bảng deduplication. Unique-conflict do concurrent same-hash request phải đợi transaction gốc rồi trả cùng result; different-hash conflict bị reject.
6. Áp per-Match guardrail ban đầu 40 commands/phút rồi lock Match, membership rows và rating rows cần thiết bằng `SELECT ... FOR UPDATE`, theo cùng một thứ tự user ID ở mọi code path.
7. Dưới lock, kiểm tra lại membership, phase, terminal state, lockout, `expected_version`, admission state và `deadline_at` bằng database time.
8. Tính clue, penalty, solve, score và winner trong server-side function; không tin score/timestamp/result do client gửi.
9. Khi Match terminal, ghi final result và cập nhật cả hai Elo trong cùng transaction. Unique settlement row theo `match_id` ngăn Elo chạy hai lần.
10. Tăng monotonically increasing `version`, ghi sanitized notification row rồi commit. Realtime subscriber chỉ coi version mới là hợp lệ sau commit.

PostgreSQL `FOR UPDATE` chặn writer/locker khác trên cùng row tới cuối transaction; `SERIALIZABLE` cho guarantee mạnh hơn nhưng application phải retry SQLSTATE `40001`. [row locks](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS), [transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)

Các invariant bắt buộc:

- `matches.version` chỉ tăng; stale command bị reject hoặc trả snapshot mới.
- `commands` unique theo `(actor_id, command_id)` và lưu canonical hash của `match_id`, action, payload, `expected_version`; result replay luôn được scope theo actor.
- `rating_settlements.match_id` unique; Practice Match không có settlement row.
- `deadline_at` và `locked_until` là server timestamps; UI chỉ render countdown từ timestamp trả về.
- Không có server timer tick mỗi giây. Deadline được kiểm tra khi command/snapshot/finalization chạy.
- Secret puzzle và PlayerState đối thủ nằm trong internal tables/payload riêng; player roles không có direct table privileges, và snapshot RPC không trả row của đối thủ. RLS không chỉ che field ở UI.
- `service_role`/secret key không bao giờ vào browser. Supabase cảnh báo secret key bypass RLS. [RLS bypass](https://supabase.com/docs/guides/database/postgres/row-level-security#bypassing-row-level-security)
- Exposed wrappers dùng `security invoker`; mọi `security definer` implementation/helper nằm trong non-exposed schema, đặt `search_path = ''`, schema-qualify mọi object và chỉ grant exact signature cần thiết cho `authenticated`. [security definer placement](https://supabase.com/docs/guides/database/postgres/row-level-security#use-security-definer-functions), [function privileges](https://supabase.com/docs/guides/database/functions#function-privileges)
- Realtime trigger chỉ phát row của sanitized notification table trong cùng Match transaction; private topic policy gọi membership helper để kiểm tra `auth.uid()`. Event chỉ là invalidation/hint. Mất event, event lặp hoặc reconnect đều được sửa bằng `GET snapshot` và version.
- Realtime cache quyền tới lần client gửi JWT mới hoặc token hết hạn. Access-token expiry đặt 600 giây; khi membership đổi, transaction rotate một unguessable channel epoch và mọi event tiếp theo chuyển sang topic mới. Membership helper phải kiểm tra cả membership lẫn current epoch trong topic. Event cuối trên topic cũ chỉ báo invalidation, không chứa secret. [Realtime policy updates](https://supabase.com/docs/guides/realtime/authorization#updating-rls-policies), [JWT expiry guidance](https://supabase.com/docs/guides/auth/sessions#what-are-recommended-values-for-access-token-jwt-expiration)
- Payload schema, actor/per-Match token buckets và new-Match admission được kiểm tra trong RPC, không chỉ ở Vercel route, để direct Data API caller không bypass guardrail.

## Quota và capacity envelope

Các con số sau chỉ là upper bound theo quota, không phải capacity/SLA:

- Supabase 200 peak connections tương đương tối đa lý thuyết 100 Match 1v1 nếu mỗi player chỉ mở đúng một socket. Tabs phụ, reconnect overlap, dashboard và presence làm ceiling thực tế thấp hơn. [Realtime quotas](https://supabase.com/docs/guides/realtime/quotas)
- Recommended path dùng HTTP Data API/RPC, không mở một PostgreSQL connection cho mỗi Vercel invocation. Nano vẫn có 60 max database connections/200 max pooler clients ở tầng dưới; nếu sau này thay bằng direct SQL từ serverless thì phải dùng shared Supavisor transaction mode và tắt prepared statements. [compute limits](https://supabase.com/docs/guides/platform/compute-and-disk#postgres-replication-slots-wal-senders-and-connections), [connection methods](https://supabase.com/docs/guides/database/connecting-to-postgres#pooler-transaction-mode)
- Pusher Sandbox 100 connections tương đương tối đa lý thuyết 50 Match 1v1; Ably Free và Supabase Free đều có 200 connections.
- Supabase Broadcast tính một message gửi cộng một message cho mỗi subscriber nhận; một event gửi tới hai player thường tiêu thụ ba message units. Database Changes tính một message cho mỗi listening client. [Realtime message counting](https://supabase.com/docs/guides/platform/manage-your-usage/realtime-messages)
- Supabase Free giới hạn 100 messages/giây và 100 channel joins/giây. Khi quá throughput, connection có thể bị disconnect bằng `tenant_events` và tự reconnect khi rate hạ. [Realtime limits](https://supabase.com/docs/guides/realtime/quotas)
- Brevo 300 sends/ngày là số email, không phải số user. Supabase Auth hiện document default 30 OTP requests/giờ cho toàn project và 60 giây giữa hai request của cùng user; cả hai có thể cấu hình. MVP phải hạ provider-side OTP limit xuống 6/giờ, tương đương tối đa 144 request/24 giờ trước Brevo. Vượt Auth rate limit trả `429`. [Supabase Auth rate limits](https://supabase.com/docs/guides/auth/rate-limits)
- Supabase project URL và publishable key là public, nên cooldown ở Vercel không chặn caller gọi thẳng `/auth/v1/otp`. Phải bật CAPTCHA tại Supabase Auth để provider kiểm tra token trên direct endpoint; app per-IP/per-email cooldown chỉ là lớp bổ sung. [Supabase CAPTCHA](https://supabase.com/docs/guides/auth/auth-captcha), [SMTP abuse guidance](https://supabase.com/docs/guides/auth/auth-smtp#dealing-with-abuse-how-to-maintain-the-sending-reputation-of-your-smtp-server)
- Vercel tính mọi Function invocation, dù request thành công hay thất bại; bot traffic vẫn tiêu quota. [Function invocations](https://vercel.com/docs/functions/usage-and-pricing#invocations)
- Mỗi API call qua Vercel tính Fast Data Transfer giữa CDN và client, đồng thời tính Fast Origin Transfer cho bytes vào/ra Function. Hobby fair-use guideline hiện là 100 GB và 10 GB/tháng tương ứng. [CDN usage](https://vercel.com/docs/manage-cdn-usage), [fair use](https://vercel.com/docs/limits/fair-use-guidelines#typical-monthly-usage-guidelines)

Không có usage model thực tế cho số command/Match trong repo, nên recommendation này là lựa chọn **ít consistency risk nhất**, chưa phải chứng nhận capacity. Trước launch phải ghi workload contract gồm simultaneous Matches, Matches/ngày, commands/Match, snapshots/retries, bytes/event, database growth và tỷ lệ magic-link/OAuth. Production project phải là project duy nhất trong dedicated Supabase Free organization; Vercel deployment cũng nằm trong dedicated Hobby team/project để workload khác không ăn cùng budget.

Vercel chỉ cho load testing trên Enterprise, nên không được chạy synthetic load test trên Hobby deployment. Transaction/concurrency correctness có thể test 50 simulated Matches trên local Supabase stack; kết quả đó không chứng nhận managed capacity. Live beta bắt đầu invite-only với cap 5 active Matches, đo traffic người dùng bình thường trong cửa sổ bảy ngày rồi HITL mới được tăng dần, tối đa 25. [Vercel load-testing policy](https://vercel.com/kb/guide/what-s-vercel-s-policy-regarding-load-testing-deployments)

Internal budget bảo thủ là projected 30-day usage không quá 50% từng quota của dedicated Vercel team/Supabase organization; database không quá 250 MB; Realtime không quá 1 triệu messages/tháng hoặc 50 messages/giây; magic link không quá 144/ngày và provider-side 6 OTP/giờ. Canary traffic từ Việt Nam phải đạt command round-trip p95 <= 750 ms, p99 <= 1.500 ms, Realtime invalidation p95 <= 1 giây, p99 <= 2 giây, dưới 1% command errors và không vi phạm invariant. Đây là internal launch budget, không phải vendor capacity proof; chỉ nâng sau quan sát traffic thật và HITL review.

## Fail-closed runbook

| Failure | Hành vi bắt buộc của ứng dụng | Hành vi vendor đã biết |
| --- | --- | --- |
| PostgreSQL unavailable hoặc transaction timeout | Reject command; UI chuyển read-only/reconnecting; không áp state optimistic thành final. | Supabase restriction có thể trả `402`, read-only hoặc pause; exact timing không cố định. |
| Realtime disconnect/quota | Không nhận command qua client broadcast; reconnect, re-auth, tải snapshot/version từ DB. | Supabase có WebSocket limit errors; message-rate excess có thể disconnect connection. |
| Vercel quota/pause | Trước khi pause, ngừng Match mới và giữ reserve cho Match đang chạy. Sau khi deployment đã pause, toàn bộ API không còn chạy: Match hiện tại cũng thất bại và chỉ có thể snapshot/recover sau khi deployment hoạt động lại. | Hobby pause thay vì on-demand billing và có thể trả `503 DEPLOYMENT_PAUSED`. [deployment paused](https://vercel.com/docs/errors/deployment_paused) |
| Auth/Brevo email quota | Supabase CAPTCHA phải reject direct `/otp` không có/không hợp lệ; provider-side limit đặt 6 OTP/giờ. App hiển thị Google OAuth và retry rõ ràng. Không hứa email tức thời nếu request đã vào retry queue. | Supabase document default 30 OTP/giờ + 60 giây/user và trả `429`; Brevo có 300 sends/ngày, tối đa 1.000 queued, sau đó không deliver. |
| Client mất mạng | Command retry dùng cùng `command_id`; sau reconnect luôn tải snapshot. | Không phụ thuộc session memory của Vercel Function. |
| Duplicate terminal/finalize request | Unique settlement + row lock trả kết quả đã có; không update Elo lần hai. | PostgreSQL transaction/constraint là guard, không phải realtime provider. |

Guardrail vận hành ưu tiên existing Match trước new admission bằng deterministic database counters cho command/event do ứng dụng tạo. Dashboard/notification vendor chỉ là signal đối soát vì Vercel không công bố freshness và Hobby không có configurable alert threshold. Bot/static traffic hoặc provider enforcement vẫn có thể làm deployment pause trước dự đoán, nên zero-cost stack **không bảo đảm** existing Match sống qua hard-stop; chấp nhận live beta đồng nghĩa chấp nhận residual risk này. Nếu requirement đòi bảo toàn Match qua hosting hard-stop, phải nới paid baseline. [Vercel usage dashboard](https://vercel.com/docs/pricing/manage-and-optimize-usage#viewing-usage)

## Region và latency

| Thành phần | Placement có thể cấu hình | Mức chắc chắn |
| --- | --- | --- |
| Vercel Function | `sin1` | Exact single region trên Hobby. |
| Supabase project | `ap-southeast-1` | Exact AWS Singapore, data nằm tại project region. |
| Neon project | `aws-ap-southeast-1` | Exact AWS Singapore, không đổi region sau khi tạo. |
| Pusher Channels | `ap1` | Public cluster tại Singapore. |
| Cloudflare Durable Object | `apac-se` hint | Best effort, không bảo đảm Singapore. |
| Ably Free | Global edge | Không pin hoặc geo-restrict Singapore trên Free. |

Khuyến nghị co-locate Vercel API và PostgreSQL tại Singapore để giảm API-to-DB distance. Không có primary source nào cung cấp p50/p95/p99 từ các ISP/mobile network Việt Nam cho topology này. Latency end-user phải ghi **unknown** cho tới khi đo từ Việt Nam bằng full command round trip và realtime delivery, không chỉ ICMP/ping.

## Rủi ro và unknowns còn lại

- Vercel chưa nói rõ Public Beta WebSockets có tự động được cấp cho mọi Hobby project.
- Vercel, Supabase, Cloudflare và Pusher không có câu official rõ ràng bảo đảm free signup không cần card; cần xác minh trong account flow thực tế trước launch.
- Cloudflare chỉ tài liệu hóa route-level `fail open`/`fail closed`; hành vi cấu hình tương đương cho `workers.dev` hoặc Worker Custom Domain không được nêu rõ.
- Supabase không đặc tả chính xác grace-period duration hoặc resource nào bị restrict trước khi tiếp tục vượt từng Free quota.
- Supabase [Auth rate-limit page](https://supabase.com/docs/guides/auth/rate-limits) hiện ghi 30 OTP/giờ nhưng [Production Checklist](https://supabase.com/docs/guides/platform/going-into-prod#auth-rate-limits) vẫn ghi 360 OTP/giờ; dùng con số 30 bảo thủ và xác nhận giá trị thật trong Dashboard/API trước launch.
- Vercel không công bố freshness guarantee cho Usage dashboard; reserve trước hard-stop chỉ là risk reduction, không phải uptime guarantee.
- Supabase nói Free project có thể pause sau bảy ngày low activity nhưng không công bố restore-time SLO hoặc first-request latency sau restore.
- Supabase Realtime cache authorization tới JWT refresh/expiry; channel-epoch rotation và token expiry ngắn giảm exposure nhưng phải được test trên project thật.
- Brevo không bảo đảm SMTP activation/deliverability cho account mới chỉ dùng free public sender domain; reset timezone và exact SMTP response tại 300/day cũng không được nêu rõ.
- Ably không công bố buffer cho phần lớn package limits; message thứ 6.000.001 không có deterministic behavior được cam kết.
- Pusher liệt kê `ap1` là public Singapore cluster và nói app được chọn cluster khi tạo, nhưng không có câu riêng xác nhận mọi public cluster đều khả dụng trên Sandbox.
- Tài liệu plan đã khảo sát của Vercel Hobby, Supabase Free, Neon Free, Brevo Free và Ably Free không công bố production uptime SLA cho các free plan đang xét.
- Supabase Free không có automatic backups; recovery posture phải dựa vào manual export/restore drill hoặc nới paid constraint.
- Supabase CLI dump mặc định loại managed schemas như `auth`/`storage` và mặc định không chứa data; không được coi một lệnh dump mặc định là full recovery set. Backup drill phải dùng separate roles/schema/data dumps theo official restore guide và chứng minh identity mapping thực sự phục hồi được. [CLI dump behavior](https://supabase.com/docs/reference/cli/supabase-db-dump), [backup/restore sequence](https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore#backup-database-using-the-cli)
- Google OAuth consent, exact `*.vercel.app` callback/redirect allowlist và magic-link redirect phải được test end-to-end; pricing/docs không chứng minh cấu hình của project cụ thể.
- Không có latency benchmark chính thức đại diện cho user Việt Nam.
- Vendor có thể đổi free quota/terms; mọi con số phải được revalidate tại launch và định kỳ sau đó.

## Quyết định đề xuất cho wayfinder

Chấp nhận topology **Vercel Hobby + Supabase Free + Brevo Free SMTP** chỉ dưới nhãn vận hành **non-commercial live beta, zero-cost, no SLA** và với PostgreSQL làm authority. Không gọi đây là production-grade nếu chưa vượt qua các launch gate sau:

1. Xác nhận mục đích sử dụng vẫn hợp lệ với Vercel Hobby non-commercial personal-use restriction.
2. Tạo account/project thật và xác nhận không account nào có payment method hoặc auto-upgrade/paid-overage path.
3. Bật Supabase CAPTCHA, cấu hình provider-side OTP limit <= 6/giờ và xác nhận direct `/auth/v1/otp` không có/không hợp lệ bị reject; với bảy recipient khác nhau trong cùng giờ, request thứ bảy phải bị `429`; test thêm same-user cooldown và app cooldown.
4. Gửi tối thiểu 10 magic links/provider tới Gmail, Outlook và Yahoo trong ít nhất hai ngày: 10/10 phải tới trước link expiry, ít nhất 9/10/provider tới inbox trong hai phút, không rejection và spam placement được tính là fail.
5. Đặt exact production Site URL/redirect path cho `*.vercel.app`; không dùng wildcard production. Preview không dùng production credentials/allowlist. Test crafted `redirectTo`, expired/replayed link và callback trên mobile/desktop. [Supabase redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)
6. Chốt workload contract và internal budget. Chạy 50 simulated Matches chỉ trên local stack để kiểm tra correctness; trên Hobby chỉ đo normal invite-only canary traffic từ ít nhất hai mobile network và một fixed ISP Việt Nam, gồm request đầu sau deploy/idle, đạt các p95/p99/error thresholds và giữ projected organization/team usage <= 50% quota.
7. Dùng dedicated Supabase organization và Vercel Hobby team không có workload khác; test RPC wrapper trực tiếp với `anon`, non-member, former-member, cross-Match, expired token, oversized/malformed payload và rate-limit abuse; enumerate exposed schemas/grants để chứng minh không `security definer` nào remote-callable.
8. Test same-ID/same-hash replay cả sau khi actor bucket đã cạn, same-ID/different-hash conflict, concurrent duplicate, stale version, concurrent VERIFY, deadline race, duplicate finalization và atomic two-player Elo update.
9. Đặt JWT expiry 600 giây. Test Realtime client không thể `INSERT`/broadcast/Presence, non-member không join được, event không chứa secret và reconnect luôn recover bằng snapshot. Với client đã connect, revoke membership phải rotate topic ngay; client cũ không nhận state event mới và bị disconnect/re-evaluate trong 10 phút.
10. Thực hiện actual pause/restore drill trên disposable Supabase Free project: đo detection/manual restore; yêu cầu operator restore <= 30 phút và first command/snapshot/Realtime join <= 5 giây sau khi Dashboard báo healthy.
11. Chạy invite-only canary tối thiểu bảy ngày với ít nhất 100 normal user commands; đối soát app counters với dashboard mỗi ngày. Controlled metrics phải lệch <= 20%, tổng usage phải dưới 25% quota trong canary; vendor alerts chỉ mang tính quan sát, không được coi là guarantee.
12. Test dependency failure để chứng minh client không tiếp tục bằng optimistic authority.
13. Mỗi 24 giờ tạo encrypted off-site recovery set bằng official three-file sequence: roles dump, schema dump và `--data-only --use-copy` dump. Restore latest set vào disposable project trong <= 4 giờ, không checksum/row-count/constraint mismatch, xác minh existing identity-to-player mapping và Match/Elo invariants; nếu managed auth identity không phục hồi được thì gate fail. HITL ký nhận RPO <= 24 giờ, RTO <= 4 giờ. [Supabase backups](https://supabase.com/docs/guides/platform/backups), [CLI backup/restore](https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore#backup-database-using-the-cli)
14. Test database-enforced new-Match admission và command/event counters bằng local/integration test; ngưỡng 50% phải chặn Match mới và phát app alert. Vendor dashboard notifications không phải acceptance mechanism.

Nếu bất kỳ gate nào thất bại, quay lại HITL thay vì thêm workaround ngầm. Ba hướng nới constraint hợp lý là: cho phép custom domain + paid email baseline, cho phép fixed paid hosting/database baseline, hoặc bỏ email magic link và chỉ giữ Google OAuth. Không nên đổi sang nhiều free vendor hơn để che một ràng buộc chưa khả thi.
