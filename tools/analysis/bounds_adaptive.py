"""Thu hẹp khoảng ADAPTIVE `[8, 16]` của #6.

Ba chế độ:

* `lb1` / `lb2` / `lb3` — **chặn dưới**. Khai triển minimax `d` mức đầu tiên
  (min trên mọi clue, max trên mọi nhánh), lá dùng chặn đếm.

  Chặn đếm: một clue chia được tối đa `b` nhánh với `b` là số đáp án **thực sự
  đạt được** của nó trên pool. `d` clue cho tối đa tích của `d` branching lớn
  nhất **còn lại** (đã trừ clue đã hỏi trên đường đi). Đây là chặn ĐÚNG cho
  mọi chiến lược, không giả định gì.

  #6 dùng `6^d >= 465.034` và ra 8. Nhưng chỉ **ba** clue có 6 đáp án
  (`Q3:B/E/H`); phần còn lại nhỏ hơn, nên chặn thật chặt hơn.

* `greedy` — **chặn trên**. Dựng lại cây greedy minimax của #6 (mỗi bước chọn
  clue làm nhỏ nhất lớp con lớn nhất) và in histogram độ sâu, để kiểm chứng
  con số 16 thay vì kế thừa nó.

Chạy: `python3 -u tools/analysis/bounds_adaptive.py <mode> [checkpoint.txt]`
"""

import itertools
import sys
import time
from bisect import bisect_left
from collections import Counter

import analysis_bounds as ab

T0 = time.time()


def log(fh, msg):
    line = "[%7.1fs] %s" % (time.time() - T0, msg)
    print(line)
    if fh:
        fh.write(line + "\n")
        fh.flush()


def reduce_to_classes(cols, class_id, n_classes):
    """Một đại diện cho mỗi lớp. Sau bước này |block| == số lớp của block."""
    seen = bytearray(n_classes)
    keep = []
    for i in range(len(class_id)):
        c = class_id[i]
        if not seen[c]:
            seen[c] = 1
            keep.append(i)
    return [bytes(c[i] for i in keep) for c in cols]


def cumprods(doms, exclude):
    """Tích luỹ tiến của các branching lớn nhất, bỏ những clue đã hỏi."""
    rest = sorted((d for j, d in enumerate(doms) if j not in exclude),
                  reverse=True)
    out = []
    p = 1
    for b in rest:
        p *= b
        out.append(p)
    return out


def base_from(cum, n):
    """Số clue tối thiểu để tích branching phủ được `n` lớp."""
    if n <= 1:
        return 0
    d = bisect_left(cum, n)
    return d + 1 if d < len(cum) else float("inf")


# --- Chặn dưới -----------------------------------------------------------

def lower_bound(cols, doms, depth, out):
    n = len(cols[0])
    nq = len(cols)
    cum0 = cumprods(doms, ())
    root_base = base_from(cum0, n)
    log(out, "chặn đếm tại gốc (n=%d): %d clue" % (n, root_base))
    if depth == 0:
        return root_base

    cum1 = {j: cumprods(doms, (j,)) for j in range(nq)}
    cum2 = {}
    cum3 = {}

    # Mức 1: kích thước block sau clue đầu tiên.
    size1 = {}
    for j in range(nq):
        size1[j] = Counter(cols[j])
    log(out, "mức 1 xong")

    if depth == 1:
        best = float("inf")
        for j in range(nq):
            if len(size1[j]) <= 1:
                continue
            worst = max(base_from(cum1[j], s) for s in size1[j].values())
            best = min(best, 1 + worst)
        return max(root_base, best)

    # Mức 2: kích thước block sau hai clue.
    size2 = {}
    for j, k in itertools.combinations(range(nq), 2):
        c = Counter(zip(cols[j], cols[k]))
        size2[(j, k)] = c
        cum2[(j, k)] = cumprods(doms, (j, k))
    log(out, "mức 2 xong (%d cặp)" % len(size2))

    def sz2(j, k, a, b):
        if j < k:
            return size2[(j, k)].get((a, b), 0)
        return size2[(k, j)].get((b, a), 0)

    def cm2(j, k):
        return cum2[(j, k)] if j < k else cum2[(k, j)]

    if depth == 2:
        best = float("inf")
        for j in range(nq):
            if len(size1[j]) <= 1:
                continue
            worst_a = 0
            for a, sa in size1[j].items():
                v_k = float("inf")
                for k in range(nq):
                    if k == j:
                        continue
                    w = 0
                    for b in range(7):
                        s = sz2(j, k, a, b)
                        if s:
                            w = max(w, base_from(cm2(j, k), s))
                    if w:
                        v_k = min(v_k, w)
                v = max(base_from(cum1[j], sa), 1 + v_k)
                worst_a = max(worst_a, v)
            best = min(best, 1 + worst_a)
        return max(root_base, best)

    # depth == 3
    best3 = {}
    done = 0
    for tri in itertools.combinations(range(nq), 3):
        c = Counter(zip(cols[tri[0]], cols[tri[1]], cols[tri[2]]))
        cum = cumprods(doms, tri)
        cum3[tri] = cum
        for perm in itertools.permutations((0, 1, 2)):
            j, k, l = tri[perm[0]], tri[perm[1]], tri[perm[2]]
            agg = {}
            for key, s in c.items():
                a, b = key[perm[0]], key[perm[1]]
                v = base_from(cum, s)
                if v > agg.get((a, b), -1):
                    agg[(a, b)] = v
            for (a, b), v in agg.items():
                cur = best3.get((j, a, k, b))
                if cur is None or v < cur:
                    best3[(j, a, k, b)] = v
        done += 1
        if done % 500 == 0:
            log(out, "  bộ ba %d/%d" % (done, 4960))
    log(out, "mức 3 xong")

    best = float("inf")
    for j in range(nq):
        if len(size1[j]) <= 1:
            continue
        worst_a = 0
        for a, sa in size1[j].items():
            v_k = float("inf")
            for k in range(nq):
                if k == j:
                    continue
                w = 0
                for b in range(7):
                    s = sz2(j, k, a, b)
                    if not s:
                        continue
                    leaf = best3.get((j, a, k, b))
                    lvl = base_from(cm2(j, k), s)
                    if leaf is not None:
                        lvl = max(lvl, 1 + leaf)
                    w = max(w, lvl)
                if w:
                    v_k = min(v_k, w)
            v = max(base_from(cum1[j], sa), 1 + v_k)
            worst_a = max(worst_a, v)
        best = min(best, 1 + worst_a)
    return max(root_base, best)


