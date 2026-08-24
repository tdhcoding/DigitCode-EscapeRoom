# Cơ chế scheduled job zero-cost trên Vercel Hobby và Supabase Free

- Ngày khảo sát: 2026-08-24
- Ticket: [#27 - Khảo sát cơ chế scheduled job zero-cost](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27)
- Phạm vi: mọi cơ chế chạy theo lịch có thể dùng để quét và finalize Match quá hạn, với chi phí định kỳ bằng 0, trên stack đã chốt Vercel Hobby + Supabase Free (`ap-southeast-1`). Không xét phương án phải nâng plan trả phí.
- Tính thời điểm: mọi quota, tần suất và điều khoản dưới đây là **snapshot đọc trực tiếp từ tài liệu vendor tại ngày 2026-08-24**. Quota vendor thay đổi liên tục; phải đọc lại trang gốc trước khi launch, không được tin số trong tài liệu này quá vài tháng.

## Kết luận điều hành

- **Vercel Cron trên Hobby bị loại vì tần suất, không phải vì chi phí.** Hobby có tối đa 100 cron job/project nhưng **minimum interval là một lần mỗi ngày**, và biểu thức cron chạy dày hơn sẽ **fail ngay lúc deploy**. Thêm nữa Hobby chỉ có **scheduling precision theo giờ (±59 phút)**. [Cron usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)
- **Câu hỏi "cron có tính vào Function Invocations không" là CÓ, nhưng đó là câu hỏi sai.** Vercel nói rõ cron job invoke Vercel Function nên áp dụng cùng usage/pricing limits, và Invocations "counts regardless of request success or failure". Nhưng ở tần suất mà Hobby thực sự cho phép (1 lần/ngày = 30 lần/tháng), chi phí invocation là **0,006% ngân sách** — hoàn toàn không đáng kể. Thứ giết phương án là giới hạn tần suất. [Cron usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing), [Fluid compute pricing](https://vercel.com/docs/functions/usage-and-pricing)
- **`pg_cron` trên Supabase Free là cơ chế duy nhất có tần suất thật sự đủ dày và chi phí thật sự bằng 0.** Supabase Cron chạy trên `pg_cron`, hỗ trợ lịch "from every second to once a year", và cú pháp sub-minute `[1-59] seconds` — **nhưng sub-minute có điều kiện phiên bản Postgres `15.1.1.61` trở lên**, và tài liệu không nói phiên bản mặc định của một project Free mới là bao nhiêu. Chạy SQL nội bộ thì không phát sinh Vercel invocation, không phát sinh Supabase egress, không phát sinh Edge Function invocation. [Supabase Cron](https://supabase.com/docs/guides/cron), [Cron quickstart](https://supabase.com/docs/guides/cron/quickstart)
- **Nhưng `pg_cron` mắc kẹt trong một cái bẫy hai đầu.** Tài liệu Supabase **không tuyên bố** hoạt động nội bộ database có được tính là "activity" để chống pause hay không — định nghĩa vendor dùng là "user database activity" / "user queries" / "API calls to your project", và danh sách cách chống pause chỉ liệt kê hai thứ đến từ **bên ngoài**. Và khi project đã pause, tài liệu **không tuyên bố** `pg_cron` còn chạy. Chi tiết ở Chiều A và Chiều B. [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing)
- **GitHub Actions scheduled workflow là cơ chế zero-cost duy nhất vừa đủ tần suất vừa nằm ngoài stack đang bị pause** — free cho public repo, tối thiểu 5 phút. Nhưng docs của GitHub tự nói `schedule` **có thể bị trễ khi tải cao**, và **tự động disable sau 60 ngày repo không có hoạt động** trên public repo. Nó là scheduler đúng nghĩa nhất trong khảo sát, nhưng không phải scheduler đáng tin. [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [Billing for GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- **Khuyến nghị: giữ nguyên kiến trúc "không có server timer tick".** Không cơ chế nào trong khảo sát cung cấp đảm bảo đủ để một Match phụ thuộc vào nó. Scheduled job chỉ nên là **tối ưu hoá cơ hội** (opportunistic sweep) chồng lên finalize lười + tự chữa ở admission, không bao giờ là đường đi duy nhất tới trạng thái đúng.

## Tiêu chí đánh giá

Trong báo cáo này:

- **Zero-cost** nghĩa là không phát sinh khoản phải trả định kỳ và không có đường tự động tạo overage khi vẫn ở free plan.
- **"Vendor tuyên bố"** nghĩa là có một câu trong tài liệu chính thức của chính vendor đó nói ra điều ấy. **"Vendor không tuyên bố"** nghĩa là đã đọc trang gốc và không tìm thấy câu nào nói ra điều ấy — đây **không** đồng nghĩa với "điều ấy sai", mà đồng nghĩa với "không được phép dựa vào nó khi thiết kế".
- Mọi con số trong tài liệu này đều đi kèm link tới tài liệu vendor sở hữu con số đó. Không có con số nào lấy từ blog, StackOverflow hay bài viết bên thứ ba.
- **Đảm bảo** được đánh giá theo ba trục: tần suất nhỏ nhất, độ tin cậy được vendor cam kết, và hành vi khi Supabase project bị pause.

## Bảng so sánh các cơ chế

| Cơ chế | Có trên free tier? | Tần suất nhỏ nhất | Số job | Hành vi khi Supabase project pause | Tính vào quota nào | Kết luận |
| --- | --- | --- | --- | --- | --- | --- |
| **Vercel Cron (Hobby)** | Có. "Cron jobs are included in **all plans**". [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing) | **Một lần/ngày.** Biểu thức dày hơn "will fail during deployment". Precision "Per-hour (±59 min)". [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing) | 100 cron job/project trên Hobby. [Limits](https://vercel.com/docs/limits), [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing) | Cron vẫn chạy (nó ở Vercel), nhưng HTTP GET tới Supabase sẽ lỗi. Invocation lỗi **vẫn tính**: "Counts regardless of request success or failure". [Fluid compute pricing](https://vercel.com/docs/functions/usage-and-pricing) | Function Invocations (trần 1.000.000/tháng Hobby). "Cron jobs are logged as function invocations". [Hobby plan](https://vercel.com/docs/plans/hobby), [manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs) | **Loại.** 1 lần/ngày là vô dụng cho finalize Match. Chi phí invocation không phải vấn đề. |
| **`pg_cron` / Supabase Cron** | Có. Tài liệu Supabase Cron **không hề phân biệt plan**; không có câu nào giới hạn nó theo tier. [Supabase Cron](https://supabase.com/docs/guides/cron) | **Một phút vô điều kiện; sub-minute CÓ ĐIỀU KIỆN.** "from every second to once a year"; cú pháp `[1-59] seconds` (ví dụ `'30 seconds'`) chỉ dùng được "as long as you're on Postgres version 15.1.1.61 or later". [Supabase Cron](https://supabase.com/docs/guides/cron), [quickstart](https://supabase.com/docs/guides/cron/quickstart), [pg_cron README](https://github.com/citusdata/pg_cron) | Không có trần tuyệt đối được công bố. Khuyến nghị: "no more than 8 Jobs run concurrently". `cron.max_running_jobs` mặc định của pg_cron là 32. [Supabase Cron](https://supabase.com/docs/guides/cron), [pg_cron README](https://github.com/citusdata/pg_cron) | **Tài liệu không tuyên bố.** Không có câu nào của Supabase nói pg_cron còn chạy hay dừng khi project pause. Xem Chiều B. [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) | SQL thuần nội bộ: không tiêu Vercel invocation, không tiêu Edge Function invocation. Egress chỉ tính "data transmitted out of the system to a connected client" nên SQL nội bộ không tính. [Egress](https://supabase.com/docs/guides/platform/manage-your-usage/egress) | **Dùng được về mặt kỹ thuật, nhưng không có đảm bảo lifecycle.** Đủ tần suất, đúng nghĩa zero-cost, nhưng không chống được pause và không biết có chạy khi pause. |
| **Supabase Scheduled Edge Function** | Có, nhưng **không phải scheduler riêng** — nó chính là `pg_cron` + `pg_net` gọi ngược vào Edge Function. [Schedule functions](https://supabase.com/docs/guides/functions/schedule-functions) | Giống `pg_cron` (sub-minute), vì scheduler là `pg_cron`. [Schedule functions](https://supabase.com/docs/guides/functions/schedule-functions) | Giống `pg_cron`. `pg_net` được "configured to reliably execute up to 200 requests per second". [pg_net](https://supabase.com/docs/guides/database/extensions/pg_net) | Giống `pg_cron` — cùng một database, cùng một compute. Tài liệu không tuyên bố. | Edge Function Invocations: Free có **500.000/tháng**. Cộng thêm egress của Edge Function. [Pricing](https://supabase.com/pricing), [Egress](https://supabase.com/docs/guides/platform/manage-your-usage/egress) | **Thừa một tầng.** Nếu công việc là SQL, gọi ra Edge Function rồi gọi ngược vào DB là tự thêm failure mode và tự tiêu quota vô ích. |
| **GitHub Actions `schedule`** | Có, free cho public repo: "GitHub Actions usage is **free** for self-hosted runners and for **public repositories** that use standard GitHub-hosted runners". [Billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) | **5 phút.** "The shortest interval you can run scheduled workflows is once every 5 minutes." [Events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) | Docs không công bố trần số scheduled workflow. | Workflow vẫn chạy (nó ở GitHub), nhưng request tới Supabase sẽ lỗi. Nếu đi qua Vercel thì invocation lỗi vẫn tính. | Không tính vào Vercel/Supabase **nếu** gọi thẳng Supabase. Nếu gọi qua Vercel API thì tính Function Invocations. | **Khả thi nhất về tần suất, nhưng có hai vết nứt:** trễ khi GitHub tải cao, và tự disable sau 60 ngày repo im lặng. |
| **cron-job.org (external free)** | Có. "Our service is absolutely free and financed entirely by voluntary donations." [cron-job.org](https://cron-job.org/en/) | **1 phút.** "Jobs can be executed with frequencies up to once per minute." [cron-job.org](https://cron-job.org/en/) | Trang chủ không công bố trần số cronjob. | Vẫn chạy, request tới Supabase lỗi. | Không tính vào Vercel/Supabase nếu gọi thẳng Supabase. | **Thêm vendor thứ ba vào stack** (sau Vercel, Supabase, GitHub) chỉ để có thêm 4 phút tần suất so với GitHub Actions. Không đáng. |

## 1. `pg_cron` trên Supabase Free

**Cơ chế.** Supabase Cron không phải sản phẩm riêng: "Supabase Cron uses the `pg_cron` Postgres database extension which is the scheduling and execution engine". Job được lưu ở bảng `cron.job` và lịch sử chạy ở `cron.job_run_details`. [Supabase Cron](https://supabase.com/docs/guides/cron)

**Có dùng được trên Free không.** Tài liệu Supabase Cron **không phân biệt plan ở bất kỳ chỗ nào** — không có câu nào nói tính năng này giới hạn theo tier, và trang tổng quan extensions cũng không phân tier ("Supabase is pre-configured with over 50 extensions"). [Supabase Cron](https://supabase.com/docs/guides/cron), [Extensions](https://supabase.com/docs/guides/database/extensions). Đây là **suy ra từ việc không có giới hạn được nêu**, không phải một tuyên bố khẳng định "Free được dùng" — cần ghi nhận sự khác biệt đó.

**Bật thế nào.** Bằng extension `pg_cron`, qua Dashboard (Integrations) hoặc SQL. [Supabase Cron](https://supabase.com/docs/guides/cron), [quickstart](https://supabase.com/docs/guides/cron/quickstart)

**Có cần thẻ không.** Xem mục riêng ["Có cần thẻ không"](#có-cần-thẻ-không) — câu trả lời ngắn là **không vendor nào tuyên bố rõ**, và #8 đã ghi nhận đúng khoảng trống đó cho cả Vercel Hobby lẫn Supabase Free.

**Granularity nhỏ nhất.** Supabase nói job chạy "from every second to once a year". [Supabase Cron](https://supabase.com/docs/guides/cron). Quickstart nói rõ cú pháp: "You can use `[1-59]` seconds (e.g. `30 seconds`) as the cron syntax to schedule sub-minute Jobs." [quickstart](https://supabase.com/docs/guides/cron/quickstart). Điều này khớp với upstream: pg_cron README ghi `'10 seconds'  # every 10 seconds` và "to use `[1-59] seconds` to schedule a job based on an interval. Note, you cannot use seconds with the other time units." [pg_cron README](https://github.com/citusdata/pg_cron)

→ **Vậy `'30 seconds'` là cú pháp hợp lệ và Supabase tuyên bố hỗ trợ nó** — nhưng **có điều kiện**, và điều kiện đó phải đi kèm mọi lần trích con số này. Chính quickstart đặt rào: "You can input seconds for your Job schedule interval **as long as you're on Postgres version 15.1.1.61 or later**." [quickstart](https://supabase.com/docs/guides/cron/quickstart)

⇒ **Sub-minute KHÔNG phải một tính chất vô điều kiện của Supabase Free.** Nó phụ thuộc phiên bản Postgres của project, và tài liệu **không tuyên bố** phiên bản mặc định của một project Free tạo mới hôm nay là bao nhiêu, cũng không tuyên bố project cũ có được nâng tự động hay không. Trước khi thiết kế dựa vào tần suất dưới một phút, phải **kiểm phiên bản thật** của project (`select version()`), không được suy từ tài liệu. Ở tần suất một phút trở lên thì điều kiện này không áp dụng.

Đây vẫn là cơ chế duy nhất trong khảo sát có granularity dưới một phút.

**Số job tối đa.** Supabase **không công bố trần tuyệt đối**, chỉ một khuyến nghị hiệu năng: "For best performance, we recommend no more than 8 Jobs run concurrently. Each Job should run no more than 10 minutes." [Supabase Cron](https://supabase.com/docs/guides/cron). Upstream pg_cron có GUC `cron.max_running_jobs` mặc định `32` — "Maximum number of jobs that can be running at the same time". [pg_cron README](https://github.com/citusdata/pg_cron). **Tài liệu Supabase không tuyên bố giá trị `cron.max_running_jobs` thực tế trên compute Nano**, và cũng không nói giá trị đó có sửa được trên Free hay không.

Bối cảnh compute: Free chạy trên **Nano** — shared CPU, tối đa 0,5 GB memory, 60 max database connections, 200 pooler max clients; kèm footnote "Compute resources on the Free plan are subject to change". [Compute and Disk](https://supabase.com/docs/guides/platform/compute-and-disk). Khuyến nghị 8 job đồng thời của Supabase nên đọc trong bối cảnh đó.

**Gọi HTTP ra ngoài được không.** Được, qua `pg_net`: "enables Postgres to make asynchronous HTTP/HTTPS requests in SQL". Ràng buộc được tài liệu nêu rõ:

- **Bất đồng bộ.** Hàm trả về `bigint` là `request_id`, không phải response. Logic không thể "chờ kết quả" trong cùng một câu lệnh.
- **"HTTP requests are not started until the transaction is committed"** — request chỉ khởi động sau commit.
- **Timeout mặc định `timeout_milliseconds int default 2000`** — 2 giây.
- **Response chỉ lưu 6 giờ** trong `net._http_response`, "stored for only 6 hours to prevent needless buildup".
- **Throughput**: "configured to reliably execute up to 200 requests per second".

[pg_net](https://supabase.com/docs/guides/database/extensions/pg_net)

**Tài liệu `pg_net` không tuyên bố** có retry khi request thất bại, cũng không tuyên bố hành vi khi queue đầy. Nghĩa là: một job dùng `pg_net` phải tự coi mỗi lần gọi là best-effort và phải idempotent.

**Chạy trong database có tính vào quota Supabase Free nào không.**

- **Egress: không**, với job chạy SQL thuần. Định nghĩa của Supabase: "You are charged for the network data transmitted out of the system to a connected client. Egress is incurred by all services - Database, Auth, Storage, Edge Functions, Realtime and Log Drains." Job pg_cron nội bộ không có "connected client" nhận dữ liệu. [Egress](https://supabase.com/docs/guides/platform/manage-your-usage/egress). Free có 5 GB. [Pricing](https://supabase.com/pricing)
- **Egress cho `pg_net`: tài liệu không tuyên bố.** Không có câu nào của Supabase nói request HTTP đi **ra** từ database có tính vào egress hay không. Trang egress liệt kê các service nhưng không đề cập outbound HTTP từ DB. Đây là một khoảng trống thật sự.
- **Realtime messages: chỉ khi có client đang nghe.** Supabase định nghĩa: "Each database change counts as one message per client that listens to the event." [Realtime messages](https://supabase.com/docs/guides/platform/manage-your-usage/realtime-messages). Vậy một job pg_cron `UPDATE` bảng Match đang publish qua Postgres Changes sẽ sinh **N message với N là số client đang nghe event đó** — không sinh message nào nếu không ai nghe. Free có 2 triệu message/tháng. [Pricing](https://supabase.com/pricing)
- **Compute hours: không áp dụng.** Bảng compute ghi Nano giá `$0`/giờ và `$0`/tháng. [Compute and Disk](https://supabase.com/docs/guides/platform/compute-and-disk)

→ Về mặt quota, `pg_cron` chạy SQL thuần **không đụng vào quota nào của Supabase Free** trừ khi nó tạo ra thay đổi mà client đang nghe.

**Nhãn cho câu trên: SUY LUẬN, không phải tuyên bố.** Supabase **chưa bao giờ viết** câu "pg_cron không tính egress". Kết luận này rút ra từ định nghĩa egress ("transmitted out of the system **to a connected client**") cộng với việc một job SQL nội bộ không có connected client nào. Khoảng trống #9 dưới đây cho thấy ca liền kề — outbound HTTP của `pg_net` — thì **vendor không tuyên bố**, nên đừng đọc suy luận này rộng hơn phạm vi của nó: nó chỉ áp cho **SQL thuần, không `pg_net`**.

## 2. Supabase Scheduled Edge Functions

**Đây không phải một scheduler riêng.** Tài liệu Supabase nói thẳng: `pg_cron` "In combination with the `pg_net` extension, this allows us to invoke Edge Functions periodically on a set schedule." Ví dụ chính thức là một câu `cron.schedule(...)` bọc quanh `net.http_post(...)` gọi tới `/functions/v1/function-name`. [Schedule functions](https://supabase.com/docs/guides/functions/schedule-functions)

Nghĩa là: **mọi thuộc tính lifecycle của nó bằng đúng với `pg_cron`.** Nếu `pg_cron` không chạy khi project pause thì scheduled Edge Function cũng không. Nó không mua thêm bất kỳ đảm bảo nào.

**Quota Edge Function trên Free:**

- **500.000 invocations/tháng** included. [Pricing](https://supabase.com/pricing)
- Max duration (wall clock) trên Free: **150s**; paid: 400s. Max memory 256MB. Max CPU time 2s. Tối đa 100 function/project trên Free. [Edge Function limits](https://supabase.com/docs/guides/functions/limits)

**Đánh giá cho DigitCode.** Một job mỗi 5 phút = 8.640 Edge Function invocation/tháng. Đối chiếu đúng mẫu số: trần Free là 500.000, và **quy tắc ngân sách nội bộ của repo (≤ 50% mỗi quota) áp cho quota này y như áp cho Vercel** ⇒ ngân sách làm việc là **250.000**, và 8.640 là **3,456% ngân sách** (0,864% trần đầy). Con số này **không** phải "1,7%" — trùng số với con số Vercel ở bảng ngân sách là trùng hợp của hai mẫu số khác nhau, và trộn hai mẫu số là đúng cái bẫy mà repo này đã vấp nhiều lần. Dù vậy, chi phí vẫn không phải vấn đề. Vấn đề là **kiến trúc**: công việc "quét Match quá hạn và finalize" là công việc SQL. Đi từ Postgres → pg_net → HTTP → Edge Function → Postgres chỉ để làm một `UPDATE` là tự thêm một network hop, một timeout 2 giây, một failure mode không retry, và tiêu quota Edge Function lẫn egress — để đổi lấy đúng con số không lợi ích. Nếu công việc là SQL, hãy để `pg_cron` chạy SQL.

## 3. Vercel Cron Jobs trên Hobby

Đây là điểm mấu chốt của ticket, và nghi ngờ trong ticket là **đúng**.

**Số cron job.** Hobby được **100 cron job/project** — bằng Pro và Enterprise. [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing), [Limits](https://vercel.com/docs/limits). Lưu ý: "Disabled cron jobs will still be listed and will count towards your cron jobs limits". [manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs)

**Tần suất tối thiểu — điểm quyết định.** Bảng chính thức của Vercel:

| | Number of cron jobs per project | Minimum interval | Scheduling precision |
| --- | --- | --- | --- |
| **Hobby** | 100 cron jobs | **Once per day** | **Per-hour (±59 min)** |
| **Pro** | 100 cron jobs | Once per minute | Per-minute |
| **Enterprise** | 100 cron jobs | Once per minute | Per-minute |

[usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)

Và nó không phải một soft limit — nó chặn ở deploy time:

> "Hobby accounts are limited to cron jobs that run **once per day**. Cron expressions that would run more frequently will fail during deployment."

> "**Daily execution limit**: Cron jobs can only run once per day. Expressions like `0 * * * *` (per-hour) or `*/30 * * * *` (every 30 minutes) will fail deployment with the error: *Hobby accounts are limited to daily cron jobs. This cron expression would run more than once per day.*"

[usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)

→ **`*/5 * * * *` không deploy được trên Hobby.** Giả định "một job mỗi 5 phút" trong ticket không thực hiện được bằng Vercel Cron ở tier hiện tại. Đây không phải chuyện tốn quota — đây là chuyện build fail.

**Vercel có bảo đảm cron chạy đúng giờ không.** Không, và Vercel nói thẳng ở hai chỗ:

> "**Timing precision**: Vercel cannot assure a timely cron job invocation. For example, a cron job configured as `0 1 * * *` (every day at 1 am) will trigger anywhere between 1:00 am and 1:59 am." [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)

> "Hobby users have two cron job restrictions. First, cron jobs can only run once per day... Second, Vercel may invoke these cron jobs at any point within the specified hour to help distribute load across all accounts. For example, an expression like `0 8 * * *` could trigger an invocation anytime between `08:00:00` and `08:59:59`." [manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs)

Ngoài ra, độc lập với plan:

> "**Cron job delivery is best effort.** Most invocations run as scheduled, but occasional transient network errors can prevent a request from reaching your function. In those cases, your function does not execute, and no runtime log is created for that scheduled run."

> "Cron delivery can also occasionally invoke the same scheduled run more than once. Because of this, cron jobs should be resilient to both missed runs and duplicate runs."

> "Vercel will not retry an invocation if a cron job fails."

[manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs)

→ Vercel Cron là **at-least-or-at-most-once, không đảm bảo** — có thể bỏ, có thể chạy hai lần, không retry. Bất kỳ handler nào cũng phải idempotent.

**Cron chỉ chạy trên production deployment.** Có:

> "To trigger a cron job, Vercel makes an HTTP GET request to your project's production deployment URL, using the `path` provided in your project's `vercel.json` file." [Cron Jobs](https://vercel.com/docs/cron-jobs)

Bổ sung: timezone "is always UTC"; cron không follow redirect ("Cron jobs do not follow redirects"); path không tồn tại vẫn được thực thi và sinh 404 ("If you create a cron job for a path that doesn't exist, it generates a 404 error. However, **Vercel still executes your cron job**"); Instant Rollback **không** cập nhật cron đang chạy. [Cron Jobs](https://vercel.com/docs/cron-jobs), [manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs)

**Cron invocation CÓ tính vào Function Invocations của Hobby không.** **CÓ.** Ba câu độc lập trong docs Vercel xác nhận:

1. "Cron jobs invoke [Vercel Functions](/docs/functions). This means the same [usage](/docs/limits) and [pricing](/pricing) limits will apply." [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)
2. "You use a function to invoke a cron job, and therefore usage and pricing limits for these functions apply to all cron job executions." [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)
3. "Cron jobs are logged as function invocations from the **Logs** section in your project dashboard sidebar." [manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs)

Và invocation **lỗi vẫn tính**: mục Invocations của Vercel ghi "Counts each request to your function", "Hobby includes 1 million invocations per month", "**Counts regardless of request success or failure**". [Fluid compute pricing](https://vercel.com/docs/functions/usage-and-pricing)

Trần Hobby được xác nhận ở ba trang: bảng Fluid compute ("**Invocations** | 1 million included"), bảng Limits ("Invocations | 1 million"), và bảng Hobby ("[Function Invocations] | First 1,000,000"). [Fluid compute pricing](https://vercel.com/docs/functions/usage-and-pricing), [Limits](https://vercel.com/docs/limits), [Hobby plan](https://vercel.com/docs/plans/hobby)

**Khi vượt quota Hobby:** "In most cases, if you exceed your usage limits on the Hobby plan, you will have to wait until 30 days have passed before you can use the feature again." [Hobby plan](https://vercel.com/docs/plans/hobby)

## Chiều A — scheduled job có giữ được Supabase Free project khỏi bị pause không?

**Câu trả lời ngắn: tài liệu vendor KHÔNG cho phép kết luận là có.**

Đây là toàn bộ những gì Supabase tuyên bố về định nghĩa inactivity, trích nguyên văn từ [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing):

> "Supabase pauses Free Plan projects that show low activity over a 7-day period to save server resources."

> "A Free plan project is considered inactive if it does not receive sufficient **user database activity** over the past week. Projects with too few **user queries** during that window are the clearest candidates for pausing. While you may be actively using the project, it's possible that usage is not enough to exclude it from automatic pausing. Typically **a few user requests to the database each day** over the previous week is enough to keep the project from being paused."

Và đây là danh sách chính thức các cách chống pause sau khi nhận email cảnh báo:

> "- Visit the project from the Supabase Dashboard to generate activity.
> - Generate a sufficient amount of activity by making **API calls to your project or sending requests via your connected application**."

**Phân tích chính xác những gì có và không có trong các câu trên:**

| Câu hỏi | Tài liệu nói gì |
| --- | --- |
| Ngưỡng inactivity là bao lâu? | **Nói rõ: 7 ngày.** |
| "Activity" là gì? | **Nói mơ hồ.** Ba cách diễn đạt khác nhau được dùng lẫn lộn: "user database activity", "user queries", "user requests to the database". Cả ba đều có tiền tố **"user"**. |
| Ngưỡng định lượng là bao nhiêu? | **Không có con số.** "sufficient", "too few", "a few user requests each day" — không có một con số nào. Không có định nghĩa "sufficient" là mấy request. |
| Một job pg_cron chạy mỗi 5 phút có được tính là activity không? | **Tài liệu KHÔNG tuyên bố.** Không có câu nào của Supabase nói hoạt động do database tự sinh ra có hay không được tính. |
| Danh sách cách chống pause có bao gồm hoạt động nội bộ DB không? | **KHÔNG.** Cả hai mục đều là hoạt động đến từ **bên ngoài**: mở Dashboard, hoặc gửi API call / request từ ứng dụng đã kết nối. |

**Hệ quả cho thiết kế.** Từ "user" trong "user database activity" và việc danh sách chống pause chỉ liệt kê hai nguồn ngoại vi là **bằng chứng gợi ý** rằng Supabase đếm request đến từ ngoài, không đếm background worker nội bộ. Nhưng đó là **suy luận từ cách dùng từ, không phải một tuyên bố**. Supabase chưa bao giờ viết ra câu "pg_cron không tính là activity", và cũng chưa bao giờ viết ra câu "pg_cron có tính".

Với một hệ thống mà việc bị pause là sự cố nghiêm trọng, khoảng trống này phải được xử lý theo hướng bảo thủ:

> **Không được thiết kế dựa trên giả định `pg_cron` giữ project sống.** Nếu vendor không hứa, hệ thống không được phụ thuộc.

Cơ chế chống pause duy nhất mà tài liệu **có** hứa là hoạt động từ bên ngoài — tức đúng thứ mà GitHub Actions hoặc một cron ngoài cung cấp, và cũng đúng thứ mà **người dùng thật đang chơi game** cung cấp. Với một game 1v1 có người chơi, chống pause không phải bài toán. Nó chỉ thành bài toán trong giai đoạn dự án im lặng — và chính giai đoạn đó thì `pg_cron` là thứ đáng ngờ nhất.

Ghi chú bổ sung: Supabase khẳng định dứt khoát rằng chỉ có Free bị pause — "Projects under a paid plan cannot be paused and are not subject to automatic pausing for inactivity." [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing). Đây là một lối thoát có thật nhưng nằm ngoài ràng buộc zero-cost.

## Chiều B — khi project đã pause thì scheduled job có chạy không?

**Câu trả lời ngắn: tài liệu vendor KHÔNG tuyên bố, và đó tự nó là một câu trả lời đủ để loại phương án.**

**Supabase nói gì về trạng thái paused.** Trang [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) mô tả **quy trình** pause và restore nhưng **không mô tả trạng thái kỹ thuật**. Cụ thể, tài liệu:

- **Không có câu nào** nói compute/Postgres bị dừng khi pause.
- **Không có câu nào** nói `pg_cron` background worker ngừng chạy khi pause.
- **Không có câu nào** nói API endpoint trả về lỗi gì khi project paused.

Bằng chứng gián tiếp duy nhất tìm được là mục đích của việc pause: "to save server resources" và bảng compute cho thấy Nano là một Postgres instance riêng ("Every project on the Supabase Platform comes with its own dedicated Postgres instance"). [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing), [Compute and Disk](https://supabase.com/docs/guides/platform/compute-and-disk). "Tiết kiệm server resources" bằng cách dừng compute là suy luận hợp lý — và pg_cron chỉ chạy khi Postgres backend chạy, vì nó là background worker nạp qua `shared_preload_libraries` ("To start the pg_cron background worker, you need to add pg_cron to `shared_preload_libraries` in postgresql.conf") [pg_cron README](https://github.com/citusdata/pg_cron) — nhưng **không có tuyên bố chính thức nào của Supabase xác nhận chuỗi suy luận này**.

**Restore là thủ công hay tự động: THỦ CÔNG.** Tài liệu nêu quy trình ba bước do người thực hiện:

> "You can restore a paused project for up to 1 year after it was paused:
> 1. Open the Supabase Dashboard
> 2. Select the organization, followed by the paused project
> 3. Click **Resume project** and confirm"

[Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing)

→ Không có auto-restore. Không có API restore được nêu trong trang này. Một project bị pause **đứng yên cho tới khi có người bấm nút**.

**Có SLO restore không: KHÔNG.** Tài liệu không nêu bất kỳ thời gian nào cho việc restore mất bao lâu. Không có "typically X minutes", không có cam kết. Nó chỉ hứa kết quả cuối: "The project will return to its previous state, including data and configurations."

**Cửa sổ restore: 1 năm.** "Once the project is paused, there is a 1-year window to restore the project on the platform from within Supabase Studio. The time limit exists because backups are only retained for a limited period..." [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing). Và "Paused projects do not count towards your free project limit." [Billing](https://supabase.com/docs/guides/platform/billing-on-supabase)

**Vercel Cron gọi vào một Supabase project đã pause thì sao.** Request sẽ thất bại (không có tuyên bố Supabase nào về mã lỗi cụ thể). Về phía Vercel, hậu quả về quota là dứt khoát:

> "Invocations — Counts each request to your function... **Counts regardless of request success or failure**." [Fluid compute pricing](https://vercel.com/docs/functions/usage-and-pricing)

Và Vercel không retry: "Vercel will not retry an invocation if a cron job fails." [manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs)

→ Trong lúc project pause, cron của Vercel vẫn đều đặn đốt invocation để nhận lỗi. Ở tần suất Hobby cho phép (1/ngày = 30/tháng) thì lượng đốt này không đáng kể. Nhưng nó cũng **không sửa được gì** — cron không thể tự resume project.

**Kết luận Chiều A + Chiều B ghép lại.**

`pg_cron` nằm trong một vòng lặp đóng không lối ra:

- Nó **có thể** không được tính là activity → không ngăn được project pause (Chiều A: vendor không hứa).
- Nó **có thể** ngừng chạy khi project đã pause → không tự sửa được (Chiều B: vendor không hứa, và cơ chế kỹ thuật gợi ý là ngừng).
- Restore đòi hỏi **con người bấm nút**, không có SLO.

Vậy giá trị thật của `pg_cron` như một cơ chế lifecycle là: **nó chỉ hoạt động trong đúng những khoảng thời gian mà hệ thống vốn đã khoẻ mạnh nhờ có người dùng thật.** Nó không thêm khả năng phục hồi nào ở đúng thời điểm cần khả năng phục hồi. Nó vẫn hữu ích như một tối ưu hoá trong giờ hoạt động — nhưng không phải một bảo đảm lifecycle, và không được ghi vào thiết kế như một.

## Bảng ngân sách invocation

Ngân sách nội bộ của repo: **projected 30-day usage ≤ 50% mỗi quota**. Trần Hobby là **1.000.000 Function Invocations/tháng** (xác nhận tại [Fluid compute pricing](https://vercel.com/docs/functions/usage-and-pricing), [Limits](https://vercel.com/docs/limits), [Hobby plan](https://vercel.com/docs/plans/hobby)) → ngân sách làm việc là **500.000 invocation/tháng**.

Cột "Deploy được trên Hobby?" tra theo minimum interval "Once per day" của [Cron usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing).

| Kịch bản | Tần suất | Lần/tháng (30 ngày) | % của 500.000 (ngân sách) | % của 1.000.000 (trần) | Deploy được trên Hobby? |
| --- | --- | --- | --- | --- | --- |
| **Vercel Cron mỗi 5 phút** (giả định trong ticket) | 12/giờ × 24 × 30 | 8.640 | **1,728%** | 0,864% | **KHÔNG.** `*/5 * * * *` fail lúc deploy. |
| Vercel Cron mỗi phút | 60/giờ × 24 × 30 | 43.200 | 8,64% | 4,32% | **KHÔNG** |
| Vercel Cron mỗi giờ | 1/giờ × 24 × 30 | 720 | 0,144% | 0,072% | **KHÔNG** |
| **Vercel Cron 1 lần/ngày** (mức Hobby thực sự cho phép) | 1/ngày × 30 | **30** | **0,006%** | 0,003% | **CÓ** (±59 phút) |
| GitHub Actions mỗi 5 phút → gọi Vercel API | 12/giờ × 24 × 30 | 8.640 | 1,728% | 0,864% | CÓ (không dùng Vercel Cron) |
| GitHub Actions mỗi 5 phút → gọi thẳng Supabase | 12/giờ × 24 × 30 | 0 (Vercel) | **0%** | 0% | CÓ |
| **`pg_cron` mỗi 5 phút, SQL nội bộ** | 12/giờ × 24 × 30 | 0 (Vercel) | **0%** | 0% | CÓ (không liên quan Vercel) |

**Đọc bảng này như thế nào.**

Con số 1,7% trong ticket là **đúng về số học nhưng không liên quan về mặt quyết định**. Nếu Vercel Cron cho phép chạy mỗi 5 phút trên Hobby thì 8.640 invocation/tháng thật sự chỉ chiếm 1,728% ngân sách — hoàn toàn chấp nhận được, và ticket sẽ kết thúc bằng "dùng đi". Nhưng Vercel Hobby **không** cho phép, và biểu thức đó fail ngay lúc deploy.

Ở tần suất mà Hobby thực sự cho phép — **1 lần/ngày, 30 lần/tháng, 0,006% ngân sách** — chi phí gần như bằng không, nhưng **giá trị nghiệp vụ cũng gần như bằng không**: một Match quá hạn có thể nằm chờ tới 24 giờ (thực tế tới ~25 giờ vì cửa sổ ±59 phút) trước khi được quét. Với một game 1v1, đó không phải finalize, đó là bỏ mặc.

→ **Kết luận của bảng: giới hạn tần suất mới là thứ giết phương án Vercel Cron, không phải chi phí invocation.** Bất kỳ thảo luận nào về "cron có tốn quota không" đều là thảo luận sai trọng tâm ở tier hiện tại.

## GitHub Actions scheduled workflow

Repo `tdhcoding/DigitCode-EscapeRoom` đã ở GitHub, nên đây không thêm vendor mới vào stack.

**Có free cho public repo không: CÓ.** "GitHub Actions usage is **free** for **self-hosted runners** and for **public repositories** that use standard GitHub-hosted runners." [Billing for GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions). Với private repo, GitHub Free có 2.000 phút/tháng và 500 MB artifact storage — tức nếu repo là private thì scheduled workflow **có** tiêu vào một quota có hạn.

**Granularity thấp nhất: 5 phút.** "The shortest interval you can run scheduled workflows is once every 5 minutes." [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)

**Docs nói gì về việc job bị trễ hoặc bỏ.** GitHub nói thẳng:

> "The `schedule` event can be delayed during periods of high loads of GitHub Actions workflow runs. High load times include the start of every hour."

> "To decrease the chance of delay, schedule your workflow to run at a different time of the hour."

[Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)

→ GitHub tuyên bố **có thể trễ** và chỉ ra nguyên nhân (đầu mỗi giờ). Cách giảm rủi ro là dùng offset lẻ, ví dụ `7,17,27,37,47,57 * * * *` thay vì `*/5`. GitHub **không** tuyên bố một giới hạn trên cho độ trễ, và **không** tuyên bố có bồi hoàn/retry cho lần chạy bị bỏ.

**Luật tự động disable sau 60 ngày.**

> "In a public repository, scheduled workflows are automatically disabled when no repository activity has occurred in 60 days."

[Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)

→ Đây là bản sao của bài toán pause ở Supabase, chỉ đổi thời hạn từ 7 ngày sang 60 ngày và đổi định nghĩa từ "user database activity" sang "repository activity". Nó **rộng rãi hơn nhiều** (60 ngày, và một commit bất kỳ là đủ), nhưng nó cùng bản chất: **một cơ chế im lặng tự tắt khi hệ thống im lặng.** Với repo đang được phát triển tích cực thì không bao giờ chạm ngưỡng; với repo đóng băng thì scheduled workflow tắt đúng lúc nó là thứ duy nhất còn chạy.

**Chi tiết khác:** "Scheduled workflows run on the latest commit on the default branch." [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)

**Đánh giá.** GitHub Actions là **cơ chế zero-cost duy nhất trong khảo sát vừa đủ tần suất (5 phút) vừa nằm ngoài Supabase**, nên nó là cơ chế duy nhất có thể đồng thời (a) quét Match với độ trễ chấp nhận được, và (b) tạo ra đúng loại hoạt động **từ bên ngoài** mà tài liệu Supabase công nhận là chống pause ("API calls to your project or sending requests via your connected application"). Đổi lại, nó có độ trễ không giới hạn trên khi GitHub tải cao và tự tắt sau 60 ngày repo im lặng. Nó không phải một scheduler đáng tin cho logic quan trọng — nhưng nó là ứng viên tốt nhất cho một sweep cơ hội.

## Cơ chế ngoài bốn cái trên

**cron-job.org.** Trang chủ tuyên bố "Our service is absolutely free and financed entirely by voluntary donations" và "Jobs can be executed with frequencies up to once per minute". [cron-job.org](https://cron-job.org/en/). Tài liệu REST API của họ chỉ nêu giới hạn API request ("By default, this limit is 100 requests per day"), không nêu giới hạn số cronjob hay interval. [cron-job.org REST API docs](https://docs.cron-job.org/rest-api.html)

**Đánh giá:** nó **thêm vendor thứ tư** vào stack (sau Vercel, Supabase, GitHub) để đổi lấy tần suất 1 phút thay vì 5 phút của GitHub Actions. Nó không có SLA, không có tuyên bố về độ tin cậy, và mô hình tài chính là quyên góp tự nguyện. Với một hệ thống mà kiến trúc đã cố tình không phụ thuộc vào timer, thêm một vendor không SLA để tăng tần suất quét từ 5 phút xuống 1 phút là đánh đổi sai hướng. **Không khuyến nghị.**

## Có cần thẻ không

Ticket hỏi đích danh chiều này ("...có tính vào quota invocation không, **có cần card không**?"). Câu trả lời trung thực: **không vendor nào trong khảo sát tuyên bố rõ rằng free tier của họ không cần thẻ** — trừ hai ngoại lệ nhỏ. Đây là cùng kết luận mà [#8](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/8) đã ghi cho Vercel Hobby và Supabase Free, và đã đọc lại trang gốc trong phiên này để xác nhận nó chưa đổi.

| Vendor | Tài liệu nói gì về thẻ | Kết luận |
| --- | --- | --- |
| **Vercel Hobby** | Trang Hobby nói "The Hobby plan is **free**" và **không có câu nào** về thẻ hay phương thức thanh toán cho chính Hobby. Thẻ chỉ xuất hiện ở quy trình **nâng lên Pro**: bước 5 của "Upgrading to Pro" là "**Enter your card details**". [Hobby plan](https://vercel.com/docs/plans/hobby) | **Không tuyên bố.** Suy được là Hobby không cần thẻ vì chỉ Pro mới hỏi thẻ, nhưng đó là suy luận. |
| **Supabase Free** | Trang pricing **không nhắc gì** tới thẻ, phương thức thanh toán hay yêu cầu billing cho Free plan. [Pricing](https://supabase.com/pricing) | **Không tuyên bố.** |
| **GitHub Actions (public repo)** | Trang billing nói thẳng usage là **free** cho public repo dùng standard runner, và **không nêu** yêu cầu thẻ cho việc đó. [Billing for GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions) | **Không tuyên bố yêu cầu thẻ**, và repo này vốn đã ở GitHub nên câu hỏi gần như không phát sinh. |
| **cron-job.org** | Tuyên bố **rõ**: "Our service is absolutely free and financed entirely by voluntary donations." [cron-job.org](https://cron-job.org/en/) | Ngoại lệ duy nhất tuyên bố rõ. Nhưng phương án này đã bị loại vì lý do khác. |

**Hệ quả cho quyết định:** chiều "cần thẻ không" **không phân biệt được** các phương án trong khảo sát này — không phương án nào có tuyên bố "cần thẻ", và không phương án nào có tuyên bố chắc chắn "không cần thẻ". Nó **không** là tiêu chí loại trừ ở đây. Nếu việc không phải nhập thẻ là ràng buộc cứng của dự án thì phải kiểm chứng bằng cách **thật sự tạo tài khoản**, không phải bằng tài liệu — cùng kiểu kiểm chứng mà #8 đã xếp vào launch gate.

## Điều tài liệu vendor KHÔNG nói

Đây là danh sách các khoảng trống thật sự — đã đọc trang gốc và không tìm thấy tuyên bố. **18 mục.** Mỗi mục là một chỗ **không được phép suy đoán khi thiết kế**.

| # | Khoảng trống | Trang đã đọc |
| --- | --- | --- |
| 1 | **Supabase không định nghĩa "activity" bằng con số.** "sufficient", "too few", "a few user requests each day" — không có ngưỡng định lượng nào. | [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) |
| 2 | **Supabase không nói hoạt động nội bộ database (pg_cron) có được tính là activity hay không.** Từ ngữ dùng là "user database activity"/"user queries" và danh sách chống pause chỉ có hai mục ngoại vi — gợi ý nhưng không tuyên bố. | [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) |
| 3 | **Supabase không nói điều gì xảy ra với compute/Postgres khi project bị pause.** Không có câu nào xác nhận database bị dừng. | [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) |
| 4 | **Supabase không nói `pg_cron` có chạy hay không khi project paused.** Không có tuyên bố nào ở cả trang Cron lẫn trang Pausing. | [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing), [Supabase Cron](https://supabase.com/docs/guides/cron) |
| 5 | **Supabase không có SLO restore.** Không nêu thời gian restore mất bao lâu. | [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) |
| 6 | **Supabase không nói mã lỗi/hành vi API khi gọi vào project đã pause.** | [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) |
| 7 | **Supabase không nói `pg_cron`/Supabase Cron có giới hạn theo plan hay không.** Việc Free dùng được là **suy ra từ việc không có giới hạn nào được nêu**, không phải từ một câu khẳng định. | [Supabase Cron](https://supabase.com/docs/guides/cron), [Extensions](https://supabase.com/docs/guides/database/extensions) |
| 8 | **Supabase không công bố trần tuyệt đối số cron job**, chỉ khuyến nghị "no more than 8 Jobs run concurrently". Cũng không công bố giá trị `cron.max_running_jobs` thực tế trên Nano hay có sửa được trên Free không. | [Supabase Cron](https://supabase.com/docs/guides/cron) |
| 9 | **Supabase không nói request HTTP đi ra từ `pg_net` có tính vào Egress hay không.** Trang egress liệt kê "Database, Auth, Storage, Edge Functions, Realtime and Log Drains" nhưng định nghĩa là "transmitted out of the system to a connected client" — không đề cập outbound HTTP từ DB. | [Egress](https://supabase.com/docs/guides/platform/manage-your-usage/egress), [pg_net](https://supabase.com/docs/guides/database/extensions/pg_net) |
| 10 | **`pg_net` không tuyên bố có retry** khi request thất bại, và không tuyên bố hành vi khi queue quá tải. | [pg_net](https://supabase.com/docs/guides/database/extensions/pg_net) |
| 11 | **Vercel không nói cron invocation có tính vào Edge Requests hay không.** Docs xác nhận nó tính vào Function Invocations và mô tả cron là "HTTP GET request to your project's production deployment URL", nhưng không nói request đó có tính vào trần 1.000.000 Edge Requests của Hobby. | [Cron Jobs](https://vercel.com/docs/cron-jobs), [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing), [Hobby plan](https://vercel.com/docs/plans/hobby) |
| 12 | **Vercel không công bố giới hạn trên cho độ trễ cron ngoài cửa sổ giờ.** "best effort" và "±59 min" là tất cả những gì được nói; không có cam kết "không bao giờ trễ quá X". | [manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs) |
| 13 | **GitHub không công bố giới hạn trên cho độ trễ `schedule`**, chỉ nói "can be delayed" và chỉ ra đầu giờ là lúc tải cao. Cũng không nói lần chạy bị bỏ có được bù hay không. | [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) |
| 14 | **GitHub không công bố trần số scheduled workflow.** | [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) |
| 15 | **cron-job.org không công bố trần số cronjob, SLA, hay cam kết độ tin cậy nào.** | [cron-job.org](https://cron-job.org/en/), [REST API docs](https://docs.cron-job.org/rest-api.html) |
| 16 | **Vercel không tuyên bố Hobby có cần thẻ hay không.** Trang Hobby chỉ nói plan là "free"; thẻ chỉ xuất hiện trong quy trình nâng lên Pro. | [Hobby plan](https://vercel.com/docs/plans/hobby) |
| 17 | **Supabase không tuyên bố Free có cần thẻ hay không.** Trang pricing không nhắc tới thẻ hay phương thức thanh toán cho Free. | [Pricing](https://supabase.com/pricing) |
| 18 | **Supabase không tuyên bố phiên bản Postgres mặc định của một project Free tạo mới**, mà cú pháp sub-minute của Cron lại đòi `15.1.1.61` trở lên. | [quickstart](https://supabase.com/docs/guides/cron/quickstart) |

## Khuyến nghị cho #3 và cho lifecycle của #4

**Cái gì KHÔNG dùng được:**

- **Vercel Cron trên Hobby: không dùng cho finalize Match.** Tần suất tối đa 1 lần/ngày với cửa sổ ±59 phút. Không phải vấn đề chi phí (30 invocation/tháng = 0,006% ngân sách) mà là vấn đề tần suất — `*/5 * * * *` fail ngay lúc deploy. [usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)
- **Supabase Scheduled Edge Function: không dùng.** Nó chỉ là `pg_cron` + `pg_net` gọi vòng ra rồi vòng vào, thêm một network hop và một timeout 2 giây, tiêu Edge Function invocation, không mua thêm đảm bảo nào. [Schedule functions](https://supabase.com/docs/guides/functions/schedule-functions)
- **cron-job.org: không dùng.** Thêm vendor thứ tư không SLA để đổi lấy 4 phút tần suất. [cron-job.org](https://cron-job.org/en/)

**Cái gì dùng được, và với đảm bảo tới đâu:**

- **`pg_cron` chạy SQL nội bộ, chi phí bằng 0, tần suất xuống tới một phút vô điều kiện** (và tới `'30 seconds'` **nếu** project ở Postgres `15.1.1.61` trở lên — phải kiểm bằng `select version()`, đừng suy từ tài liệu).** Đây là công cụ đúng cho một sweep finalize. Đảm bảo: tần suất **tốt** (sub-minute), chi phí **tốt** (không đụng quota nào trừ khi sinh Realtime message có người nghe), hành vi khi pause **không xác định**. [Supabase Cron](https://supabase.com/docs/guides/cron), [quickstart](https://supabase.com/docs/guides/cron/quickstart)
- **GitHub Actions mỗi 5 phút, gọi thẳng vào Supabase, free vì repo public.** Đây là cơ chế duy nhất tạo ra hoạt động **từ bên ngoài** — đúng loại mà tài liệu Supabase công nhận chống pause. Đảm bảo: tần suất **chấp nhận được** (5 phút), độ tin cậy **best-effort có thể trễ**, tự tắt sau 60 ngày repo im lặng. [Events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [Billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)

**Khuyến nghị cụ thể cho #3 (finalize Match quá hạn):**

**Giữ nguyên quyết định "không có server timer tick". Không đưa scheduled job vào đường đi bắt buộc.** Lý do đến từ chính tài liệu vendor, không phải từ sở thích kiến trúc:

1. Cơ chế duy nhất đủ tần suất và ở trong stack (`pg_cron`) **không được vendor bảo đảm còn chạy** đúng lúc cần nó nhất (Chiều B).
2. Cơ chế duy nhất chống được pause (hoạt động từ ngoài) **tự tắt sau 60 ngày im lặng** (GitHub Actions) hoặc **chỉ chạy 1 lần/ngày** (Vercel Hobby).
3. Mọi cơ chế trong khảo sát đều được chính vendor mô tả là best-effort, không retry, và có thể chạy trùng. Vercel: "Cron job delivery is best effort... cron jobs should be resilient to both missed runs and duplicate runs". GitHub: "can be delayed during periods of high loads". [manage cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs), [Events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)

→ **Finalize lười + tự chữa ở admission vẫn phải là đường đi duy nhất tới trạng thái đúng.** Không có gì trong khảo sát này biện minh cho việc nới lỏng ràng buộc đó.

**Nếu vẫn muốn thêm một sweep cơ hội** (để Match zombie không nằm chờ tới lần admission kế tiếp), thứ tự ưu tiên:

1. **`pg_cron` chạy một hàm SQL idempotent mỗi 1–5 phút.** Rẻ nhất, gần dữ liệu nhất, không network hop. Bắt buộc: hàm phải idempotent và phải dùng cùng transition guard với đường finalize lười — không được là một đường thứ hai có logic riêng.
2. **Không cần và không nên** ghép thêm Vercel Cron hay Edge Function vào việc này.

**Khuyến nghị cho lifecycle của #4 (chống pause):**

- **Không được coi `pg_cron` là biện pháp chống pause.** Vendor không hứa (khoảng trống #2). Nếu thiết kế dựa vào nó, thiết kế đang dựa vào một giả định không có nguồn.
- **Biện pháp chống pause duy nhất có nguồn là hoạt động từ bên ngoài**: "making API calls to your project or sending requests via your connected application". [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing). Trong giai đoạn có người chơi thật, điều này tự động thoả mãn — chống pause **không phải bài toán khi hệ thống đang được dùng**.
- **Bài toán chỉ tồn tại trong giai đoạn im lặng** (giữa các đợt phát triển, hoặc sau khi beta kết thúc). Cho giai đoạn đó, một GitHub Actions workflow mỗi 5 phút (hoặc thưa hơn nhiều, ví dụ mỗi 6 giờ — vì Supabase chỉ cần "a few user requests to the database each day") gọi một endpoint đọc nhẹ là biện pháp có nguồn, free, và không thêm vendor. Nhưng phải ghi nhận nó **cũng** tự tắt sau 60 ngày repo im lặng.
- **Cần có runbook thủ công cho tình huống đã pause.** Vì restore là thủ công, không có API restore được nêu, và không có SLO. [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing)
- **Nếu tại thời điểm launch việc bị pause là không chấp nhận được**, lối thoát duy nhất mà vendor tuyên bố là nâng lên Pro: "**Paid projects** cannot be paused..." (mục *Preventing project pausing*), và ở phần mở đầu: "Projects under a paid plan are not subject to **automatic** pausing for inactivity." — **hai câu riêng biệt trên cùng trang**, không phải một câu. [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing). Đây là quyết định của human-in-the-loop, nằm ngoài ràng buộc zero-cost của ticket này.

## Cần kiểm tra lại trước launch

- Đọc lại [Vercel Cron usage & pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing) để xác nhận Hobby minimum interval vẫn là "Once per day" — đây là con số quyết định toàn bộ kết luận về Vercel Cron.
- **Kiểm phiên bản Postgres thật của project** bằng `select version()` nếu định dùng tần suất dưới một phút — quickstart của Supabase Cron đặt điều kiện `15.1.1.61` trở lên và không nói phiên bản mặc định của project Free mới.
- Đọc lại [Supabase Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) xem Supabase đã bổ sung định nghĩa định lượng cho "activity" chưa, và đã nói rõ về hoạt động nội bộ database chưa.
- **Kiểm chứng thực nghiệm khoảng trống #2 và #4** nếu vẫn muốn dựa vào `pg_cron`: dựng một Supabase Free project chỉ có một job `pg_cron` chạy mỗi 5 phút, không có traffic ngoài, và quan sát trong 7–14 ngày xem có nhận email cảnh báo pause không. Đây là cách duy nhất để trả lời câu hỏi mà tài liệu không trả lời. Kết quả thực nghiệm vẫn **không** phải một cam kết của vendor và có thể thay đổi bất kỳ lúc nào.
- Xác nhận repo còn là public (điều kiện để GitHub Actions free), vì nếu chuyển private thì scheduled workflow bắt đầu tiêu vào 2.000 phút/tháng. [Billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
