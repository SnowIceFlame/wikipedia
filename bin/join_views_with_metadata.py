import argparse
import csv
from pathlib import Path
import sys

""" 
python3 ./bin/join_views_with_metadata.py ./vg_designers_by_views_2024_2025.csv ./vg_designers_metadata_2024_2025.csv  --output vg_designers_combined_2024_2025.csv 
"""

def main() -> None:
    parser = argparse.ArgumentParser(description="Join yearly views CSV with metadata CSV on pageid.")
    parser.add_argument("views_csv", help="CSV with columns: pageid,title,category,yearly_views")
    parser.add_argument(
        "meta_csv", help="CSV with columns from write_metadata (pageid,title,shortdesc,quality,...)"
    )
    parser.add_argument("--output", required=True, help="Output CSV path for joined data")
    args = parser.parse_args()
    out_path = Path(args.output)
    if out_path.exists():
        print(f"Error: output file {args.output} already exists. "
            f"Remove it first if you want to regenerate.", file=sys.stderr)
        sys.exit(1)

    metadata_by_pageid: dict[int, dict[str, str]] = {}
    with open(args.meta_csv, newline="") as meta_file:
        meta_reader = csv.DictReader(meta_file)
        for row in meta_reader:
            try:
                pageid = int(row["pageid"])
            except (KeyError, ValueError):
                continue
            # metadata_by_pageid[int(row["pageid"])] = row
            metadata_by_pageid[pageid] = {
                "shortdesc": row.get("shortdesc", ""),
                "word_count": row.get("word_count", ""),
                "quality": row.get("quality", ""),
            }

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

    with open(args.views_csv, newline="") as views_file, open(args.output, "w", newline="") as output_file:
        views_reader = csv.DictReader(views_file)
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(views_reader, start=1):
            try:
                pageid = int(row["pageid"])
            except (KeyError, ValueError):
                continue
            meta = metadata_by_pageid.get(pageid, {})
            output_row = {
                "rank": rank,
                "pageid": row.get("pageid", ""),
                "title": row.get("title", ""),
                "category": row.get("category", ""),
                "yearly_views": row.get("yearly_views", ""),
                "shortdesc": meta.get("shortdesc", ""),
                "word_count": meta.get("word_count", ""),
                "quality": meta.get("quality", ""),
            }
            writer.writerow(output_row)

        # for row in views_reader:
        #     try:
        #         pageid = int(row["pageid"])
        #     except (KeyError, ValueError):
        #         continue
        #     joined_row = {**row, **metadata_by_pageid.get(pageid, {})}
        #     writer.writerow(joined_row)


if __name__ == "__main__":
    main()
