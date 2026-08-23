# Findings — Thu hẹp hai khoảng còn hở của #6

Ticket nguồn: [Định lượng độ công bằng và khả năng giải của Puzzle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6) (đã đóng)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)
Branch: `research/puzzle-clue-bounds`, dựng từ `feat/puzzle-fairness-characterization` (`9056443`)
Soạn: phiên đêm 2026-08-24, không giám sát.

`findings.md` mục 9 của #6 ghi hai khoảng **chưa đóng** và gọi việc đóng chúng
là "công việc còn lại, không phải kết luận". Tài liệu này làm phần việc đó.

Giữ nguyên quy ước nhãn của #6:

* **EXACT** — chứng minh được, không phụ thuộc chiến lược hay seed.
* **BOUND** — chặn đúng nhưng chưa biết có đạt được không.
* **HEURISTIC** — kết quả của một chiến lược cụ thể; chiến lược khác có thể tốt hơn.

---

## Tóm tắt

| Đại lượng | #6 để lại | Phiên này | Nhãn mới |
| --- | --- | --- | --- |
| Tập clue **CỐ ĐỊNH** | `[14, 22]` — 14 EXACT, 22 BOUND | **đúng 22** = 110 điểm — **ĐÃ ĐÓNG** | **EXACT** |
| Chiến lược **ADAPTIVE** | `[8, 16]` — 8 EXACT, 16 HEURISTIC | **`[10, 16]`** | LB **EXACT**, UB **HEURISTIC** |

Khoảng cố định đóng hẳn. Khoảng adaptive hẹp lại từ 9 giá trị xuống 7, bằng
cách nâng chặn dưới; chặn trên 16 vẫn đứng và **đã được tái lập độc lập**.

**Không mở ticket mới** cho phần còn hở của adaptive, theo yêu cầu.

---

## 0. Mọi con số kế thừa đều được dựng lại từ đầu

Không con số nào dưới đây chép từ #6; tất cả tính lại từ `digitcode.py` (mô
hình port 1-1 từ `gameboard.cpp`) rồi mới đối chiếu.

| Đại lượng | Phiên này | #6 | |
| --- | --- | --- | --- |
| Secret hợp lệ | 465.120 | 465.120 | ✓ |
| Cặp collision | 86 | 86 | ✓ |
| Lớp phân biệt được | 465.034 | 465.034 | ✓ |
| Clue **bắt buộc** (drop-one test) | 9 — cả 6 Q1 + 3 Q2 **dọc** | 9, cùng danh sách | ✓ |
| Số lớp mà 9 clue bắt buộc chia được | 512 = 2⁹ | 512 | ✓ |
| Branching **thực sự đạt được** của 32 clue | `[6,6,6, 5,5,5, 4×10, 3,3,3, 2×13]` | khớp bảng "Miền đạt được" | ✓ |

Ngân sách điểm cũng tính lại từ luật của #9, không lấy lại từ #6:

```text
100 Score, 5/Clue, −1 mỗi 60 giây, deadline 900 giây
  hao mòn tối đa 15  ->  còn 85 cho Clue  ->  17 lần mua   (khớp R-S-12)
ở chu kỳ 30 giây : hao mòn 30 -> còn 70  ->  14 lần mua    (khớp R-S-12)
```

---

## 1. Tập clue CỐ ĐỊNH — đóng ở đúng **22**

### 1.1 Bài toán đúng là *minimum hitting set*

#6 tiếp cận bằng chặn tích (`classes(M ∪ X) ≤ 512 · classes(X)`) rồi vét cạn
theo cỡ. Chặn đó rất lỏng: ở `|X| = 5` nó không loại được gì, nên #6 dừng ở
chặn dưới 14.

Cách nhìn chặt hơn: một tập clue là hợp lệ **khi và chỉ khi** nó tách được
*mọi* cặp secret khác lớp. Với mỗi cặp, tập clue tách được nó là một bitmask.
Vậy bài toán **đúng bằng** hitting set nhỏ nhất trên họ mask đó — không phải
một xấp xỉ.

Vấn đề: `C(465.034, 2) ≈ 1,08 × 10¹¹` cặp, không liệt kê nổi.

### 1.2 CEGAR — sinh ràng buộc lười

