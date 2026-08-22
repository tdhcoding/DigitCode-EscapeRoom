# Findings — Issue #6: Định lượng độ công bằng và khả năng giải của Puzzle

Ticket: https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/6
Branch: `feat/puzzle-fairness-characterization`

Tài liệu này chỉ chứa **facts, bounds, counterexamples và decision inputs**.
Nó **không** chọn competitive policy — đó là việc của
[ticket game spec #9](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9).

Mỗi con số dưới đây gắn nhãn:

| Nhãn | Nghĩa |
| --- | --- |
| **EXACT** | Vét cạn toàn bộ không gian, số học chính xác (`Fraction`), không lấy mẫu |
| **BOUND** | Chặn có chứng minh; khoảng chưa đóng được nêu rõ |
| **HEURISTIC** | Kết quả của một chiến lược cụ thể — chỉ là upper bound, **không** phải optimum |

## Cách tái chạy

```bash
git checkout feat/puzzle-fairness-characterization
python3 tools/analysis/puzzle_fairness.py --all        # toàn bộ báo cáo
python3 tools/analysis/test_analysis.py                # 23 test ghim mô hình
```

Chỉ cần Python 3 standard library. Không network, không dịch vụ ngoài, không
cần build Qt (không đụng C++/CMake/QML). Mọi kết quả deterministic — chạy lại
cho output byte-identical; RNG duy nhất (tìm upper bound tập clue) seed cố định
`20260822`.

Môi trường và thời gian đã đo (clean checkout của branch này):

| | |
| --- | --- |
| Môi trường | Python 3.9.6 CPython, macOS 15.1, arm64 |
| `puzzle_fairness.py --all` | **4 phút 46 giây** (liệt kê 0,21s · generator 1,77s · signature 45,8s · cost 238,6s) |
| `test_analysis.py` | 23 test, **12,8 giây**, tất cả PASS |
| `git diff --check` | sạch |

---

## 1. Mô hình generator — port 1-1 từ source C++

`tools/analysis/digitcode.py` mô hình hoá `backend/gameboard.cpp:471-482`:

```text
while (code.length() < 6):
    ch = bounded(10)                                  # đều trên 0..9
    C1  nếu prefix đã có >= 2 lần ch          -> bốc lại
    C2  nếu i % 3 != 0 và prefix[i-1] == ch   -> bốc lại   (i ∈ {1,2,4,5})
    C3  nếu i >= 3   và prefix[i-3] == ch     -> bốc lại   (i ∈ {3,4,5})
    code += ch
```

Trên bảng 2×3:

```text
┌────┬────┬────┐   C2 = hai LED cạnh nhau theo HÀNG phải khác nhau
│ T0 │ U1 │ V2 │   C3 = hai LED cạnh nhau theo CỘT phải khác nhau
├────┼────┼────┤   C1 = mỗi chữ số dùng tối đa 2 lần
│ W3 │ X4 │ Y5 │
└────┴────┴────┘   Vị trí 3 KHÔNG bị C2 chặn (3 % 3 == 0) — code[3] == code[2] hợp lệ.
```

**Điểm then chốt: đây không phải uniform sampling.** Mỗi vị trí được bốc lại
độc lập tới khi hợp lệ, nên chữ số tại vị trí `i` phân bố **đều trên tập cho
phép** `A_i(prefix)`, và

```text
P(code) = ∏ 1/|A_i(prefix_i)|
```

Sampler không bao giờ kẹt: `|A_i| >= 7` với mọi prefix hợp lệ (**EXACT**, đo
trên toàn bộ cây prefix).

## 2. Số secret hợp lệ và phân phối thực

**465.120 secret hợp lệ** — **EXACT**, xác nhận bằng **ba đường độc lập**:

| Đường | Cách làm | Kết quả |
| --- | --- | --- |
| Liệt kê | đi theo đúng luật sampler | 465.120 |
| DP / transfer matrix | 34 state, không hề duyệt qua tập secret | 465.120 |
| Phân hoạch màu | tô màu lưới 2×3 + matching trên đồ thị bù, dạng đóng | 465.120 |

Brute-force toàn bộ 10⁶ mã trong `test_analysis.py` cũng cho 465.120.

**Phân phối của sampler có đúng 4 giá trị xác suất** (**EXACT**, `Fraction`):

| `D = ∏\|A_i\|` | `p = 1/D` | số secret | khối lượng | `p / p_uniform` |
| --- | --- | --- | --- | --- |
| 408.240 | 1/408240 | 45.360 | 1/9 | 646/567 ≈ **1,1393** |
| 459.270 | 1/459270 | 40.320 | 64/729 | 5168/5103 ≈ 1,0127 |
| 466.560 | 1/466560 | 328.320 | 19/27 | 323/324 ≈ 0,9969 |
| 524.880 | 1/524880 | 51.120 | 71/729 | 646/729 ≈ **0,8861** |

- Tổng xác suất = **đúng 1** (exact, không phải xấp xỉ float).
- `p_max / p_min = **9/7**` — **EXACT**, là đẳng thức chứ không phải xấp xỉ.
  Lý do cấu trúc: `|A_0..A_3|` cố định bằng `10·9·9·9 = 7290`, chỉ còn
  `|A_4|·|A_5| ∈ {56, 63, 64, 72}`, và `72/56 = 9/7`.
- Total variation distance tới uniform = `407/27702 ≈ **0,0147**`.
- Kỳ vọng số lần gọi `bounded(10)` cho một ván: `69841/10206 ≈ 6,843`.

**Bias nằm ở đâu — và tại sao không phát hiện được bằng thống kê chữ số.**
Marginal của từng chữ số ở từng vị trí **đều tuyệt đối**: mỗi cặp (vị trí, chữ
số) có đúng 46.512 secret, dưới cả phân phối sampler lẫn uniform (**EXACT**, độ
lệch bằng 0). Bias chỉ nằm ở **mẫu va chạm vị trí**:

| Nhóm | `p_tb / p_uniform` |
| --- | --- |
| có `code[0] == code[2]` | 646/567 ≈ 1,1393 (được ưu ái nhất) |
| có `code[2] == code[4]`, hoặc mẫu `(1,3)(2,4)` | 646/729 ≈ 0,8861 (thiệt nhất) |

→ **Decision input cho #9:** chênh lệch ±14% giữa secret dễ ra nhất và khó ra
nhất là thuộc tính của *sampler*, không phải của *độ khó*. Nếu Ranked Match cần
phân phối đề đồng đều thì phải thay sampler (ví dụ liệt kê rồi bốc uniform);
kiểm tra tần suất chữ số sẽ **không** phát hiện được bias này.

## 3. Signature và partition của Q1–Q4

| Họ | Số câu | Số lớp thực tế | Trần danh nghĩa | Ghi chú |
| --- | --- | --- | --- | --- |
| Q1 (chẵn/lẻ) | 6 | 64 | 64 | 6 bit độc lập hoàn toàn |
| Q2 (so sánh) | 7 | **98** | 2⁷ = 128 | không độc lập — xem dưới |
| Q3 (đếm) | 19 | 226.972 | rất lớn | dư thừa nặng |
| Q4 (FULL) | 19 | 9.212 | 2¹⁹ | suy ra từ Q3 |
| Q1+Q2+Q3 | 32 | **465.034** | — | **không đạt 465.120** |
| Q1+Q2+Q3+Q4 | 51 | **465.034** | — | Q4 thêm 0 thông tin |

Ba dữ kiện cấu trúc, tất cả **EXACT**:

**(a) Q2 chỉ mang 1 bit mỗi câu, không phải log₂3.** C2/C3 cấm hai LED liền kề
bằng nhau, mà 7 cặp Q2 đúng là 7 cặp liền kề đó — nên nhánh `'='`
(`gameboard.cpp:318`) và fallback `return 0` của `cmpValueForPair`
(`gameboard.cpp:696`) là **code chết**: 0 secret nào chạm tới.

**(b) 7 câu Q2 không độc lập với nhau.** Chúng là một *hướng hoá* của đồ thị
lưới 2×3, và chỉ hướng hoá **phi chu trình** mới hiện thực hoá được (vì so sánh
sinh từ một thứ tự toàn phần). Số bộ dấu khả thi = **98**, khớp chính xác với
số hướng hoá phi chu trình tính độc lập bằng đa thức sắc `|χ(−1)| = 49·2 = 98`.

**(c) 19 câu đếm có đúng 2 quan hệ tuyến tính nguyên thuỷ** (hạng ma trận 17):

```text
A + C + D + F + G + I  =  K + M + P + R          (khối segment {b,c,e,f})
B + E + H              =  J + L + N + O + Q + S  (khối segment {a,g,d})
```

Quan hệ quen thuộc `Σ(cột) = Σ(hàng)` chỉ là **tổng** của hai quan hệ trên, nên
nó không phải ràng buộc nguyên thuỷ duy nhất.

**(d) Q4 suy hoàn toàn từ Q3.** `Q4(node) := Q3(node) == MAX_LED[node]`
(`gameboard.cpp:632`); 0 vi phạm trên toàn bộ 465.120 secret. Đứng một mình Q4
thô hơn Q3 **24,6 lần** (9.212 vs 226.972 lớp).

**(e) Cặp chữ số 2 và 5 không phân biệt được bằng bất kỳ câu đếm nào.** Chúng
có cùng vector cột `(left, mid, right) = (1,3,1)` **và** cùng vector hàng
`(a, f+b, g, e+c, d) = (1,1,1,1,1)`. Phép đổi tên 2↔5 giữ nguyên **toàn bộ 19
đáp án Q3** trên 367.008 secret mà nó làm thay đổi — nhưng luôn đổi ít nhất một
đáp án Q1 (2 chẵn, 5 lẻ), nên nó **không** tạo collision.

## 4. Collision — Puzzle không thể phân biệt

**86 cặp secret không thể phân biệt kể cả khi biết TOÀN BỘ clue** — **EXACT**,
xác nhận bằng ba đường độc lập (gom nhóm signature, quét phép đổi cột, công
thức tổ hợp).

```text
465.120 secret  ──toàn bộ 51 câu clue──>  465.034 lớp
                                          ├── 464.948 lớp cỡ 1
                                          └──      86 lớp cỡ 2   ← 172 secret
```

**Counterexample cụ thể** (`406517` vs `604715`): **không một câu nào** trong cả
51 câu Q1+Q2+Q3+Q4 cho đáp án khác nhau.

```text
   4 0 6        6 0 4        Q1 : 4,6 cùng chẵn; 5,7 cùng lẻ        -> giống
   5 1 7   vs   7 1 5        Q3 : col(4)+col(5) = col(6)+col(7)     -> giống
                             Q3 : mỗi hàng giữ nguyên multiset      -> giống
   đổi chỗ cột trái <-> cột phải    Q2 : 4 trên 5, 6 trên 7 xếp song song -> giống
```

**Cả 86 cặp là MỘT họ duy nhất**: đổi chỗ cột trái và cột phải của bảng
(vị trí 0↔2 và 3↔5), với cặp chữ số (4,6) ở một hàng và (5,7) ở hàng kia.

→ **Decision input cho #9.** Với 172 secret này (0,037% số ván), người chơi suy
luận hoàn hảo vẫn còn **2 ứng viên** và buộc phải đoán 50/50. Hệ quả **khác
nhau** giữa native và Notes của map, nên đây là quyết định chứ không phải sự đã
rồi:

| Luật | Chi phí của một collision cỡ 2 |
| --- | --- |
| Native, đoán bằng cách **vẽ** (`gameboard.cpp:764`) | **0** — vẽ sai không bị gì, vẽ đúng thắng ngay; đoán miễn phí không giới hạn |
| Native, đoán bằng **VERIFY** (`:806-838`) | 0 điểm; sai lần 1 chỉ cảnh báo, lần 2 mới bị loại — nên vẫn giải chắc chắn |
| Notes của map #1 (sai lần đầu −10 điểm + khoá 10 giây) | **kỳ vọng −5 điểm và −5 giây**, quyết định bởi tung đồng xu |

Puzzle collision **không phải** bất khả giải. Vấn đề là ở **Ranked Match**: hai
Player nhận cùng Puzzle, cả hai suy luận tối ưu, và người thắng được quyết định
bởi may rủi chứ không phải kỹ năng — đúng vào lúc Score chênh nhau ít nhất.
#9 phải chọn một trong: loại 172 secret này khỏi Ranked, đổi luật đoán sai,
thêm một clue phá được đối xứng cột, hay chấp nhận rủi ro 0,037%.

## 5. Chi phí clue — ba khái niệm phải tách bạch

Vì 86 collision không thể phá, **mục tiêu đúng không phải "xác định duy nhất"**
mà là "thu hẹp về lớp collision". Mọi con số dưới đây dùng mốc 465.034 lớp.

### 5.1 Tập clue CỐ ĐỊNH (non-adaptive)

Chọn trước một tập câu, không nhìn đáp án.

**9 câu là BẮT BUỘC** — **EXACT**. Bỏ riêng bất kỳ câu nào trong 9 câu này là
mất thông tin, nên **mọi** tập clue hợp lệ phải chứa cả 9:

```text
Q1:T  Q1:U  Q1:V  Q1:W  Q1:X  Q1:Y     ← cả 6 câu chẵn/lẻ
Q2:T-W  Q2:U-X  Q2:V-Y                 ← 3 so sánh DỌC
```

4 so sánh **ngang** (T-U, U-V, W-X, X-Y) thì **không** bắt buộc, và không câu
Q3 nào bắt buộc. Riêng 9 câu này chia được 512 lớp (= 2⁹, tức chúng độc lập
hoàn toàn với nhau).

| Đại lượng | Giá trị | Nhãn |
| --- | --- | --- |
| Lower bound | **14 câu = 70 điểm** | **EXACT LOWER BOUND** |
| Upper bound | **22 câu = 110 điểm** | **BOUND** (40 lần bỏ tham lam, seed 20260822) |

Phương pháp lower bound: mọi tập hợp lệ là `M ∪ X`, và
`classes(M ∪ X) ≤ classes(M) · classes(X) = 512 · classes(X)`, nên cần
`classes(X) ≥ 908,27`. Loại dần theo cỡ, chỉ phải đo các `X` còn qua được chặn
tích:

| `\|X\|` | ứng viên qua chặn tích | lớp đạt tối đa | kết luận |
| --- | --- | --- | --- |
| 1–3 | 0 | — | bất khả thi (duyệt hết) |
| 4 | 3 | 674 | **bất khả thi** (duyệt hết, 674 < 908,27) |
| 5 | 12.761 | ≥ 940 | chặn không loại được |

→ `\|X\| ≥ 5`, tức tập cố định cần **≥ 9 + 5 = 14 câu**.

Khoảng `[14, 22]` **chưa đóng**. Upper bound 22 đến từ bỏ tham lam ngẫu nhiên,
chỉ cho tập **tối tiểu theo bao hàm** (không bỏ thêm được câu nào) — **không
phải** tập nhỏ nhất tuyệt đối. Không được gọi 22 là optimum.

### 5.2 Chiến lược ADAPTIVE

Chọn câu sau khi thấy đáp án trước đó.

| Đại lượng | Giá trị | Nhãn |
| --- | --- | --- |
| Lower bound | **8 câu = 40 điểm** | **EXACT LOWER BOUND** (`6^d ≥ 465.034`, nhánh tối đa của một câu là 6) |
| Upper bound | **16 câu = 80 điểm** | **HEURISTIC** (greedy minimax, chạy trên toàn bộ 465.120 secret) |

Greedy minimax (mỗi bước chọn câu làm nhỏ nhất lớp con lớn nhất), câu mở đầu là
`Q3:B`:

```text
độ sâu :  5   6    7     8      9     10     11     12     13     14     15   16
secret : 15  296 2216 10070  28279  57337  89102 106811  95226  57281  17633  854
                                            ▲ trung vị 12          p99 = 15  ▲ worst
```

- trung bình (uniform) **11,84 lần mua = 59,2 điểm**
- trung bình (phân phối **thực** của sampler) **11,83** — gần như y hệt

→ Bias ±14% của sampler **không** chuyển thành bias độ khó. Đây là dữ kiện
quan trọng cho #9: sửa sampler là vấn đề công bằng *thống kê*, không phải vấn
đề *độ khó*.

Khoảng adaptive `[8, 16]` cũng **chưa đóng**; 16 là kết quả của một chiến lược
cụ thể, không phải cây quyết định tối ưu.

### 5.3 Không cần xác định hết — chỉ cần đủ để đoán

Người chơi có thể dừng suy luận sớm rồi đoán. Với greedy minimax:

| Thu hẹp còn ≤ | worst case | trung bình | ghi chú |
| --- | --- | --- | --- |
| 8 ứng viên | 13 lần mua (65 điểm) | 9,43 (47,2 điểm) | |
| 4 ứng viên | 14 lần mua (70 điểm) | 10,22 (51,1 điểm) | |
| 2 ứng viên | 15 lần mua (75 điểm) | 11,03 (55,2 điểm) | |
| 1 ứng viên | 16 lần mua (80 điểm) | 11,84 (59,2 điểm) | **172 secret không bao giờ đạt được** |

### 5.4 Q4 không hạ được chi phí theo điểm

Q4 mua **2 nút trong một lần 5 điểm**, nhưng mỗi nút chỉ trả một boolean, nên
một lần mua Q4 chia được **tối đa 4 lớp**. Cùng giá 5 điểm, `Q3:B/E/H` chia
được **6 lớp**. Q4 vì thế bị trội theo lượng thông tin trên mỗi điểm, và không
thêm được gì khi đã có Q3 của cùng nút (mục 3d). Giá trị thật của Q4 nằm ở tác
dụng phụ: khi FULL nó **tự vẽ và khoá** các segment (`gameboard.cpp:391-436`)
— tức nó bán thao tác vẽ chứ không bán thông tin.

## 6. Ngân sách điểm — và vì sao non-adaptive là bất khả thi

100 điểm khởi đầu, 5 điểm mỗi lần mua, −1 điểm mỗi 60 giây
(`gameboard.cpp:99-103`), thua khi điểm `<= 0` (`:106`).

| Thời gian chơi | hao mòn | mua được tối đa | điểm đã tiêu |
| --- | --- | --- | --- |
| 3 phút | 3 | 19 | 95 |
| 6 phút | 6 | 18 | 90 |
| 10 phút | 10 | 17 | 85 |
| 15 phút | 15 | 16 | 80 |
| 20 phút | 20 | 15 | 75 |

Đối chiếu:

```text
ngân sách khả dụng ở mốc 15 phút : 16 lần mua  ────────────────┐
                                                               │
adaptive greedy, worst case      : 16 lần mua  ════════════════╡ vừa đúng sát
adaptive greedy, trung bình      : 11,84 lần mua ══════════╡    │
adaptive, lower bound            :  8 lần mua  ══════╡          │
                                                               │
tập clue CỐ ĐỊNH, lower bound    : 14 lần mua  ═══════════╡     │
tập clue CỐ ĐỊNH, upper bound    : 22 lần mua  ══════════════════════╪══> VƯỢT
```

→ **Decision input cho #9:** với luật điểm hiện tại, một người chơi mua theo
danh sách cố định **không thể** hoàn thành trong ngân sách (22 lần mua = 110
điểm > 100). Ván chỉ chơi được theo lối adaptive, và ngay cả greedy worst-case
cũng chạm sát trần ở mốc 15 phút. Nếu #9 đổi tốc độ hao mòn sang 30 giây/điểm
như Notes của map, trần này tụt xuống **13 lần mua ở mốc 15 phút** — thấp hơn
cả worst case của greedy adaptive.

## 7. Hành vi native KHÔNG được đóng băng thành canonical rule

Audit đầy đủ 43 hành vi kèm `file:line`, 20 mục cấm đóng băng, bảng đối chiếu
với Notes của map #1 và câu hỏi mở cho #9 nằm ở
[`native-behaviors.md`](native-behaviors.md). Ba mục ảnh hưởng trực tiếp tới
các con số trong tài liệu này:

**(a) Vẽ đúng mẫu là thắng ngay — không cần VERIFY.**
`updateSeg()` gọi `checkWinCondition()` (`gameboard.cpp:764`), nên đoán bằng
cách vẽ là **miễn phí và không giới hạn lượt**. Toàn bộ chính sách Wrong Guess
trở nên tuỳ chọn. Định lượng: thay vì phải xác định duy nhất (11,84 lần mua
trung bình), người chơi chỉ cần thu hẹp về ≤ 8 ứng viên (**9,43** lần mua) rồi
vẽ thử cả 8 với chi phí 0 — tiết kiệm khoảng **12 điểm mỗi ván**.

**(b) WebSocket không xác thực, broadcast đáp án.**
`HardwareServer` lắng nghe `QHostAddress::Any:8080` ở `NonSecureMode`
(`hardwareserver.cpp:10-16`), `sendToHardware()` gửi cho **mọi** client
(`:146-152`), và client mới kết nối được replay toàn bộ bàn cờ + dòng OLED cuối
(`:64-89`). Dòng OLED chính là đáp án clue (`"T: ODD (.)"`,
`"A has 3 demon(s)"`). Thêm nữa `m_secretCode` được in thẳng ra log
(`gameboard.cpp:483`). Không có ranh giới bí mật nào — trái thẳng yêu cầu
"state đối thủ được giữ kín" trong Notes của map #1.

**(c) Ván không có terminal state.**
Thua không xoá `m_secretCode` (`gameboard.cpp:106-116`, `:823-833`), nên sau
khi thua người chơi vẫn mua được clue và vẫn "thắng" được.

**Cảnh báo về việc port:** cả ba đều là *lifecycle coupling* của bản Qt
single-player. Bất kỳ con số fairness nào ở mục 5–6 chỉ đúng với mô hình
**thông tin**; native hiện tại còn rẻ hơn thế vì (a).

## 8. Công cụ và cách kiểm chứng

| File | Vai trò |
| --- | --- |
| `tools/analysis/digitcode.py` | Mô hình Puzzle, port 1-1 từ `gameboard.cpp`. Nguồn sự thật duy nhất. |
| `tools/analysis/analysis_generator.py` | Mục 1–2: đếm secret, phân phối sampler |
| `tools/analysis/analysis_signature.py` | Mục 3–4: partition, phụ thuộc, collision |
| `tools/analysis/analysis_cost.py` | Mục 5–6: chi phí clue, difficulty proxies |
| `tools/analysis/puzzle_fairness.py` | Driver, in báo cáo deterministic |
| `tools/analysis/test_analysis.py` | 23 test ghim mô hình chống regression |

Test không kiểm tra kết luận phân tích — chúng ghim **mô hình** vào những dữ
kiện suy được độc lập từ source: `MAX_LED` suy từ hình học phải khớp bảng
hardcode `getMaxLed`; `DIGIT_MAP` phải khớp ký hiệu bảy đoạn chuẩn; 9 nút cột
và 10 nút hàng mỗi bên phải phủ đúng 42 ô một lần; đếm bằng liệt kê phải khớp
brute-force 10⁶; và hai golden SHA-256 ghim toàn bộ danh sách secret cùng bảng
32 đáp án của chúng.

### Đối chiếu hypothesis từ audit trước

| # | Hypothesis | Kết quả | Nhãn |
| --- | --- | --- | --- |
| 1 | 465.120 secret hợp lệ | **ĐÚNG** (3 đường độc lập) | EXACT |
| 2 | 86 cặp trùng full Q1+Q2+Q3 signature | **ĐÚNG** (3 đường độc lập) | EXACT |
| 3 | Q4 suy từ Q3 nên không phá được collision đó | **ĐÚNG** (0 vi phạm / 465.120) | EXACT |
| 4 | Sampler có tỉ lệ max/min ≈ 9/7 | **ĐÚNG, và là đẳng thức exact** — sai lệch 0 | EXACT |

Không hypothesis nào bị bác bỏ. Ba phát hiện **ngoài** danh sách hypothesis:

1. Q2 chỉ mang **1 bit** mỗi câu (nhánh `'='` là code chết), và 7 câu Q2 chỉ
   sinh **98** bộ dấu chứ không phải 2⁷ = 128.
2. 19 câu đếm có **2** quan hệ tuyến tính nguyên thuỷ, không phải 1.
3. Cả 86 collision là **một họ đối xứng duy nhất** (đổi chỗ cột trái/phải với
   (4,6)/(5,7)) — nên chúng có thể bị phá bằng **một** clue phá đối xứng cột,
   nếu #9 muốn.

## 9. Ranh giới của kết quả

- Mục 2, 5.2 giả định `QRandomGenerator::global()->bounded(10)` là **đều và
  độc lập** giữa các lần bốc. Đó là hợp đồng tài liệu của Qt nhưng **không
  kiểm chứng được từ code trong repo**. Số đếm 465.120 và toàn bộ mục 3–4
  **không** phụ thuộc giả định này.
- Hai khoảng `[14, 22]` (fixed) và `[8, 16]` (adaptive) **chưa đóng**. Đóng
  được chúng cần vét cạn ở cỡ lớn hơn, vượt ngân sách thời gian của session
  này — đó là công việc còn lại, không phải kết luận.
- Audit hành vi native là **đọc code**, không chạy app; các exploit ở mục 7
  chưa có bằng chứng thực thi. Xem Phụ lục C của `native-behaviors.md`.
- Tài liệu này **không** chọn competitive policy. Mọi mục "Decision input" là
  đầu vào cho [#9](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/9).
