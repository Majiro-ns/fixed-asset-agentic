import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pipeline import run_pdf_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract PDF then classify to final JSON outputs")
    parser.add_argument("--pdf", dest="pdf_path", required=True, help="Input PDF path")
    parser.add_argument(
        "--out",
        dest="out_dir",
        default=str(PROJECT_ROOT / "data" / "results"),
        help="Output directory for JSON artifacts (defaults to data/results)",
    )
    parser.add_argument("--policy", dest="policy_path", default=None, help="Optional policy JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_pdf_pipeline(Path(args.pdf_path), Path(args.out_dir), args.policy_path)
    except Exception as exc:
        print(f"[run_pdf] failed: {exc}", file=sys.stderr)
        return 1

    warnings = result["final_doc"].get("warnings") or []

    print(f"[run_pdf] stored PDF copy at: {result['upload_path']}")
    print(f"[run_pdf] Generated: {result['extraction_path'].name} / {result['final_path'].name}")
    print(f"[run_pdf] saved extraction JSON: {result['extraction_path']}")
    print(f"[run_pdf] saved final JSON: {result['final_path']}")
    if warnings:
        print(f"[run_pdf] warnings ({len(warnings)}):")
        for w in warnings:
            page = f" (page {w.get('page')})" if w.get("page") is not None else ""
            print(f"  - {w.get('code')}: {w.get('message')}{page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
