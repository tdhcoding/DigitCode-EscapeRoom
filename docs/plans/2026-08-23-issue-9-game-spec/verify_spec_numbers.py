#!/usr/bin/env python3
"""Kiểm chứng độc lập các con số mà game-spec.md dựa vào.

Chỉ dùng thư viện chuẩn. Không mạng, không build Qt. Chạy:

    python3 -u verify_spec_numbers.py

Script này KHÔNG lặp lại phân tích của ticket #6 (chi phí clue, cây adaptive).
Nó chỉ ghim những invariant mà chính spec tuyên bố ở mục 13, cộng số học ngân
sách ở mục 5. Nguồn của mọi hằng số cấu trúc là backend/gameboard.cpp:5-27,
375-388, 512-556 trên branch feat/puzzle-fairness-characterization.
"""

from itertools import product

# --- Hằng số port từ backend/gameboard.cpp -----------------------------------

SEG = "abcdefg"  # :5-7 — thứ tự chỉ số 0..6
DIGIT_MAP = {    # :22-27
    "0": (1, 1, 1, 1, 1, 1, 0), "1": (0, 1, 1, 0, 0, 0, 0),
    "2": (1, 1, 0, 1, 1, 0, 1), "3": (1, 1, 1, 1, 0, 0, 1),
    "4": (0, 1, 1, 0, 0, 1, 1), "5": (1, 0, 1, 1, 0, 1, 1),
    "6": (1, 0, 1, 1, 1, 1, 1), "7": (1, 1, 1, 0, 0, 0, 0),
    "8": (1, 1, 1, 1, 1, 1, 1), "9": (1, 1, 1, 1, 0, 1, 1),
}

# 19 bộ đếm: id -> (các LED index, các segment index)   :512-556
COUNTERS = {}
for k, (leds, segs) in enumerate([((0, 3), "fe"), ((0, 3), "agd"), ((0, 3), "bc"),
                                  ((1, 4), "fe"), ((1, 4), "agd"), ((1, 4), "bc"),
                                  ((2, 5), "fe"), ((2, 5), "agd"), ((2, 5), "bc")]):
    COUNTERS["ABCDEFGHI"[k]] = (leds, tuple(SEG.index(c) for c in segs))
for k, (leds, segs) in enumerate([((0, 1, 2), "a"), ((0, 1, 2), "fb"), ((0, 1, 2), "g"),
                                  ((0, 1, 2), "ec"), ((0, 1, 2), "d"),
                                  ((3, 4, 5), "a"), ((3, 4, 5), "fb"), ((3, 4, 5), "g"),
                                  ((3, 4, 5), "ec"), ((3, 4, 5), "d")]):
    COUNTERS["JKLMNOPQRS"[k]] = (leds, tuple(SEG.index(c) for c in segs))

# 7 cặp LED kề nhau — R-C-04 / generator :478-479
ADJACENT = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]

fails = []