Giải hitting set trên một **tập con** ràng buộc cho một **chặn dưới hợp lệ**.
Thử lời giải; nếu nó chưa tách được thì chính các cặp bị bỏ sót sinh ra ràng
buộc mới. Lặp lại.

Tính chất quan trọng: **mọi trạng thái trung gian đều cho một khoảng `[LB, UB]`
đúng**, nên chạy dở vẫn ra kết quả dùng được.

`tools/analysis/bounds_fixed.py`, **43 giây**:

```text
iter  1: LB= 9  ứng viên  9 clue ->     512 / 465.034 lớp
iter  2: LB=15  ứng viên 15 clue ->  59.492
iter  5: LB=17  ứng viên 17 clue -> 292.079
iter  9: LB=19  ứng viên 19 clue -> 464.592
iter 11: LB=21  ứng viên 21 clue -> 446.160
...
KẾT QUẢ  LB=21  UB=22
```

`[14, 22]` → `[21, 22]`.

### 1.3 Chứng minh không tồn tại tập 21 clue

9 clue bắt buộc luôn có mặt, nên một tập 21 clue là "9 bắt buộc + 12 trong 23
clue tuỳ chọn" — `C(23, 12) = 1.352.078` khả năng.

`tools/analysis/bounds_fixed_close.py` duyệt DFS hitting set: chỉ tập nào hit
hết mọi ràng buộc đã biết mới được kiểm tra tách thật; mỗi lần trượt lại nạp
thêm ràng buộc, cắt tiếp cây. DFS kết thúc mà không tìm được tập nào ⇒ không
tồn tại.

```text
gieo ràng buộc: 6.879
19 ứng viên được kiểm tra tách thật, tất cả đều trượt
DFS vét cạn xong sau 20 vòng
KẾT LUẬN: KHÔNG tồn tại tập 21 clue tách được.
```

Chỉ 19 ứng viên phải kiểm tra thật — phần còn lại của `1.352.078` bị ràng buộc
cắt sạch.

### 1.4 Kiểm chứng bằng thuật toán **khác hẳn**

Kết luận trên là một khẳng định phủ định, và nó dựa vào một bộ đếm cây do chính
phiên này viết — nên không đủ tin nếu chỉ có một đường. `bounds_fixed_verify.py`
chứng minh lại bằng cách **không dùng DFS, không dùng branch & bound**:

1. Gieo ràng buộc từ tập bắt buộc và **mọi cặp** clue tuỳ chọn → 28.496 mask,
   rút về **64 mask tối tiểu** (nhỏ nhất 2 bit, lớn nhất 8 bit).
2. Vét cạn cả `C(23, 11) = 1.352.078` cách bỏ 11 clue tuỳ chọn.
3. 1.348.789 cách bị 64 mask tối tiểu bác ngay; **3.289 sống sót**.
4. Kiểm tra tách thật cả 3.289 → **không cái nào tách được**.

```text
duyệt xong 1352078 cách bỏ 11 clue; còn sống 3289
KẾT LUẬN ĐỘC LẬP: không ứng viên nào tách được => tối thiểu 22 (EXACT)
```

Hai đường độc lập cùng kết luận.

### 1.5 Hai nhân chứng cho 22

Chặn trên cần một tập thật. Có hai, tìm bằng hai đường khác nhau, **cùng cỡ 22
nhưng khác thành phần** — nên 22 không phải đặc sản của một chiến lược:

| | Tập |
| --- | --- |
| Tham lam + bỏ dần | 6 Q1, `Q2:T-U`, `Q2:X-Y`, `Q2:T-W`, `Q2:U-X`, `Q2:V-Y`, `Q3:A..I` (cả 9), `Q3:K`, `Q3:P` |
| DFS ở `target = 13` | 6 Q1, `Q2:T-U`, `Q2:U-V`, `Q2:W-X`, `Q2:T-W`, `Q2:U-X`, `Q2:V-Y`, `Q3:A`,`B`,`D`,`E`,`G`,`H`,`I`, `Q3:K`, `Q3:N`, `Q3:P` |

Cả hai đều kiểm chứng trực tiếp: `n_blocks = 465.034`.

Điểm chung đáng chú ý: **cả hai đều lấy đủ 9 clue bắt buộc, ít nhất 7 trong 9
bộ đếm cột `A..I`, và đúng 2 bộ đếm hàng.** Cấu trúc 22 = 9 + 13 khá cứng.

