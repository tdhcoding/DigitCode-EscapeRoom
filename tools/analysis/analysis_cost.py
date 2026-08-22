#!/usr/bin/env python3
"""U3 — Chi phí clue và difficulty proxies cho issue #6.

Tách bạch ba khái niệm, và KHÔNG gọi heuristic là optimum:

* **fixed clue set** (non-adaptive): chọn trước một tập câu, không nhìn đáp án;
* **adaptive strategy**: chọn câu sau khi thấy đáp án trước đó;
* **heuristic**: chiến lược tham lam cụ thể — chỉ cho upper bound.

Mọi con số đều được gắn nhãn EXACT / LOWER BOUND / UPPER BOUND / HEURISTIC.
Deterministic: RNG duy nhất được seed cố định bằng `REMOVAL_SEED`.
"""

import math
import os
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from operator import itemgetter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import digitcode as dc  # noqa: E402

REMOVAL_SEED = 20260822
REMOVAL_TRIALS = 40
LOWER_BOUND_NODE_BUDGET = 40000

# Luật điểm của native engine.
START_POINTS = 100                # gameboard.cpp:30, :445
CLUE_COST = dc.CLUE_COST_POINTS   # 5, gameboard.cpp:266,311,341,620
DECAY_SECONDS = 60                # gameboard.cpp:99 — 1 điểm mỗi 60 giây


# =====================================================================
# Hạ tầng: bảng đáp án + đếm lớp nhanh
# =====================================================================

def _build_table(secrets):
    qids = dc.BASE_QUESTION_IDS
    return qids, [tuple(dc.answer(c, q) for q in qids) for c in secrets]


def _classes(table, idx):
    """Số lớp mà tập câu hỏi `idx` (tuple chỉ số cột) chia tập secret."""
    if len(idx) == 1:
        return len(set(map(itemgetter(idx[0]), table)))
    return len(set(map(itemgetter(*idx), table)))


# =====================================================================
# A. Fixed clue set (non-adaptive)
# =====================================================================

def _fixed_clue_set(qids, table, target):
    n = len(qids)
    everything = tuple(range(n))
    ranges = [len(set(map(itemgetter(i), table))) for i in range(n)]

    # A1 — câu BẮT BUỘC: bỏ riêng nó ra là đã mất thông tin.
    # Vì họ tập hợp lệ là upward-closed, mọi tập hợp lệ phải chứa toàn bộ
    # tập này. Đây là kết quả EXACT, không phải bound.
    mandatory = []
    removable = []
    for i in range(n):
        rest = tuple(j for j in everything if j != i)
        (removable if _classes(table, rest) == target else mandatory).append(i)

    # A2 — LOWER BOUND chặt chẽ.
    #
    # Mọi tập hợp lệ có dạng M ∪ X với X ⊆ removable, và
    #     classes(M ∪ X) <= classes(M) * classes(X).
    # Nên nếu KHÔNG e-subset X nào đạt classes(X) >= target/classes(M) thì
    # |X| = e là bất khả thi.  Ta loại từng cỡ e một, dùng chặn tích
    # prod(range) >= classes(X) để chỉ phải đo các ứng viên còn khả năng.
    #
    # Một cỡ e chỉ được TUYÊN BỐ bất khả thi khi đã duyệt HẾT ứng viên của
    # nó; nếu chạm trần công sức thì dừng và báo bound đạt được tới đó.
    from itertools import combinations
    classes_m = _classes(table, tuple(mandatory)) if mandatory else 1
    need = Fraction(target, classes_m)
    ladder = []
    extra = 1
    while extra <= len(removable):
        cands = []
        for X in combinations(removable, extra):
            prod = 1
            for i in X:
                prod *= ranges[i]
            if prod >= need:
                cands.append(X)
        best = 0
        exhausted = True
        for seen, X in enumerate(cands):
            if seen >= LOWER_BOUND_NODE_BUDGET:
                exhausted = False
                break
            c = _classes(table, X)
            if c > best:
                best = c
            if best >= need:
                break
        ruled_out = exhausted and best < need
        ladder.append({"extra_questions": extra, "candidates": len(cands),
                       "best_classes": best, "ruled_out": ruled_out,
                       "fully_enumerated": exhausted})
        if not ruled_out:
            break
        extra += 1
    lower_bound = len(mandatory) + extra

    # A3 — UPPER BOUND: bỏ tham lam theo nhiều thứ tự ngẫu nhiên có seed.
    #      Mỗi lần chạy cho một tập hợp lệ TỐI TIỂU THEO NGHĨA BAO HÀM
    #      (không bỏ thêm được câu nào), nhưng chưa chắc nhỏ nhất tuyệt đối.
    import random
    rnd = random.Random(REMOVAL_SEED)
    best = set(everything)
    sizes = []
    for _ in range(REMOVAL_TRIALS):
        order = list(removable)
        rnd.shuffle(order)
        keep = set(everything)
        for i in order:
            trial = tuple(sorted(keep - {i}))
            if _classes(table, trial) == target:
                keep.discard(i)
        sizes.append(len(keep))
        if len(keep) < len(best):
            best = set(keep)
    upper_bound = len(best)

    return {
        "target_classes": target,
        "unique_identification_possible": False,
        "question_ranges": dict(zip(qids, ranges)),
        "mandatory": [qids[i] for i in mandatory],
        "mandatory_count": len(mandatory),
        "individually_removable": [qids[i] for i in removable],
        "classes_of_mandatory_alone": classes_m,
        "lower_bound_ladder": ladder,
        "lower_bound_needed_classes": float(need),
        "lower_bound_questions": lower_bound,
        "lower_bound_points": lower_bound * CLUE_COST,
        "upper_bound_questions": upper_bound,
        "upper_bound_points": upper_bound * CLUE_COST,
        "upper_bound_set": sorted(qids[i] for i in best),
        "minimal_set_sizes_found": sorted(Counter(sizes).items()),
        "trials": REMOVAL_TRIALS,
        "seed": REMOVAL_SEED,
    }


