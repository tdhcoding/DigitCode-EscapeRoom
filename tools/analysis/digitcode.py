"""Mô hình Puzzle của native engine, port 1-1 từ `backend/gameboard.cpp`.

Module này là nguồn sự thật duy nhất cho mọi script phân tích trong
`tools/analysis/`. Nó KHÔNG phân tích gì cả — chỉ mô tả:

* luật sinh secret của rejection sampler (`gameboard.cpp:471-482`),
* bảng `DIGIT_MAP` (`gameboard.cpp:22-27`),
* bốn loại clue Q1..Q4 và partition mà mỗi clue tạo ra.

Chỉ dùng standard library. Deterministic: không có RNG.
"""

from fractions import Fraction

# --- Hình học bảng ------------------------------------------------------
#
# 6 LED bảy đoạn xếp 2 hàng x 3 cột.  Chỉ số LED trong C++:
#
#     LED 0 (T)   LED 1 (U)   LED 2 (V)      <- hàng trên
#     LED 3 (W)   LED 4 (X)   LED 5 (Y)      <- hàng dưới
#
# Segment lưu theo thứ tự [a, b, c, d, e, f, g] (SEG_MAP, gameboard.cpp:5-7).

SEGMENT_ORDER = ("a", "b", "c", "d", "e", "f", "g")
SEG_INDEX = {name: i for i, name in enumerate(SEGMENT_ORDER)}

# gameboard.cpp:22-27 — chép nguyên, thứ tự [a,b,c,d,e,f,g].
DIGIT_MAP = {
    0: (1, 1, 1, 1, 1, 1, 0),
    1: (0, 1, 1, 0, 0, 0, 0),
    2: (1, 1, 0, 1, 1, 0, 1),
    3: (1, 1, 1, 1, 0, 0, 1),
    4: (0, 1, 1, 0, 0, 1, 1),
    5: (1, 0, 1, 1, 0, 1, 1),
    6: (1, 0, 1, 1, 1, 1, 1),
    7: (1, 1, 1, 0, 0, 0, 0),
    8: (1, 1, 1, 1, 1, 1, 1),
    9: (1, 1, 1, 1, 0, 1, 1),
}

LED_LABELS = ("T", "U", "V", "W", "X", "Y")  # LED 0..5

# COL_GROUPS / ROW_GROUPS, gameboard.cpp:8-13.
COL_GROUPS = {0: ("f", "e"), 1: ("a", "g", "d"), 2: ("b", "c")}
ROW_GROUPS = {0: ("a",), 1: ("f", "b"), 2: ("g",), 3: ("e", "c"), 4: ("d",)}

# Nút Q3/Q4 cột A..I: COL_LED_MAP + COL_IDX_MAP, gameboard.cpp:14-21.
# A,B,C -> cặp LED (0,3); D,E,F -> (1,4); G,H,I -> (2,5).
COL_NODES = ("A", "B", "C", "D", "E", "F", "G", "H", "I")
# Nút Q3/Q4 hàng J..S: gameboard.cpp:406-419.
# J..N -> LED (0,1,2) với rowIdx 0..4; O..S -> LED (3,4,5) với rowIdx 0..4.
ROW_NODES = ("J", "K", "L", "M", "N", "O", "P", "Q", "R", "S")
COUNT_NODES = COL_NODES + ROW_NODES

# Cặp LED liền kề hợp lệ cho Q2 (isAdjacent, gameboard.cpp:365-373) đã chuẩn
# hoá alphabetical như processQ2 làm (gameboard.cpp:299).  Thứ tự ở đây khớp
# thứ tự tra cứu trong cmpValueForPair (gameboard.cpp:687-697).
Q2_PAIRS = ("T-U", "U-V", "W-X", "X-Y", "T-W", "U-X", "V-Y")
_Q2_POSITIONS = {
    "T-U": (0, 1),
    "U-V": (1, 2),
    "W-X": (3, 4),
    "X-Y": (4, 5),
    "T-W": (0, 3),
    "U-X": (1, 4),
    "V-Y": (2, 5),
}