def check(label, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {got}" + ("" if ok else f"  (kỳ vọng {want})"))
    if not ok:
        fails.append(label)


def valid(code):
    """R-P-04: mỗi chữ số <= 2 lần; hai LED kề nhau theo hàng/cột khác nhau."""
    if any(code.count(c) > 2 for c in set(code)):
        return False
    return all(code[i] != code[j] for i, j in ADJACENT)


print("Liệt kê toàn bộ 10^6 mã...", flush=True)
codes = ["".join(t) for t in product("0123456789", repeat=6)]
valid_codes = [c for c in codes if valid(c)]

# 1. Kích thước không gian đề — R-P-05
check("Số mã hợp lệ (R-P-05)", len(valid_codes), 465_120)

# 2. Hai phân hoạch 42 ô — R-C-08
col_cells, row_cells = [], []
for cid in "ABCDEFGHI":
    leds, segs = COUNTERS[cid]
    col_cells += [(l, s) for l in leds for s in segs]
for cid in "JKLMNOPQRS":
    leds, segs = COUNTERS[cid]
    row_cells += [(l, s) for l in leds for s in segs]
check("Ô do A..I phủ (R-C-08)", len(col_cells), 42)
check("A..I không trùng ô (R-C-08)", len(set(col_cells)), 42)
check("Ô do J..S phủ (R-C-08)", len(row_cells), 42)
check("J..S không trùng ô (R-C-08)", len(set(row_cells)), 42)

# 3. Miền đáp án của 19 bộ đếm — R-C-07
DOMAIN = {**{c: 4 for c in "ACDFGI"}, **{c: 6 for c in "BEH"},
          **{c: 3 for c in "JLNOQS"}, **{c: 6 for c in "KMPR"}}
bad_domain = [cid for cid, (leds, segs) in COUNTERS.items()
              if len(leds) * len(segs) != DOMAIN[cid]]
check("Miền đáp án 19 bộ đếm khớp R-C-07", bad_domain, [])


def signature(code):
    """Toàn bộ thông tin mua được: 6 Q1 + 7 Q2 + 19 Q3."""
    st = [DIGIT_MAP[ch] for ch in code]
    q1 = tuple(int(ch) % 2 for ch in code)
    q2 = tuple(1 if code[i] > code[j] else -1 for i, j in ADJACENT)
    q3 = tuple(sum(st[l][s] for l in COUNTERS[c][0] for s in COUNTERS[c][1])
               for c in "ABCDEFGHIJKLMNOPQRS")
    return q1 + q2 + q3


# 4. Q2 không bao giờ trả EQUAL — R-C-06
check("Mã hợp lệ làm Q2 trả EQUAL (R-C-06)",
      sum(1 for c in valid_codes if any(c[i] == c[j] for i, j in ADJACENT)), 0)

print("Tính signature cho 465.120 mã...", flush=True)
groups = {}
for c in valid_codes:
    groups.setdefault(signature(c), []).append(c)

# 5. Collision — R-P-11
sizes = {}
for g in groups.values():
    sizes[len(g)] = sizes.get(len(g), 0) + 1
pairs = [g for g in groups.values() if len(g) == 2]
check("Số lớp signature", len(groups), 465_034)
check("Lớp có cỡ > 2", [n for n in sizes if n > 2], [])
check("Số cặp collision (R-P-11)", len(pairs), 86)
check("Số mã dính collision (R-P-10)", 2 * len(pairs), 172)


def swap_columns(code):
    """Đổi chỗ cột trái và cột phải: vị trí 0<->2 và 3<->5."""
    return code[2] + code[1] + code[0] + code[5] + code[4] + code[3]


check("Cả 86 cặp đều là họ đổi cột (R-P-11)",
      sum(1 for a, b in pairs if swap_columns(a) == b), 86)
check("Mọi cặp dùng chữ số (4,6) và (5,7) (R-P-11)",
      sum(1 for a, b in pairs
          if {a[0], a[2]} == {"4", "6"} and {a[3], a[5]} == {"5", "7"}
          or {a[0], a[2]} == {"5", "7"} and {a[3], a[5]} == {"4", "6"}), 86)
check("Counterexample 406517 / 604715 (R-P-11)",
      signature("406517") == signature("604715"), True)

# 6. Pool Ranked — R-P-09 / R-P-10
collided = {c for g in pairs for c in g}
check("Pool Practice (R-P-09)", len(valid_codes), 465_120)
check("Pool Ranked (R-P-10)", len(valid_codes) - len(collided), 464_948)


# 7. Ngân sách điểm — mục 5 của spec
def ceiling(start, price, decay_seconds, deadline_seconds):
    """Số lần mua tối đa khi chơi tới deadline, Score sàn 0 (R-S-07/08)."""
    decay = deadline_seconds // decay_seconds
    return (start - decay) // price


check("Trần lần mua, hao mòn 60s (R-S-05, R-S-06)", ceiling(100, 5, 60, 900), 17)
check("Score còn lại sau 17 lần mua ở 15:00", 100 - 900 // 60 - 17 * 5, 0)
check("Trần lần mua nếu hao mòn 30s (R-S-11)", ceiling(100, 5, 30, 900), 14)

# R-S-12: cùng công thức nhưng dưới luật native "Score <= 0 là thua" — phải
# chừa lại >= 1 Score — cho đúng hai con số 16 / 13 trong bảng của ticket #6.
def ceiling_native(start, price, decay_seconds, deadline_seconds):
    return (start - deadline_seconds // decay_seconds - 1) // price


check("Trần dưới luật native, 60s (R-S-12)", ceiling_native(100, 5, 60, 900), 16)
check("Trần dưới luật native, 30s (R-S-12)", ceiling_native(100, 5, 30, 900), 13)

# 8. Không thể mua hết Clue — R-S-10
check("Số Clue trong catalogue (R-C-01)", 6 + 7 + 19, 32)
check("Giá mua hết catalogue vượt Score khởi đầu (R-S-10)", 32 * 5 > 100, True)

print()
if fails:
    print(f"{len(fails)} KIỂM TRA THẤT BẠI: {', '.join(fails)}")
    raise SystemExit(1)
print("Tất cả kiểm tra PASS.")