### 1.6 Hệ quả: kết luận "chỉ lối adaptive mới chơi được" bây giờ mới **đúng**

Đây là phần đáng chú ý nhất cho #9.

Dòng tóm tắt #6 trên map ghi: *"tập clue cố định tốn `[70, 110]` điểm nên vượt
ngân sách 100 — chỉ lối adaptive mới chơi được"*. Nhưng `[70, 110]` **không**
kéo theo kết luận đó: cận dưới 70 điểm (14 clue) nằm **thoải mái trong** ngân
sách 85 điểm cho Clue của ruleset 1.0.0. Chừng nào khoảng còn hở, khả năng "tập
cố định rẻ và chơi được" vẫn chưa bị loại.

Đóng khoảng ở 22 mới loại nó:

```text
tối thiểu 22 clue × 5 điểm = 110 điểm
  > 100 điểm Score khởi đầu (R-S-01)      -> bất khả thi kể cả khi bỏ qua hao mòn
  > 85 điểm ngân sách Clue thực tế         -> thiếu 25 điểm, tức 5 lần mua
```

Nói cách khác: kết luận thì đúng, nhưng **tiền đề của nó trước đây chưa đủ**.
Giờ nó là EXACT.

Ràng buộc phái sinh, kiểm chứng được bằng test: một Ruleset hợp lệ muốn giữ
tính chất "không chơi được kiểu non-adaptive" chỉ cần
`Score khởi đầu < 22 × giá Clue`. Ở `1.0.0`: `100 < 110` ✓. Đây là họ hàng của
R-K-05 (`Score khởi đầu < 32 × giá Clue`, tức `100 < 160`) nhưng **chặt hơn nhiều**:
R-K-05 còn dư 60 điểm biên, ràng buộc này chỉ còn **10 điểm**. Nói cách khác,
R-K-05 một mình **không** bảo vệ tính chất "non-adaptive là bất khả thi" — nó
vẫn cho phép những Ruleset mà tập cố định 22 clue mua nổi.

---

## 2. Chiến lược ADAPTIVE — `[8, 16]` → **`[10, 16]`**

### 2.1 Vì sao chặn dưới 8 của #6 quá lỏng

#6 dùng `6^d ≥ 465.034`, ra `d ≥ 8`. Nó giả định **mọi** clue chia được 6 nhánh.
Thực tế chỉ **ba** clue làm được: `Q3:B`, `Q3:E`, `Q3:H`. Multiset branching
thật là `[6,6,6, 5,5,5, 4×10, 3,3,3, 2×13]`.

`d` clue cho tối đa tích của `d` branching lớn nhất:

```text
6·6·6·5·5·5       = 27.000      (6 clue)  < 465.034
              ·4  = 108.000     (7 clue)  < 465.034
              ·4  = 432.000     (8 clue)  < 465.034   <- #6 dừng ở đây
              ·4  = 1.728.000   (9 clue)  >= 465.034
```

⇒ `d ≥ 9` ngay, chỉ bằng cách thay trần nhánh giả định bằng trần nhánh thật.
Đây là lập luận đếm thuần tuý, đúng cho **mọi** chiến lược.

### 2.2 Khai triển minimax → **10**

Chặn đếm ở gốc bỏ qua một điều: sau khi hỏi một clue, clue đó không dùng lại
được, và các nhánh **không đều nhau**. Khai triển `d` mức đầu (min trên mọi
clue, max trên mọi nhánh), lá dùng chặn đếm với danh sách branching **đã trừ
clue đã hỏi trên đường đi**:

| Khai triển | Chặn dưới |
| --- | --- |
| 0 mức (chỉ chặn đếm ở gốc) | 9 |
| 2 mức | 9 |
| **3 mức** | **10** |

Khai triển 3 mức duyệt cả `C(32,3) = 4.960` bộ ba clue (mỗi bộ ba phục vụ cả 6
hoán vị), ~161 giây. Kết quả **10** là EXACT: nó là chặn dưới đúng cho mọi cây
quyết định, không phụ thuộc chiến lược.

### 2.3 Chặn trên 16 — tái lập được, nhưng **phụ thuộc cách phá hoà**

