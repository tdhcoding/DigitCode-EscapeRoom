#!/usr/bin/env python3
"""Test chống regression cho chính analysis tool của issue #6.

Chạy:  python3 tools/analysis/test_analysis.py
       python3 tools/analysis/test_analysis.py -v

Các test này KHÔNG kiểm tra kết luận phân tích; chúng ghim mô hình trong
`digitcode.py` vào những dữ kiện suy được độc lập từ `backend/gameboard.cpp`,
để một thay đổi vô tình trong mô hình bị phát hiện ngay.
"""

import hashlib
import os
import sys
import unittest
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import digitcode as dc

# Golden hash của toàn bộ bảng đáp án, tính lần đầu ở commit dựng mô hình.
# Dòng thứ i: "<secret>:<đáp án của 32 câu Q1+Q2+Q3, phân tách bằng dấu phẩy>\n"
GOLDEN_SIGNATURE_SHA256 = "940b9f9b188ddb81089e9cd2806a435bde0774bcd93dde1940c71fdfb4424a99"
# Golden hash của danh sách secret hợp lệ theo thứ tự sinh ra.
GOLDEN_SECRETS_SHA256 = "b7e70ad5a21200dda0d4eeb5f40123785b7bbee72b59f15834661d661f8c7d9f"

EXPECTED_VALID_SECRETS = 465120


def _all_secrets():
    if not hasattr(_all_secrets, "cache"):
        _all_secrets.cache = list(dc.iter_valid_secrets())
    return _all_secrets.cache


class TestBoardGeometry(unittest.TestCase):
    def test_max_led_derived_matches_cpp_table(self):
        """MAX_LED suy từ hình học phải khớp getMaxLed hardcode (gameboard.cpp:375-388)."""
        self.assertEqual(dc.MAX_LED, dc.MAX_LED_CPP)

    def test_column_nodes_partition_all_cells(self):
        cells = [cell for n in dc.COL_NODES for cell in dc.NODE_CELLS[n]]
        self.assertEqual(len(cells), 42)
        self.assertEqual(len(set(cells)), 42)

    def test_row_nodes_partition_all_cells(self):
        cells = [cell for n in dc.ROW_NODES for cell in dc.NODE_CELLS[n]]
        self.assertEqual(len(cells), 42)
        self.assertEqual(len(set(cells)), 42)

    def test_digit_map_patterns_are_distinct(self):
        """Nếu hai chữ số cùng mẫu segment thì bảng LED không giải mã được."""
        self.assertEqual(len(set(dc.DIGIT_MAP.values())), 10)

    def test_digit_map_matches_standard_seven_segment(self):
        """Đối chiếu độc lập với ký hiệu chuẩn 'chữ cái segment nào sáng'."""
        standard = {
            0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg",
            5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg",
        }
        for digit, lit in standard.items():
            expect = tuple(1 if s in lit else 0 for s in dc.SEGMENT_ORDER)
            self.assertEqual(dc.DIGIT_MAP[digit], expect, "chữ số %d" % digit)


class TestGeneratorConstraints(unittest.TestCase):
    def test_rejects_digit_used_three_times(self):
        self.assertFalse(dc.is_valid_secret((1, 2, 1, 3, 1, 4)))

    def test_rejects_equal_horizontal_neighbour(self):
        self.assertFalse(dc.is_valid_secret((1, 1, 2, 3, 4, 5)))
        self.assertFalse(dc.is_valid_secret((1, 2, 3, 4, 5, 5)))

    def test_rejects_equal_vertical_neighbour(self):
        self.assertFalse(dc.is_valid_secret((1, 2, 3, 1, 4, 5)))
        self.assertFalse(dc.is_valid_secret((1, 2, 3, 4, 5, 3)))

    def test_allows_wrap_across_row_boundary(self):
        """Vị trí 3 KHÔNG bị C2 chặn (3 % 3 == 0) nên code[3] == code[2] hợp lệ."""
        self.assertTrue(dc.is_valid_secret((0, 1, 2, 2, 0, 1)))

    def test_allows_same_digit_twice(self):
        self.assertTrue(dc.is_valid_secret((0, 1, 2, 3, 0, 1)))

    def test_allowed_set_is_never_empty(self):
        """Sampler không thể treo: mọi prefix hợp lệ đều còn chữ số để bốc."""
        def walk(prefix):
            if len(prefix) == dc.SECRET_LENGTH:
                return
            allowed = dc.allowed_digits(prefix)
            self.assertTrue(allowed, "prefix bị kẹt: %r" % (prefix,))
            for d in allowed:
                walk(prefix + (d,))
        walk(())

    def test_enumeration_matches_brute_force(self):
        """Đường 1: đi theo luật sampler. Đường 2: quét toàn bộ 10^6 mã."""
        enumerated = len(_all_secrets())
        brute = 0
        for n in range(1000000):
            code = tuple(int(ch) for ch in "%06d" % n)
            if dc.is_valid_secret(code):
                brute += 1
        self.assertEqual(enumerated, brute)
        self.assertEqual(enumerated, EXPECTED_VALID_SECRETS)

    def test_every_enumerated_secret_is_valid(self):
        self.assertTrue(all(dc.is_valid_secret(c) for c in _all_secrets()))


