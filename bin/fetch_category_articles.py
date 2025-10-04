import argparse
import csv
import sys

from wiki.categories import crawl_category
from wiki.clients import mw_session

# python3 ./bin/fetch_category_articles.py "Video game designers" --depth 2 --exclude "Category:Video games by designer" --output articles_vg_designers_by_views_2024_2025.csv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect Wikipedia articles from a category (with optional recursion)."
    )
    parser.add_argument("category", help='Category title, with or without "Category:" prefix')
    parser.add_argument("--depth", type=int, default=2, help="Max subcategory depth to traverse (default: 2)")
    parser.add_argument(
        "--exclude",
        default="",
        help='Comma-separated list of category titles to skip (with or without "Category:" prefix)',
    )
    parser.add_argument("--output", default="-", help='Output CSV path or "-" for stdout (default: "-")')
    args = parser.parse_args()

    session = mw_session()
    exclude_set = {item.strip() for item in args.exclude.split(",") if item.strip()}

    articles, _visited = crawl_category(
        root_category=args.category,
        max_depth=args.depth,
        exclude=exclude_set,
        session=session,
    )

    output_stream = sys.stdout if args.output == "-" else open(args.output, "w", newline="")
    try:
        writer = csv.writer(output_stream)
        writer.writerow(["pageid", "title", "category"])
        for pageid, (title, source_category) in articles.items():
            writer.writerow([pageid, title, source_category])
    finally:
        if output_stream is not sys.stdout:
            output_stream.close()


if __name__ == "__main__":
    main()
