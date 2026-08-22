# U5 — Audit hành vi native engine (ticket #6)

Ticket: https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6
Map: https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1

**Mục đích.** Liệt kê hành vi của Qt/ESP32 engine hiện tại là **bug**, **lifecycle
coupling** hay **divergence** so với Notes của map, để ticket #9 (game spec bản web
multiplayer) không vô tình đóng băng chúng thành canonical rule.

**Phạm vi.** Đây là audit đọc-hiểu. Không sửa source, không chạy app, không đo
runtime. Mọi khẳng định dưới đây đều trích `file:line` từ worktree
`wt-issue6-puzzle-fairness`. Ticket #6 **không chọn policy** — phần 4 chỉ đặt câu hỏi.

**Lưu ý nguồn.** `CONTEXT.md` ở repo root **không tồn tại** (chỉ có
`docs/agents/domain.md` mô tả cách dùng nó). Từ vựng domain dùng ở đây lấy từ
`PRJ_DigitCode_Master_Context.md` và Notes của map #1. Đây là gap cho
`domain-modeling`, không phải lỗi của #6.

**Ký hiệu phân loại**

| Mã | Nghĩa |
| --- | --- |
| `BUG` | Sai so với chính ý định của code (comment/doc/rules popup nói khác) |
| `LIFECYCLE` | Coupling giữa luật chơi và vòng đời UI/timer/tiến trình — không port được sang server-authoritative |
| `DIVERGENCE` | Code chạy đúng nhưng lệch Notes của map #1 |
| `INTENTIONAL` | Chủ ý, nhưng vẫn cần #9 xác nhận có giữ hay không |
| `INTEGRITY` | Lỗ hổng toàn vẹn/chống gian lận (kề fairness, bắt buộc phải giải quyết ở bản web) |

---

## 1. Bảng phân loại hành vi

### 1.1 Điều kiện thắng và đường thắng

| ID | Hành vi | `file:line` | Code làm chính xác gì | Loại | Ảnh hưởng công bằng / khả năng giải | Quyết định #9 phải đưa ra |
| --- | --- | --- | --- | --- | --- | --- |
| N01 | **Vẽ đúng = thắng ngay, không cần VERIFY** | `backend/gameboard.cpp:764` (`updateSeg` gọi `checkWinCondition`), `:734-744` (`tapSegment`), `:152-156` (`tapDrawingPad`), `:63-92` (`checkWinCondition`) | Mỗi lần một vạch LED đổi trạng thái, engine so toàn bộ 6 LED với `DIGIT_MAP[m_secretCode[i]]`; khớp thì dừng đồng hồ, xoá `m_secretCode` (`:82`) và `emit gameWon()` (`:90`) | **BUG / LIFECYCLE** | **Nghiêm trọng nhất.** Đoán bằng cách vẽ là **miễn phí và không giới hạn**: mỗi lần chạm vạch là một lần thử ngầm, engine tự báo khi trúng. Người chơi duy lý **không bao giờ bấm VERIFY** → luật 2-strike (N09) trở thành hình phạt tự nguyện, chỉ trừng phạt người chơi cẩn thận. Với 1v1 đây là đường thắng thống trị | Solve được định nghĩa bởi **hành động VERIFY tường minh** hay bởi **trạng thái bàn cờ**? Nếu giữ auto-detect thì cost của một guess là bao nhiêu và đếm ở đâu? |
| N02 | `setLedSegState` cũng gọi `checkWinCondition`, `setLedDigit` thì **không** | `:777-784` (có, `:783`), `:767-775` (không) | Ba hàm ghi `m_segStates`; chỉ 2/3 kiểm tra thắng | **BUG** | Ba đường ghi bàn cờ có 3 ngữ nghĩa thắng khác nhau. Hiện **cả `setLedSegState` lẫn `setLedDigit` đều không có caller nào** trong app (grep toàn `UI/`, `backend/`, `main.cpp`) → là API chết vẫn `Q_INVOKABLE` (`backend/gameboard.h:38-39`). Đường sống duy nhất là `updateSeg` | Có giữ nhiều đường ghi board không? Nếu có, kiểm tra thắng phải nằm ở **một** chỗ (invariant sau mỗi transition) chứ không rải theo entry point |
| N03 | **`lockAndLightUpFull()` ghi thẳng `m_segStates` nhưng không kiểm tra thắng** | `:391-436`, ghi ở `:431`, emit ở `:433-434`; không gọi `checkWinCondition` | Khi Q3/Q4 trả FULL, engine tự bật + khoá vĩnh viễn toàn bộ vạch của nhóm đó | **BUG** | Nếu nét auto-fill cuối cùng làm bàn cờ khớp đúng mã, **chiến thắng bị bỏ lỡ tại thời điểm đó**. Người chơi đứng trên mã đúng mà không được báo; chỉ phát hiện lại khi (a) chạm rồi chạm lại một vạch bất kỳ (`updateSeg` → check) hoặc (b) bấm `BTN_VERIFY`. Trong 1v1 đây là mất thời gian thuần tuý và không quan sát được | Auto-fill có được coi là "player progress" (kích hoạt điều kiện thắng) hay chỉ là hiển thị? |
| N04 | **Hai đường thắng chấp nhận hai tập trạng thái khác nhau (hold = 2)** | `:746-753` (`holdSegment` set `2`), `:63-92` (`checkWinCondition` so **danh sách chính xác**, `:70`), `:562-578` (`decodeDigitFromSegments` chuẩn hoá `!=0 → 1`, `:567-570`) | `checkWinCondition` so `QVariantList` nguyên vẹn nên `2 != 1` → không bao giờ thắng; `BTN_VERIFY` decode board thì coi `2` là sáng | **BUG** | Cùng một bàn cờ: đường auto-detect nói "chưa đúng", đường VERIFY nói "đúng". Người chơi dùng long-press (`UI/LedDisplay.qml:70`) để đánh dấu vạch sẽ **không bao giờ tự thắng** dù đã vẽ đúng mã — phạt ngầm một thói quen UI hợp lệ | Trạng thái vạch là nhị phân (on/off) hay ba trạng thái (off / on / marked)? Nếu ba, trạng thái `marked` có tính là "on" khi chấm bài không? |
| N05 | Bấm VERIFY bằng phần cứng đọc bàn cờ; bằng QML thì gõ text | `:177-201` (`BTN_VERIFY` decode 6 LED), `UI/ScreenGame.qml:199` (`verifyCode(txtCodeInput.text)`) | Hai nguồn guess khác nhau đổ vào cùng `verifyCode` | **LIFECYCLE** | Người chơi QML có thể gõ mã mà **không cần vẽ**; người chơi phần cứng bắt buộc phải vẽ đủ 6 chữ số hợp lệ mới guess được (`:190` từ chối nếu có LED không decode ra 0-9). Chi phí thao tác của một guess khác nhau theo thiết bị | Guess là "6 chữ số nộp lên" hay "trạng thái bàn cờ tại thời điểm nộp"? |

### 1.2 Vòng đời ván chơi (terminal state)

