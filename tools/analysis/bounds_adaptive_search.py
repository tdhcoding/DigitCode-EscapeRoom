"""Chặn TRÊN cho ADAPTIVE: quét nhiều biến thể greedy minimax.

Bối cảnh: #6 báo worst case **16** cho greedy minimax, clue mở đầu `Q3:B`.
Chạy lại đúng luật đã mô tả ("mỗi bước chọn câu làm nhỏ nhất lớp con lớn
nhất") nhưng phá hoà theo thứ tự chỉ số cho worst case **17**, clue mở đầu
`Q3:A`. Hai clue này hoà nhau ở gốc, nên con số 16 phụ thuộc **cách phá hoà**
chứ không suy được từ luật greedy.

Script này quét có hệ thống để tìm chiến lược tốt nhất mà nó tự kiểm chứng
được: bốn luật phá hoà × ép từng clue mở đầu. Worst case nhỏ nhất tìm được là
một chặn TRÊN thật (có nhân chứng là chính cây đó), nhãn HEURISTIC vì nó vẫn
không phải cây quyết định tối ưu.

Chạy: `python3 -u tools/analysis/bounds_adaptive_search.py <mode> [ckpt.txt]`
  mode = `tiebreaks`  — 4 luật phá hoà, clue mở đầu để greedy tự chọn
         `sweep`      — quét cả 32 clue mở đầu × 4 luật phá hoà
"""

import sys
import time
from collections import Counter

import analysis_bounds as ab
from bounds_adaptive import reduce_to_classes

T0 = time.time()


def log(fh, msg):
    line = "[%7.1fs] %s" % (time.time() - T0, msg)
    print(line)
    if fh:
        fh.write(line + "\n")
        fh.flush()


def _score(parts, rule):
    sizes = [len(v) for v in parts.values()]
    worst = max(sizes)
    if rule == "index":
        return (worst,)
    if rule == "blocks":
        return (worst, -len(sizes))
    if rule == "sumsq":
        return (worst, sum(s * s for s in sizes))
    if rule == "sumsq_only":
        return (sum(s * s for s in sizes), worst)
    raise KeyError(rule)


def greedy(cols, rule, forced_first=None, cutoff=None):
    """Cây greedy minimax. `cutoff` cắt sớm khi đã vượt worst case cần beat."""
    nq = len(cols)
    n = len(cols[0])
    depths = Counter()
    stack = [(list(range(n)), frozenset(), 0)]
    while stack:
        idxs, used, d = stack.pop()
        if len(idxs) <= 1:
            depths[d] += len(idxs)
            continue
        if cutoff is not None and d >= cutoff:
            depths[d + 99] += len(idxs)   # đánh dấu vượt ngưỡng, dừng nhánh
            continue
        if d == 0 and forced_first is not None:
            cand = [forced_first]
        else:
            cand = [j for j in range(nq) if j not in used]
        best_j, best_key, best_parts = None, None, None
        for j in cand:
            parts = {}
            cj = cols[j]
            for i in idxs:
                parts.setdefault(cj[i], []).append(i)
            if len(parts) <= 1:
                continue
            key = _score(parts, rule)
            if best_key is None or key < best_key:
                best_key, best_j, best_parts = key, j, parts
        if best_j is None:
            depths[d] += len(idxs)
            continue
        nu = used | {best_j}
        for v in best_parts.values():
            stack.append((v, nu, d + 1))
    return depths


def summarize(depths):
    tot = sum(depths.values())
    mx = max(depths)
    mean = sum(d * c for d, c in depths.items()) / tot
    acc = 0
    p99 = None
    for d in sorted(depths):
        acc += depths[d]
        if p99 is None and acc >= 0.99 * tot:
            p99 = d
    return mx, mean, p99, tot


RULES = ("index", "blocks", "sumsq", "sumsq_only")


def main():
    mode = sys.argv[1]
    out = open(sys.argv[2], "w") if len(sys.argv) > 2 else None

    secrets, qids, cols, class_id, n_classes = ab.build()
    rcols = reduce_to_classes(cols, class_id, n_classes)
    log(out, "N=%d classes=%d" % (len(secrets), n_classes))

    best = (99, None)
    if mode == "tiebreaks":
        for rule in RULES:
            d = greedy(rcols, rule)
            mx, mean, p99, tot = summarize(d)
            log(out, "rule=%-10s worst=%d mean=%.4f p99=%s tot=%d"
                % (rule, mx, mean, p99, tot))
            if mx < best[0]:
                best = (mx, (rule, None), dict(sorted(d.items())))
    elif mode == "sweep":
        for rule in RULES:
            for j in range(len(rcols)):
                d = greedy(rcols, rule, forced_first=j)
                mx, mean, p99, tot = summarize(d)
                flag = ""
                if mx < best[0]:
                    best = (mx, (rule, qids[j]), dict(sorted(d.items())))
                    flag = "  <-- tốt nhất tới giờ"
                log(out, "rule=%-10s first=%-7s worst=%2d mean=%.4f p99=%s%s"
                    % (rule, qids[j], mx, mean, p99, flag))
    else:
        raise SystemExit("mode: tiebreaks|sweep")

    log(out, "TỐT NHẤT: worst case = %d  (%s)" % (best[0], best[1]))
    log(out, "histogram: %s" % best[2])
    if out:
        out.close()


if __name__ == "__main__":
    main()
