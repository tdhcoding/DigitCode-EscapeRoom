# Plan — Issue #6: Định lượng độ công bằng và khả năng giải của Puzzle

Ticket: https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6
Map: https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1
Branch: `feat/puzzle-fairness-characterization`

## Mục tiêu

Tạo characterization **tái chạy được** cho không gian Puzzle và clue của native
engine, đủ để ticket game spec (#9) quyết định eligibility contract cho
competitive Match, mà không đóng băng bug/lifecycle coupling của bản Qt.

Ticket này **chỉ tạo facts, bounds, counterexamples và decision inputs**. Không
chọn policy competitive, không sửa source sản phẩm (C++/QML/CMake/firmware).

## Nguồn sự thật

Toàn bộ mô hình phải suy ra từ `backend/gameboard.cpp` + `backend/gameboard.h`:

| Thành phần | Vị trí |
| --- | --- |
| Rejection sampler sinh secret | `backend/gameboard.cpp:471-482` |
| `DIGIT_MAP` (7 segment `[a,b,c,d,e,f,g]`) | `backend/gameboard.cpp:22-27` |
| Q1 chẵn/lẻ | `backend/gameboard.cpp:491-495`, `250-280` |
| Q2 so sánh cặp liền kề | `backend/gameboard.cpp:497-509`, `282-326`, `365-373`, `687-697` |
| Q3 đếm segment theo cột/hàng | `backend/gameboard.cpp:511-556`, `328-363` |
| Q4 FULL/NOT FULL | `backend/gameboard.cpp:589-656`, `getMaxLed` `375-388` |
| Auto-lock/auto-light khi FULL | `backend/gameboard.cpp:391-436` |
| Win/lose lifecycle | `backend/gameboard.cpp:62-139`, `806-838` |

## Work units

Agent chính (session này) giữ `tools/analysis/digitcode.py` — mô hình dùng
chung — và review toàn bộ output. Các unit dưới đây **không chồng file**.

| Unit | File sở hữu | Nội dung |
| --- | --- | --- |
| U0 (agent chính) | `tools/analysis/digitcode.py` | Mô hình generator + clue, port 1-1 từ C++ |
| U1 | `tools/analysis/analysis_generator.py` | Đếm secret hợp lệ, phân phối chính xác của sampler, tỉ lệ max/min, so sánh với uniform |
| U2 | `tools/analysis/analysis_signature.py` | Partition của Q1/Q2/Q3/Q4, quan hệ suy ra giữa các clue, collision + counterexample |
| U3 | `tools/analysis/analysis_cost.py` | Chi phí clue: lower bound information-theoretic, exhaustive ở k nhỏ, greedy/beam upper bound, adaptive simulation, difficulty proxies |
| U4 | `tools/analysis/test_analysis.py` | Test/fixture chống regression cho chính analysis tool |
| U5 | `docs/plans/2026-08-22-issue-6-puzzle-fairness/native-behaviors.md` | Audit hành vi native: cái nào là bug/lifecycle coupling, không được đóng băng |

Driver `tools/analysis/puzzle_fairness.py` (agent chính) gọi U1-U3 và in report
deterministic.

## Ràng buộc kỹ thuật

- Python 3.9, **chỉ standard library**, không network, không dịch vụ ngoài.
- Deterministic: không dùng RNG không seed; mọi con số phải tái lập bit-for-bit.
- Cấm task agent dùng `git restore`, `git checkout --`, `git reset`.
- Không sửa file ngoài file mình sở hữu.

## Hypothesis cần xác minh độc lập (từ audit trước, **chưa** được coi là fact)

1. 465.120 secret hợp lệ.
2. 86 cặp secret trùng full Q1+Q2+Q3 signature.
3. Q4 suy được từ Q3 nên không phá các collision đó.
4. Tỉ lệ xác suất max/min của sampler ≈ 9/7.

## Verification

- `python3 tools/analysis/puzzle_fairness.py --all` từ clean checkout, ghi lại
  thời gian chạy + môi trường.
- Mỗi invariant kiểm bằng ≥ 2 đường độc lập khi khả thi (ví dụ: đếm secret bằng
  brute force 10^6 **và** bằng DP theo vị trí).
- `python3 -m unittest tools.analysis.test_analysis -v`.
- `git diff --check`.
- Không rebuild Qt (không đụng C++/CMake/QML).

## Acceptance criteria (theo ticket #6)

1. [ ] Mô hình chính xác constraint generator từ source C++
2. [ ] Tổng số secret hợp lệ + phân phối xác suất thực tế của sampler
3. [ ] Signature/partition Q1-Q4, clue nào độc lập / suy ra được
4. [ ] Collision + counterexample cụ thể
5. [ ] Chi phí clue tối thiểu hoặc bounds có phương pháp rõ ràng (phân biệt fixed set / adaptive / heuristic)
6. [ ] Difficulty proxies đủ cho #9 quyết định eligibility
7. [ ] Danh sách native behaviors là bug/lifecycle coupling, không được canonical hoá
8. [ ] Script deterministic + lệnh chạy + output kiểm chứng
