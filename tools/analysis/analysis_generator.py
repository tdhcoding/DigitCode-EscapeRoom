# -*- coding: utf-8 -*-
"""Đặc trưng hoá rejection sampler sinh secret của DigitCode (issue #6).

Sampler nằm ở `backend/gameboard.cpp:471-482`, đã port sang
`digitcode.allowed_digits` / `is_valid_secret` / `secret_probability`.  Module
này KHÔNG sửa mô hình; nó chỉ đo:

1. tổng số secret hợp lệ — bằng BA đường độc lập nhau,
2. phân phối xác suất CHÍNH XÁC của sampler (Fraction, không float),
3. kiểm tra hypothesis "p_max/p_min ~= 9/7" của audit trước,
4. kỳ vọng số lần gọi `bounded(10)` để sinh một secret,
5. marginal của chữ số ở từng vị trí (sampler thật vs uniform),
6. bias theo cấu trúc (nhóm secret nào được ưu ái / thiệt thòi).

Hợp đồng công khai::

    analyse(secrets=None) -> dict   # JSON-serialisable, deterministic
    format_report(results) -> str   # plain text, deterministic

Chỉ dùng standard library, không RNG, không network.  Chạy hai lần cho ra
output y hệt nhau.
"""

import json
import os
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from functools import lru_cache
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import digitcode as dc  # noqa: E402  (phải chạy sau khi vá sys.path)


N_POS = dc.SECRET_LENGTH
DIGIT_BASE = 10  # `bounded(10)`


# =====================================================================
# Tiện ích trình bày
# =====================================================================

def _frac(value):
    """Đóng gói một Fraction thành dict JSON-serialisable (giữ nguyên exact)."""
    fr = Fraction(value)
    if fr.denominator == 1:
        text = str(fr.numerator)
    else:
        text = "%d/%d" % (fr.numerator, fr.denominator)
    return {
        "num": fr.numerator,
        "den": fr.denominator,
        "exact": text,
        "float": float(fr),
    }


def _falling(n, k):
    out = 1
    for j in range(k):
        out *= n - j
    return out


# =====================================================================
# 1a. Đếm bằng phân hoạch màu (độc lập hoàn toàn với thứ tự vị trí)
# =====================================================================
#
# C2/C3 nói: code là một PHÉP TÔ MÀU ĐÚNG của đồ thị ràng buộc trên 6 vị trí
# (đồ thị lưới 2x3: cạnh ngang 0-1, 1-2, 3-4, 4-5; cạnh dọc 0-3, 1-4, 2-5).
# C1 nói: mỗi màu (chữ số) dùng tối đa 2 lần, tức mỗi lớp màu có kích thước
# <= 2 và phải là tập độc lập.
#
# Vậy: chọn một phân hoạch 6 vị trí thành các khối kích thước 1 hoặc 2, trong
# đó mọi khối kích thước 2 là một CẶP KHÔNG KỀ (non-edge) và các cặp rời nhau
# — đúng bằng một matching trong đồ thị bù.  Với k khối, số cách gán chữ số
# phân biệt cho các khối là (10)_k = 10*9*...*(10-k+1).
#
#     tổng = sum_m  M(m) * (10)_(6-m),   M(m) = số matching cỡ m của đồ thị bù.
#
# Đường này không hề đi theo vị trí, không dùng prefix, nên độc lập với cả DP
# lẫn phép liệt kê.

def _constraint_edges():
    """Cạnh của đồ thị ràng buộc, suy thẳng từ C2/C3 trong sampler."""
    edges = set()
    for i in range(1, N_POS):
        if i % 3 != 0:                      # C2: code[i] != code[i-1]
            edges.add((i - 1, i))
    for i in range(3, N_POS):               # C3: code[i] != code[i-3]
        edges.add((i - 3, i))
    return edges


