#!/usr/bin/env python3
"""Driver phân tích Puzzle cho issue #6.

Chạy các module phân tích trong `tools/analysis/` và in một báo cáo
deterministic. Không phụ thuộc dịch vụ ngoài, chỉ standard library.

    python3 tools/analysis/puzzle_fairness.py --all
    python3 tools/analysis/puzzle_fairness.py --section signature
    python3 tools/analysis/puzzle_fairness.py --all --json out.json
"""

import argparse
import importlib
import json
import os
import platform
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import digitcode as dc  # noqa: E402

SECTIONS = (
    ("generator", "analysis_generator", "Phân phối của rejection sampler"),
    ("signature", "analysis_signature", "Partition, phụ thuộc clue, collision"),
    ("cost", "analysis_cost", "Chi phí clue và difficulty proxies"),
)


def _environment():
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
    }


def run(section_names, secrets=None):
    if secrets is None:
        t0 = time.time()
        secrets = list(dc.iter_valid_secrets())
        enumerate_seconds = time.time() - t0
    else:
        enumerate_seconds = None

    out = {
        "environment": _environment(),
        "valid_secret_count": len(secrets),
        "enumerate_seconds": enumerate_seconds,
        "sections": {},
    }

    for name, module_name, _title in SECTIONS:
        if name not in section_names:
            continue
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            out["sections"][name] = {"error": "không import được %s: %s" % (module_name, exc)}
            continue
        t0 = time.time()
        results = module.analyse(secrets)
        out["sections"][name] = {
            "seconds": round(time.time() - t0, 3),
            "results": results,
            "report": module.format_report(results),
        }
    return out


def format_report(out):
    lines = []
    lines.append("=" * 78)
    lines.append("DigitCode — characterization Puzzle (issue #6)")
    lines.append("=" * 78)
    env = out["environment"]
    lines.append("Python %s (%s) trên %s / %s"
                 % (env["python"], env["implementation"], env["platform"], env["machine"]))
    lines.append("Secret hợp lệ: %d" % out["valid_secret_count"])
    if out["enumerate_seconds"] is not None:
        lines.append("Thời gian liệt kê: %.2fs" % out["enumerate_seconds"])
    for name, _module_name, title in SECTIONS:
        block = out["sections"].get(name)
        if block is None:
            continue
        lines.append("")
        lines.append("-" * 78)
        lines.append("[%s] %s" % (name, title))
        lines.append("-" * 78)
        if "error" in block:
            lines.append("BỎ QUA: %s" % block["error"])
            continue
        lines.append("(chạy trong %.2fs)" % block["seconds"])
        lines.append(block["report"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="chạy mọi section")
    parser.add_argument("--section", action="append", default=[],
                        choices=[s[0] for s in SECTIONS],
                        help="chỉ chạy section này (lặp lại được)")
    parser.add_argument("--json", metavar="PATH", help="ghi kết quả thô ra file JSON")
    args = parser.parse_args(argv)

    if args.all or not args.section:
        wanted = set(s[0] for s in SECTIONS)
    else:
        wanted = set(args.section)

    out = run(wanted)
    print(format_report(out))

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=False, default=str)
        print("\nĐã ghi JSON: %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
