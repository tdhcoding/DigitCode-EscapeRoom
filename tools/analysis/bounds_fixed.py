"""Tìm tập clue CỐ ĐỊNH nhỏ nhất — đóng khoảng `[14, 22]` của #6.

Bài toán: chọn tập con nhỏ nhất của 32 clue sao cho signature hạn chế trên
tập đó vẫn tách được đúng 465.034 lớp (86 cặp collision không tách được nên
không tính).

Cách làm — **CEGAR** (sinh ràng buộc lười):

1. Mọi tập hợp lệ phải tách được MỌI cặp secret khác lớp. Với một cặp, tập
   clue tách được nó là một bitmask. Nên bài toán đúng bằng **hitting set nhỏ
   nhất** trên họ mask đó. Liệt kê hết cặp là 1,08e11 — bất khả thi.
2. Thay vào đó: giải hitting set trên một tập con ràng buộc (cho **chặn dưới**
   hợp lệ), thử nghiệm lời giải, nếu chưa tách được thì nạp thêm ràng buộc từ
   chính các cặp bị vi phạm, lặp lại.
3. Khi lời giải của hitting set tách được thật, nó vừa đạt chặn dưới vừa khả
   thi ⇒ **tối ưu**, nhãn EXACT.

Mọi trạng thái trung gian đều cho một khoảng `[LB, UB]` hợp lệ, nên chạy dở
vẫn ra kết quả dùng được.

Chạy: `python3 -u tools/analysis/bounds_fixed.py [checkpoint.txt]`
"""

import sys
import time

import analysis_bounds as ab


def log(fh, msg):
    line = "[%7.1fs] %s" % (time.time() - T0, msg)
    print(line)
    if fh:
        fh.write(line + "\n")
        fh.flush()


T0 = time.time()


def greedy_cover(cols, n_classes, seed):
    """Bổ sung tham lam (chọn clue làm tăng số lớp nhiều nhất) tới khi tách được."""
    cur = list(seed)
    while ab.n_blocks(cols, cur) < n_classes:
        best_j, best_v = None, -1
        for j in range(len(cols)):
            if j in cur:
                continue
            v = ab.n_blocks(cols, cur + [j])
            if v > best_v:
                best_v, best_j = v, j
        cur.append(best_j)
    return cur


def minimalize(cols, n_classes, subset, forced):
    """Bỏ dần cho tới khi tối tiểu theo bao hàm. Duyệt xác định, không RNG."""
    cur = list(subset)
    changed = True
    while changed:
        changed = False
        for j in sorted(cur, reverse=True):
            if j in forced:
                continue
            trial = [k for k in cur if k != j]
            if ab.n_blocks(cols, trial) == n_classes:
                cur = trial
                changed = True
    return cur


def main():
    out = open(sys.argv[1], "w") if len(sys.argv) > 1 else None

    log(out, "dựng dữ liệu nền...")
    secrets, qids, cols, class_id, n_classes = ab.build()
    log(out, "N=%d classes=%d collision_pairs=%d"
        % (len(secrets), n_classes, len(secrets) - n_classes))

    ess = ab.essential_clues(cols, n_classes)
    log(out, "essential (%d): %s" % (len(ess), [qids[j] for j in ess]))

    # UB ban đầu: tham lam rồi bỏ dần.
    g = greedy_cover(cols, n_classes, ess)
    log(out, "greedy cover: %d clue -> %s" % (len(g), [qids[j] for j in g]))
    g = minimalize(cols, n_classes, g, set(ess))
    ub_set = list(g)
    UB = len(ub_set)
    log(out, "UB sau khi tối tiểu hoá: %d -> %s" % (UB, [qids[j] for j in ub_set]))

    # Ràng buộc khởi điểm: mỗi clue bắt buộc là một mask đơn.
    constraints = set(1 << j for j in ess)
    LB = len(ess)

    it = 0
    while True:
        it += 1
        size, mask, proved = ab.min_hitting_set(list(constraints), UB)
        if mask == 0 and proved:
            # Không có lời giải nào < UB ⇒ UB chính là tối ưu.
            LB = UB
            log(out, "iter %d: hitting set chứng minh không có tập < %d" % (it, UB))
            break
        if not proved:
            LB = max(LB, size)
            log(out, "iter %d: hết node budget, LB=%d UB=%d (dừng, chưa đóng)"
                % (it, LB, UB))
            break
        LB = max(LB, size)
        cand = ab.mask_to_list(mask)
        nb = ab.n_blocks(cols, cand)
        log(out, "iter %d: LB=%d ứng viên %d clue -> %d/%d lớp"
            % (it, LB, len(cand), nb, n_classes))
        if nb == n_classes:
            ub_set = cand
            UB = len(cand)
            log(out, "iter %d: ỨNG VIÊN TÁCH ĐƯỢC — tối ưu = %d" % (it, UB))
            LB = UB
            break
        new = ab.violated_masks(cols, class_id, cand, limit=256)
        before = len(constraints)
        constraints.update(new)
        log(out, "iter %d: nạp %d ràng buộc (tổng %d)"
            % (it, len(constraints) - before, len(constraints)))
        if len(constraints) == before:
            log(out, "iter %d: không sinh thêm được ràng buộc — dừng" % it)
            break

    log(out, "KẾT QUẢ  LB=%d  UB=%d  %s"
        % (LB, UB, "ĐÓNG (EXACT)" if LB == UB else "chưa đóng"))
    log(out, "tập đạt UB (%d clue): %s" % (UB, [qids[j] for j in sorted(ub_set)]))
    log(out, "kiểm chứng lại: n_blocks=%d (cần %d)"
        % (ab.n_blocks(cols, ub_set), n_classes))
    if out:
        out.close()


if __name__ == "__main__":
    main()