def count_secrets_by_partition():
    """Đếm secret hợp lệ bằng phân hoạch thành lớp màu (không liệt kê mã)."""
    edges = _constraint_edges()
    non_edges = [p for p in combinations(range(N_POS), 2) if p not in edges]

    matchings = Counter()

    def rec(start, used, size):
        matchings[size] += 1
        for k in range(start, len(non_edges)):
            a, b = non_edges[k]
            if a in used or b in used:
                continue
            rec(k + 1, used | {a, b}, size + 1)

    rec(0, frozenset(), 0)

    terms = []
    total = 0
    for m in sorted(matchings):
        blocks = N_POS - m
        falling = _falling(DIGIT_BASE, blocks)
        term = matchings[m] * falling
        total += term
        terms.append({
            "pairs": m,
            "matchings": matchings[m],
            "blocks": blocks,
            "falling_10_k": falling,
            "term": term,
        })
    return total, {
        "edges": sorted(edges),
        "non_edges": non_edges,
        "terms": terms,
    }


# =====================================================================
# 1b. Đếm bằng transfer matrix / DP theo vị trí (state đã chuẩn hoá)
# =====================================================================
#
# State trước khi đặt vị trí i:
#   * window = (code[i-1], code[i-2], code[i-3]) — đủ cho mọi ràng buộc còn
#     lại: vị trí i cần code[i-1] & code[i-3], vị trí i+1 cần code[i-2],
#     vị trí i+2 cần code[i-1];
#   * counts của đúng các chữ số đang nằm trong window;
#   * n0 / n1 = số chữ số NGOÀI window đang có count 0 / count 1.
#     (Chữ số ngoài window có count 2 vĩnh viễn không dùng được nữa nên không
#     cần nhớ.)
#
# Chuẩn hoá: chữ số trong window được đánh nhãn 0,1,2 theo thứ tự xuất hiện;
# các chữ số ngoài window là hoán vị được cho nhau nên chỉ cần đếm.  Nhờ vậy
# không gian state co lại còn vài chục phần tử — DP này KHÔNG duyệt qua
# 465120 mã, hoàn toàn khác đường liệt kê.

_NEW0 = -1   # bốc một chữ số mới, hiện count 0
_NEW1 = -2   # bốc lại một chữ số ngoài window đang có count 1
_EMPTY = -3  # ô window chưa tồn tại (i < 3)


def count_secrets_by_dp():
    """Đếm secret hợp lệ bằng DP theo vị trí; trả (tổng, số state đã thăm)."""

    def advance(window, counts, n0, n1, chosen):
        w0, w1, w2 = window
        cnt = list(counts)
        if chosen == _NEW0:
            d = len(cnt)
            cnt.append(1)
            n0 -= 1
        elif chosen == _NEW1:
            d = len(cnt)
            cnt.append(2)
            n1 -= 1
        else:
            d = chosen
            cnt[d] += 1

        new_window = (d, w0, w1)            # code[i-3] cũ bị đẩy ra ngoài
        if w2 != _EMPTY and w2 not in new_window:
            if cnt[w2] == 1:
                n1 += 1                     # count 2 -> vô dụng, không cần nhớ

        relabel = {}
        out = []
        for x in new_window:
            if x == _EMPTY:
                out.append(_EMPTY)
                continue
            if x not in relabel:
                relabel[x] = len(relabel)
            out.append(relabel[x])
        new_counts = [0] * len(relabel)
        for old, new in relabel.items():
            new_counts[new] = cnt[old]
        return tuple(out), tuple(new_counts), n0, n1

    @lru_cache(maxsize=None)
    def ways(i, window, counts, n0, n1):
        if i == N_POS:
            return 1
        forbidden = set()
        if i % 3 != 0 and window[0] != _EMPTY:
            forbidden.add(window[0])
        if i >= 3 and window[2] != _EMPTY:
            forbidden.add(window[2])

        total = 0
        for label in sorted(set(x for x in window if x != _EMPTY)):
            if counts[label] >= 2 or label in forbidden:
                continue
            total += ways(i + 1, *advance(window, counts, n0, n1, label))
        if n0:
            total += n0 * ways(i + 1, *advance(window, counts, n0, n1, _NEW0))
        if n1:
            total += n1 * ways(i + 1, *advance(window, counts, n0, n1, _NEW1))
        return total

    total = ways(0, (_EMPTY, _EMPTY, _EMPTY), (), DIGIT_BASE, 0)
    states = ways.cache_info().currsize
    ways.cache_clear()
    return total, states


# =====================================================================
# 2. Quét toàn bộ tập secret: xác suất, marginal, cấu trúc
# =====================================================================

