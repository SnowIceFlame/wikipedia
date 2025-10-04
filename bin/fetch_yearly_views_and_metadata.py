import argparse
import csv
from pathlib import Path
import sys

# # --- local src/ bootstrap so `python3 bin/...` works without installing the package ---
# REPO_ROOT = Path(__file__).resolve().parents[1]
# SRC_PATH = REPO_ROOT / "src"
# if str(SRC_PATH) not in sys.path:
#     sys.path.insert(0, str(SRC_PATH))
# -------------------------------------------------------------------------------------

from wiki.io import read_article_refs  # noqa: E402
from wiki.enrich import compute_yearly_views, fetch_metadata  # noqa: E402


def derive_output_paths(
    input_csv: Path, write_intermediate: bool, explicit_output: str | None
) -> tuple[Path, Path | None, Path | None]:
    """
    From `articles_some_suffix.csv` produce:
      combined: some_suffix_combined.csv
      views:    some_suffix_views.csv (optional)
      meta:     some_suffix_meta.csv  (optional)

    If the input doesn't start with 'articles_', we use the stem as the base.
    If explicit_output is provided, use that for the combined path and keep intermediates next to it.
    """
    if explicit_output:
        combined_path = Path(explicit_output)
        base = combined_path.with_suffix("").name
        views_path = combined_path.with_name(f"{base}_views.csv") if write_intermediate else None
        meta_path = combined_path.with_name(f"{base}_meta.csv") if write_intermediate else None
        return combined_path, views_path, meta_path

    stem = input_csv.stem
    core = stem[9:] if stem.startswith("articles_") else stem
    parent = input_csv.parent
    combined_path = parent / f"{core}_combined.csv"
    views_path = parent / f"{core}_views.csv" if write_intermediate else None
    meta_path = parent / f"{core}_meta.csv" if write_intermediate else None
    return combined_path, views_path, meta_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch yearly pageviews and metadata, then write a combined CSV with rank.\n"
            "Input CSV must have columns: pageid,title,category."
        )
    )
    parser.add_argument("articles_csv", help="Path to articles CSV (e.g., articles_some_suffix.csv)")
    parser.add_argument(
        "--start",
        default="20240801",
        help='Start date YYYYMMDD (inclusive). Example monthly range start: "20240801".',
    )
    parser.add_argument(
        "--end",
        default="20250701",
        help='End date YYYYMMDD (exclusive). Example monthly range end: "20250701".',
    )
    parser.add_argument(
        "--output",
        help="Optional explicit output path for combined CSV. If omitted, derives from the input filename.",
    )
    parser.add_argument(
        "--write-intermediate",
        action="store_true",
        help="Also write <base>_views.csv and <base>_meta.csv alongside the combined file.",
    )
    args = parser.parse_args()

    input_csv = Path(args.articles_csv)
    combined_path, views_path, meta_path = derive_output_paths(
        input_csv=input_csv,
        write_intermediate=args.write_intermediate,
        explicit_output=args.output,
    )
    if combined_path.exists():
        print(f"Error: output file {combined_path} already exists. "
            f"Remove it first if you want to regenerate.", file=sys.stderr)
        sys.exit(1)

    # 1) Read article refs (pageid, title, category)
    article_refs = read_article_refs(input_csv)

    # 2) Compute yearly views for the given range
    pageview_totals = compute_yearly_views(article_refs, start=args.start, end=args.end)

    # Optionally persist views
    if views_path:
        with open(views_path, "w", newline="") as views_file:
            writer = csv.writer(views_file)
            writer.writerow(["pageid", "title", "category", "yearly_views"])
            for record in pageview_totals:
                writer.writerow([record.pageid, record.title, record.category, record.yearly_views])

    # 3) Fetch metadata (shortdesc, word_count, quality come from here)
    metadata_records = fetch_metadata(article_refs)

    # Optionally persist metadata (only the columns we care about for this join)
    if meta_path:
        with open(meta_path, "w", newline="") as meta_file:
            writer = csv.writer(meta_file)
            writer.writerow(["pageid", "shortdesc", "word_count", "quality"])
            for meta in metadata_records:
                writer.writerow(
                    [meta.pageid, meta.shortdesc, meta.word_count, meta.quality or ""]
                )

    # 4) Join + rank (rank = 1 for the highest yearly_views)
    metadata_by_pageid: dict[int, tuple[str, int, str]] = {
        meta.pageid: (meta.shortdesc, meta.word_count, meta.quality or "")
        for meta in metadata_records
    }

    # Sort by views desc, then title for stable ties
    pageview_totals.sort(key=lambda r: (-r.yearly_views, r.title.lower()))

    fieldnames = [
        "rank",
        "pageid",
        "title",
        "category",
        "yearly_views",
        "shortdesc",
        "word_count",
        "quality",
    ]

    with open(combined_path, "w", newline="") as combined_file:
        writer = csv.DictWriter(combined_file, fieldnames=fieldnames)
        writer.writeheader()

        for rank, total in enumerate(pageview_totals, start=1):
            shortdesc, word_count, quality = metadata_by_pageid.get(
                total.pageid, ("", 0, "")
            )
            output_row = {
                "rank": rank,
                "pageid": total.pageid,
                "title": total.title,
                "category": total.category,
                "yearly_views": total.yearly_views,
                "shortdesc": shortdesc,
                "word_count": word_count,
                "quality": quality,
            }
            writer.writerow(output_row)

    print(f"Wrote: {combined_path}")


if __name__ == "__main__":
    main()
