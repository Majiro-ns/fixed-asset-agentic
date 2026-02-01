import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run adapter then classifier to produce frozen schema output")
    parser.add_argument("--in", dest="in_path", default="data/opal_outputs/01_opal.json", help="Input Opal JSON path")
    parser.add_argument("--out", dest="out_path", default="data/results/01_final.json", help="Output path for normalized + classified JSON")
    parser.add_argument("--policy", dest="policy_path", default=None, help="Optional policy JSON path (overridden by POLICY_PATH env var)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    policy_path = os.environ.get("POLICY_PATH") or args.policy_path
    output_path = run_pipeline(args.in_path, args.out_path, policy_path)
    print(f"Saved pipeline output to {Path(output_path)}")


if __name__ == "__main__":
    main()