def _collision_pattern(code):
    """Tuple các cặp vị trí (j, i) mà code[j] == code[i], đã sắp xếp."""
    seen = {}
    for idx, d in enumerate(code):
        seen.setdefault(d, []).append(idx)
    return tuple(sorted(tuple(v) for v in seen.values() if len(v) == 2))


def _scan(secrets):
    """Một lượt duy nhất qua tập secret, gom mọi thống kê cần thiết."""
    sizes = {}                       # prefix -> |A_i(prefix)|
    den_of_secret = Counter()        # D = prod|A_i| -> số secret
    marginal = Counter()             # (position, digit, D) -> số secret
    pattern_count = Counter()        # pattern -> số secret
    pattern_den = {}                 # pattern -> D (phải là hằng số)
    pattern_sizes = {}               # pattern -> tuple |A_i|
    pattern_conflict = []

    for code in secrets:
        den = 1
        sizes_here = []
        for i in range(N_POS):
            pre = code[:i]
            s = sizes.get(pre)
            if s is None:
                s = len(dc.allowed_digits(pre))
                sizes[pre] = s
            sizes_here.append(s)
            den *= s
        den_of_secret[den] += 1
        for i in range(N_POS):
            marginal[(i, code[i], den)] += 1

        pat = _collision_pattern(code)
        pattern_count[pat] += 1
        known = pattern_den.get(pat)
        if known is None:
            pattern_den[pat] = den
            pattern_sizes[pat] = tuple(sizes_here)
        elif known != den:
            pattern_conflict.append((pat, known, den))

    # Mẫu số tích luỹ của từng prefix: den[pre] = prod |A_j| với j < len(pre).
    prefix_den = {(): 1}
    by_len = defaultdict(list)
    for pre in sizes:
        by_len[len(pre)].append(pre)
    for i in range(1, N_POS):
        for pre in by_len[i]:
            head = pre[:-1]
            prefix_den[pre] = prefix_den[head] * sizes[head]

    return {
        "sizes": sizes,
        "prefix_den": prefix_den,
        "by_len": by_len,
        "den_of_secret": den_of_secret,
        "marginal": marginal,
        "pattern_count": pattern_count,
        "pattern_den": pattern_den,
        "pattern_sizes": pattern_sizes,
        "pattern_conflict": pattern_conflict,
    }


# =====================================================================
# analyse()
# =====================================================================