# --- Chặn trên: greedy minimax ------------------------------------------

def greedy_minimax(cols, out):
    nq = len(cols)
    n = len(cols[0])
    depths = Counter()
    first_clue = [None]

    stack = [(list(range(n)), frozenset(), 0)]
    processed = 0
    while stack:
        idxs, used, d = stack.pop()
        if len(idxs) <= 1:
            depths[d] += len(idxs)
            processed += len(idxs)
            if processed % 50000 < len(idxs):
                log(out, "  đã xử lý %d/%d lớp, sâu nhất tới giờ %d"
                    % (processed, n, max(depths) if depths else 0))
            continue
        best_j, best_worst, best_parts = None, None, None
        for j in range(nq):
            if j in used:
                continue
            parts = {}
            cj = cols[j]
            for i in idxs:
                parts.setdefault(cj[i], []).append(i)
            if len(parts) <= 1:
                continue
            worst = max(len(v) for v in parts.values())
            if best_worst is None or worst < best_worst:
                best_worst, best_j, best_parts = worst, j, parts
        if best_j is None:
            depths[d] += len(idxs)
            processed += len(idxs)
            continue
        if d == 0:
            first_clue[0] = best_j
        nu = used | {best_j}
        for v in best_parts.values():
            stack.append((v, nu, d + 1))
    return depths, first_clue[0]


def main():
    mode = sys.argv[1]
    out = open(sys.argv[2], "w") if len(sys.argv) > 2 else None

    secrets, qids, cols, class_id, n_classes = ab.build()
    log(out, "N=%d classes=%d" % (len(secrets), n_classes))
    rcols = reduce_to_classes(cols, class_id, n_classes)
    doms = ab.domain_sizes(rcols)
    log(out, "rút gọn về %d đại diện lớp; branching: %s"
        % (len(rcols[0]), sorted(doms, reverse=True)))

    if mode.startswith("lb"):
        depth = int(mode[2:])
        v = lower_bound(rcols, doms, depth, out)
        log(out, "CHẶN DƯỚI ADAPTIVE (khai triển %d mức) = %s clue" % (depth, v))
    elif mode == "greedy":
        depths, fj = greedy_minimax(rcols, out)
        tot = sum(depths.values())
        mx = max(depths)
        log(out, "clue mở đầu greedy chọn: %s" % qids[fj])
        log(out, "histogram độ sâu: %s" % dict(sorted(depths.items())))
        log(out, "worst case = %d, tổng lớp = %d" % (mx, tot))
        mean = sum(d * c for d, c in depths.items()) / tot
        log(out, "trung bình (uniform trên lớp) = %.4f lần mua" % mean)
        acc = 0
        for d in sorted(depths):
            acc += depths[d]
            if acc >= 0.99 * tot:
                log(out, "p99 = %d" % d)
                break
    else:
        raise SystemExit("mode: lb0|lb1|lb2|lb3|greedy")
    if out:
        out.close()


if __name__ == "__main__":
    main()