| ID | Hành vi | `file:line` | Code làm chính xác gì | Loại | Ảnh hưởng | Quyết định #9 |
| --- | --- | --- | --- | --- | --- | --- |
| N06 | **Thua KHÔNG kết thúc ván trong engine** | `m_secretCode` chỉ bị xoá ở `:82` và `:812` (cả hai đều là đường **thắng**). Ba đường thua `:106-116`, `:125-132`, `:823-833` **không** xoá | Sau khi `emit gameLost()`, `m_secretCode` vẫn còn, `m_ansEvenOdd` vẫn còn, `handleButtonPress` vẫn nhận lệnh (`:171` chỉ chặn khi chưa từng sinh ván) | **BUG / LIFECYCLE — nghiêm trọng** | **Thắng được sau khi đã thua.** Sau game over, người chơi phần cứng vẫn vẽ được (`tapDrawingPad` → `updateSeg` → `checkWinCondition`) và vẫn bấm `BTN_VERIFY` được → `emit gameWon()` chồng lên màn Result thua. Vẫn mua được clue (trừ điểm âm). `gameLost` có thể bắn nhiều lần. Engine **không có khái niệm terminal state**; marker duy nhất là `m_secretCode` rỗng và chỉ đường thắng set nó | Round state phải là gì (`ACTIVE / SOLVED / ELIMINATED / EXPIRED`)? Sau terminal, input nào còn được chấp nhận? |
| N07 | Không có state DEFAULT sau khi thắng/thua | `:120-139` `onPenaltyTimeout` `return` ở `:131` bỏ qua reset `m_currentState = DEFAULT` (`:137`); `checkWinCondition` `:63-92` không đụng `m_currentState` | Thắng/thua trong lúc đang chờ chọn mục tiêu Q1-Q4 để lại state machine ở `WAIT_*` | **BUG** | Lần bấm nút kế tiếp sau khi ván kết thúc bị diễn giải là câu trả lời cho câu hỏi cũ, và **trừ 5 điểm** | Lifecycle của "câu hỏi đang treo" khi round chuyển terminal? |
| N08 | `generateRandomPuzzle()` là lệnh huỷ diệt không xác nhận, gọi được mọi lúc | `:163-166` (`BTN_NEWGAME`), `firmware/.../DigitCodeFirmware.ino:282-293` (giữ 5s ở phía firmware) | Backend không kiểm tra gì, wipe ván đang chạy ngay | **INTENTIONAL / LIFECYCLE** | Rào chắn "giữ 5 giây" nằm **ở firmware**, không ở engine → bất kỳ client WebSocket nào gửi `{"type":"ACTION","btnId":"BTN_NEWGAME"}` đều reset ván tức thì (xem N26) | Ai được quyền reset một Match, và rào chắn nằm ở đâu (client hay server)? |

### 1.3 Chính sách đoán sai và điểm

| ID | Hành vi | `file:line` | Code làm chính xác gì | Loại | Ảnh hưởng | Quyết định #9 |
| --- | --- | --- | --- | --- | --- | --- |
| N09 | **Sai lần 1 không trừ điểm, không khoá; sai lần 2 thua ngay** | `:806-838`; `m_guessCount++` `:821`; `>= 2` → `m_points = 0` + `gameLost` `:823-833`; lần 1 chỉ `emit wrongGuessWarning()` `:836` | Không có `m_points -= 10`, không có timer khoá nào trong nhánh sai lần 1 | **DIVERGENCE** (Notes: lần đầu −10 điểm + khoá 10 giây) | Chi phí guess sai lần 1 trong engine = **0 điểm, 0 giây**. Kết hợp với N01, hình phạt đoán sai gần như không tồn tại | Chính sách Wrong Guess của bản web: trừ điểm? khoá? bao nhiêu strike? Áp cho cả đường auto-detect (N01) hay chỉ VERIFY? |
| N10 | Hình phạt "sai lần 1" thực chất nằm ở **QML**, và phần cứng không nhận được gì | `wrongGuessWarning` chỉ có consumer duy nhất là `UI/ScreenGame.qml:49-52` → popup chặn 4 giây (`UI/ScreenGame.qml:230`). `backend/hardwareserver.cpp:20-28` **không** connect `gameWon`/`gameLost`/`wrongGuessWarning` | Người chơi desktop bị chặn UI 4 giây (đồng hồ vẫn chạy); người chơi thuần phần cứng **không có phản hồi nào** cho lần đoán sai đầu | **BUG / LIFECYCLE** | Cùng một engine, **hai mức phạt khác nhau theo thiết bị**. Người chơi phần cứng không biết mình đã cháy 1 strike cho tới khi chết ở lần 2 | Penalty là state của server (mọi client thấy như nhau) hay hiệu ứng UI? |
| N11 | **Kiểm tra thua vì cạn điểm chỉ chạy trong 2 slot của timer** | Chỉ `:106-116` (`onGlobalTimerTick`) và `:125-132` (`onPenaltyTimeout`). Bốn chỗ trừ 5 điểm `:266`, `:311`, `:341`, `:620` **không** kiểm tra | Mua clue có thể đẩy `m_points` xuống `<= 0` (kể cả **âm**) mà chưa thua | **BUG / LIFECYCLE** | Bình thường trễ tối đa 1 giây. Nhưng nếu `m_globalTimer` đã dừng (pause N12, hoặc sau terminal N06) thì **kiểm tra không bao giờ chạy** → bất tử | Điều kiện thua phải là invariant kiểm sau **mỗi** transition, hay là tick-driven? |
| N12 | **`pauseGame()` dừng cả đồng hồ tổng lẫn đồng hồ phạt; `resumeGame()` chỉ khởi động lại đồng hồ tổng** | `:793-797`, `:799-804`; điều kiện `:801`; gọi từ `UI/ScreenGame.qml:70`, `:306`, `UI/ScreenMenu.qml:57` | Pause → không mất điểm theo thời gian, và **khung phạt 10 giây bị huỷ vĩnh viễn** (resume không start lại `m_penaltyTimer`) | **BUG / LIFECYCLE — nghiêm trọng** | Ba exploit chồng nhau: (1) suy nghĩ vô hạn không mất điểm; (2) bấm Q1 → Pause → Continue = **bỏ hoàn toàn deadline 10 giây** cho câu hỏi đó; (3) nếu điểm rơi `<= 0` trong lúc pause (phần cứng vẫn mua clue được), `resumeGame` từ chối start lại (`m_points > 0` sai) → đồng hồ **không bao giờ chạy lại**, N11 không bao giờ kiểm tra → **bất tử + thời gian đóng băng, vẫn thắng được bằng cách vẽ** | 1v1 online có Pause không? Nếu có, pause tác động thế nào tới đồng hồ chung của Match và tới đối thủ? |
| N13 | `onPenaltyTimeout` trừ 1 điểm khi chần chừ quá 10 giây | `:120-139`, `-1` ở `:121`; timer start `:224` với `10000` | Bấm nút câu hỏi rồi không chọn mục tiêu trong 10 giây → −1 điểm, huỷ lệnh, về `DEFAULT` | **INTENTIONAL** (nhưng comment `:119` ghi nhầm "5 GIÂY") | Hợp lý về ý định. Vấn đề là **10 giây phủ cả chuỗi nhiều bước**: Q2/Q4 cần 2 lần chọn nhưng vẫn dùng chung một khung 10 giây khởi động từ lúc bấm `BTN_Qx` (`:224`), không reset giữa các bước (`:285-290`, `:592-597`) | Có giữ deadline chần chừ không? Tính theo mỗi bước hay cả chuỗi? |
| N14 | Bấm lại `BTN_Qx` reset khung 10 giây, miễn phí | `:204-226`, đặc biệt `:224` | Mỗi lần bấm nút câu hỏi (kể cả cùng một câu) đều `start(10000)` lại | **BUG (nhỏ)** | Deadline chần chừ có thể né vô hạn bằng cách bấm lại Q1 mỗi <10 giây, không mất gì | Deadline có reset được không, và reset có tốn gì không? |
| N15 | Bấm nút sai loại trong lúc `WAIT_*` bị nuốt im lặng, đồng hồ phạt vẫn chạy | `:252` (Q1 bỏ qua A-S), `:283` (Q2), `:329` (Q3), `:590` (Q4) — tất cả `return` không thông báo, không dừng timer | Không OLED, không âm thanh, không hoàn tác | **BUG (UX/fairness)** | Người chơi tưởng đã trả lời, thực ra vẫn đang đếm ngược → −1 điểm | Input không hợp lệ phải trả lỗi tường minh hay im lặng? |
| N16 | `m_guessCount` **không được khởi tạo** trong constructor | `backend/gameboard.h:123`; ctor `:29-33` chỉ init `m_points`, `m_activeDigit`, `m_currentState`, `m_playTimeSeconds`; gán đầu tiên ở `:442` | Giá trị bất định cho tới lần `generateRandomPuzzle()` đầu tiên | **BUG** | Trong luồng thực tế không quan sát được (mọi ván đều đi qua `:442`), nhưng là UB và là dấu hiệu state không có một nơi khởi tạo duy nhất | Round state khởi tạo ở đâu — constructor hay hàm start? |