def analyse(secrets=None):
    """Trả dict kết quả JSON-serialisable, deterministic."""
    if secrets is None:
        secrets = list(dc.iter_valid_secrets())
    else:
        secrets = list(secrets)

    n_enum = len(secrets)
    n_distinct = len(set(secrets))
    n_invalid = sum(1 for c in secrets if not dc.is_valid_secret(c))

    n_dp, dp_states = count_secrets_by_dp()
    n_part, part_detail = count_secrets_by_partition()

    scan = _scan(secrets)
    den_of_secret = scan["den_of_secret"]
    total_count = sum(den_of_secret.values())

    # --- tổng xác suất phải đúng 1 -----------------------------------
    total_mass = sum((Fraction(c, d) for d, c in den_of_secret.items()),
                     Fraction(0))

    uniform_p = Fraction(1, total_count) if total_count else Fraction(0)

    distinct = []
    for d in sorted(den_of_secret):
        c = den_of_secret[d]
        distinct.append({
            "denominator": d,
            "p": _frac(Fraction(1, d)),
            "count": c,
            "mass": _frac(Fraction(c, d)),
            "p_over_uniform": _frac(Fraction(total_count, d)),
        })

    d_min = min(den_of_secret)          # mẫu số nhỏ nhất -> p lớn nhất
    d_max = max(den_of_secret)
    p_max = Fraction(1, d_min)
    p_min = Fraction(1, d_max)
    ratio = p_max / p_min

    tv = sum((abs(Fraction(1, d) - uniform_p) * c
              for d, c in den_of_secret.items()), Fraction(0)) / 2

    # --- phân phối |A_i| theo vị trí ----------------------------------
    sizes = scan["sizes"]
    prefix_den = scan["prefix_den"]
    allowed_by_pos = []
    expected_calls_pos = []
    for i in range(N_POS):
        per_size_prefixes = Counter()
        per_size_mass_den = defaultdict(Counter)
        cost_den = Counter()
        for pre in scan["by_len"][i]:
            s = sizes[pre]
            dpre = prefix_den[pre]
            per_size_prefixes[s] += 1
            per_size_mass_den[s][dpre] += 1
            cost_den[dpre * s] += 1

        rows = []
        for s in sorted(per_size_prefixes):
            mass = sum((Fraction(c, d) for d, c in per_size_mass_den[s].items()),
                       Fraction(0))
            rows.append({
                "size": s,
                "prefixes": per_size_prefixes[s],
                "prefix_mass": _frac(mass),
            })
        allowed_by_pos.append({"position": i, "rows": rows})

        e_i = sum((Fraction(DIGIT_BASE * c, d) for d, c in cost_den.items()),
                  Fraction(0))
        expected_calls_pos.append({"position": i, "expected_calls": _frac(e_i)})

    expected_calls = sum((Fraction(r["expected_calls"]["num"],
                                   r["expected_calls"]["den"])
                          for r in expected_calls_pos), Fraction(0))

    # --- marginal chữ số ----------------------------------------------
    marginal = scan["marginal"]
    sampler_marg = defaultdict(lambda: Fraction(0))
    uniform_marg = Counter()
    for (i, d, den), c in marginal.items():
        sampler_marg[(i, d)] += Fraction(c, den)
        uniform_marg[(i, d)] += c

    marg_rows = []
    max_dev_sampler = Fraction(0)
    max_dev_uniform = Fraction(0)
    for i in range(N_POS):
        digits = []
        for d in range(DIGIT_BASE):
            ps = sampler_marg[(i, d)]
            pu = (Fraction(uniform_marg[(i, d)], total_count)
                  if total_count else Fraction(0))
            dev_s = abs(ps - Fraction(1, DIGIT_BASE))
            dev_u = abs(pu - Fraction(1, DIGIT_BASE))
            max_dev_sampler = max(max_dev_sampler, dev_s)
            max_dev_uniform = max(max_dev_uniform, dev_u)
            digits.append({
                "digit": d,
                "sampler": _frac(ps),
                "uniform_count": uniform_marg[(i, d)],
                "uniform": _frac(pu),
            })
        marg_rows.append({"position": i, "digits": digits})

    # --- bias theo cấu trúc -------------------------------------------
    pattern_count = scan["pattern_count"]
    pattern_den = scan["pattern_den"]
    pattern_sizes = scan["pattern_sizes"]

    by_pairs_count = Counter()
    by_pairs_mass = defaultdict(lambda: Fraction(0))
    pattern_rows = []
    for pat in sorted(pattern_count, key=lambda p: (len(p), p)):
        c = pattern_count[pat]
        d = pattern_den[pat]
        mass = Fraction(c, d)
        by_pairs_count[len(pat)] += c
        by_pairs_mass[len(pat)] += mass
        pattern_rows.append({
            "pattern": [list(pair) for pair in pat],
            "pattern_text": ("".join("(%d,%d)" % pair for pair in pat)
                             or "(khong co cap lap)"),
            "pairs": len(pat),
            "count": c,
            "denominator": d,
            "allowed_sizes": list(pattern_sizes[pat]),
            "p": _frac(Fraction(1, d)),
            "mass": _frac(mass),
            "p_over_uniform": _frac(Fraction(total_count, d)),
        })

    group_rows = []
    for k in sorted(by_pairs_count):
        c = by_pairs_count[k]
        mass = by_pairs_mass[k]
        group_rows.append({
            "pairs": k,
            "distinct_digits": N_POS - k,
            "count": c,
            "uniform_share": _frac(Fraction(c, total_count)),
            "sampler_mass": _frac(mass),
            "mean_p": _frac(mass / c),
            "mean_p_over_uniform": _frac(mass / c * total_count),
        })

    hypothesis = Fraction(9, 7)
    results = {
        "meta": {
            "source": "backend/gameboard.cpp:471-482",
            "model_module": "tools/analysis/digitcode.py",
            "secret_length": N_POS,
            "digit_base": DIGIT_BASE,
            "deterministic": True,
        },
        "total_secrets": {
            "by_enumeration": n_enum,
            "by_dp": n_dp,
            "by_partition": n_part,
            "all_agree": (n_enum == n_dp == n_part),
            "distinct_secrets_in_input": n_distinct,
            "invalid_secrets_in_input": n_invalid,
            "dp_states_visited": dp_states,
            "partition_detail": part_detail,
        },
        "probability": {
            "total_mass": _frac(total_mass),
            "total_mass_is_one": (total_mass == 1),
            "distinct_values": distinct,
            "n_distinct_values": len(distinct),
            "p_max": _frac(p_max),
            "p_min": _frac(p_min),
            "ratio_max_min": _frac(ratio),
            "uniform_p": _frac(uniform_p),
            "p_max_over_uniform": _frac(p_max / uniform_p) if uniform_p else None,
            "p_min_over_uniform": _frac(p_min / uniform_p) if uniform_p else None,
            "total_variation_distance": _frac(tv),
            "allowed_sizes_by_position": allowed_by_pos,
        },
        "hypothesis_9_over_7": {
            "claim": "p_max / p_min ~= 9/7",
            "claimed_value": _frac(hypothesis),
            "actual_value": _frac(ratio),
            "holds": (ratio == hypothesis),
            "absolute_error": _frac(abs(ratio - hypothesis)),
        },
        "sampler_cost": {
            "expected_bounded_calls": _frac(expected_calls),
            "per_position": expected_calls_pos,
            "lower_bound_trivial": N_POS,
        },
        "marginals": {
            "positions": marg_rows,
            "sampler_max_deviation_from_uniform_digit": _frac(max_dev_sampler),
            "uniform_max_deviation_from_uniform_digit": _frac(max_dev_uniform),
            "sampler_is_digit_uniform": (max_dev_sampler == 0),
            "set_is_digit_uniform": (max_dev_uniform == 0),
        },
        "structure_bias": {
            "by_pair_count": group_rows,
            "by_pattern": pattern_rows,
            "pattern_denominator_conflicts": [
                {"pattern": [list(p) for p in pat], "seen": a, "then": b}
                for pat, a, b in scan["pattern_conflict"]
            ],
        },
    }

    json.dumps(results)  # hợp đồng: kết quả phải JSON-serialisable
    return results


