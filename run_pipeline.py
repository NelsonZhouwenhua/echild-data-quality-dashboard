"""Rebuild synthetic data, processed tables and reviewer-facing reports."""
from __future__ import annotations

import argparse
from pathlib import Path

from src.generate_reports import generate_reports
from src.generate_synthetic_data import SyntheticConfig, generate_all
from src.process_data import build_processed


def run_pipeline(repo_root: Path, n_children: int = 5_000, seed: int = 20260601) -> None:
    config = SyntheticConfig(n_children=n_children, seed=seed)
    generate_all(repo_root, config)
    build_processed(repo_root)
    generate_reports(repo_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-children", type=int, default=5_000, help="Number of synthetic children to generate")
    parser.add_argument("--seed", type=int, default=20260601, help="Random seed")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    root = Path(__file__).resolve().parent
    run_pipeline(root, n_children=args.n_children, seed=args.seed)
    print(f"Synthetic V2 pipeline completed successfully for {args.n_children:,} children.")