### 1.4 Kinh tế clue (Q1-Q4)

| ID | Hành vi | `file:line` | Code làm chính xác gì | Loại | Ảnh hưởng | Quyết định #9 |
| --- | --- | --- | --- | --- | --- | --- |
| N17 | **Bất đối xứng khoá Q3/Q4** | `processQ3` `:331` từ chối khi `m_askedQ3 \|\| m_lockedFull`; `processQ4` `:607-608` từ chối khi **một trong hai** nút thuộc `m_askedQ3 \|\| m_lockedFull` | `processQ3` **không** kiểm tra `m_askedQ4` → hỏi Q3 sau Q4 luôn được | **INTENTIONAL nhưng bất đối xứng** | Thứ tự mua quyết định tổng chi phí: Q4 trước rồi Q3 sau = hợp lệ, tổng 10 điểm cho thông tin đầy đủ 1 nút; Q3 trước thì Q4 trên nút đó bị khoá vĩnh viễn. Người chơi biết luật ăn đứt người không biết — kiến thức meta, không phải kỹ năng giải đố | Quan hệ bao hàm giữa các loại clue (Q3 ⊃ Q4 cho cùng một nút) có được mã hoá tường minh trong giá và trong quy tắc trùng lặp không? |
| N18 | **Q4 không chống trùng chính nó → vẫn trừ 5 điểm cho thông tin bằng 0** | `:607-608` chỉ tra `m_askedQ3`/`m_lockedFull`; `m_askedQ4` chỉ được đọc ở `processReview` `:675` | Hỏi lại đúng cặp Q4 cũ (nếu cả hai đều NOT FULL) → qua kiểm tra, `-5` ở `:620`, trả lại y hệt kết quả cũ | **BUG** | Q1/Q2/Q3 từ chối trùng **miễn phí** (`:255-261`, `:301-307`, `:331-337`), riêng Q4 **tính tiền cho câu trùng**. Bẫy thuần tuý với người chơi hay quên | Trùng lặp clue: từ chối, hay tính tiền? Áp dụng nhất quán cho mọi loại clue |
| N19 | Một nút "bẩn" giết cả cặp Q4 | `:610-616` | Nếu **một** trong hai nút đã hỏi Q3/đã khoá, toàn bộ request Q4 bị huỷ (không trừ điểm) và state về `DEFAULT` | **INTENTIONAL** | Không mất điểm nhưng mất 2 lần bấm + tiêu tốn khung 10 giây; phải bấm `BTN_Q4` lại từ đầu | Clue nhiều mục tiêu xử lý partial-validity thế nào? |
| N20 | **Kết quả FULL của Q3/Q4 vừa cho thông tin vừa làm hộ việc vẽ** | `:349-352` (Q3), `:632-636` (Q4) → `lockAndLightUpFull` `:391-436` bật + khoá vạch | Nhóm FULL được tự động vẽ sẵn lên bàn cờ và khoá không cho tắt (`:427`, chặn ở `:738`, `:750`) | **INTENTIONAL — nhưng giá trị phụ thuộc kết quả** | Cùng giá 5 điểm, một clue trả FULL đáng giá hơn hẳn clue trả NOT FULL: nó vừa cho thông tin vừa **xoá bớt thao tác vẽ** (mà thao tác vẽ chính là đường thắng ở N01). Ngược lại, count = 0 **không** được auto-clear tương ứng (`:349` chỉ so với `getMaxLed`) → phần thưởng chỉ có một chiều | Clue có được phép thay đổi trạng thái bàn cờ của người chơi không, hay chỉ được cho thông tin? |
| N21 | Q3 tính trên **đáp án**, không phải trên nét người chơi đang vẽ | `:486-489` dựng `st` từ `DIGIT_MAP[m_secretCode[i]]`, `:512-556` đếm trên `st`; `:344-346` tra bảng đã tính sẵn | Đúng ý định, nhưng chuỗi OLED "X has N demon(s)" (`:355`) và việc auto-bật vạch trên chính bàn cờ người chơi làm hai khái niệm trông như một | **INTENTIONAL** | Không phải bug, nhưng ngôn ngữ domain đang chập "bàn cờ đáp án" và "bàn cờ người chơi" — rủi ro cao khi #9 viết spec | Vocabulary: `Solution board` vs `Player board` phải là hai thực thể riêng trong spec |
| N22 | **19 counter Q3 là dư thừa: cột và hàng cùng phân hoạch đúng 42 ô** | `:524-533` (A-I: `{f,e}/{a,g,d}/{b,c}` cho từng cặp LED `(0,3),(1,4),(2,5)`) và `:546-556` (J-S: `{a}/{f,b}/{g}/{e,c}/{d}` cho từng hàng 3 LED) | A-I phủ trọn 6 LED × 7 vạch = 42 ô, đúng một lần; J-S cũng vậy → `sum(A..I) == sum(J..S)` | **INTENTIONAL — nhưng giá không phản ánh** | Biết 18/19 counter là suy ra counter thứ 19 miễn phí, nhưng engine vẫn tính 5 điểm cho nó. Đây là ví dụ tổng quát: **giá clue phẳng 5 điểm không phản ánh lượng thông tin thực** (chi tiết định lượng thuộc U2/U3) | Giá clue là phẳng hay theo lượng thông tin? Clue suy ra được có được bán không? |
| N23 | **Ngân sách điểm chặn cứng số clue mua được** | Điểm khởi đầu 100 (`:30`, `:445`), mỗi clue −5 (`:266`, `:311`, `:341`, `:620`), chết khi `<= 0` (`:106`) | Tổng slot clue phân biệt: Q1 = 6 LED (`:252`), Q2 = 7 cặp liền kề (`:367-369`), Q3 = 19 hàng/cột (`:375-388`) → 32 clue = 160 điểm | **INTENTIONAL** | **Không thể mua hết**: tối đa **19 lần mua** (20 lần → 0 điểm → chết ở tick kế tiếp), và còn phải trừ hao mòn theo thời gian (N24) + phạt chần chừ (N13). Đây là ràng buộc fairness cứng mà #9 kế thừa hoặc thay | Ngân sách và giá clue của bản web là bao nhiêu, và có cố ý giữ "không bao giờ mua hết" không? |
| N24 | Trừ 1 điểm mỗi **60** giây | `:99-103` (`m_playTimeSeconds % 60 == 0`); rules popup `UI/ScreenGame.qml:361`; `UI/ScreenReady.qml:48` | Chỉ trừ ở đúng bội số 60 của **thời gian chơi tích luỹ** | **DIVERGENCE** (Notes: mỗi 30 giây) | Trần thời gian ngầm = 100 phút nếu không mua gì. Notes muốn 30s → trần 50 phút | Tốc độ hao mòn của bản web? |
| N25 | **Không có deadline 15 phút ở bất kỳ đâu** | `onGlobalTimerTick` `:94-117` chỉ tăng `m_playTimeSeconds` và kiểm tra điểm; không có hằng số thời lượng nào trong `backend/` | Điều kiện thua duy nhất: điểm `<= 0`, hoặc sai lần 2 | **DIVERGENCE** (Notes: deadline Match 15 phút) | Bản native không có khái niệm hết giờ → không có precedent nào để port | Deadline là hard-stop cho cả Match, cho mỗi Player, hay không có? |

