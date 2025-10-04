import argparse

from wiki.io import read_article_refs, write_views
from wiki.enrich import compute_yearly_views

"""
Read a CSV of (pageid,title), fetch monthly pageviews for Aug 2024–Jul 2025
from the Wikimedia Pageviews REST API, sum per article, and write a new CSV
(pageid,title,yearly_views) sorted by yearly_views (desc).

Usage:
  python3 ./bin/fetch_yearly_views.py input_articles.csv --output article_views_2024_2025.csv

"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute total pageviews over a monthly range for a list of articles.")
    parser.add_argument("articles_csv", help="Input CSV with columns: pageid,title,category")
    parser.add_argument(
        "--start",
        default="20240801",
        help='Start date YYYYMMDD (inclusive). For monthly granularity, e.g. "20240801".',
    )
    parser.add_argument(
        "--end",
        default="20250701",
        help='End date YYYYMMDD (exclusive). For monthly granularity, e.g. "20250701".',
    )
    parser.add_argument("--output", required=True, help="Output CSV path for yearly_views")
    args = parser.parse_args()

    article_refs = read_article_refs(args.articles_csv)
    totals = compute_yearly_views(article_refs, start=args.start, end=args.end)
    totals.sort(key=lambda record: (-record.yearly_views, record.title.lower()))
    write_views(args.output, totals)


if __name__ == "__main__":
    main()