# =====================================================================
# B. Adaptive — cây quyết định tham lam trên TOÀN BỘ tập secret
# =====================================================================

def _greedy_tree(qids, table, full_class):
    """Dựng cây quyết định tham lam; trả độ sâu của từng secret.

    Tiêu chí tham lam: chọn câu làm NHỎ NHẤT lớp con lớn nhất (hướng
    worst-case), hoà thì chọn câu chia được nhiều lớp hơn.

    Dừng ở một nút khi mọi ứng viên còn lại cùng một lớp collision — lúc đó
    không câu hỏi nào tách chúng được nữa (xem module signature).
    """
    n = len(qids)
    rows = [(i, table[i], full_class[i]) for i in range(len(table))]

    depth = [0] * len(table)
    first_at_most = {1: [None] * len(table), 2: [None] * len(table),
                     4: [None] * len(table), 8: [None] * len(table)}

    def record(bucket, d):
        size = len(bucket)
        for thr in (1, 2, 4, 8):
            if size <= thr:
                for _i, _row, _fc in bucket:
                    if first_at_most[thr][_i] is None:
                        first_at_most[thr][_i] = d

    record(rows, 0)
    level = [rows]
    d = 0
    chosen_at_root = None
    while level:
        d += 1
        nxt = []
        for node in level:
            best_q, best_key = None, None
            for q in range(n):
                counts = Counter(row[1][q] for row in node)
                key = (max(counts.values()), -len(counts))
                if best_key is None or key < best_key:
                    best_key, best_q = key, q
            if d == 1:
                chosen_at_root = qids[best_q]
            buckets = defaultdict(list)
            for row in node:
                buckets[row[1][best_q]].append(row)
            for bucket in buckets.values():
                for i, _row, _fc in bucket:
                    depth[i] = d
                record(bucket, d)
                if len(set(fc for _i, _row, fc in bucket)) > 1:
                    nxt.append(bucket)
        level = nxt
    return depth, first_at_most, chosen_at_root


def _percentiles(values, weights=None):
    pairs = sorted(Counter(values).items())
    total = sum(c for _v, c in pairs)
    out = {}
    for p in (50, 90, 99, 100):
        cut = total * p / 100.0
        acc = 0
        for v, c in pairs:
            acc += c
            if acc >= cut:
                out["p%d" % p] = v
                break
    out["mean"] = sum(v * c for v, c in pairs) / float(total)
    return out


# =====================================================================
# C. Ngân sách điểm
# =====================================================================

def _points_budget():
    rows = []
    for minutes in (3, 6, 10, 15, 20):
        decay = (minutes * 60) // DECAY_SECONDS
        # Sống sót ở nhịp đồng hồ đó cần points >= 1.
        max_purchases = (START_POINTS - 1 - decay) // CLUE_COST
        rows.append({
            "minutes": minutes,
            "time_decay_points": decay,
            "max_purchases": max_purchases,
            "points_spent": max_purchases * CLUE_COST,
        })
    return rows


