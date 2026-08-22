"""U2 — Partition, quan hệ phụ thuộc giữa clue, và collision của Puzzle.

Module này KHÔNG mô tả luật chơi; nó chỉ *đo* mô hình trong `digitcode.py`
(nguồn sự thật duy nhất, port 1-1 từ `backend/gameboard.cpp`).  Mọi con số ở
đây suy ra bằng vét cạn trên toàn bộ tập secret hợp lệ — không lấy mẫu, không
RNG, nên tái lập bit-for-bit.

Nội dung:

1. Partition của từng câu hỏi đơn (32 câu Q1+Q2+Q3 và 19 câu Q4): số lớp, kích
   thước lớp, entropy dưới phân phối uniform và dưới phân phối thực của
   rejection sampler.
2. Nhánh chết Q2 '=' (giá trị 0) — xác nhận không secret hợp lệ nào chạm tới.
3. Quan hệ phụ thuộc: Q4 là hàm của Q3; hạng chính xác của hệ 19 câu đếm; câu
   nào dư thừa khi đã có 31 câu còn lại.
4. Chữ số không phân biệt được bằng đếm segment.
5. Collision dưới toàn bộ clue + counterexample + đặc trưng hoá cấu trúc.
6. Sức mạnh của từng họ câu hỏi.

Chỉ standard library.  Python 3.9 compatible.

Chạy:  python3 tools/analysis/analysis_signature.py
"""

import math
import os
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from operator import itemgetter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import digitcode as dc  # noqa: E402


# ---------------------------------------------------------------------------
# Tiện ích chung
# ---------------------------------------------------------------------------

def _frac_str(fr):
    """Fraction -> chuỗi 'num/den' (JSON-serialisable, không mất chính xác)."""
    return "%d/%d" % (fr.numerator, fr.denominator)


def _entropy_from_counts(counts, total):
    """Entropy (bit) của phân phối uniform trên `total` phần tử, gộp theo lớp.

    Trả về float.  Uniform nên tỉ lệ là hữu tỉ chính xác; chỉ phép log là float.
    """
    h = 0.0
    for n in counts:
        if n:
            p = n / total
            h -= p * math.log2(p)
    return h


def _entropy_from_masses(masses):
    """Entropy (bit) từ danh sách khối lượng xác suất Fraction chính xác.

    Khối lượng lớp tính bằng Fraction (chính xác tuyệt đối); chỉ bước lấy log
    mới chuyển sang float.  Sai số vì thế chỉ là sai số làm tròn của log2, cỡ
    1e-15 bit — nêu rõ trong báo cáo.
    """
    h = 0.0
    for m in masses:
        if m:
            p = float(m)
            h -= p * math.log2(p)
    return h


def _denominators(secrets):
    """Mẫu số D của xác suất sampler cho từng secret: P(code) = 1/D.

    `dc.secret_probability` trả Fraction bằng tích 1/|A_i(prefix)|.  Vì mọi
    |A_i| là số nguyên nên P luôn có dạng 1/D với D = prod |A_i|.  Ở đây ta
    tính D trực tiếp và memo hoá theo prefix để khỏi gọi `allowed_digits`
    465120*6 lần.
    """
    cache = {}
    out = []
    for code in secrets:
        den = 1
        for i in range(dc.SECRET_LENGTH):
            pre = code[:i]
            k = cache.get(pre)
            if k is None:
                k = len(dc.allowed_digits(pre))
                cache[pre] = k
            den *= k
        out.append(den)
    return out


def _check_denominators(secrets, dens, stride=4001):
    """Đối chiếu D với `dc.secret_probability` trên một mẫu tất định."""
    checked = 0
    for i in range(0, len(secrets), stride):
        assert dc.secret_probability(secrets[i]) == Fraction(1, dens[i]), secrets[i]
        checked += 1
    for i in range(min(50, len(secrets))):
        assert dc.secret_probability(secrets[i]) == Fraction(1, dens[i]), secrets[i]
        checked += 1
    return checked


def _distinct(table, idx):
    """Số lớp của partition sinh bởi tập cột `idx` (tuple chỉ số) trên `table`."""
    if not idx:
        return 1
    if len(idx) == 1:
        get = itemgetter(idx[0])
        return len(set(map(get, table)))
    return len(set(map(itemgetter(*idx), table)))


# ---------------------------------------------------------------------------
# Đại số tuyến tính chính xác trên Q (Fraction)
# ---------------------------------------------------------------------------

class _Echelon:
    """Cơ sở dạng bậc thang của một không gian con của Q^n, dùng Fraction."""

    def __init__(self, n):
        self.n = n
        self.piv = {}   # cột trụ -> hàng

    def add(self, vec):
        w = [Fraction(x) for x in vec]
        for c in range(self.n):
            if w[c] == 0:
                continue
            row = self.piv.get(c)
            if row is None:
                self.piv[c] = w
                return True
            f = w[c] / row[c]
            w = [a - f * b for a, b in zip(w, row)]
        return False

    def rank(self):
        return len(self.piv)

    def nullspace(self):
        """Cơ sở của {x : basis . x = 0} (null space bên phải), dạng Fraction."""
        cols = sorted(self.piv)
        rows = [self.piv[c][:] for c in cols]
        for i in range(len(cols) - 1, -1, -1):
            pv = rows[i][cols[i]]
            rows[i] = [x / pv for x in rows[i]]
            for k in range(i):
                f = rows[k][cols[i]]
                if f:
                    rows[k] = [a - f * b for a, b in zip(rows[k], rows[i])]
        free = [c for c in range(self.n) if c not in self.piv]
        out = []
        for f in free:
            v = [Fraction(0)] * self.n
            v[f] = Fraction(1)
            for r, c in enumerate(cols):
                v[c] = -rows[r][f]
            out.append(v)
        return out


