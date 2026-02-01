import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pipeline import run_adapter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Opal output to frozen schema v1.0")
    parser.add_argument("--in", dest="in_path", required=True, help="Input Opal JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output path for normalized JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = run_adapter(args.in_path, args.out_path)
    print(f"Saved normalized output to {Path(output_path)}")


if __name__ == "__main__":
    main()
