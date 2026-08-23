"""Đóng khoảng tập clue CỐ ĐỊNH: chứng minh không tồn tại tập 21 clue.

`bounds_fixed.py` đã đưa `[14, 22]` của #6 về `[21, 22]`: tồn tại tập 22 clue
tách được (khả thi, kiểm chứng trực tiếp), và hitting set trên các ràng buộc
đã sinh cho chặn dưới 21.

Script này duyệt **vét cạn** mọi tập 21 clue còn khả dĩ:

* 9 clue bắt buộc luôn có mặt (drop-one test), nên chỉ còn chọn 12 trong 23
  clue tuỳ chọn — `C(23,12) = 1.352.078` tập.
* Duyệt bằng DFS hitting set: chỉ những tập **hit hết** các ràng buộc cặp đã
  biết mới được kiểm tra thật sự. Mỗi lần một ứng viên trượt, các cặp nó chưa
  tách được biến thành ràng buộc mới, cắt tiếp phần còn lại của cây.
* DFS kết thúc mà không tìm được tập nào ⇒ **không tồn tại tập 21 clue**, tức
  22 là tối ưu — nhãn EXACT.

Chạy: `python3 -u tools/analysis/bounds_fixed_close.py [checkpoint.txt] [target_size]`
"""

import sys
import time

import analysis_bounds as ab

T0 = time.time()


def log(fh, msg):
    line = "[%7.1fs] %s" % (time.time() - T0, msg)
    print(line)
    if fh:
        fh.write(line + "\n")
        fh.flush()


def main():
    out = open(sys.argv[1], "w") if len(sys.argv) > 1 else None
    target_optional = int(sys.argv[2]) if len(sys.argv) > 2 else 12

    secrets, qids, cols, class_id, n_classes = ab.build()
    ess = ab.essential_clues(cols, n_classes)
    ess_mask = 0
    for j in ess:
        ess_mask |= 1 << j
    optional = [j for j in range(len(cols)) if j not in ess]
    log(out, "N=%d classes=%d essential=%d optional=%d target=%d+%d"
        % (len(secrets), n_classes, len(ess), len(optional),
           len(ess), target_optional))

    # Chỉ số nội bộ 0..22 cho clue tuỳ chọn.
    opt_index = {j: t for t, j in enumerate(optional)}

    def reduce_mask(m):
        """Đưa mask 32-bit về mask trên chỉ số tuỳ chọn. None nếu đã bị hit."""
        if m & ess_mask:
            return None
        r = 0
        for j in ab.mask_to_list(m):
            r |= 1 << opt_index[j]
        return r

    cons = set()

    def seed_constraints(subset):
        added = 0
        for m in ab.violated_masks(cols, class_id, subset, limit=4096):
            r = reduce_mask(m)
            if r is not None and r not in cons:
                cons.add(r)
                added += 1
        return added

    log(out, "gieo ràng buộc từ tập bắt buộc...")
    log(out, "  +%d ràng buộc (tổng %d)" % (seed_constraints(ess), len(cons)))

    # Gieo thêm từ vài tập con "gần đủ" để cây bị cắt sớm.
    import itertools
    seeds = 0
    for extra in itertools.combinations(optional, 3):
        seed_constraints(ess + list(extra))
        seeds += 1
        if seeds >= 12:
            break
    log(out, "  sau khi gieo thêm: %d ràng buộc" % len(cons))

    tested = [0]
    found = [None]

    def dfs(remaining, chosen, budget, banned):
        if found[0] is not None:
            return
        if not remaining:
            cand = ess + [optional[t] for t in ab.mask_to_list(chosen)]
            tested[0] += 1
            nb = ab.n_blocks(cols, cand)
            if nb == n_classes:
                found[0] = cand
                log(out, "TÌM THẤY tập %d clue tách được: %s"
                    % (len(cand), [qids[j] for j in sorted(cand)]))
                return
            new = 0
            for m in ab.violated_masks(cols, class_id, cand, limit=512):
                r = reduce_mask(m)
                if r is not None and r not in cons:
                    cons.add(r)
                    new += 1
            if tested[0] % 25 == 0 or new:
                log(out, "  thử #%d: %d/%d lớp, +%d ràng buộc (tổng %d)"
                    % (tested[0], nb, n_classes, new, len(cons)))
            raise Restart()
        if budget == 0:
            return
        if ab.greedy_lb(remaining) > budget:
            return
        pivot = min(remaining, key=lambda x: bin(x).count("1"))
        pivot &= ~banned
        local_ban = banned
        b = 0
        m = pivot
        while m:
            if m & 1:
                bit = 1 << b
                nxt = [c for c in remaining if not (c & bit)]
                dfs(nxt, chosen | bit, budget - 1, local_ban)
                if found[0] is not None:
                    return
                local_ban |= bit
            m >>= 1
            b += 1

    class Restart(Exception):
        pass

    rounds = 0
    while found[0] is None:
        rounds += 1
        try:
            dfs(sorted(cons, key=lambda x: bin(x).count("1")), 0,
                target_optional, 0)
        except Restart:
            continue
        if found[0] is not None:
            break
        # DFS chạy hết mà không raise Restart và không tìm thấy gì.
        log(out, "DFS vét cạn xong sau %d vòng, %d ứng viên đã kiểm tra"
            % (rounds, tested[0]))
        log(out, "KẾT LUẬN: KHÔNG tồn tại tập %d clue tách được."
            % (len(ess) + target_optional))
        log(out, "=> tối thiểu = %d clue (EXACT), khoảng [14,22] của #6 ĐÃ ĐÓNG."
            % (len(ess) + target_optional + 1))
        break

    if found[0] is not None:
        log(out, "=> tồn tại tập %d clue: UB giảm xuống %d"
            % (len(found[0]), len(found[0])))
    if out:
        out.close()


if __name__ == "__main__":
    main()
