#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from wiki.report import ReportConfig, generate_report, load_and_prepare_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze Wikipedia article metadata CSV.")
    parser.add_argument("csv_file", help="Path to the CSV file")
    parser.add_argument("--out", dest="output_dir", type=Path, default=Path("wikipedia_report"),
                        help="Directory to write outputs (default: wikipedia_report)")
    parser.add_argument("--bins", dest="histogram_bins", type=int, default=50,
                        help="Number of bins for histograms (default: 50)")
    parser.add_argument("--size-cap", dest="size_bytes_cap", type=int, default=175_000,
                        help="Cap for size_bytes hist (default: 175000)")
    parser.add_argument("--word-cap", dest="word_count_cap", type=int, default=10_000,
                        help="Cap for word_count hist (default: 10000)")
    parser.add_argument("--edit-cutoff", dest="last_edit_cutoff", default="2024-05-01",
                        help="ISO date cutoff for last_edit histogram (default: 2024-05-01). Use '' to disable.")
    parser.add_argument("--top-wikiprojects", dest="top_wikiprojects", type=int, default=30,
                        help="How many WikiProjects to chart (default: 30)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s"
    )

    cutoff = args.last_edit_cutoff if str(args.last_edit_cutoff).strip() else None

    cfg = ReportConfig(
        output_dir=args.output_dir,
        histogram_bins=args.histogram_bins,
        size_bytes_cap=args.size_bytes_cap,
        word_count_cap=args.word_count_cap,
        last_edit_cutoff=cutoff,
        top_wikiprojects=args.top_wikiprojects,
    )

    df: pd.DataFrame = load_and_prepare_data(args.csv_file)
    generate_report(df, cfg)


if __name__ == "__main__":
    main()