# =====================================================================
def analyse(secrets=None):
    if secrets is None:
        secrets = list(dc.iter_valid_secrets())
    qids, table = _build_table(secrets)
    target = len(set(table))

    # id lớp collision của từng secret (dưới TOÀN BỘ clue)
    class_id = {}
    full_class = []
    for row in table:
        cid = class_id.setdefault(row, len(class_id))
        full_class.append(cid)
    class_sizes = Counter(full_class)

    fixed = _fixed_clue_set(qids, table, target)

    depth, first_at_most, root_q = _greedy_tree(qids, table, full_class)
    probs = [dc.secret_probability(c) for c in secrets]

    max_branching = max(fixed["question_ranges"].values())
    adaptive_lb = int(math.ceil(math.log(target, max_branching)))

    weighted_mean = float(sum(p * d for p, d in zip(probs, depth)))
    depth_hist = sorted(Counter(depth).items())

    thresholds = {}
    for thr, arr in sorted(first_at_most.items()):
        vals = [v for v in arr if v is not None]
        thresholds[thr] = {
            "worst_case": max(vals),
            "mean": sum(vals) / float(len(vals)),
            "unreachable": len(arr) - len(vals),
            "histogram": sorted(Counter(vals).items()),
        }

    # D — difficulty proxies
    opening = tuple(qids.index(q) for q in ("Q3:B", "Q3:E", "Q3:H"))
    opening_buckets = Counter(map(itemgetter(*opening), table))
    residual_bits = []
    for row in table:
        residual_bits.append(math.log(opening_buckets[itemgetter(*opening)(row)], 2))

    proxies = {
        "greedy_depth": {"histogram": depth_hist,
                         "uniform": _percentiles(depth),
                         "sampler_weighted_mean": weighted_mean},
        "collision_class_size": sorted(Counter(class_sizes[c] for c in full_class).items()),
        "residual_bits_after_opening_BEH": {
            "opening": ["Q3:B", "Q3:E", "Q3:H"],
            "classes": len(opening_buckets),
            "min": min(residual_bits), "max": max(residual_bits),
            "mean": sum(residual_bits) / float(len(residual_bits)),
            "largest_bucket": max(opening_buckets.values()),
        },
        "sampler_probability": {
            "distinct_values": len(set(probs)),
            "max_over_min": str(max(probs) / min(probs)),
        },
    }

    return {
        "valid_secrets": len(secrets),
        "max_attainable_classes": target,
        "unresolvable_pairs": sum(1 for _c, s in class_sizes.items() if s > 1),
        "fixed_clue_set": fixed,
        "adaptive": {
            "max_branching_factor": max_branching,
            "lower_bound_questions": adaptive_lb,
            "lower_bound_points": adaptive_lb * CLUE_COST,
            "greedy_root_question": root_q,
            "greedy_worst_case": max(depth),
            "greedy_stats_uniform": _percentiles(depth),
            "greedy_mean_sampler_weighted": weighted_mean,
            "greedy_depth_histogram": depth_hist,
            "narrow_to_at_most": thresholds,
        },
        "points_budget": _points_budget(),
        "difficulty_proxies": proxies,
    }


def _bar(title):
    return "\n" + "=" * 74 + "\n" + title + "\n" + "=" * 74


