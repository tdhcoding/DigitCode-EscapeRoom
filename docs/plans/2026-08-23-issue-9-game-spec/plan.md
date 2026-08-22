# Plan — Ticket #9: Chốt competitive game specification chuẩn

Ticket: https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9
Map: https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1
Branch: `feat/competitive-game-spec` (tách từ `origin/main` = `8137758`)
Loại ticket: `wayfinder:grilling` → **HITL**. Agent **không** tự trả lời thay
người dùng; mọi policy dưới đây do người dùng chốt trong hội thoại.

## Ticket hỏi gì

Canonical competitive ruleset: Puzzle eligibility/generation, semantics và
duplicate policy của Q1–Q4, pending-question timeout, segment/lock model,
Score, Wrong Guess, Player terminal states, Match outcome, và những giá trị nào
phải configurable — kế thừa standing decisions của map #1 nhưng **không** port
bug native.

## Đầu vào (đã đọc, không chép lại)

| Nguồn | Dùng để |
| --- | --- |
| Map #1 Notes | standing decisions phải kế thừa |
| [#6 findings.md](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6) mục 4, 5, 6 | collision 86 cặp, chi phí clue `[14,22]`/`[8,16]`, ngân sách điểm |
| #6 `native-behaviors.md` mục 2 | 20 hành vi **cấm** đóng băng |
| #6 `native-behaviors.md` mục 4 | 31 câu hỏi mở, là xương sống của design tree |
| `CONTEXT.md` (untracked ở worktree chính) | từ vựng Player / Puzzle / Match / Score / Solve / Wrong Guess |

Bốn quyết định #6 cố ý đẩy sang #9: eligibility của 172 secret collision;
chính sách sampler; ngân sách điểm (30s vs 60s hao mòn); Wrong Guess và đường
thắng (vẽ-là-thắng vs VERIFY).

## Cách làm

1. **Grilling theo rounds.** Frontier của design tree được hỏi trọn một lượt,
   mỗi câu kèm khuyến nghị; chờ người dùng trả lời rồi mới tính frontier kế.
2. **Fact-finding là việc của agent.** Một task agent trích semantics Q1–Q4,
   mô hình segment/lock và pending-question timer từ source, ghi ra
   `clue-reference.md` cạnh file này. Fact-only, không chọn policy.
3. **Spec.** Sau khi frontier rỗng, viết `game-spec.md`: ruleset chuẩn duy
   nhất, đánh số rule để execution ticket trích dẫn được, kèm bảng
   configurable values và bảng đối chiếu "không port bug native".
4. **Domain.** Từ vựng mới chốt trong lúc grilling được ghi thẳng vào phần
   glossary; `CONTEXT.md` ở worktree chính là existing change của phiên trước,
   **không đụng vào**.
5. **Resolution.** Comment resolution lên #9, close, append đúng một context
   pointer vào "Decisions so far" của map #1.

## Ranh giới

- Không implementation web, không scaffold code, không PR, không commit vào `main`.
- Không resolve ticket thứ hai (#4, #7 vẫn blocked).
- Khoảng `[14,22]` và `[8,16]` của #6 chỉ mở ticket mới nếu spec thực sự cần
  con số chính xác.
