"""Kiểm chứng ĐỘC LẬP kết luận "tối thiểu = 22 clue".

`bounds_fixed_close.py` chứng minh bằng DFS hitting set. Script này chứng minh
lại bằng một thuật toán khác hẳn — **vét cạn tổ hợp**, không dùng DFS, không
dùng branch & bound — để một lỗi trong bộ đếm cây không thể lọt qua cả hai.

Ý tưởng:

1. Sinh một họ ràng buộc cặp thật: với mỗi cặp secret khác lớp mà một tập con
   nào đó chưa tách được, mask các clue tách được nó. Mọi tập hợp lệ MUST hit
   toàn bộ họ này (điều kiện **cần**, nên đủ để bác bỏ).
2. 9 clue bắt buộc luôn có mặt, nên một tập 21 clue bỏ đúng **11** trong 23
   clue tuỳ chọn. Duyệt cả `C(23, 11) = 1.352.078` cách bỏ.
3. Với mỗi cách bỏ `T`, nếu tồn tại ràng buộc `c` thoả `c ⊆ T` thì tập tương
   ứng bỏ sót một cặp ⇒ không hợp lệ.
4. Nếu **mọi** `T` đều bị bác ⇒ không tập 21 clue nào tách được.

Chạy: `python3 -u tools/analysis/bounds_fixed_verify.py [checkpoint.txt]`
"""

import itertools
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

    secrets, qids, cols, class_id, n_classes = ab.build()
    ess = ab.essential_clues(cols, n_classes)
    ess_mask = 0
    for j in ess:
        ess_mask |= 1 << j
    optional = [j for j in range(len(cols)) if j not in ess]
    opt_index = {j: t for t, j in enumerate(optional)}
    log(out, "essential=%d optional=%d" % (len(ess), len(optional)))

    # --- Sinh họ ràng buộc ------------------------------------------------
    cons = set()

    def harvest(subset):
        for m in ab.violated_masks(cols, class_id, subset, limit=8192):
            if m & ess_mask:
                continue          # đã bị clue bắt buộc tách -> không ràng buộc
            r = 0
            for j in ab.mask_to_list(m):
                r |= 1 << opt_index[j]
            cons.add(r)

    harvest(ess)
    log(out, "từ tập bắt buộc: %d ràng buộc" % len(cons))
    for extra in itertools.combinations(optional, 2):
        harvest(ess + list(extra))
    log(out, "sau khi gieo mọi cặp tuỳ chọn: %d ràng buộc" % len(cons))

    # Chỉ giữ ràng buộc TỐI TIỂU (bỏ mọi mask là siêu tập của mask khác).
    by_size = sorted(cons, key=lambda x: bin(x).count("1"))
    minimal = []
    for m in by_size:
        if not any((k & m) == k for k in minimal):
            minimal.append(m)
    minimal.sort(key=lambda x: bin(x).count("1"))
    log(out, "ràng buộc tối tiểu: %d (nhỏ nhất %d bit, lớn nhất %d bit)"
        % (len(minimal), bin(minimal[0]).count("1"),
           bin(minimal[-1]).count("1")))

    # --- Vét cạn C(23, 11) ------------------------------------------------
    n_opt = len(optional)
    drop = n_opt - 12          # tập 21 clue = 9 bắt buộc + 12 tuỳ chọn
    total = 0
    survivors = []
    t_last = time.time()
    for combo in itertools.combinations(range(n_opt), drop):
        T = 0
        for t in combo:
            T |= 1 << t
        total += 1
        alive = True
        for c in minimal:
            if (c & T) == c:
                alive = False
                break
        if alive:
            survivors.append(T)
        if total % 200000 == 0 and time.time() - t_last > 5:
            t_last = time.time()
            log(out, "  đã duyệt %d/%d, còn sống %d"
                % (total, 1352078, len(survivors)))

    log(out, "duyệt xong %d cách bỏ 11 clue; còn sống %d"
        % (total, len(survivors)))

    if not survivors:
        log(out, "KẾT LUẬN ĐỘC LẬP: không tập 21 clue nào tách được => tối thiểu 22 (EXACT)")
    else:
        log(out, "còn %d ứng viên sống — kiểm tra tách thật:" % len(survivors))
        ok = None
        for T in survivors:
            keep = [optional[t] for t in range(n_opt) if not (T >> t) & 1]
            cand = ess + keep
            if ab.n_blocks(cols, cand) == n_classes:
                ok = cand
                break
        if ok:
            log(out, "TÌM THẤY tập 21 clue: %s" % [qids[j] for j in sorted(ok)])
        else:
            log(out, "KẾT LUẬN ĐỘC LẬP: không ứng viên nào tách được => tối thiểu 22 (EXACT)")
    if out:
        out.close()


if __name__ == "__main__":
    main()