# getMaxLed, gameboard.cpp:375-388 — chép nguyên để đối chiếu với giá trị suy
# ra từ hình học (xem `_self_check`).
MAX_LED_CPP = {
    "A": 4, "D": 4, "G": 4,
    "B": 6, "E": 6, "H": 6,
    "C": 4, "F": 4, "I": 4,
    "J": 3, "O": 3,
    "K": 6, "P": 6,
    "L": 3, "Q": 3,
    "M": 6, "R": 6,
    "N": 3, "S": 3,
}


def _node_cells(node):
    """Trả về list (led_index, segment_index) mà một nút Q3/Q4 đếm."""
    if node in COL_NODES:
        block = COL_NODES.index(node) // 3      # 0 -> LED (0,3), 1 -> (1,4), 2 -> (2,5)
        col_idx = COL_NODES.index(node) % 3     # COL_IDX_MAP
        leds = (block, block + 3)
        segs = COL_GROUPS[col_idx]
    elif node in ROW_NODES:
        pos = ROW_NODES.index(node)
        is_row2 = pos >= 5
        row_idx = pos - 5 if is_row2 else pos
        offset = 3 if is_row2 else 0
        leds = (offset, offset + 1, offset + 2)
        segs = ROW_GROUPS[row_idx]
    else:
        raise KeyError(node)
    return [(led, SEG_INDEX[s]) for led in leds for s in segs]


NODE_CELLS = {node: _node_cells(node) for node in COUNT_NODES}
MAX_LED = {node: len(NODE_CELLS[node]) for node in COUNT_NODES}


# --- Rejection sampler sinh secret --------------------------------------
#
# gameboard.cpp:471-482:
#
#     while (code.length() < 6) {
#         int currentLength = code.length();
#         QString ch = QString::number(bounded(10));
#         if (code.count(ch) >= 2) continue;                                   // C1
#         if (currentLength % 3 != 0 && code.at(currentLength-1) == ch) continue;  // C2
#         if (currentLength >= 3 && code.at(currentLength-3) == ch) continue;      // C3
#         code += ch;
#     }
#
# C1: mỗi chữ số xuất hiện tối đa 2 lần trong cả mã.
# C2: tại i thuộc {1,2,4,5}, code[i] != code[i-1]  (liền kề ngang).
# C3: tại i thuộc {3,4,5},   code[i] != code[i-3]  (liền kề dọc).
#
# Mỗi vị trí được bốc lại độc lập cho tới khi hợp lệ, nên chữ số tại vị trí i
# phân bố ĐỀU trên tập cho phép A_i(prefix), và
#     P(code) = prod_i 1 / |A_i(prefix_i)|
# tức sampler KHÔNG uniform trên tập secret hợp lệ.

SECRET_LENGTH = 6


def allowed_digits(prefix):
    """Tập chữ số mà sampler chấp nhận ở vị trí `len(prefix)`."""
    i = len(prefix)
    out = []
    for d in range(10):
        if prefix.count(d) >= 2:
            continue
        if i % 3 != 0 and prefix[i - 1] == d:
            continue
        if i >= 3 and prefix[i - 3] == d:
            continue
        out.append(d)
    return out


def is_valid_secret(code):
    """True nếu `code` (tuple 6 int) thoả cả ba ràng buộc C1/C2/C3."""
    if len(code) != SECRET_LENGTH:
        return False
    for d in set(code):
        if code.count(d) > 2:
            return False
    for i in (1, 2, 4, 5):
        if code[i] == code[i - 1]:
            return False
    for i in (3, 4, 5):
        if code[i] == code[i - 3]:
            return False
    return True


def iter_valid_secrets():
    """Sinh mọi secret hợp lệ theo thứ tự từ điển, bằng chính luật của sampler."""
    def walk(prefix):
        if len(prefix) == SECRET_LENGTH:
            yield prefix
            return
        for d in allowed_digits(prefix):
            for s in walk(prefix + (d,)):
                yield s
    return walk(())