def format_report(r):
    L = []
    A = L.append
    A(_bar("U3 — CHI PHÍ CLUE VÀ DIFFICULTY PROXIES"))
    A("Secret hợp lệ                         : %d" % r["valid_secrets"])
    A("Số lớp TỐI ĐA đạt được bằng mọi clue  : %d  [EXACT]" % r["max_attainable_classes"])
    A("Cặp không bao giờ tách được           : %d" % r["unresolvable_pairs"])
    A("=> Xác định DUY NHẤT là BẤT KHẢ THI. Mục tiêu đúng của mọi chiến lược")
    A("   là thu hẹp về lớp collision, không phải về một secret.")

    f = r["fixed_clue_set"]
    A(_bar("A. FIXED CLUE SET (non-adaptive)"))
    A("Câu BẮT BUỘC (%d)  [EXACT — bỏ riêng câu nào cũng mất thông tin]:" % f["mandatory_count"])
    A("  " + ", ".join(f["mandatory"]))
    A("Số lớp của riêng tập bắt buộc         : %d" % f["classes_of_mandatory_alone"])
    A("")
    A("LOWER BOUND  : %2d câu = %3d điểm   [EXACT LOWER BOUND]" %
      (f["lower_bound_questions"], f["lower_bound_points"]))
    A("               = |bắt buộc| + cỡ nhỏ nhất của X chưa bị loại")
    A("  Cần classes(X) >= %.2f. Loại dần theo cỡ:" % f["lower_bound_needed_classes"])
    for row in f["lower_bound_ladder"]:
        A("    |X|=%d : %6d ứng viên qua chặn tích, đạt tối đa %6d lớp -> %s"
          % (row["extra_questions"], row["candidates"], row["best_classes"],
             "BẤT KHẢ THI (đã duyệt hết)" if row["ruled_out"]
             else ("chưa loại được" if row["fully_enumerated"] else "chạm trần công sức")))
    A("UPPER BOUND  : %2d câu = %3d điểm   [UPPER BOUND — %d lần bỏ tham lam, seed %d]" %
      (f["upper_bound_questions"], f["upper_bound_points"], f["trials"], f["seed"]))
    A("  tập tìm được: " + ", ".join(f["upper_bound_set"]))
    A("  cỡ các tập tối tiểu theo bao hàm gặp được: %s" %
      ", ".join("%d câu x%d" % (s, c) for s, c in f["minimal_set_sizes_found"]))
    A("KHOẢNG CHƯA ĐÓNG: [%d, %d] câu. Upper bound KHÔNG được coi là optimum:" %
      (f["lower_bound_questions"], f["upper_bound_questions"]))
    A("  bỏ tham lam chỉ cho tập tối tiểu theo bao hàm, không phải nhỏ nhất tuyệt đối.")

    a = r["adaptive"]
    A(_bar("B. ADAPTIVE STRATEGY"))
    A("Nhánh tối đa của một câu hỏi          : %d" % a["max_branching_factor"])
    A("LOWER BOUND  : %2d câu = %3d điểm   [EXACT LOWER BOUND: %d^d >= %d]" %
      (a["lower_bound_questions"], a["lower_bound_points"],
       a["max_branching_factor"], r["max_attainable_classes"]))
    A("UPPER BOUND  : %2d câu = %3d điểm   [HEURISTIC — greedy minimax trên TOÀN BỘ tập]" %
      (a["greedy_worst_case"], a["greedy_worst_case"] * CLUE_COST))
    A("  câu mở đầu greedy chọn            : %s" % a["greedy_root_question"])
    st = a["greedy_stats_uniform"]
    A("  trung bình (uniform)              : %.3f câu" % st["mean"])
    A("  trung bình (phân phối sampler)    : %.3f câu" % a["greedy_mean_sampler_weighted"])
    A("  phân vị p50/p90/p99/max           : %d / %d / %d / %d" %
      (st["p50"], st["p90"], st["p99"], st["p100"]))
    A("  histogram độ sâu                  : %s" %
      ", ".join("%d:%d" % kv for kv in a["greedy_depth_histogram"]))
    A("")
    A("Số lần mua để thu hẹp còn <= k ứng viên (greedy, worst-case / trung bình):")
    for thr, d in sorted(a["narrow_to_at_most"].items()):
        A("  <= %-2d ứng viên : worst %2d, trung bình %.2f, không bao giờ đạt được: %d secret"
          % (thr, d["worst_case"], d["mean"], d["unreachable"]))

    A(_bar("C. NGÂN SÁCH ĐIỂM (100 điểm, 5/lần mua, -1 mỗi 60 giây)"))
    A("  phút   hao mòn   mua tối đa   điểm đã tiêu")
    for row in r["points_budget"]:
        A("  %4d   %7d   %10d   %12d" %
          (row["minutes"], row["time_decay_points"], row["max_purchases"], row["points_spent"]))
    A("  (điều kiện sống: points >= 1 tại nhịp đồng hồ; gameboard.cpp:106)")

    p = r["difficulty_proxies"]
    A(_bar("D. DIFFICULTY PROXIES (đầu vào cho ticket #9)"))
    A("1) Độ sâu greedy adaptive theo từng secret")
    A("   histogram: %s" % ", ".join("%d:%d" % kv for kv in p["greedy_depth"]["histogram"]))
    A("2) Cỡ lớp collision của secret (1 = xác định được, 2 = phải đoán 50/50)")
    A("   %s" % ", ".join("cỡ %d: %d secret" % kv for kv in p["collision_class_size"]))
    o = p["residual_bits_after_opening_BEH"]
    A("3) Bit còn lại sau opening cố định %s" % "+".join(o["opening"]))
    A("   số lớp %d, lớp lớn nhất %d ứng viên, bit còn lại min %.2f / tb %.2f / max %.2f"
      % (o["classes"], o["largest_bucket"], o["min"], o["mean"], o["max"]))
    A("4) Xác suất sampler sinh ra secret: %s giá trị phân biệt, max/min = %s"
      % (p["sampler_probability"]["distinct_values"], p["sampler_probability"]["max_over_min"]))
    A("")
    stuck = dict(p["collision_class_size"]).get(2, 0)
    A("Proxy (2) phân tách mạnh nhất về mặt eligibility: %d secret nằm trong lớp" % stuck)
    A("cỡ 2 — suy luận thuần tuý dừng ở 2 ứng viên, phải đoán 50/50.")
    A("")
    A("Lưu ý so sánh với ngân sách: upper bound cho tập clue CỐ ĐỊNH là %d điểm," %
      r["fixed_clue_set"]["upper_bound_points"])
    A("vượt quá 100 điểm khởi đầu — chiến lược non-adaptive không mua nổi.")
    return "\n".join(L)


if __name__ == "__main__":
    print(format_report(analyse()))