#6 báo worst case 16 cho greedy minimax, clue mở đầu `Q3:B`. Chạy lại đúng luật
đã mô tả — *"mỗi bước chọn câu làm nhỏ nhất lớp con lớn nhất"* — nhưng phá hoà
theo thứ tự chỉ số thì ra **17**, clue mở đầu `Q3:A`. `Q3:A` và `Q3:B` hoà nhau
ở gốc.

Quét bốn luật phá hoà trên cùng một bộ khung:

| Phá hoà | worst | trung bình | p99 |
| --- | --- | --- | --- |
| theo chỉ số | **17** | 12,1052 | 15 |
| nhiều lớp con nhất | **16** | 11,8351 | 15 |
| tổng bình phương cỡ lớp nhỏ nhất | **16** | 11,8324 | 15 |
| chỉ tổng bình phương (bỏ minimax) | **17** | 11,6818 | 15 |

Luật *"nhiều lớp con nhất"* tái lập đúng con số của #6: worst 16, trung bình
11,835 (khớp 11,84), p99 15. Histogram cũng gần khớp; chênh lệch còn lại là do
#6 đếm trên 465.120 **secret** còn ở đây đếm trên 465.034 **lớp**, cộng với phá
hoà ở các mức sâu hơn.

**Kết luận về nhãn:** 16 là HEURISTIC theo đúng nghĩa mạnh của từ — nó không
suy được từ mô tả *"greedy minimax"*; đổi một quy tắc phá hoà mà #6 không ghi
lại là mất nó. Chặn trên mà tài liệu này tự kiểm chứng được vẫn là **16**, và
nhân chứng là cây do luật *"nhiều lớp con nhất"* sinh ra.

### 2.4 Quét chiến lược rộng hơn

Quét 4 luật phá hoà × ép từng clue trong 32 làm clue mở đầu — **128 lượt dựng
cây đầy đủ**, ~21 phút (`bounds_adaptive_search.py sweep`).

Phân bố worst case trên 128 lượt:

| worst case | số lượt |
| --- | --- |
| **16** | 30 |
| 17 | 88 |
| 18 | 10 |

| Luật phá hoà | worst tốt nhất | số lượt đạt 16 |
| --- | --- | --- |
| theo chỉ số | 16 | 6 |
| nhiều lớp con nhất | 16 | 12 |
| tổng bình phương nhỏ nhất | 16 | 12 |
| chỉ tổng bình phương | 17 | 0 |

**Không lượt nào xuống dưới 16.** 16 đạt được từ ba luật phá hoà khác nhau và
nhiều clue mở đầu khác nhau (ví dụ `Q2:T-W` với phá hoà theo chỉ số, histogram
`{6:28, 7:336, 8:2.966, 9:12.717, 10:36.822, 11:77.228, 12:114.763, 13:119.812,
14:75.523, 15:24.091, 16:748}`), nên nó không phải đặc sản của một cấu hình
duy nhất — nhưng vẫn chỉ là chặn trên trong **họ greedy minimax**.

Đọc ngược lại: 98 trong 128 cấu hình greedy hợp lý cho worst case **17 hoặc 18**,
tức **vượt** trần 17 lần mua của ruleset 1.0.0 hoặc dùng sạch nó. Chỉ 30 cấu
hình đạt 16. Con số 16 mà R-S-11 dựa vào là **thiểu số** trong họ chiến lược
của chính nó.

---

## 3. Điều này nói gì với ruleset `digitcode-ruleset/1.0.0`

Không phải quyết định — chỉ là dữ kiện cho #9 và các ticket sau.

1. **Biên an toàn của R-S-11 mỏng đúng như spec nói, và lý do thì mỏng hơn.**
   R-S-11 chọn hao mòn 60 giây vì trần 17 lần mua "phủ được worst case 16 với
   đúng một lần mua dư". Con số 16 nay đã được tái lập độc lập, nên lập luận
   đứng vững — nhưng nó tựa vào một quy tắc phá hoà **không được ghi ở đâu cả**.
   Cùng họ greedy, phá hoà khác đi thì worst case là 17, và biên dư thành **0**.
2. **Khoảng thật là `[10, 16]`.** Cây tối ưu có thể chỉ cần 10 lần mua. Spec đã
   nói đúng hướng ("cây tối ưu có thể cần ít hơn, không bao giờ cần nhiều hơn");
   giờ "ít hơn" có cận dưới cứng là 10 thay vì 8.