def _integerize(vec):
    """Chuẩn hoá vector Fraction thành vector số nguyên nguyên tố cùng nhau."""
    den = 1
    for x in vec:
        den = den * x.denominator // math.gcd(den, x.denominator)
    iv = [int(x * den) for x in vec]
    g = 0
    for x in iv:
        g = math.gcd(g, abs(x))
    if g:
        iv = [x // g for x in iv]
    # Chuẩn hoá dấu: hệ số khác 0 đầu tiên là dương (để output tất định).
    for x in iv:
        if x:
            if x < 0:
                iv = [-y for y in iv]
            break
    return iv


def _exact_rank(sample_vectors, all_vectors, dim):
    """Hạng chính xác của `all_vectors` trong Q^dim, có chứng cứ vét cạn.

    Chiến lược: dựng cơ sở từ một mẫu tất định `sample_vectors`, lấy null space
    N của cơ sở đó, rồi kiểm tra TOÀN BỘ `all_vectors` đều trực giao với N.
    Nếu đúng thì span(all) nằm trong N^perp (số chiều = rank cơ sở) mà cơ sở đã
    sinh trọn N^perp, nên hạng đúng bằng hạng của cơ sở.  Đây là chứng minh đầy
    đủ, không phải ước lượng.
    """
    ech = _Echelon(dim)
    for v in sample_vectors:
        ech.add(v)
        if ech.rank() == dim:
            break
    null = [_integerize(v) for v in ech.nullspace()]
    violations = 0
    for v in all_vectors:
        for n in null:
            if sum(a * b for a, b in zip(v, n)) != 0:
                violations += 1
                break
    return ech.rank(), null, violations


# ---------------------------------------------------------------------------
# Đặc trưng của chữ số dưới Q3/Q4
# ---------------------------------------------------------------------------

def _digit_col_vector(d):
    """(left = f+e, mid = a+g+d, right = b+c) — suy từ dc.COL_GROUPS."""
    seg = dc.DIGIT_MAP[d]
    return tuple(sum(seg[dc.SEG_INDEX[s]] for s in dc.COL_GROUPS[i]) for i in range(3))


def _digit_row_vector(d):
    """(a, f+b, g, e+c, d) — suy từ dc.ROW_GROUPS."""
    seg = dc.DIGIT_MAP[d]
    return tuple(sum(seg[dc.SEG_INDEX[s]] for s in dc.ROW_GROUPS[i]) for i in range(5))


def _q2_edges():
    """Bảy cặp LED của Q2 dưới dạng cặp chỉ số, suy từ dc.Q2_PAIRS."""
    out = []
    for pair in dc.Q2_PAIRS:
        a, b = pair.split("-")
        out.append((dc.LED_LABELS.index(a), dc.LED_LABELS.index(b)))
    return out


def _count_acyclic_orientations(edges, n_nodes):
    """Số hướng hoá phi chu trình của đồ thị — vét cạn 2^|E|.

    Một bộ dấu Q2 khả thi <=> hướng hoá phi chu trình: quan hệ '>' phải là một
    thứ tự bộ phận nên không được có chu trình có hướng; ngược lại mọi hướng hoá
    phi chu trình đều hiện thực hoá được bằng một linear extension gán 6 chữ số
    ĐÔI MỘT KHÁC NHAU (thoả luôn C1/C2/C3).
    """
    total = 0
    for mask in range(1 << len(edges)):
        adj = [[] for _ in range(n_nodes)]
        for k, (a, b) in enumerate(edges):
            if mask >> k & 1:
                adj[a].append(b)
            else:
                adj[b].append(a)
        color = [0] * n_nodes
        acyclic = True
        for start in range(n_nodes):
            if color[start]:
                continue
            stack = [(start, iter(adj[start]))]
            color[start] = 1
            while stack:
                u, it = stack[-1]
                nxt = next(it, None)
                if nxt is None:
                    color[u] = 2
                    stack.pop()
                    continue
                if color[nxt] == 1:
                    acyclic = False
                    break
                if color[nxt] == 0:
                    color[nxt] = 1
                    stack.append((nxt, iter(adj[nxt])))
            if not acyclic:
                break
        if acyclic:
            total += 1
    return total


def _column_swap(code):
    """Đổi chỗ cột trái và cột phải của bảng 2x3 (vị trí 0<->2 và 3<->5)."""
    return (code[2], code[1], code[0], code[5], code[4], code[3])


def _classify_pair(a, b):
    """Đặc trưng hoá phép biến đổi đưa secret `a` thành `b`."""
    diff = tuple(p for p in range(dc.SECRET_LENGTH) if a[p] != b[p])
    info = {
        "diff_positions": list(diff),
        "n_diff": len(diff),
        "same_multiset": sorted(a) == sorted(b),
        "is_column_swap": _column_swap(a) == b,
    }
    # Hoán vị vị trí: có sigma sao cho b[p] = a[sigma(p)] không?
    perm = None
    used = [False] * dc.SECRET_LENGTH
    ok = True
    sigma = []
    for p in range(dc.SECRET_LENGTH):
        found = -1
        for qpos in range(dc.SECRET_LENGTH):
            if not used[qpos] and a[qpos] == b[p]:
                found = qpos
                break
        if found < 0:
            ok = False
            break
        used[found] = True
        sigma.append(found)
    if ok:
        perm = tuple(sigma)
    info["position_permutation"] = list(perm) if perm is not None else None
    # Đổi tên chữ số TOÀN CỤC nhất quán: có song ánh tau với b[p] = tau(a[p])?
    tau = {}
    inv = {}
    consistent = True
    for p in range(dc.SECRET_LENGTH):
        x, y = a[p], b[p]
        if tau.setdefault(x, y) != y or inv.setdefault(y, x) != x:
            consistent = False
            break
    info["is_global_digit_relabel"] = consistent
    info["digit_relabel"] = (
        sorted((k, v) for k, v in tau.items() if k != v) if consistent else None
    )
    # Cặp chữ số bị hoán đổi tại các vị trí khác nhau (mô tả cục bộ).
    info["local_digit_swaps"] = sorted({tuple(sorted((a[p], b[p]))) for p in diff})
    return info


# ---------------------------------------------------------------------------
# Phân tích chính
# ---------------------------------------------------------------------------

def analyse(secrets=None):
    """Trả dict kết quả JSON-serialisable, deterministic."""
    if secrets is None:
        secrets = list(dc.iter_valid_secrets())
    else:
        secrets = list(secrets)
    n = len(secrets)

    base_ids = list(dc.BASE_QUESTION_IDS)      # 32 câu Q1+Q2+Q3
    q4_ids = list(dc.Q4_IDS)                   # 19 câu Q4
    base_index = {q: i for i, q in enumerate(base_ids)}

    # Bảng đáp án tính MỘT LẦN qua dc.answer (nguồn sự thật).
    table = [tuple(dc.answer(c, q) for q in base_ids) for c in secrets]
    table_q4 = [tuple(dc.answer(c, q) for q in q4_ids) for c in secrets]

    dens = _denominators(secrets)
    n_prob_checked = _check_denominators(secrets, dens)
    total_mass = sum(Fraction(cnt, d) for d, cnt in sorted(Counter(dens).items()))

    results = {
        "meta": {
            "n_secrets": n,
            "n_base_questions": len(base_ids),
            "n_q4_questions": len(q4_ids),
            "base_question_ids": base_ids,
            "q4_question_ids": q4_ids,
            "sampler_distinct_denominators": sorted(set(dens)),
            "sampler_total_mass_exact": _frac_str(total_mass),
            "sampler_prob_min_exact": _frac_str(Fraction(1, max(dens))),
            "sampler_prob_max_exact": _frac_str(Fraction(1, min(dens))),
            "sampler_prob_ratio_max_over_min_exact": _frac_str(
                Fraction(max(dens), min(dens))
            ),
            "n_secret_probability_cross_checked": n_prob_checked,
            "entropy_note": (
                "Khối lượng lớp tính bằng Fraction chính xác; entropy là float "
                "vì log2 là float (sai số làm tròn cỡ 1e-15 bit)."
            ),
        }
    }

    # --- 1. Partition của từng câu hỏi đơn --------------------------------
    def single_partitions(ids, tab):
        out = []
        for i, qid in enumerate(ids):
            col = [r[i] for r in tab]
            counts = Counter(col)
            mass = defaultdict(Counter)
            for v, d in zip(col, dens):
                mass[v][d] += 1
            classes = []
            masses = []
            for v in sorted(counts):
                m = sum(Fraction(c, d) for d, c in sorted(mass[v].items()))
                masses.append(m)
                classes.append({
                    "value": v,
                    "count": counts[v],
                    "share_uniform_exact": _frac_str(Fraction(counts[v], n)),
                    "mass_sampler_exact": _frac_str(m),
                    "mass_sampler_float": float(m),
                })
            out.append({
                "qid": qid,
                "n_classes": len(counts),
                "classes": classes,
                "entropy_uniform_bits": _entropy_from_counts(
                    [counts[v] for v in sorted(counts)], n),
                "entropy_sampler_bits": _entropy_from_masses(masses),
                "max_entropy_bits": math.log2(len(counts)) if counts else 0.0,
            })
        return out

    results["single_question_partitions"] = {
        "base": single_partitions(base_ids, table),
        "q4": single_partitions(q4_ids, table_q4),
    }

    # --- 2. Nhánh chết Q2 '=' ---------------------------------------------
    q2_idx = tuple(base_index[q] for q in dc.Q2_IDS)
    per_q2_zero = {}
    for q in dc.Q2_IDS:
        j = base_index[q]
        per_q2_zero[q] = sum(1 for r in table if r[j] == 0)
    any_zero = sum(1 for r in table if any(r[j] == 0 for j in q2_idx))
    q2_values = {q: sorted({r[base_index[q]] for r in table}) for q in dc.Q2_IDS}
    q2_edges = _q2_edges()
    n_q2_patterns = _distinct(table, q2_idx)
    n_acyclic = _count_acyclic_orientations(q2_edges, len(dc.LED_LABELS))
    results["q2_dead_branch"] = {
        "nominal_values": [-1, 0, 1],
        "realised_values_per_question": {q: q2_values[q] for q in dc.Q2_IDS},
        "secrets_with_any_q2_equal": any_zero,
        "secrets_with_q2_equal_per_question": per_q2_zero,
        "max_bits_per_q2_question": 1.0,
        "n_q2_patterns_realised": n_q2_patterns,
        "n_q2_patterns_if_independent": 2 ** len(dc.Q2_IDS),
        "n_acyclic_orientations_of_led_graph": n_acyclic,
        "acyclic_orientation_match": n_q2_patterns == n_acyclic,
        "joint_note": (
            "Bảy câu Q2 KHÔNG độc lập: chúng là hướng hoá của đồ thị lưới 2x3 trên "
            "6 LED, và chỉ hướng hoá PHI CHU TRÌNH mới hiện thực hoá được. Số bộ dấu "
            "khả thi vì thế là %d chứ không phải 2^7 = %d — khớp chính xác với số "
            "hướng hoá phi chu trình đếm độc lập bằng vét cạn."
            % (n_q2_patterns, 2 ** len(dc.Q2_IDS))
        ),
        "note": (
            "C2 cấm code[i] == code[i-1] với i in {1,2,4,5} và C3 cấm "
            "code[i] == code[i-3] với i in {3,4,5}; bảy cặp Q2 đúng bằng bảy cặp "
            "LED liền kề đó nên giá trị 0 ('=') không bao giờ đạt tới. Mỗi câu Q2 "
            "vì vậy có đúng 2 giá trị, tức tối đa 1 bit, không phải log2(3) bit."
        ),
    }

    # --- 3. Quan hệ phụ thuộc ---------------------------------------------
    dep = {}

    # 3a. Q4(node) là hàm của Q3(node).
    q4_of_q3 = {}
    violations = 0
    for k, node in enumerate(dc.COUNT_NODES):
        j = base_index["Q3:" + node]
        seen = {}
        bad = 0
        for r, r4 in zip(table, table_q4):
            v = r[j]
            if v in seen:
                if seen[v] != r4[k]:
                    bad += 1
            else:
                seen[v] = r4[k]
        violations += bad
        q4_of_q3[node] = {
            "max_led": dc.MAX_LED[node],
            "q3_values_seen": sorted(seen),
            "q3_to_q4": {str(v): seen[v] for v in sorted(seen)},
            "violations": bad,
        }
    q3_idx = tuple(base_index[q] for q in dc.Q3_IDS)
    n_cls_q3 = _distinct(table, q3_idx)
    combined = [a + b for a, b in zip(map(itemgetter(*q3_idx), table), table_q4)]
    n_cls_q3_q4 = len(set(combined))
    n_cls_q4 = len(set(table_q4))
    dep["q4_is_function_of_q3"] = {
        "violations_total": violations,
        "per_node": q4_of_q3,
        "n_classes_q3_all": n_cls_q3,
        "n_classes_q4_all": n_cls_q4,
        "n_classes_q3_and_q4": n_cls_q3_q4,
        "q4_adds_nothing_given_q3": n_cls_q3_q4 == n_cls_q3,
        "q4_coarser_than_q3_standalone": n_cls_q4 < n_cls_q3,
    }

    # 3b. Phụ thuộc tuyến tính giữa 19 câu đếm.
    cells = [(led, seg) for led in range(6) for seg in range(7)]
    cell_index = {c: i for i, c in enumerate(cells)}
    incidence = []
    for node in dc.COUNT_NODES:
        row = [0] * len(cells)
        for c in dc.NODE_CELLS[node]:
            row[cell_index[c]] = 1
        incidence.append(row)
    # Hạng của ma trận 19x42 trên Q.
    ech_inc = _Echelon(len(cells))
    for row in incidence:
        ech_inc.add(row)
    rank_incidence = ech_inc.rank()
    # Quan hệ giữa các HÀNG = null space trái = null space của ma trận chuyển vị.
    ech_left = _Echelon(len(dc.COUNT_NODES))
    transpose = [[incidence[i][j] for i in range(len(dc.COUNT_NODES))]
                 for j in range(len(cells))]
    for row in transpose:
        ech_left.add(row)
    left_null = [_integerize(v) for v in ech_left.nullspace()]

    def relation_str(vec):
        pos = " + ".join(
            ("%d*%s" % (vec[i], dc.COUNT_NODES[i])) if vec[i] != 1 else dc.COUNT_NODES[i]
            for i in range(len(vec)) if vec[i] > 0)
        neg = " + ".join(
            ("%d*%s" % (-vec[i], dc.COUNT_NODES[i])) if vec[i] != -1 else dc.COUNT_NODES[i]
            for i in range(len(vec)) if vec[i] < 0)
        return "%s = %s" % (pos, neg)

    # Kiểm tra bằng số liệu trên toàn bộ secret.
    q3_vectors = [tuple(r[j] for j in q3_idx) for r in table]
    col_row_violations = sum(1 for v in q3_vectors if sum(v[:9]) != sum(v[9:]))
    relation_violations = []
    for vec in left_null:
        bad = sum(1 for v in q3_vectors
                  if sum(a * b for a, b in zip(v, vec)) != 0)
        relation_violations.append(bad)
    # Hạng thực tế của tập vector đáp án 19 chiều (tuyến tính và affine).
    distinct_q3 = sorted(set(q3_vectors))
    step = max(1, len(distinct_q3) // 4000)
    sample = ([distinct_q3[i] for i in range(0, len(distinct_q3), step)]
              + distinct_q3[:500] + distinct_q3[-500:])
    rank_lin, null_lin, viol_lin = _exact_rank(sample, q3_vectors, 19)
    # Ràng buộc Sigma(cot) = Sigma(hang) có phải quan hệ nguyên thuỷ duy nhất?
    sum_vec = [1] * len(dc.COL_NODES) + [-1] * len(dc.ROW_NODES)
    ech_probe = _Echelon(len(dc.COUNT_NODES))
    for vec in left_null:
        ech_probe.add(vec)
    sum_vec_in_span = not ech_probe.add(sum_vec)
    sum_vec_is_only_relation = sum_vec_in_span and len(left_null) == 1
    base_vec = distinct_q3[0]
    sample_aff = [tuple(a - b for a, b in zip(v, base_vec)) for v in sample]
    all_aff = [tuple(a - b for a, b in zip(v, base_vec)) for v in q3_vectors]
    rank_aff, null_aff, viol_aff = _exact_rank(sample_aff, all_aff, 19)

    dep["counting_question_linear_structure"] = {
        "n_cells": len(cells),
        "col_nodes_partition_cells": sorted(
            Counter(c for node in dc.COL_NODES for c in dc.NODE_CELLS[node]).values()),
        "row_nodes_partition_cells": sorted(
            Counter(c for node in dc.ROW_NODES for c in dc.NODE_CELLS[node]).values()),
        "rank_incidence_19x42_over_Q": rank_incidence,
        "n_independent_relations": len(dc.COUNT_NODES) - rank_incidence,
        "relations": [
            {"vector": vec, "human": relation_str(vec),
             "violations_over_all_secrets": bad}
            for vec, bad in zip(left_null, relation_violations)
        ],
        "sum_col_minus_sum_row_violations": col_row_violations,
        "sum_col_eq_sum_row_in_relation_span": sum_vec_in_span,
        "sum_col_eq_sum_row_is_only_relation": sum_vec_is_only_relation,
        "sum_col_eq_sum_row_note": (
            "Sigma(cot) = Sigma(hang) ĐÚNG (0 vi phạm) nhưng KHÔNG phải ràng buộc "
            "nguyên thuỷ duy nhất: nó là TỔNG của hai quan hệ mịn hơn ở trên. "
            "Tập segment tách thành hai khối {a,g,d} và {b,c,e,f}, mỗi khối vừa là "
            "hợp của nhóm cột vừa là hợp của nhóm hàng, nên có ĐÚNG 2 quan hệ "
            "tuyến tính độc lập chứ không phải 1."
        ),
        "rank_answer_vectors_linear": rank_lin,
        "rank_answer_vectors_linear_null": null_lin,
        "rank_answer_vectors_linear_violations": viol_lin,
        "rank_answer_vectors_affine": rank_aff,
        "rank_answer_vectors_affine_null": null_aff,
        "rank_answer_vectors_affine_violations": viol_aff,
        "affine_base_vector": list(base_vec),
        "rank_method": (
            "Dựng cơ sở từ mẫu tất định rồi CHỨNG MINH bằng cách kiểm tra toàn bộ "
            "465120 vector trực giao với null space của cơ sở đó (0 vi phạm => hạng "
            "đúng bằng hạng cơ sở). Không phải ước lượng."
        ),
    }

    # 3c. Mỗi câu q trong 32 câu có phải hàm của 31 câu còn lại không.
    n_cls_full = len(set(table))
    redundancy = []
    for i, qid in enumerate(base_ids):
        idx = tuple(j for j in range(len(base_ids)) if j != i)
        cnt = _distinct(table, idx)
        redundancy.append({
            "qid": qid,
            "n_classes_without": cnt,
            "n_classes_full": n_cls_full,
            "redundant": cnt == n_cls_full,
            "classes_lost": n_cls_full - cnt,
        })
    # Tập con dư-thừa-tối-thiểu theo thứ tự BASE (greedy, tất định).
    keep = list(range(len(base_ids)))
    for i in range(len(base_ids)):
        trial = [j for j in keep if j != i]
        if trial and _distinct(table, tuple(trial)) == n_cls_full:
            keep = trial
    dep["single_question_redundancy"] = {
        "n_classes_full_32": n_cls_full,
        "per_question": redundancy,
        "redundant_questions": [r["qid"] for r in redundancy if r["redundant"]],
        "irredundant_questions": [r["qid"] for r in redundancy if not r["redundant"]],
        "greedy_irredundant_subset": [base_ids[j] for j in keep],
        "greedy_irredundant_size": len(keep),
        "greedy_dropped": [base_ids[j] for j in range(len(base_ids)) if j not in keep],
        "greedy_note": (
            "Greedy bỏ theo đúng thứ tự BASE_QUESTION_IDS nên tất định, và cho một "
            "tập KHÔNG THỂ BỎ THÊM (irredundant), nhưng KHÔNG chứng minh được đó là "
            "tập nhỏ nhất (minimum). Thứ tự bỏ khác có thể ra tập khác cỡ khác."
        ),
        "note": (
            "'Dư thừa' ở đây là dư thừa ĐƠN LẺ: bỏ đúng một câu không mất lớp nào. "
            "Bỏ nhiều câu dư thừa CÙNG LÚC thì có thể mất — xem greedy subset."
        ),
    }
    results["dependencies"] = dep

    # --- 4. Chữ số không phân biệt được bằng đếm segment -------------------
    by_col = defaultdict(list)
    by_row = defaultdict(list)
    by_both = defaultdict(list)
    digit_rows = []
    for d in range(10):
        cv = _digit_col_vector(d)
        rv = _digit_row_vector(d)
        by_col[cv].append(d)
        by_row[rv].append(d)
        by_both[(cv, rv)].append(d)
        digit_rows.append({
            "digit": d,
            "segments_abcdefg": list(dc.DIGIT_MAP[d]),
            "col_vector_left_mid_right": list(cv),
            "row_vector_a_fb_g_ec_d": list(rv),
            "total_segments": sum(dc.DIGIT_MAP[d]),
        })
    both_groups = [sorted(v) for v in by_both.values() if len(v) > 1]
    results["digit_features"] = {
        "digits": digit_rows,
        "col_vector_collisions": sorted(sorted(v) for v in by_col.values() if len(v) > 1),
        "row_vector_collisions": sorted(sorted(v) for v in by_row.values() if len(v) > 1),
        "fully_indistinguishable_groups": sorted(both_groups),
        "parity_of_groups": [
            {"group": g, "parities": [d % 2 for d in g]} for g in sorted(both_groups)
        ],
        "note": (
            "Hai chữ số có CẢ col-vector lẫn row-vector giống nhau thì không câu "
            "Q3/Q4 nào phân biệt được khi chúng đứng ở cùng vị trí; chỉ Q1 (chẵn/lẻ) "
            "hoặc Q2 (so sánh) mới tách được."
        ),
    }
    # Đo trực tiếp: đổi 2<->5 ở mọi vị trí có bảo toàn Q3 không.
    swap_pairs = both_groups[0] if both_groups else []
    if len(swap_pairs) == 2:
        a_d, b_d = swap_pairs
        def relabel(code):
            return tuple(b_d if x == a_d else (a_d if x == b_d else x) for x in code)
        valid_set = set(secrets)
        q3_by_secret = dict(zip(secrets, q3_vectors))
        moved = 0
        img_valid = 0
        q3_preserved = 0
        q1q2_broken = 0
        sig_by_secret = dict(zip(secrets, table))
        for code in secrets:
            img = relabel(code)
            if img == code:
                continue
            moved += 1
            if img in valid_set:
                img_valid += 1
                if q3_by_secret[img] == q3_by_secret[code]:
                    q3_preserved += 1
                if sig_by_secret[img] != sig_by_secret[code]:
                    q1q2_broken += 1
        results["digit_features"]["relabel_probe"] = {
            "relabel": [a_d, b_d],
            "secrets_moved": moved,
            "image_still_valid": img_valid,
            "image_valid_and_q3_identical": q3_preserved,
            "image_valid_and_full_signature_differs": q1q2_broken,
            "note": (
                "Ảnh luôn hợp lệ (C1/C2/C3 bất biến dưới mọi song ánh chữ số). "
                "Đổi %d<->%d giữ NGUYÊN cả 19 đáp án Q3 (và do đó cả Q4) trên "
                "TOÀN BỘ secret bị nó làm thay đổi, nhưng LUÔN đổi ít nhất một đáp "
                "án Q1 vì %d chẵn còn %d lẻ — nên nó không tạo collision nào dưới "
                "bộ clue đầy đủ." % (a_d, b_d, a_d, b_d)
            ),
        }

    # --- 5. Collision dưới toàn bộ clue -----------------------------------
    groups = defaultdict(list)
    for i, r in enumerate(table):
        groups[r].append(i)
    size_hist = Counter(len(v) for v in groups.values())
    non_singleton = sum(len(v) for v in groups.values() if len(v) > 1)
    n_pairs = sum(len(v) * (len(v) - 1) // 2 for v in groups.values())
    coll_pairs = []
    for v in groups.values():
        if len(v) > 1:
            for a in range(len(v)):
                for b in range(a + 1, len(v)):
                    coll_pairs.append((secrets[v[a]], secrets[v[b]]))
    coll_pairs.sort()

    groups_q4 = defaultdict(list)
    for i, (r, r4) in enumerate(zip(table, table_q4)):
        groups_q4[r + r4].append(i)
    size_hist_q4 = Counter(len(v) for v in groups_q4.values())
    n_pairs_q4 = sum(len(v) * (len(v) - 1) // 2 for v in groups_q4.values())

    # Đặc trưng hoá cấu trúc.
    classifications = [_classify_pair(a, b) for a, b in coll_pairs]
    transform_stats = Counter()
    for info in classifications:
        if info["is_column_swap"]:
            key = "column swap (pos 0<->2 and 3<->5)"
        elif info["position_permutation"] is not None:
            key = "position permutation %s" % (tuple(info["position_permutation"]),)
        elif info["is_global_digit_relabel"]:
            key = "global digit relabel %s" % (tuple(info["digit_relabel"]),)
        else:
            key = "other"
        transform_stats[key] += 1
    diff_pattern_stats = Counter(tuple(i["diff_positions"]) for i in classifications)
    local_swap_stats = Counter(
        tuple(tuple(s) for s in i["local_digit_swaps"]) for i in classifications)
    global_relabel_stats = Counter(i["is_global_digit_relabel"] for i in classifications)
    same_multiset_stats = Counter(i["same_multiset"] for i in classifications)

    # Kiểm chứng độc lập #1: chỉ áp phép đổi cột, không dùng bảng gom nhóm.
    valid_set = set(secrets)
    sig_by_secret = dict(zip(secrets, table))
    swap_pairs_found = 0
    for code in secrets:
        img = _column_swap(code)
        if img != code and img > code and img in valid_set:
            if sig_by_secret[img] == sig_by_secret[code]:
                swap_pairs_found += 1
    # Kiểm chứng độc lập #2: công thức tổ hợp đóng suy từ đặc trưng hoá.
    #   Cột ngoài mang {4,6} ở một hàng và {5,7} ở hàng kia, xếp "song song"
    #   (4 trên 5, 6 trên 7) để Q2 dọc bảo toàn; chữ số giữa m1 phải nằm ngoài
    #   khoảng (4,6) và khác 4,6  -> m1 not in {4,5,6};  m2 not in {5,6,7};
    #   C3 buộc m1 != m2.
    m1_choices = [d for d in range(10) if d not in (4, 5, 6)]
    m2_choices = [d for d in range(10) if d not in (5, 6, 7)]
    closed_form = 2 * sum(1 for a in m1_choices for b in m2_choices if a != b)

    counterexamples = []
    for a, b in coll_pairs:
        info = _classify_pair(a, b)
        counterexamples.append({
            "code_a": "".join(str(d) for d in a),
            "code_b": "".join(str(d) for d in b),
            "diff_positions": info["diff_positions"],
            "diff_leds": [dc.LED_LABELS[p] for p in info["diff_positions"]],
            "digit_changes": [
                {"position": p, "led": dc.LED_LABELS[p], "a": a[p], "b": b[p]}
                for p in info["diff_positions"]
            ],
            "transform": ("column swap (pos 0<->2 and 3<->5)"
                          if info["is_column_swap"] else "other"),
            "same_multiset": info["same_multiset"],
            "is_global_digit_relabel": info["is_global_digit_relabel"],
        })

    results["collisions"] = {
        "n_classes_32": len(groups),
        "class_size_histogram_32": {str(k): v for k, v in sorted(size_hist.items())},
        "secrets_in_non_singleton_classes": non_singleton,
        "indistinguishable_unordered_pairs": n_pairs,
        "n_classes_32_plus_q4": len(groups_q4),
        "class_size_histogram_32_plus_q4": {
            str(k): v for k, v in sorted(size_hist_q4.items())},
        "indistinguishable_unordered_pairs_with_q4": n_pairs_q4,
        "q4_breaks_no_collision": n_pairs_q4 == n_pairs and len(groups_q4) == len(groups),
        "counterexamples": counterexamples,
        "transform_statistics": dict(sorted(transform_stats.items())),
        "diff_position_statistics": {str(k): v
                                     for k, v in sorted(diff_pattern_stats.items())},
        "local_digit_swap_statistics": {str(k): v
                                        for k, v in sorted(local_swap_stats.items())},
        "global_digit_relabel_statistics": {str(k): v
                                            for k, v in sorted(global_relabel_stats.items())},
        "same_multiset_statistics": {str(k): v
                                     for k, v in sorted(same_multiset_stats.items())},
        "cross_check_column_swap_scan": swap_pairs_found,
        "cross_check_closed_form": closed_form,
        "hypothesis_86_pairs": {
            "claimed": 86,
            "measured": n_pairs,
            "verdict": "CONFIRMED" if n_pairs == 86 else "REFUTED",
        },
    }

    # --- 6. Sức mạnh của từng họ câu hỏi ----------------------------------
    q1_idx = tuple(base_index[q] for q in dc.Q1_IDS)
    q2_idx_t = tuple(base_index[q] for q in dc.Q2_IDS)

    def realised_alphabet(ids, tab):
        return [len({r[i] for r in tab}) for i in range(len(ids))]

    alpha_base = realised_alphabet(base_ids, table)
    alpha_q4 = realised_alphabet(q4_ids, table_q4)
    nominal = {}
    for q in dc.Q1_IDS:
        nominal[q] = 2
    for q in dc.Q2_IDS:
        nominal[q] = 3
    for node in dc.COUNT_NODES:
        nominal["Q3:" + node] = dc.MAX_LED[node] + 1
        nominal["Q4:" + node] = 2

    def product(vals):
        p = 1
        for v in vals:
            p *= v
        return p

    def family(name, idx, extra_q4=False):
        if extra_q4 and idx:
            tab = [a + b for a, b in zip(map(itemgetter(*idx), table), table_q4)]
            cls = len(set(tab))
            ids = [base_ids[i] for i in idx] + q4_ids
            alpha = [alpha_base[i] for i in idx] + alpha_q4
        elif extra_q4:
            cls = len(set(table_q4))
            ids = list(q4_ids)
            alpha = list(alpha_q4)
        else:
            cls = _distinct(table, idx)
            ids = [base_ids[i] for i in idx]
            alpha = [alpha_base[i] for i in idx]
        nom = product(nominal[q] for q in ids)
        real = product(alpha)
        return {
            "family": name,
            "n_questions": len(ids),
            "n_classes": cls,
            "max_classes_nominal_alphabet": nom,
            "max_classes_realised_alphabet": real,
            "max_classes_capped_by_secret_count": min(real, n),
            "redundancy_factor_vs_realised": (real / cls) if cls else float("inf"),
            "coverage_of_secret_space": cls / n,
            "bits_uniform": math.log2(cls),
        }

    families = [
        family("Q1 only (6)", q1_idx),
        family("Q2 only (7)", q2_idx_t),
        family("Q3 only (19)", q3_idx),
        family("Q4 only (19)", (), extra_q4=True),
        family("Q1+Q2 (13)", q1_idx + q2_idx_t),
        family("Q1+Q3 (25)", q1_idx + q3_idx),
        family("Q2+Q3 (26)", q2_idx_t + q3_idx),
        family("Q1+Q2+Q3 (32)", tuple(range(len(base_ids)))),
        family("Q1+Q2+Q3+Q4 (51)", tuple(range(len(base_ids))), extra_q4=True),
    ]
    results["question_family_power"] = {
        "families": families,
        "total_bits_needed": math.log2(n),
        "note": (
            "max_classes_nominal_alphabet dùng bảng giá trị danh nghĩa "
            "(Q2 có 3 giá trị kể cả '=' bất khả thi, Q3 có MAX_LED+1 giá trị); "
            "max_classes_realised_alphabet chỉ dùng các giá trị THỰC SỰ xuất hiện. "
            "Cả hai đều là chặn trên, chưa tính ràng buộc chéo giữa các câu."
        ),
    }

    return results


# ---------------------------------------------------------------------------
# Báo cáo
# ---------------------------------------------------------------------------

def _bar(title):
    return "=" * 78 + "\n" + title + "\n" + "=" * 78


def format_report(results):
    """Trả str báo cáo plain-text deterministic."""
    L = []
    meta = results["meta"]
    n = meta["n_secrets"]

    L.append(_bar("U2 — PARTITION / PHỤ THUỘC CLUE / COLLISION"))
    L.append("Nguồn: tools/analysis/digitcode.py (port 1-1 từ backend/gameboard.cpp)")
    L.append("Phương pháp: VÉT CẠN toàn bộ tập secret hợp lệ. Không lấy mẫu, không RNG.")
    L.append("")
    L.append("Số secret hợp lệ                       : %d" % n)
    L.append("Số câu hỏi nguyên tử Q1+Q2+Q3          : %d" % meta["n_base_questions"])
    L.append("Số câu hỏi nguyên tử Q4                : %d" % meta["n_q4_questions"])
    L.append("Mẫu số xác suất sampler (P = 1/D)      : %s"
             % ", ".join(str(d) for d in meta["sampler_distinct_denominators"]))
    L.append("Tổng khối lượng xác suất (chính xác)   : %s"
             % meta["sampler_total_mass_exact"])
    L.append("P_max / P_min (chính xác)              : %s"
             % meta["sampler_prob_ratio_max_over_min_exact"])
    L.append("Đối chiếu với dc.secret_probability    : %d mẫu, khớp 100%%"
             % meta["n_secret_probability_cross_checked"])
    L.append("Ghi chú entropy: %s" % meta["entropy_note"])
    L.append("")

    # --- 1 -----------------------------------------------------------------
    L.append(_bar("1. PARTITION CỦA TỪNG CÂU HỎI ĐƠN"))
    L.append("")
    L.append("H_unif = entropy dưới phân phối ĐỀU trên tập hợp lệ.")
    L.append("H_samp = entropy dưới phân phối THỰC của rejection sampler.")
    L.append("H_max  = log2(số lớp) = trần thông tin của câu hỏi đó.")
    L.append("")
    for section, label in (("base", "Q1 + Q2 + Q3 (32 câu)"), ("q4", "Q4 (19 câu)")):
        L.append("-- %s %s" % (label, "-" * (60 - len(label))))
        L.append("%-10s %7s %8s %8s %8s   %s"
                 % ("câu", "số lớp", "H_unif", "H_samp", "H_max", "kích thước lớp"))
        for row in results["single_question_partitions"][section]:
            sizes = ", ".join("%s:%d" % (c["value"], c["count"]) for c in row["classes"])
            L.append("%-10s %7d %8.5f %8.5f %8.5f   %s"
                     % (row["qid"], row["n_classes"], row["entropy_uniform_bits"],
                        row["entropy_sampler_bits"], row["max_entropy_bits"], sizes))
        L.append("")
    L.append("Khối lượng xác suất sampler chính xác của từng lớp (Fraction) nằm trong")
    L.append("results['single_question_partitions'][*][i]['classes'][j]['mass_sampler_exact'].")
    L.append("")

    # --- 2 -----------------------------------------------------------------
    dead = results["q2_dead_branch"]
    L.append(_bar("2. NHÁNH CHẾT Q2 '=' (giá trị 0)"))
    L.append("")
    L.append("Số secret có BẤT KỲ Q2 nào trả 0       : %d"
             % dead["secrets_with_any_q2_equal"])
    for q in sorted(dead["secrets_with_q2_equal_per_question"]):
        L.append("  %-10s Q2==0 : %d   giá trị thực tế: %s"
                 % (q, dead["secrets_with_q2_equal_per_question"][q],
                    dead["realised_values_per_question"][q]))
    L.append("")
    L.append(dead["note"])
    L.append("=> Trần thông tin của mỗi câu Q2 là %.1f bit (không phải log2(3)=1.585)."
             % dead["max_bits_per_q2_question"])
    L.append("")
    L.append("Bảy câu Q2 còn ràng buộc CHÉO với nhau:")
    L.append("  Số bộ dấu Q2 thực sự xuất hiện        : %d"
             % dead["n_q2_patterns_realised"])
    L.append("  Nếu 7 câu độc lập thì phải là 2^7     : %d"
             % dead["n_q2_patterns_if_independent"])
    L.append("  Số hướng hoá phi chu trình của đồ thị : %d  (đếm độc lập, vét cạn 2^7)"
             % dead["n_acyclic_orientations_of_led_graph"])
    L.append("  Khớp: %s" % dead["acyclic_orientation_match"])
    L.append("  " + dead["joint_note"])
    L.append("")

    # --- 3 -----------------------------------------------------------------
    dep = results["dependencies"]
    L.append(_bar("3. QUAN HE PHU THUOC GIUA CAC CLUE"))
    L.append("")
    q4d = dep["q4_is_function_of_q3"]
    L.append("3a. Q4(node) la HAM cua Q3(node)")
    L.append("    So vi pham (2 secret cung Q3 khac Q4) : %d" % q4d["violations_total"])
    L.append("    So lop partition Q3 toan bo (19 cau)  : %d" % q4d["n_classes_q3_all"])
    L.append("    So lop partition Q4 toan bo (19 cau)  : %d" % q4d["n_classes_q4_all"])
    L.append("    So lop partition Q3 + Q4 (38 cau)     : %d" % q4d["n_classes_q3_and_q4"])
    L.append("    => Q4 KHONG them thong tin khi da co toan bo Q3: %s"
             % q4d["q4_adds_nothing_given_q3"])
    L.append("    => Dung mot minh, Q4 THO HON Q3 rat nhieu (%d vs %d lop, ti le %.1fx)"
             % (q4d["n_classes_q4_all"], q4d["n_classes_q3_all"],
                q4d["n_classes_q3_all"] / q4d["n_classes_q4_all"]))
    L.append("    Nguong FULL tung nut (Q3 == MAX_LED):")
    for node in dc.COUNT_NODES:
        info = q4d["per_node"][node]
        L.append("      %-2s MAX_LED=%d  Q3 quan sat duoc=%s  Q4=1 khi Q3=%d"
                 % (node, info["max_led"], info["q3_values_seen"], info["max_led"]))
    L.append("")

    lin = dep["counting_question_linear_structure"]
    L.append("3b. Cau truc tuyen tinh cua 19 cau dem")
    L.append("    9 nut cot phu %d o, moi o dung 1 lan : %s"
             % (lin["n_cells"], set(lin["col_nodes_partition_cells"]) == {1}))
    L.append("    10 nut hang phu %d o, moi o dung 1 lan: %s"
             % (lin["n_cells"], set(lin["row_nodes_partition_cells"]) == {1}))
    L.append("    Sigma(cot) != Sigma(hang) tren secret : %d vi pham"
             % lin["sum_col_minus_sum_row_violations"])
    L.append("")
    L.append("    Hang ma tran incidence 19x42 tren Q  : %d"
             % lin["rank_incidence_19x42_over_Q"])
    L.append("    So quan he tuyen tinh doc lap        : %d  (19 - hang)"
             % lin["n_independent_relations"])
    L.append("    CAC QUAN HE NGUYEN THUY:")
    for rel in lin["relations"]:
        L.append("      %s   (vi pham tren 465120 secret: %d)"
                 % (rel["human"], rel["violations_over_all_secrets"]))
    L.append("")
    L.append("    " + lin["sum_col_eq_sum_row_note"].replace("\n", "\n    "))
    L.append("")
    L.append("    Hang cua TAP VECTOR DAP AN 19 chieu (tuyen tinh) : %d  (vi pham: %d)"
             % (lin["rank_answer_vectors_linear"],
                lin["rank_answer_vectors_linear_violations"]))
    L.append("    Hang cua tap vector dap an (affine)              : %d  (vi pham: %d)"
             % (lin["rank_answer_vectors_affine"],
                lin["rank_answer_vectors_affine_violations"]))
    L.append("    => Hang thuc te KHOP hang cau truc: khong co quan he tuyen tinh")
    L.append("       'ngau nhien' nao ngoai hai quan he hinh hoc tren.")
    L.append("    Phuong phap: %s" % lin["rank_method"])
    L.append("")

    red = dep["single_question_redundancy"]
    L.append("3c. Bo mot cau khoi 32 cau — co mat kha nang phan biet khong?")
    L.append("    So lop khi dung du 32 cau : %d" % red["n_classes_full_32"])
    L.append("")
    L.append("    %-10s %12s %12s  %s" % ("cau", "so lop", "mat lop", "ket luan"))
    for row in red["per_question"]:
        L.append("    %-10s %12d %12d  %s"
                 % (row["qid"], row["n_classes_without"], row["classes_lost"],
                    "DU THUA HOAN TOAN" if row["redundant"] else "can thiet"))
    L.append("")
    L.append("    Cau DU THUA don le (%d cau): %s"
             % (len(red["redundant_questions"]), ", ".join(red["redundant_questions"])))
    L.append("    Cau KHONG the bo (%d cau)  : %s"
             % (len(red["irredundant_questions"]), ", ".join(red["irredundant_questions"])))
    L.append("    " + red["note"])
    L.append("")
    L.append("    Tap con irredundant tim bang greedy (%d/32 cau, giu nguyen %d lop):"
             % (red["greedy_irredundant_size"], red["n_classes_full_32"]))
    L.append("      GIU : %s" % ", ".join(red["greedy_irredundant_subset"]))
    L.append("      BO  : %s" % ", ".join(red["greedy_dropped"]))
    L.append("    " + red["greedy_note"])
    L.append("")

    # --- 4 -----------------------------------------------------------------
    df = results["digit_features"]
    L.append(_bar("4. CHU SO KHONG PHAN BIET DUOC BANG DEM SEGMENT"))
    L.append("")
    L.append("%-6s %-16s %-14s %-16s %s"
             % ("chu so", "abcdefg", "col(L,M,R)", "row(a,f+b,g,e+c,d)", "tong seg"))
    for row in df["digits"]:
        L.append("%-6d %-16s %-14s %-16s %d"
                 % (row["digit"],
                    "".join(str(x) for x in row["segments_abcdefg"]),
                    str(tuple(row["col_vector_left_mid_right"])),
                    str(tuple(row["row_vector_a_fb_g_ec_d"])),
                    row["total_segments"]))
    L.append("")
    L.append("Trung col-vector (chi nhom COT khong tach duoc) : %s"
             % df["col_vector_collisions"])
    L.append("Trung row-vector (chi nhom HANG khong tach duoc): %s"
             % df["row_vector_collisions"])
    L.append("TRUNG CA HAI -> khong Q3/Q4 nao tach duoc       : %s"
             % df["fully_indistinguishable_groups"])
    for g in df["parity_of_groups"]:
        L.append("   nhom %s co chan/le = %s  -> Q1 tach duoc: %s"
                 % (g["group"], g["parities"], len(set(g["parities"])) > 1))
    L.append("")
    L.append(df["note"])
    if "relabel_probe" in df:
        pr = df["relabel_probe"]
        L.append("")
        L.append("Do truc tiep phep doi ten %d<->%d tren toan bo tap secret:" % tuple(pr["relabel"]))
        L.append("  secret bi phep doi lam thay doi        : %d" % pr["secrets_moved"])
        L.append("  anh van hop le VA Q3 giong het         : %d" % pr["image_valid_and_q3_identical"])
        L.append("  anh van hop le NHUNG full signature khac: %d"
                 % pr["image_valid_and_full_signature_differs"])
        L.append("  " + pr["note"])
    L.append("")

    # --- 5 -----------------------------------------------------------------
    co = results["collisions"]
    L.append(_bar("5. COLLISION DUOI TOAN BO CLUE"))
    L.append("")
    L.append("-- Chi 32 cau Q1+Q2+Q3 --")
    L.append("  So lop                                : %d" % co["n_classes_32"])
    L.append("  Histogram kich thuoc lop              : %s"
             % ", ".join("size %s -> %d lop" % (k, v)
                         for k, v in sorted(co["class_size_histogram_32"].items(),
                                            key=lambda x: int(x[0]))))
    L.append("  Secret nam trong lop KHONG singleton  : %d"
             % co["secrets_in_non_singleton_classes"])
    L.append("  So CAP khong phan biet duoc (vo huong): %d"
             % co["indistinguishable_unordered_pairs"])
    L.append("")
    L.append("-- Them ca 19 cau Q4 (51 cau) --")
    L.append("  So lop                                : %d" % co["n_classes_32_plus_q4"])
    L.append("  Histogram kich thuoc lop              : %s"
             % ", ".join("size %s -> %d lop" % (k, v)
                         for k, v in sorted(co["class_size_histogram_32_plus_q4"].items(),
                                            key=lambda x: int(x[0]))))
    L.append("  So cap khong phan biet duoc           : %d"
             % co["indistinguishable_unordered_pairs_with_q4"])
    L.append("  => Q4 KHONG pha duoc collision nao    : %s" % co["q4_breaks_no_collision"])
    L.append("")
    hyp = co["hypothesis_86_pairs"]
    L.append("HYPOTHESIS tu audit truoc: %d cap trung full signature" % hyp["claimed"])
    L.append("  Do duoc: %d  ->  %s" % (hyp["measured"], hyp["verdict"]))
    L.append("  Kiem chung doc lap #1 (chi quet phep doi cot, khong gom nhom): %d cap"
             % co["cross_check_column_swap_scan"])
    L.append("  Kiem chung doc lap #2 (cong thuc to hop dong)                : %d cap"
             % co["cross_check_closed_form"])
    L.append("")
    L.append("COUNTEREXAMPLE (in %d cap dau; ca %d cap nam trong "
             "results['collisions']['counterexamples']):"
             % (min(12, len(co["counterexamples"])), len(co["counterexamples"])))
    L.append("  %-8s %-8s  %s" % ("ma A", "ma B", "khac nhau o dau"))
    for ex in co["counterexamples"][:12]:
        detail = ", ".join("pos%d(LED %s): %d->%d"
                           % (c["position"], c["led"], c["a"], c["b"])
                           for c in ex["digit_changes"])
        L.append("  %-8s %-8s  %s" % (ex["code_a"], ex["code_b"], detail))
    L.append("")
    L.append("DAC TRUNG HOA CAU TRUC cua cac cap collision:")
    L.append("  Dang bien doi:")
    for k, v in sorted(co["transform_statistics"].items()):
        L.append("    %-40s : %d cap" % (k, v))
    L.append("  Mau vi tri khac nhau:")
    for k, v in sorted(co["diff_position_statistics"].items()):
        L.append("    %-40s : %d cap" % (k, v))
    L.append("  Cap chu so bi hoan doi tai cac vi tri khac:")
    for k, v in sorted(co["local_digit_swap_statistics"].items()):
        L.append("    %-40s : %d cap" % (k, v))
    L.append("  Cung multiset chu so:")
    for k, v in sorted(co["same_multiset_statistics"].items()):
        L.append("    %-40s : %d cap" % (k, v))
    L.append("  La phep doi ten chu so TOAN CUC nhat quan:")
    for k, v in sorted(co["global_digit_relabel_statistics"].items()):
        L.append("    %-40s : %d cap" % (k, v))
    L.append("")
    L.append("  Doc ket qua: toan bo collision la MOT ho duy nhat — doi cho cot trai")
    L.append("  va cot phai cua bang 2x3 (vi tri 0<->2 va 3<->5). No song song 4<->6")
    L.append("  o mot hang va 5<->7 o hang kia. Ly do:")
    L.append("    * col(4)+col(5) = col(6)+col(7) nen 3 nut cot moi cap giu nguyen;")
    L.append("    * moi hang giu nguyen MULTISET chu so nen 10 nut hang giu nguyen;")
    L.append("    * 4,6 cung chan va 5,7 cung le nen Q1 giu nguyen;")
    L.append("    * chu so giua phai nam ngoai khoang (4,6) resp. (5,7) va xep")
    L.append("      'song song' (4 tren 5, 6 tren 7) nen 7 dau so sanh Q2 giu nguyen.")
    L.append("")

    # --- 6 -----------------------------------------------------------------
    fam = results["question_family_power"]
    L.append(_bar("6. SUC MANH CUA TUNG HO CAU HOI"))
    L.append("")
    L.append("Can %.4f bit de xac dinh duy nhat 1 trong %d secret."
             % (fam["total_bits_needed"], n))
    L.append("")
    L.append("%-22s %4s %10s %8s %16s %10s"
             % ("ho cau hoi", "#cau", "so lop", "bit", "tran (alphabet)", "du thua"))
    for f in fam["families"]:
        L.append("%-22s %4d %10d %8.4f %16d %9.1fx"
                 % (f["family"], f["n_questions"], f["n_classes"], f["bits_uniform"],
                    f["max_classes_realised_alphabet"],
                    f["redundancy_factor_vs_realised"]))
    L.append("")
    L.append("Tran danh nghia (ke ca gia tri khong bao gio xuat hien):")
    for f in fam["families"]:
        L.append("  %-22s : %d" % (f["family"], f["max_classes_nominal_alphabet"]))
    L.append("")
    L.append(fam["note"])
    L.append("")
    L.append("Do phu khong gian secret (so lop / %d):" % n)
    for f in fam["families"]:
        L.append("  %-22s : %.6f" % (f["family"], f["coverage_of_secret_space"]))
    L.append("")
    L.append(_bar("HET"))
    return "\n".join(L)


if __name__ == "__main__":
    print(format_report(analyse()))