# =====================================================================
# format_report()
# =====================================================================

def _rule(char="-", width=72):
    return char * width


def format_report(results):
    """Trả str báo cáo plain-text deterministic."""
    out = []
    add = out.append

    add(_rule("="))
    add("DIGITCODE - DAC TRUNG HOA REJECTION SAMPLER SINH SECRET")
    add("Nguon: %s | Mo hinh: %s"
        % (results["meta"]["source"], results["meta"]["model_module"]))
    add(_rule("="))

    # ---- 1 ----------------------------------------------------------
    tot = results["total_secrets"]
    add("")
    add("1. TONG SO SECRET HOP LE")
    add(_rule())
    add("  Liet ke   (dc.iter_valid_secrets)      : %d" % tot["by_enumeration"])
    add("  DP vi tri (transfer matrix, %3d state) : %d"
        % (tot["dp_states_visited"], tot["by_dp"]))
    add("  Phan hoach mau (khong theo vi tri)     : %d" % tot["by_partition"])
    add("  => Ba phuong phap %s"
        % ("KHOP NHAU." if tot["all_agree"] else "*** KHONG KHOP ***"))
    add("  Input: %d secret, %d phan biet, %d khong hop le."
        % (tot["by_enumeration"], tot["distinct_secrets_in_input"],
           tot["invalid_secrets_in_input"]))
    add("")
    add("  Chi tiet duong phan hoach mau:")
    add("    Do thi rang buoc (C2/C3) = luoi 2x3, canh: %s"
        % ", ".join("%d-%d" % e for e in tot["partition_detail"]["edges"]))
    add("    tong = sum_m M(m) * (10)_(6-m), M(m) = so matching co m cua do thi bu")
    add("    %-6s %-10s %-8s %-12s %s"
        % ("m", "M(m)", "so khoi", "(10)_k", "so hang"))
    for t in tot["partition_detail"]["terms"]:
        add("    %-6d %-10d %-8d %-12d %d"
            % (t["pairs"], t["matchings"], t["blocks"], t["falling_10_k"],
               t["term"]))

    # ---- 2 ----------------------------------------------------------
    prob = results["probability"]
    add("")
    add("2. PHAN PHOI XAC SUAT CHINH XAC CUA SAMPLER")
    add(_rule())
    add("  Moi vi tri duoc boc lai toi khi hop le => chu so tai vi tri i phan bo")
    add("  DEU tren A_i(prefix), nen P(code) = prod_i 1/|A_i|.  Tat ca so lieu")
    add("  duoi day tinh bang fractions.Fraction, khong dung float.")
    add("")
    add("  Tong xac suat = %s  -> %s"
        % (prob["total_mass"]["exact"],
           "DUNG BANG 1 (exact)." if prob["total_mass_is_one"]
           else "*** KHAC 1 ***"))
    add("")
    add("  Cac gia tri xac suat phan biet (%d gia tri):"
        % prob["n_distinct_values"])
    add("    %-10s %-22s %-9s %-16s %s"
        % ("mau so D", "p = 1/D", "so secret", "khoi luong", "p / p_uniform"))
    for row in prob["distinct_values"]:
        add("    %-10d %-22s %-9d %-16s %s"
            % (row["denominator"], row["p"]["exact"], row["count"],
               row["mass"]["exact"], row["p_over_uniform"]["exact"]))
    add("")
    add("  p_max        = %s  (~ %.6e)"
        % (prob["p_max"]["exact"], prob["p_max"]["float"]))
    add("  p_min        = %s  (~ %.6e)"
        % (prob["p_min"]["exact"], prob["p_min"]["float"]))
    add("  p_max/p_min  = %s  (~ %.6f)"
        % (prob["ratio_max_min"]["exact"], prob["ratio_max_min"]["float"]))
    add("")
    add("  Uniform tren tap hop le: p_uniform = %s (~ %.6e)"
        % (prob["uniform_p"]["exact"], prob["uniform_p"]["float"]))
    add("  p_max / p_uniform = %s (~ %.6f)"
        % (prob["p_max_over_uniform"]["exact"],
           prob["p_max_over_uniform"]["float"]))
    add("  p_min / p_uniform = %s (~ %.6f)"
        % (prob["p_min_over_uniform"]["exact"],
           prob["p_min_over_uniform"]["float"]))
    add("  Total variation distance toi uniform = %s (~ %.6f)"
        % (prob["total_variation_distance"]["exact"],
           prob["total_variation_distance"]["float"]))
    add("")
    add("  Phan phoi |A_i| theo vi tri (so prefix do dai i cho moi gia tri,")
    add("  kem khoi luong xac suat cua nhom prefix do):")
    add("    %-4s %-8s %-12s %s" % ("i", "|A_i|", "so prefix", "khoi luong prefix"))
    for block in prob["allowed_sizes_by_position"]:
        for row in block["rows"]:
            add("    %-4d %-8d %-12d %s"
                % (block["position"], row["size"], row["prefixes"],
                   row["prefix_mass"]["exact"]))

    # ---- 3 ----------------------------------------------------------
    hyp = results["hypothesis_9_over_7"]
    add("")
    add("3. KIEM TRA HYPOTHESIS CUA AUDIT TRUOC")
    add(_rule())
    add("  Hypothesis      : %s" % hyp["claim"])
    add("  Gia tri gia dinh: %s (~ %.6f)"
        % (hyp["claimed_value"]["exact"], hyp["claimed_value"]["float"]))
    add("  Gia tri thuc te : %s (~ %.6f)"
        % (hyp["actual_value"]["exact"], hyp["actual_value"]["float"]))
    add("  Sai lech        : %s (~ %.6f)"
        % (hyp["absolute_error"]["exact"], hyp["absolute_error"]["float"]))
    add("  KET LUAN        : Hypothesis %s."
        % ("DUNG" if hyp["holds"] else "SAI"))

    # ---- 4 ----------------------------------------------------------
    cost = results["sampler_cost"]
    add("")
    add("4. HIEU SUAT SAMPLER (so lan goi bounded(10))")
    add(_rule())
    add("  Tai vi tri i, so lan boc la bien hinh hoc voi xac suat thanh cong")
    add("  |A_i|/10, ky vong 10/|A_i|.  Lay ky vong theo phan phoi prefix:")
    add("    %-4s %-24s %s" % ("i", "E[so lan boc]", "~ float"))
    for row in cost["per_position"]:
        add("    %-4d %-24s %.6f"
            % (row["position"], row["expected_calls"]["exact"],
               row["expected_calls"]["float"]))
    add("  TONG E[bounded(10)] = %s (~ %.6f) cho moi secret."
        % (cost["expected_bounded_calls"]["exact"],
           cost["expected_bounded_calls"]["float"]))
    add("  Can duoi tam thuong (khong bao gio bi tu choi) = %d."
        % cost["lower_bound_trivial"])

    # ---- 5 ----------------------------------------------------------
    marg = results["marginals"]
    add("")
    add("5. MARGINAL CHU SO TAI TUNG VI TRI")
    add(_rule())
    add("  Cot 'sampler' dung trong so xac suat that; cot 'uniform' dem deu")
    add("  tren tap secret hop le.")
    add("    %-4s %-7s %-14s %-10s %s"
        % ("i", "chu so", "sampler", "so secret", "uniform"))
    for block in marg["positions"]:
        for row in block["digits"]:
            add("    %-4d %-7d %-14s %-10d %s"
                % (block["position"], row["digit"], row["sampler"]["exact"],
                   row["uniform_count"], row["uniform"]["exact"]))
    add("")
    add("  Do lech lon nhat so voi 1/10 - sampler : %s"
        % marg["sampler_max_deviation_from_uniform_digit"]["exact"])
    add("  Do lech lon nhat so voi 1/10 - uniform : %s"
        % marg["uniform_max_deviation_from_uniform_digit"]["exact"])
    add("  => Sampler %s lech theo chu so; tap hop le %s lech theo chu so."
        % ("KHONG" if marg["sampler_is_digit_uniform"] else "CO",
           "KHONG" if marg["set_is_digit_uniform"] else "CO"))
    add("  (Luat C1/C2/C3 bat bien duoi moi hoan vi 10 chu so, nen ca hai phan")
    add("   phoi deu bat bien theo hoan vi => marginal moi vi tri dung 1/10.)")

    # ---- 6 ----------------------------------------------------------
    bias = results["structure_bias"]
    add("")
    add("6. BIAS THEO CAU TRUC")
    add(_rule())
    add("  Nhom theo so cap chu so lap (0 cap = 6 chu so phan biet):")
    add("    %-6s %-10s %-9s %-16s %-22s %s"
        % ("so cap", "chu so pb", "so secret", "ty le uniform", "khoi luong sampler",
           "p_tb / p_uniform"))
    for row in bias["by_pair_count"]:
        add("    %-6d %-10d %-9d %-16s %-22s %s (~ %.6f)"
            % (row["pairs"], row["distinct_digits"], row["count"],
               row["uniform_share"]["exact"], row["sampler_mass"]["exact"],
               row["mean_p_over_uniform"]["exact"],
               row["mean_p_over_uniform"]["float"]))
    add("")
    add("  Chi tiet theo MAU va cham (pattern) - xac suat chi phu thuoc pattern,")
    add("  khong phu thuoc chu so cu the:")
    add("    %-22s %-6s %-9s %-20s %-10s %s"
        % ("pattern", "so cap", "so secret", "|A_0..A_5|", "D", "p/p_uniform"))
    for row in bias["by_pattern"]:
        add("    %-22s %-6d %-9d %-20s %-10d %s"
            % (row["pattern_text"], row["pairs"], row["count"],
               ",".join(str(s) for s in row["allowed_sizes"]),
               row["denominator"], row["p_over_uniform"]["exact"]))
    if bias["pattern_denominator_conflicts"]:
        add("  *** CANH BAO: pattern co nhieu mau so khac nhau: %d truong hop ***"
            % len(bias["pattern_denominator_conflicts"]))
    else:
        add("  (Kiem tra: moi pattern chi ung voi DUNG MOT mau so D.)")

    add("")
    add(_rule("="))
    return "\n".join(out)


if __name__ == "__main__":
    print(format_report(analyse()))