### 1.5 Toàn vẹn / lỗ hổng đầu vào

| ID | Hành vi | `file:line` | Code làm chính xác gì | Loại | Ảnh hưởng | Quyết định #9 |
| --- | --- | --- | --- | --- | --- | --- |
| N26 | **WebSocket server không xác thực, bind `Any:8080`, broadcast mọi thứ cho mọi client** | `backend/hardwareserver.cpp:12` (`listen(QHostAddress::Any, 8080)`), `:146-152` (`sendToHardware` gửi cho **tất cả** client), `:107-134` (nhận `ACTION`/`PAD_*` không kiểm tra nguồn) | Bất kỳ ai trong LAN đều kết nối được, nhận toàn bộ gói `OLED`/`DRAW`/`STATS` và **bơm được** input | **INTEGRITY — nghiêm trọng** | Gói `OLED` chứa **đáp án nguyên văn** (`:273`, `:319`, `:355`, `:651`). Client thứ hai xem trộm toàn bộ clue đã mua và can thiệp bàn cờ đối thủ | Kênh nào là authoritative, ai được ghi, và state đối thủ được giữ kín bằng cơ chế gì (Notes #1 yêu cầu giữ kín)? |
| N27 | Client mới kết nối được **replay toàn bộ trạng thái** | `backend/hardwareserver.cpp:64-74` (42 gói `DRAW`), `:76-86` (dòng OLED cuối), `:89` (`STATS`) | Không cần bằng chứng danh tính nào | **INTEGRITY** | Kết nối muộn = nhận nguyên bàn cờ + clue cuối cùng | Reconnect/resume của bản web xác thực thế nào? |
| N28 | **Mã bí mật được in ra stdout** | `:483` (`qDebug() << "[PUZZLE GENERATOR] New Secret Code:" << m_secretCode`); clue in ở `:582` | Log lộ đáp án mỗi ván | **INTEGRITY / BUG khi port** | Vô hại trên desktop cá nhân, **chí mạng** nếu bê nguyên tư duy đó sang server/client web (log, devtools, response payload) | Đáp án được phép tồn tại ở đâu (chỉ server? có bao giờ rời server không?) |
| N29 | **So sánh chuỗi thay vì whitelist id nút** | `:230` (`btnId >= "A" && btnId <= "S"`), `:232` (`>= "T" && <= "Y"`), `:252`, `:283`, `:329`, `:590`, `:659` | So sánh **lexicographic trên QString**, không phải kiểm tra ký tự đơn | **BUG / INTEGRITY** | Chuỗi nhiều ký tự lọt lưới: `"AB"` thoả `>= "A" && <= "S"` → `processReview` (`:658`) dùng `btnId.at(0)` (`:669`) → **trả lời cho cột A** cho một id không tồn tại. Chuỗi `"TT"` thoả `>= "T" && <= "Y"` (`:232`, `:252`) → trong `WAIT_Q1`, `QString("TUVWXYZ").indexOf("TT")` = **−1** (`:271`) → `m_ansEvenOdd[-1]` = **đọc ngoài biên**, UB/crash. Chỉ khai thác được qua N26 | Id/enum của bản web phải là tập đóng được validate ở server; mọi input ngoài tập → lỗi tường minh |
| N30 | `"TUVWXYZ"` (7 ký tự, thừa `Z`) vs `"TUVWXY"` | `:271` (Q1) vs `:704` (Review) | Hai bảng tra khác nhau cho cùng một ánh xạ nút → chỉ số | **BUG (không sống)** — **điểm bạn nêu cần chỉnh** | Ký tự `Z` **không bao giờ tới được**: guard `:252` loại `btnId > "Y"`. Với T-Y hai chuỗi cho cùng chỉ số → **không sai kết quả**. Rủi ro thật ở dòng `:271` không phải chữ `Z` mà là `indexOf` trả −1 cho chuỗi nhiều ký tự (N29) | Không cần quyết định riêng; gộp vào N29 (validate input) |

### 1.6 Sinh đề và luật chết

| ID | Hành vi | `file:line` | Code làm chính xác gì | Loại | Ảnh hưởng | Quyết định #9 |
| --- | --- | --- | --- | --- | --- | --- |
| N31 | **Nhánh `'='` của Q2 là luật chết** | `processQ2` `:318` (`val > 0 ? ">" : (val < 0 ? "<" : "=")`), `cmpValueForPair` `:687-697` (fallback `return 0` ở `:696`), generator `:478-479`, `isAdjacent` `:365-373`, `cmp` `:498` | Generator cấm `code[L] == code[L-1]` khi `L%3 != 0` (`:478`) → đúng 4 cặp ngang `(0,1),(1,2),(3,4),(4,5)`; cấm `code[L] == code[L-3]` khi `L>=3` (`:479`) → đúng 3 cặp dọc `(0,3),(1,4),(2,5)`. Bảy cặp đó **chính xác** là tập `hPairs ∪ vPairs` của `isAdjacent` (`:367-369`) | **Xác nhận: luật chết** | Q2 luôn cho đúng 1 bit (`<` hoặc `>`), không bao giờ có kết quả "bằng nhau". `return 0` ở `:696` cũng không tới được (chỉ gọi với cặp đã qua `isAdjacent`). Nếu bản web nới ràng buộc sinh mã mà giữ nguyên hiển thị 3 giá trị thì lượng thông tin của Q2 thay đổi | Ràng buộc sinh mã của bản web có giữ "hai LED liền kề luôn khác nhau" không? Nếu bỏ, Q2 thành clue 3 giá trị và toàn bộ tính toán chi phí ở U3 phải làm lại |
| N32 | **Vòng lặp sinh mã không thể quay vô hạn** | `:472-481` | Xem chứng minh ở Phụ lục A | **INTENTIONAL — đã chứng minh** | Tại mọi vị trí luôn còn `>= 6/10` chữ số hợp lệ → dừng với xác suất 1, kỳ vọng `<= 10/6` lần rút mỗi vị trí. **Không có trường hợp treo** | Không phải quyết định luật; nhưng #9 cần biết sampler này **không đều** (xem N33) |
| N33 | Sampler là rejection theo từng vị trí → **phân phối không đều** trên tập mã hợp lệ | `:472-481` (`continue` rút lại **cùng vị trí**, không rút lại cả mã) | Xác suất của một mã = tích `1/|allowed_i|`; `|allowed_i|` thay đổi theo prefix (10, 9, 9, 9, 7-8, 6-9) | **BUG tiềm ẩn về fairness** | Một số mã có xác suất xuất hiện cao hơn mã khác → nếu #9 dùng "cùng một Puzzle cho hai Player" thì độ khó kỳ vọng lệch giữa các Match. **Con số chính xác là việc của U1**, ở đây chỉ khẳng định tính không đều | Puzzle được rút uniform trên tập hợp lệ, hay giữ nguyên bias của sampler? |
| N34 | **Không có seed / puzzle id** | `backend/gameboard.h:53` (`generateRandomPuzzle()` không tham số), `:474` (`QRandomGenerator::global()`) | Không tái lập được một ván | **LIFECYCLE — thiếu năng lực** | Notes #1 yêu cầu "Match dùng cùng một Puzzle" — native **không có** cách nào phát cùng một Puzzle cho hai người. Đây là năng lực phải xây mới, không phải hành vi để port | Puzzle được định danh và phân phát thế nào (seed? id? bản ghi đầy đủ)? |
| N35 | Mỗi chữ số xuất hiện tối đa 2 lần | `:477` (`if (code.count(ch) >= 2) continue`) | Mã 6 chữ số có ít nhất 3 chữ số phân biệt | **INTENTIONAL** | Ràng buộc này (cùng `:478`, `:479`) định nghĩa toàn bộ không gian đề — là input cho U1 | Giữ nguyên ràng buộc hay đổi? |

### 1.7 Review Mode

| ID | Hành vi | `file:line` | Code làm chính xác gì | Loại | Ảnh hưởng | Quyết định #9 |
| --- | --- | --- | --- | --- | --- | --- |
| N36 | **Review Mode miễn phí, không dùng timer** | `:229-236` (chỉ khi `m_currentState == DEFAULT`), `processReview` `:658-685`, `processReviewTarget` `:699-728` | Không `m_points -= …`, không `m_penaltyTimer->start(…)` trong cả hai hàm | **INTENTIONAL** | **Rò rỉ gì:** không rò rỉ gì chưa mua. Mọi nhánh đều gác bằng `m_lockedFull` (`:662`) / `m_askedQ3` (`:667`) / `m_askedQ4` (`:675`) / `m_askedQ1` (`:703`) / `m_askedQ2` (`:718`); nhánh còn lại in `"No cheating..."` (`:682`, `:708`). **Rò rỉ gì thêm:** Q4-FULL được review dưới dạng `"X FULL"` (`:664`, qua `m_lockedFull`) còn Q4-NOT-FULL chỉ ra `"not full, guess how many"` (`:677`) — đúng lượng thông tin đã mua, không hơn | Clue đã mua có được xem lại miễn phí không? (nếu có, memory không còn là một phần của kỹ năng) |
| N37 | Review Q2 phụ thuộc `m_lastReviewTarget` — biến bị bấm nút vẽ làm nhiễu | `:714-724` (ghép cặp với nút T-Y bấm ngay trước), `:724` (ghi đè mỗi lần bấm); chỉ xoá ở `:450`. Firmware gửi **cả** `PAD_SELECT` **và** `ACTION` cho mỗi nút T-Y (`firmware/DigitCodeFirmware/DigitCodeFirmware.ino:302-307`) | Chọn LED để vẽ cũng đồng thời là một lần "review target" | **LIFECYCLE (coupling nút)** | Bấm T rồi U chỉ để chuyển LED vẽ sẽ in ra so sánh T-U (nếu đã mua) và reset đồng hồ xoá OLED (`:727`). Không rò rỉ thông tin chưa mua, nhưng **một nút mang hai nghĩa** và cả hai đều kích hoạt | Một hành động của người chơi có được phép có hai tác dụng luật chơi không? |
| N38 | Cùng nút T-Y trong `WAIT_Q1`/`WAIT_Q2` **vừa trả lời câu hỏi vừa đổi LED đang vẽ** | `:239-245` (dispatch theo state) + `backend/hardwareserver.cpp:116-119` (`PAD_SELECT` xử lý độc lập state) | Một lần bấm phần cứng → `selectTargetDigit` (`:142-150`) **và** `processQ1` (`-5` điểm ở `:266`) | **LIFECYCLE — nghiêm trọng về UX** | Người chơi phần cứng muốn đổi LED để vẽ trong lúc có câu hỏi treo sẽ **bị trừ 5 điểm** và tiêu một slot clue ngoài ý muốn | Input model của bản web: một nút một nghĩa, hay modal state? |

### 1.8 Reset trạng thái và code chết

| ID | Hành vi | `file:line` | Code làm chính xác gì | Loại | Ảnh hưởng | Quyết định #9 |
| --- | --- | --- | --- | --- | --- | --- |
| N39 | **`generateRandomPuzzle()` reset gần đủ — đối chiếu từng biến thành viên của `gameboard.h`** | Xem bảng đối chiếu ở Phụ lục B | Bỏ sót `m_activeDigit` (`gameboard.h:117`) và không dừng `m_oledClearTimer` (`gameboard.h:121`) | **BUG (nhỏ)** | `m_activeDigit` giữ nguyên LED của ván trước → nét vẽ đầu tiên của ván mới có thể rơi vào LED sai (`:152-156`), và không `emit activeDigitChanged()` nên UI không đồng bộ; firmware cũng giữ `activeDigit` cục bộ riêng (`.ino:150`, `:155-166`) nên đèn DP nhấp nháy lệch. `m_oledClearTimer` còn treo từ ván cũ có thể xoá OLED ngay đầu ván mới (`:55-60`) | Reset một round phải là "dựng state mới" hay "xoá từng biến"? (nguyên nhân gốc: state không được gom thành một struct) |
| N40 | `m_backups` khai báo nhưng không bao giờ dùng | `backend/gameboard.h:85`; 0 tham chiếu trong `backend/gameboard.cpp` | Biến chết | **BUG (dead code)** | Không ảnh hưởng luật chơi; là dấu vết của cơ chế "draft/undo" đã bỏ | Bản web có cơ chế nháp/undo không? (đừng port dấu vết này) |
| N41 | Signal `topStatsChanged` khai báo, không bao giờ emit, không ai connect | `backend/gameboard.h:60`; 0 emit trong `backend/gameboard.cpp` | Dead signal | **BUG (dead code)** | — | — |
| N42 | QML gọi hai hàm backend **không tồn tại** | `UI/LedDisplay.qml:45-46` gọi `gameBoard.turnOnGroupQml` / `gameBoard.restoreGroupQml`; không có trong `backend/gameboard.h` | Sẽ ném TypeError nếu `turnOnGroup`/`restoreGroup` được gọi — hiện **không nơi nào gọi** | **BUG (dead code)** | Không sống, nhưng cho thấy từng có cơ chế "bật cả nhóm rồi khôi phục" | — |
| N43 | 4 component QML đăng ký trong CMake nhưng không được dùng | `CMakeLists.txt:27-31` liệt kê `CounterBox.qml`, `EoDot.qml`, `CmpArrow.qml`, `DraftGrid.qml`; 0 lần instantiate (BottomBoard tự định nghĩa `EODotBox` `:30-39`, `HArrow` `:42-53`, `VArrow` `:56-68`, `CBox` `:71-77`) | Dead UI | **BUG (dead code)** | `DraftGrid.qml` chứa cơ chế "gạch số ứng viên + tự suy ra khi còn 1 số" (`:21-48`) — một trợ lý giải đố **đã bị bỏ**. Đừng nhầm nó là luật hiện hành | Bản web có công cụ ghi chú/loại trừ ứng viên cho người chơi không? |
| N44 | `m_playTimeSeconds` là **thời gian chơi**, không phải thời gian thực | `:95` (chỉ tăng khi `m_globalTimer` chạy), bị dừng bởi `pauseGame` `:795` và bởi mọi đường terminal `:78`, `:110`, `:128`, `:809`, `:828` | "Clear time" hiển thị (`:85-89`, `:814-817`) là tổng thời gian đồng hồ chạy | **LIFECYCLE** | Notes #1 dùng Solve time làm tiêu chí phụ để xếp Winner. Với native, hai người chơi cùng "clear time" có thể đã dùng lượng thời gian thực rất khác nhau (N12) | Solve time đo bằng wall-clock của Match hay bằng thời gian "đang chơi"? |

---

## 2. Danh sách "KHÔNG ĐƯỢC ĐÓNG BĂNG"

Những hành vi dưới đây **tuyệt đối không được** coi là canonical rule cho bản web.
Chúng là bug, hoặc là hệ quả của việc luật chơi bị dính vào vòng đời UI/timer/tiến
trình của bản Qt.

| # | Không được đóng băng | Ref | Lý do (một câu) |
| --- | --- | --- | --- |
| 1 | Thắng tự động khi bàn cờ khớp mã, không cần VERIFY | N01 `:764` | Biến việc đoán thành miễn phí và không giới hạn, làm toàn bộ chính sách Wrong Guess trở nên vô nghĩa. |
| 2 | Auto-fill (`lockAndLightUpFull`) không kích hoạt kiểm tra thắng | N03 `:391-436` | Người chơi có thể đang đứng trên đáp án đúng mà engine không công nhận. |
| 3 | Trạng thái `hold = 2` được VERIFY chấp nhận nhưng auto-detect từ chối | N04 `:752` vs `:70` vs `:567-570` | Hai đường thắng chấm cùng một bàn cờ ra hai kết quả khác nhau. |
| 4 | Thua không xoá `m_secretCode` (không có terminal state) | N06 `:106-116`, `:823-833` | Cho phép thắng, mua clue và thua lại **sau khi** ván đã kết thúc. |
| 5 | `pauseGame`/`resumeGame` (dừng đồng hồ + huỷ vĩnh viễn khung phạt 10 giây + soft-lock khi điểm `<= 0`) | N12 `:793-804` | Pause là exploit hoàn chỉnh: bỏ deadline, bỏ hao mòn thời gian, và có thể khiến người chơi bất tử vĩnh viễn. |
| 6 | Kiểm tra thua chỉ chạy trong slot của timer | N11 `:106`, `:125` | Khi đồng hồ dừng, điều kiện thua **không bao giờ** được kiểm tra. |
| 7 | Sai lần 1 = 0 điểm, 0 giây, và phần cứng không nhận phản hồi nào | N09, N10 `:834-837` | Hình phạt nằm trong popup QML chứ không nằm trong engine → không đồng nhất giữa các client. |
| 8 | Q4 tính tiền cho câu hỏi trùng, còn Q1/Q2/Q3 thì không | N18 `:607-608` vs `:255`, `:301`, `:331` | Quy tắc trùng lặp không nhất quán, phạt trí nhớ chứ không phạt quyết định. |
| 9 | Q3 khoá Q4 nhưng Q4 không khoá Q3 | N17 `:331` vs `:607-608` | Thứ tự mua clue quyết định chi phí — thưởng cho kiến thức meta về bug. |
| 10 | Nhánh `'='` của Q2 và fallback `return 0` của `cmpValueForPair` | N31 `:318`, `:696` | Luật chết dưới ràng buộc sinh mã hiện tại; sao chép nguyên si sẽ ẩn giấu một quyết định thiết kế chưa được đưa ra. |
| 11 | Bias phân phối của rejection sampler theo từng vị trí | N33 `:472-481` | Độ khó kỳ vọng không đồng đều giữa các Match — không chấp nhận được với Ranked. |
| 12 | So sánh chuỗi `btnId >= "A" && btnId <= "S"` làm cơ chế validate | N29 `:230`, `:232`, `:271` | Cho chuỗi rác lọt vào logic luật chơi, kể cả đường dẫn tới đọc ngoài biên. |
| 13 | WebSocket không xác thực, broadcast đáp án cho mọi client, replay state cho client mới | N26, N27 `hardwareserver.cpp:12`, `:64-89`, `:146-152` | Không có ranh giới bí mật nào — trái thẳng yêu cầu "state đối thủ được giữ kín" của Notes #1. |
| 14 | In `m_secretCode` ra log | N28 `:483` | Đáp án không được rời khỏi biên giới authoritative trong bản web. |
| 15 | Trừ 1 điểm mỗi 60 giây; không có deadline | N24, N25 `:99-103` | Lệch Notes #1 (30 giây / 15 phút) — phải là quyết định chủ động, không phải kế thừa mặc định. |
| 16 | Một nút T-Y vừa trả lời clue vừa chọn LED để vẽ | N38 `.ino:302-307` + `:239-245` | Một thao tác vô tình trừ 5 điểm và tiêu một slot clue. |
| 17 | `m_activeDigit` không reset khi sinh đề mới; `m_oledClearTimer` không dừng | N39 `:440-466` | Trạng thái ván cũ rò rỉ sang ván mới. |
| 18 | Code chết: `m_backups`, `topStatsChanged`, `turnOnGroupQml`/`restoreGroupQml`, `DraftGrid`/`EoDot`/`CmpArrow`/`CounterBox` | N40-N43 | Không phải luật hiện hành; đặc biệt `DraftGrid` là trợ lý giải đố đã bị bỏ, dễ bị đọc nhầm thành feature. |
| 19 | Giá phẳng 5 điểm cho mọi clue kể cả clue suy ra được | N22 `:524-556` | Giá không phản ánh lượng thông tin (counter thứ 19 luôn suy ra được từ 18 cái kia). |
| 20 | Auto-fill khi FULL làm hộ thao tác vẽ | N20 `:391-436` | Clue thay đổi bàn cờ người chơi, khiến giá trị clue phụ thuộc kết quả trả về. |

---

## 3. Đối chiếu native vs Notes của map #1

Nguồn Notes: `gh issue view 1 --repo tdhcoding/DigitCode-EscapeRoom` (mục **Notes**).

| Hạng mục | Native (kèm `file:line`) | Notes của map #1 | Lệch chỗ nào |
| --- | --- | --- | --- |
| Điểm khởi đầu | 100 (`backend/gameboard.cpp:30` ctor, `:445` mỗi ván mới) | "Mỗi Player bắt đầu 100 Score" | **Khớp.** |
| Giá clue | −5 mỗi lần mua hợp lệ: Q1 `:266`, Q2 `:311`, Q3 `:341`, Q4 `:620` | "clue mới hợp lệ giá 5" | **Lệch về đơn vị:** Q4 tính 5 điểm cho **hai** nút (`:624-648`) → 2,5 điểm/nút, rẻ hơn Q3 (5/nút) dù cho ít thông tin hơn. Ngoài ra Q4 tính tiền cả câu trùng (N18) trong khi Notes nói "clue **mới hợp lệ**". |
| Tốc độ hao mòn theo thời gian | −1 điểm mỗi **60** giây (`:99-103`) | "mất 1 mỗi **30** giây cho đến terminal" | **Lệch 2×.** Native cho trần thời gian ngầm 100 phút, Notes ngụ ý 50 phút. |
| Hình phạt đoán sai lần 1 | 0 điểm, 0 giây khoá; chỉ `emit wrongGuessWarning()` (`:834-837`) → popup QML chặn 4 giây (`UI/ScreenGame.qml:49-52`, `:230`), phần cứng **không nhận gì** (`hardwareserver.cpp:20-28`) | "Wrong Guess đầu mất **10** và khoá **10 giây**" | **Lệch hoàn toàn:** thiếu cả −10 điểm lẫn khoá 10 giây; hình phạt thực tế phụ thuộc client. |
| Hình phạt đoán sai lần 2 | `m_points = 0` + `gameLost()` ngay (`:823-833`) | "lần hai bị loại" | **Khớp về kết quả**, nhưng native **không** chuyển round sang terminal thật (N06) nên vẫn thắng được sau đó. |
| Đoán sai bằng cách vẽ | **Không tính là guess**, không tăng `m_guessCount`, thắng ngay khi trúng (`:764`, `:63-92`) | Notes chỉ biết đến "VERIFY đúng tạo Solve" | **Lệch về mô hình:** Notes giả định mọi Solve đi qua VERIFY; native có một đường Solve thứ hai, miễn phí và vô hạn lượt. |
| Deadline | Không tồn tại (`onGlobalTimerTick` `:94-117` không có kiểm tra thời lượng nào) | "Deadline Match là 15 phút" | **Native thiếu hoàn toàn.** Không có precedent để port. |
| Điều kiện thua | Điểm `<= 0` (`:106`) hoặc sai lần 2 (`:823`) | Terminal khi hết Score, bị loại, hoặc hết deadline | **Lệch:** thiếu nhánh hết giờ; và kiểm tra hết điểm chỉ chạy trong tick (N11). |
| Cách xác định Winner | Không có khái niệm Winner. Thắng = escape cá nhân (`:90`, `:818`); "Clear time" chỉ để hiển thị (`:85-89`, `:814-817`); nút 1v1 bị vô hiệu hoá (`UI/ScreenMenu.qml:87-91`) | "VERIFY đúng tạo Solve và khoá kết quả cá nhân, **không** tự động quyết định Winner. Khi cả hai Solve, **Score cao hơn thắng**, rồi mới xét Solve time" | **Lệch về kiến trúc:** native gộp "Solve" và "kết thúc ván"; không có so sánh Score, không có tiebreak, không có khái niệm hai Player. |
| Đo Solve time | `m_playTimeSeconds` = thời gian **đồng hồ chạy**, loại trừ pause (`:95`, `:795`) | "rồi mới xét Solve time" | **Lệch về định nghĩa:** không phải wall-clock; hai người cùng số này có thể đã dùng thời gian thực khác nhau. |
| Một Puzzle cho cả hai Player | Không có seed/id, mỗi lần gọi sinh một mã mới (`gameboard.h:53`, `:474`) | "Match dùng cùng một Puzzle nhưng Player State riêng" | **Native không có năng lực này.** Phải xây mới. |
| Giữ kín state đối thủ | Broadcast mọi gói cho mọi client, không xác thực (`hardwareserver.cpp:12`, `:146-152`, `:64-89`) | "state đối thủ được giữ kín trong lúc chơi" | **Trái ngược.** Không có ranh giới bí mật nào. |
| Practice vs Ranked, Elo | Không tồn tại trong native | "Ranked Match cập nhật Elo; Practice không" | **Native không có.** Ngoài phạm vi #6, ghi để #9 không tìm precedent. |

---

## 4. Câu hỏi mở cho ticket #9

Ticket #6 **không trả lời** những câu này.

**A. Định nghĩa Solve và chi phí đoán**

1. Solve được kích hoạt bởi hành động VERIFY tường minh, hay bởi trạng thái bàn cờ khớp đáp án (N01)?
2. Nếu giữ auto-detect: mỗi lần bàn cờ khớp/không khớp có tính là một Guess không, và tính phí thế nào?
3. Nếu bỏ auto-detect: người chơi có được phản hồi trung gian nào không (ví dụ "đủ 6 chữ số hợp lệ") hay hoàn toàn mù cho tới khi VERIFY?
4. Trạng thái vạch là 2 hay 3 giá trị (off / on / marked)? Trạng thái `marked` có tính là "on" khi chấm bài (N04)?
5. Clue có được phép ghi vào bàn cờ của người chơi không, hay chỉ được trả thông tin (N20)?

**B. Chính sách Wrong Guess**

6. Guess sai thứ nhất phải trả giá gì: điểm, thời gian khoá, cả hai, hay không gì?
7. Số strike tối đa là bao nhiêu, và hết strike là thua ngay hay chỉ khoá VERIFY?
8. Hình phạt là state của server (mọi client nhìn thấy giống nhau) hay hiệu ứng client (N10)?

**C. Kinh tế điểm và thời gian**

9. Điểm khởi đầu, giá clue, và tốc độ hao mòn (30s theo Notes, 60s theo native, hay khác)?
10. Giá clue phẳng hay theo lượng thông tin? Clue suy ra được từ clue đã mua có được bán không (N22)?
11. Clue nhiều mục tiêu (kiểu Q4) tính giá theo request hay theo mục tiêu (N17)?
12. Quy tắc trùng lặp: từ chối miễn phí, hay tính tiền? Áp cho **mọi** loại clue như nhau (N18)?
13. Quan hệ bao hàm giữa các clue (Q3 chứa Q4 cho cùng một nút) có được mã hoá tường minh không, và có khoá chéo không (N17)?
14. Có giữ khung phạt chần chừ 10 giây không? Tính theo mỗi bước chọn hay cả chuỗi (N13)? Reset có tốn phí không (N14)?
15. Điểm có được xuống âm không, và điều kiện thua được kiểm tra sau mỗi transition hay theo tick (N11)?
16. Deadline: có hay không? Cho cả Match hay cho mỗi Player? Hết deadline là thua, hay là chấm điểm theo trạng thái hiện tại (N25)?

**D. Vòng đời Match và Pause**

17. Round state gồm những giá trị nào (`ACTIVE / SOLVED / ELIMINATED / EXPIRED`…), và sau terminal thì input nào còn được chấp nhận (N06)?
18. 1v1 online có Pause không? Nếu có, nó tác động tới đồng hồ chung của Match và tới đối thủ như thế nào (N12)?
19. Solve time đo bằng wall-clock của Match hay bằng thời gian "đang chơi" (N44)?
20. Ai được quyền reset/huỷ một Match, và rào chắn nằm ở client hay server (N08)?
21. Reconnect giữa ván khôi phục state thế nào, và xác thực bằng gì (N27)?

**E. Puzzle và độ khó**

22. Puzzle được rút uniform trên tập mã hợp lệ, hay chấp nhận bias của sampler hiện tại (N33)?
23. Puzzle được định danh và phân phát cho hai Player bằng cơ chế nào (seed, id, hay bản ghi đầy đủ) (N34)?
24. Ràng buộc sinh mã có giữ nguyên "hai LED liền kề luôn khác nhau" không? Nếu bỏ, Q2 thành clue 3 giá trị và toàn bộ tính toán chi phí phải làm lại (N31, N35).
25. Có eligibility contract cho Puzzle của Ranked Match không (ví dụ chặn dưới về chi phí clue tối thiểu), và ngưỡng lấy từ đâu (kết quả U1-U3)?
26. Ngân sách điểm có cố ý giữ tính chất "không bao giờ mua hết mọi clue" của native không (N23)?

**F. Toàn vẹn**

27. Đáp án được phép tồn tại ở đâu, và có bao giờ rời khỏi biên giới authoritative không (N28)?
28. Tập id hợp lệ (LED, hàng/cột, loại clue) được validate ở đâu, và input ngoài tập xử lý thế nào (N29)?
29. State đối thủ được giữ kín bằng cơ chế gì trong lúc chơi, và được mở ra khi nào (N26)?
30. Một hành động của người chơi có được phép mang hai nghĩa luật chơi không (N37, N38)?

**G. Domain / tài liệu**

31. `CONTEXT.md` chưa tồn tại ở repo root — `Solution board` vs `Player board`, `Solve` vs `Win`, `Score` vs `Points`, `Clue` vs `Question` cần được chốt trước khi #9 viết spec (N21).

---

## Phụ lục A — Chứng minh vòng lặp sinh mã luôn dừng

Code: `backend/gameboard.cpp:472-481`.

```
while (code.length() < 6) {
    int L = code.length();
    ch = random 0..9
    if (code.count(ch) >= 2) continue;                    // (i)  :477
    if (L % 3 != 0 && code.at(L-1) == ch) continue;       // (ii) :478
    if (L >= 3   && code.at(L-3) == ch) continue;         // (iii):479
    code += ch;
}
```

Tại mỗi vị trí `L ∈ {0..5}`, một chữ số `d` bị loại khi và chỉ khi thoả (i), (ii) hoặc (iii):

- (i) loại các chữ số đã xuất hiện **đủ 2 lần** trong prefix độ dài `L`. Số chữ số như vậy `<= ⌊L/2⌋ <= 2`.
- (ii) loại **nhiều nhất 1** chữ số (`code[L-1]`).
- (iii) loại **nhiều nhất 1** chữ số (`code[L-3]`).

Vậy `|forbidden| <= ⌊L/2⌋ + 2 <= 4` với mọi `L <= 5`, tức **`|allowed| >= 6 > 0` tại mọi vị trí**.

Chi tiết theo vị trí:

| `L` | Chặn trên của `|forbidden|` | `|allowed|` tối thiểu |
| --- | --- | --- |
| 0 | 0 — (ii) và (iii) không áp dụng | 10 |
| 1 | 1 — chỉ (ii) | 9 |
| 2 | 1 — (i) bất khả (prefix 2 chữ số luôn khác nhau do (ii) tại `L=1`) | 9 |
| 3 | 1 — (ii) không áp dụng (`3 % 3 == 0`); nếu có chữ số lặp đôi thì nó chính là `code[0]` mà (iii) đã loại | 9 |
| 4 | 3 | 7 |
| 5 | 4 | 6 |

**Kết luận:** tập cho phép **không bao giờ rỗng**, mỗi vòng lặp là một phép thử Bernoulli với xác suất thành công `>= 0,6`; số lần rút cho mỗi vị trí là biến hình học, kỳ vọng `<= 10/6 ≈ 1,67`. Vòng lặp dừng với xác suất 1 và **không tồn tại trường hợp treo**. (Hệ quả: vì `|allowed|` **thay đổi** theo prefix ở `L = 4, 5`, phân phối trên tập mã hợp lệ **không đều** — xem N33; định lượng thuộc U1.)

---

## Phụ lục B — Đối chiếu reset của `generateRandomPuzzle()` với biến thành viên

Nguồn: `backend/gameboard.h:84-133` vs `backend/gameboard.cpp:440-466`.

| Biến (`gameboard.h`) | Reset trong `generateRandomPuzzle()`? | Vị trí |
| --- | --- | --- |
| `m_segStates` (`:84`) | ✅ về `{0,…,0}` cho cả 6 LED | `:458-462` |
| `m_backups` (`:85`) | ❌ — **biến chết**, 0 tham chiếu trong `.cpp` | N40 |
| `m_secretCode` (`:86`) | ✅ gán mã mới | `:482` |
| `m_ansEvenOdd` (`:88`) | ✅ `clear()` + tính lại | `:492-495` |
| `m_ansHCmp` (`:89`) | ✅ | `:500-504` |
| `m_ansVCmp` (`:90`) | ✅ | `:506-509` |
| `m_ansColCounts` (`:91`) | ✅ | `:524-533` |
| `m_ansRowCounts` (`:92`) | ✅ | `:546-556` |
| `m_points` (`:116`) | ✅ = 100 | `:445` |
| **`m_activeDigit` (`:117`)** | ❌ **bỏ sót** — giữ LED của ván trước, cũng không `emit activeDigitChanged()` | N39 |
| `m_currentState` (`:118`) | ✅ = `DEFAULT` | `:448` |
| `m_penaltyTimer` (`:119`) | ✅ `stop()` nếu đang chạy | `:464` |
| `m_globalTimer` (`:120`) | ✅ `start(1000)` | `:466` |
| **`m_oledClearTimer` (`:121`)** | ❌ **bỏ sót** — không `stop()`; timer treo từ ván cũ có thể bắn `onOledClearTimeout` (`:55-60`) ngay đầu ván mới | N39 |
| `m_playTimeSeconds` (`:122`) | ✅ = 0 | `:443-444` |
| `m_guessCount` (`:123`) | ✅ = 0 (nhưng **không** init trong ctor — N16) | `:442` |
| `m_tempTarget1` (`:126`) | ✅ `clear()` | `:449` |
| `m_lastReviewTarget` (`:127`) | ✅ `clear()` | `:450` |
| `m_askedQ1` (`:128`) | ✅ | `:451` |
| `m_askedQ2` (`:129`) | ✅ | `:452` |
| `m_askedQ3` (`:130`) | ✅ | `:453` |
| `m_askedQ4` (`:131`) | ✅ | `:454` |
| `m_lockedFull` (`:132`) | ✅ | `:455` |
| `m_lockedSegments` (`:133`) | ✅ | `:456` |

**Kết luận:** 22/24 biến được reset. Hai chỗ bỏ sót (`m_activeDigit`, `m_oledClearTimer`) đều là hệ quả của việc state ván chơi bị rải thành 24 biến thành viên rời rạc thay vì một struct dựng lại được — đây là nguyên nhân gốc, không phải hai lỗi độc lập.

---

## Phụ lục C — Những điểm chưa xác minh

| Điểm | Vì sao chưa xác minh |
| --- | --- |
| Hành vi runtime thật của các exploit N01, N06, N12 | Ticket cấm build/chạy app; kết luận suy ra từ đọc code và truy vết signal/slot, **chưa** có bằng chứng thực thi. |
| `QVariantList::operator[](-1)` ở `:271` gây crash hay đọc rác trong Qt 6.10 release build | Phụ thuộc build flags (`Q_ASSERT` bị loại ở release); chỉ khẳng định là **truy cập ngoài biên**, không khẳng định triệu chứng. |
| Con số chính xác về độ lệch phân phối của sampler | Thuộc U1 (`tools/analysis/analysis_generator.py`); ở đây chỉ chứng minh **tính không đều**, không đưa số. |
| Số collision signature và chi phí clue tối thiểu | Thuộc U2/U3; U5 không đưa con số nào để tránh mâu thuẫn với output chính thức. |
| Có tồn tại ván nào mà auto-fill (N03) thực sự hoàn tất đúng bàn cờ hay không | Cần liệt kê tổ hợp mã × tập nhóm FULL; thuộc U2/U3. Ở đây chỉ khẳng định **đường code cho phép** điều đó xảy ra. |