3. **R-P-16 (cấm ngưỡng độ khó cho Ranked) không bị lung lay.** Lý do R-P-16 nêu
   là khoảng `[8, 16]` chưa đóng nên không có cây tối ưu để đặt ngưỡng. Thu hẹp
   về `[10, 16]` không đổi điều đó — vẫn chưa có cây tối ưu.
4. **Ràng buộc Ruleset mới, kiểm chứng được:** `Score khởi đầu < 22 × giá Clue`
   giữ tính chất "non-adaptive là bất khả thi". Ở `1.0.0` là `100 < 110`, biên
   **10 điểm** — đổi giá Clue xuống 4 (`100 < 88`) vẫn giữ được, xuống 4 và nâng
   Score khởi đầu lên 90 thì mất.

---

## 4. Công cụ và cách tái chạy

Chỉ dùng standard library — máy chạy phiên này **không có numpy**, và
`tools/analysis/` vốn đã là stdlib-only. Deterministic: không có RNG ở bất kỳ
đâu, nên không cần seed (khác với chặn trên 22 của #6, vốn dùng bỏ tham lam có
seed `20260822`).

| File | Vai trò |
| --- | --- |
| `tools/analysis/analysis_bounds.py` | Dữ liệu nền, chặn đếm, hitting set chính xác |
| `tools/analysis/bounds_fixed.py` | CEGAR: `[14,22]` → `[21,22]` |
| `tools/analysis/bounds_fixed_close.py` | Chứng minh không tồn tại tập 21 clue |
| `tools/analysis/bounds_fixed_verify.py` | Kiểm chứng độc lập bằng vét cạn `C(23,11)` |
| `tools/analysis/bounds_adaptive.py` | Chặn dưới (khai triển minimax) và greedy gốc |
| `tools/analysis/bounds_adaptive_search.py` | Quét luật phá hoà và clue mở đầu |

```bash
cd tools/analysis
python3 -u bounds_fixed.py                  # ~45 giây  -> [21, 22]
python3 -u bounds_fixed_close.py ck.txt 12  # ~20 giây  -> không có tập 21
python3 -u bounds_fixed_verify.py           # ~10 phút  -> xác nhận độc lập
python3 -u bounds_adaptive.py lb3           # ~3 phút   -> chặn dưới 10
python3 -u bounds_adaptive_search.py sweep  # ~25 phút  -> chặn trên 16
```

Bắt buộc `python3 -u`: không có nó output bị buffer và không theo dõi được.

Mẹo biểu diễn khiến mọi thứ chạy được bằng Python thuần: đáp án của mỗi clue
lưu thành một `bytes` dài 465.120, nên `len(set(zip(*cols_selected)))` — phép
đếm lớp, chạy hàng nghìn lần — nằm hoàn toàn ở tầng C.

---

## 5. Ranh giới của kết quả

- Khoảng adaptive **vẫn hở**: `[10, 16]`. Đóng nó cần cây quyết định tối ưu, mà
  bài toán đó là NP-hard nói chung và không gian trạng thái ở đây là 465.034
  lớp. Khai triển 4 mức sẽ tốn khoảng 32 lần mức 3 (`C(32,4) = 35.960` bộ bốn),
  ước lượng ~1,5 giờ, và không chắc nâng được chặn dưới thêm.
- Chặn trên 16 là **HEURISTIC**. 128 lượt quét không tìm được cây nào tốt hơn,
  nhưng quét trong họ greedy thì không nói được gì về ngoài họ đó. Cây tối ưu
  nằm đâu đó trong `[10, 16]` và tài liệu này không thu hẹp thêm được.
- Cả hai kết quả đo trên tập **lớp** (465.034), tức đã gộp 86 cặp collision —
  đúng mốc mà #6 dùng ở mục 5. Với Ranked, R-P-10 loại hẳn 172 secret đó khỏi
  pool, nên mốc còn sạch hơn.
- Kết quả **không** phụ thuộc giả định về `QRandomGenerator` (điều mà #6 phải
  ghi chú ở mục 9): mọi thứ ở đây là tính chất tổ hợp của tập secret hợp lệ và
  bảng đáp án, không đụng tới phân phối của sampler.
- Tài liệu này **không** chọn policy nào và **không** đề xuất sửa ruleset. Mục 3
  là dữ kiện cho #9 xem lại nếu muốn, không phải quyết định.