def secret_probability(code):
    """Xác suất chính xác (Fraction) sampler sinh ra `code`."""
    p = Fraction(1)
    for i in range(SECRET_LENGTH):
        p *= Fraction(1, len(allowed_digits(code[:i])))
    return p


# --- Clue ---------------------------------------------------------------

def segments_of(code):
    """Ma trận 6x7 trạng thái segment của secret (DIGIT_MAP đã tra sẵn)."""
    return [DIGIT_MAP[d] for d in code]


def q1(code, label):
    """Q1 — chẵn/lẻ của một LED. 1 = ODD, 0 = EVEN (gameboard.cpp:491-495)."""
    return code[LED_LABELS.index(label)] % 2


def q2(code, pair):
    """Q2 — so sánh hai LED liền kề: 1 = '>', -1 = '<', 0 = '=' (dead branch).

    Trả 0 là bất khả thi với secret hợp lệ: C2/C3 cấm hai LED liền kề bằng nhau.
    """
    a, b = _Q2_POSITIONS[pair]
    x, y = code[a], code[b]
    return 1 if x > y else (-1 if x < y else 0)


def q3(code, node):
    """Q3 — số segment đang sáng trong nhóm hàng/cột (gameboard.cpp:511-556)."""
    segs = segments_of(code)
    return sum(1 for led, s in NODE_CELLS[node] if segs[led][s] > 0)


def q4(code, node):
    """Q4 — nhóm có FULL không. Suy trực tiếp từ Q3 (gameboard.cpp:632)."""
    return 1 if q3(code, node) == MAX_LED[node] else 0


# --- Sổ đăng ký câu hỏi -------------------------------------------------
#
# Một "question" là một phép đo nguyên tử người chơi có thể mua.  Q4 mua theo
# cặp nút (một lần 5 điểm cho hai nút) nhưng vẫn là hai phép đo nguyên tử.

Q1_IDS = tuple("Q1:%s" % l for l in LED_LABELS)
Q2_IDS = tuple("Q2:%s" % p for p in Q2_PAIRS)
Q3_IDS = tuple("Q3:%s" % n for n in COUNT_NODES)
Q4_IDS = tuple("Q4:%s" % n for n in COUNT_NODES)

ALL_QUESTION_IDS = Q1_IDS + Q2_IDS + Q3_IDS + Q4_IDS
BASE_QUESTION_IDS = Q1_IDS + Q2_IDS + Q3_IDS  # Q4 suy được từ Q3 nên không nằm ở đây

CLUE_COST_POINTS = 5  # processQ1/2/3/4 đều trừ đúng 5 (gameboard.cpp:266,311,341,620)


def answer(code, qid):
    kind, arg = qid.split(":", 1)
    if kind == "Q1":
        return q1(code, arg)
    if kind == "Q2":
        return q2(code, arg)
    if kind == "Q3":
        return q3(code, arg)
    if kind == "Q4":
        return q4(code, arg)
    raise KeyError(qid)


def signature(code, qids):
    return tuple(answer(code, q) for q in qids)


def answer_table(secrets, qids):
    """Bảng đáp án dạng list-of-tuples, cùng thứ tự với `secrets`."""
    return [signature(code, qids) for code in secrets]


# --- Self-check ---------------------------------------------------------

def _self_check():
    """Kiểm tra mô hình khớp với các hằng số hardcode trong C++."""
    assert MAX_LED == MAX_LED_CPP, (MAX_LED, MAX_LED_CPP)
    # Mỗi ô (led, segment) phải được đúng một nút cột và đúng một nút hàng phủ.
    from collections import Counter
    col_cover = Counter()
    row_cover = Counter()
    for node in COL_NODES:
        col_cover.update(NODE_CELLS[node])
    for node in ROW_NODES:
        row_cover.update(NODE_CELLS[node])
    assert len(col_cover) == 42 and set(col_cover.values()) == {1}, col_cover
    assert len(row_cover) == 42 and set(row_cover.values()) == {1}, row_cover
    # Chuẩn hoá cặp Q2 phải alphabetical như processQ2 làm.
    for pair in Q2_PAIRS:
        a, b = pair.split("-")
        assert a < b, pair
    return True


_self_check()