class TestSamplerDistribution(unittest.TestCase):
    def test_probability_mass_of_a_subtree_is_exact(self):
        """Tổng xác suất các secret nối tiếp một prefix phải bằng đúng P(prefix).

        Kiểm tra exact bằng Fraction trên một nhánh nhỏ thay vì cả cây, để test
        chạy nhanh mà vẫn là phép kiểm tra chính xác chứ không phải xấp xỉ.
        """
        prefix = (0, 1, 2)
        p_prefix = Fraction(1)
        for i in range(len(prefix)):
            p_prefix *= Fraction(1, len(dc.allowed_digits(prefix[:i])))

        total = Fraction(0)
        for code in _all_secrets():
            if code[:3] == prefix:
                total += dc.secret_probability(code)
        self.assertEqual(total, p_prefix)

    def test_sampler_is_not_uniform(self):
        """Nếu sampler uniform thì mọi secret cùng xác suất — nó không như vậy."""
        probs = set(dc.secret_probability(c) for c in _all_secrets()[:20000])
        self.assertGreater(len(probs), 1)


class TestClues(unittest.TestCase):
    def test_q2_equal_branch_is_unreachable(self):
        """C2/C3 cấm hai LED liền kề bằng nhau, nên Q2 không bao giờ trả 0."""
        for code in _all_secrets():
            for pair in dc.Q2_PAIRS:
                self.assertNotEqual(dc.q2(code, pair), 0, "%r / %s" % (code, pair))

    def test_q4_is_a_function_of_q3(self):
        for code in _all_secrets()[::997]:
            for node in dc.COUNT_NODES:
                expect = 1 if dc.q3(code, node) == dc.MAX_LED[node] else 0
                self.assertEqual(dc.q4(code, node), expect)

    def test_column_and_row_counts_have_the_same_total(self):
        """9 nút cột và 10 nút hàng phủ cùng 42 ô, nên hai tổng phải bằng nhau."""
        for code in _all_secrets()[::997]:
            col = sum(dc.q3(code, n) for n in dc.COL_NODES)
            row = sum(dc.q3(code, n) for n in dc.ROW_NODES)
            lit = sum(sum(dc.DIGIT_MAP[d]) for d in code)
            self.assertEqual(col, row)
            self.assertEqual(col, lit)

    def test_q1_matches_digit_parity(self):
        for code in _all_secrets()[::997]:
            for i, label in enumerate(dc.LED_LABELS):
                self.assertEqual(dc.q1(code, label), code[i] % 2)

    def test_question_registry_is_complete(self):
        self.assertEqual(len(dc.Q1_IDS), 6)
        self.assertEqual(len(dc.Q2_IDS), 7)
        self.assertEqual(len(dc.Q3_IDS), 19)
        self.assertEqual(len(dc.Q4_IDS), 19)
        self.assertEqual(len(dc.BASE_QUESTION_IDS), 32)
        self.assertEqual(len(set(dc.ALL_QUESTION_IDS)), 51)


class TestGoldenHashes(unittest.TestCase):
    """Ghim toàn bộ mô hình: đổi bất kỳ đáp án nào cũng làm hash lệch."""

    def test_secret_list_hash(self):
        h = hashlib.sha256()
        for code in _all_secrets():
            h.update(("".join(map(str, code)) + "\n").encode())
        self.assertEqual(h.hexdigest(), GOLDEN_SECRETS_SHA256)

    def test_full_signature_table_hash(self):
        h = hashlib.sha256()
        qids = dc.BASE_QUESTION_IDS
        for code in _all_secrets():
            row = ",".join(str(dc.answer(code, q)) for q in qids)
            h.update(("".join(map(str, code)) + ":" + row + "\n").encode())
        self.assertEqual(h.hexdigest(), GOLDEN_SIGNATURE_SHA256)


class TestAnalysisModuleContract(unittest.TestCase):
    """Mọi module phân tích phải theo cùng một hợp đồng cho driver."""

    MODULES = ("analysis_generator", "analysis_signature", "analysis_cost")

    def test_modules_expose_analyse_and_format_report(self):
        import importlib
        missing = []
        for name in self.MODULES:
            try:
                mod = importlib.import_module(name)
            except ImportError:
                missing.append(name)
                continue
            self.assertTrue(callable(getattr(mod, "analyse", None)), name)
            self.assertTrue(callable(getattr(mod, "format_report", None)), name)
        if missing:
            self.skipTest("chưa có module: %s" % ", ".join(missing))


if __name__ == "__main__":
    unittest.main(verbosity=2)
