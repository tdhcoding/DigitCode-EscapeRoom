"""Thu hẹp hai khoảng mà #6 để hở ở `findings.md` mục 9.

* tập clue **CỐ ĐỊNH** (non-adaptive): #6 để `[14, 22]`
* chiến lược **ADAPTIVE**: #6 để `[8, 16]`

Module này chỉ dựng dữ liệu nền và các phép nguyên thuỷ nhanh; hai script
`bounds_fixed.py` và `bounds_adaptive.py` dùng lại nó.

Chỉ dùng standard library (máy chạy không có numpy), giống mọi script khác
trong `tools/analysis/`. Deterministic: không có RNG ở bất kỳ đâu.

Biểu diễn:
  * `cols[j]` là một `bytes` dài N, đáp án của clue thứ `j` cho từng secret.
    Nhờ vậy `zip(*cols_selected)` chạy hoàn toàn ở tầng C.
  * `class_id[i]` là chỉ số lớp (signature đầy đủ 32 clue) của secret `i`.
    Hai secret cùng lớp là một cặp collision — không clue nào tách được.
"""

import array
import math

import digitcode as dc


# --- Dữ liệu nền --------------------------------------------------------

def build():
    """Dựng (secrets, qids, cols, class_id, n_classes).

    `qids` là 32 clue mua được: 6 Q1 + 7 Q2 + 19 Q3. Q4 bị loại vì #6 đã
    chứng minh nó suy hoàn toàn từ Q3 (0 vi phạm / 465.120).
    """
    secrets = list(dc.iter_valid_secrets())
    qids = list(dc.BASE_QUESTION_IDS)
    cols = []
    for q in qids:
        vals = [dc.answer(s, q) for s in secrets]
        lo = min(vals)
        # Q2 trả -1/1 -> dời về 0/2. Dời không đổi partition.
        cols.append(bytes(v - lo for v in vals))

    class_id = array.array("i", bytes(4 * len(secrets)))
    seen = {}
    for i, sig in enumerate(zip(*cols)):
        cid = seen.get(sig)
        if cid is None:
            cid = len(seen)
            seen[sig] = cid
        class_id[i] = cid
    return secrets, qids, cols, class_id, len(seen)


def domain_sizes(cols):
    """Số đáp án THỰC SỰ đạt được của từng clue trên toàn bộ pool."""
    return [len(set(c)) for c in cols]


# --- Phép nguyên thuỷ ---------------------------------------------------

def n_blocks(cols, subset):
    """Số lớp mà `subset` chia được. Chạy ở tầng C."""
    if not subset:
        return 1
    return len(set(zip(*[cols[j] for j in subset])))


def separates(cols, subset, n_classes):
    """True nếu `subset` tách được đúng bằng toàn bộ 32 clue.

    Partition của một tập con luôn THÔ HƠN partition của toàn bộ clue, nên
    bằng nhau về số lớp thì hai partition trùng nhau. Không cần so từng lớp.
    """
    return n_blocks(cols, subset) == n_classes


def violated_masks(cols, class_id, subset, limit=64):
    """Tìm các cặp secret mà `subset` chưa tách được.

    Trả về list bitmask trên 32 clue: bit `j` bật nếu clue `j` tách được cặp
    đó. Mỗi mask là một ràng buộc cho bài toán hitting set.
    """
    if not subset:
        raise ValueError("subset phải khác rỗng")
    keys = zip(*[cols[j] for j in subset])
    first = {}
    out = []
    for i, k in enumerate(keys):
        cid = class_id[i]
        prev = first.get(k)
        if prev is None:
            first[k] = (i, cid)
            continue
        pi, pcid = prev
        if pcid == cid:
            continue
        m = 0
        for j, c in enumerate(cols):
            if c[i] != c[pi]:
                m |= 1 << j
        out.append(m)
        if len(out) >= limit:
            break
    return out


def essential_clues(cols, n_classes):
    """Clue mà bỏ đi là mất thông tin — mọi tập hợp lệ MUST chứa chúng."""
    allj = list(range(len(cols)))
    ess = []
    for j in allj:
        rest = [k for k in allj if k != j]
        if n_blocks(cols, rest) < n_classes:
            ess.append(j)
    return ess


# --- Chặn đếm ------------------------------------------------------------

def count_bound(n_targets, branchings):
    """Số clue tối thiểu để một chiến lược ADAPTIVE tách `n_targets` lớp.

    Một clue chia được tối đa `b` nhánh với `b` là số đáp án đạt được của nó,
    nên `d` clue cho tối đa tích của `d` branching lớn nhất còn lại. Đây là
    chặn dưới ĐÚNG (sound): nó chỉ dùng trần nhánh, không giả định gì về
    chiến lược.
    """
    if n_targets <= 1:
        return 0
    prod = 1
    for d, b in enumerate(sorted(branchings, reverse=True), start=1):
        prod *= b
        if prod >= n_targets:
            return d
    return math.inf


# --- Hitting set chính xác ----------------------------------------------

def _popcount(x):
    return bin(x).count("1")


def greedy_lb(constraints):
    """Chặn dưới: số ràng buộc đôi một rời nhau (chọn tham lam theo cỡ)."""
    used = 0
    c = 0
    for m in sorted(constraints, key=_popcount):
        if not (m & used):
            used |= m
            c += 1
    return c


def min_hitting_set(constraints, upper_bound, node_budget=4_000_000):
    """Hitting set nhỏ nhất trên tập bit, branch & bound chính xác.

    Trả `(size, mask, proved)`. `proved=False` nghĩa là hết node budget —
    khi đó `size` vẫn là một CHẶN DƯỚI hợp lệ chưa chứng minh đạt được.
    """
    cons = list(set(constraints))
    if not cons:
        return 0, 0, True

    best = [upper_bound, None]
    nodes = [0]
    exhausted = [False]

    def rec(remaining, count, chosen):
        if exhausted[0]:
            return
        nodes[0] += 1
        if nodes[0] > node_budget:
            exhausted[0] = True
            return
        if not remaining:
            if count < best[0]:
                best[0] = count
                best[1] = chosen
            return
        if count + greedy_lb(remaining) >= best[0]:
            return
        pivot = min(remaining, key=_popcount)
        bit = 0
        m = pivot
        while m:
            if m & 1:
                nxt = [c for c in remaining if not (c >> bit) & 1]
                rec(nxt, count + 1, chosen | (1 << bit))
            m >>= 1
            bit += 1

    rec(cons, 0, 0)
    if best[1] is None:
        return greedy_lb(cons), 0, False
    return best[0], best[1], not exhausted[0]


def mask_to_list(mask):
    out = []
    j = 0
    while mask:
        if mask & 1:
            out.append(j)
        mask >>= 1
        j += 1
    return out
