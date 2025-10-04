import argparse

from wiki.io import read_article_refs, write_metadata
from wiki.enrich import fetch_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch article metadata (size, word count, quality, projects, etc.)")
    parser.add_argument("articles_csv", help="Input CSV with columns: pageid,title,category")
    parser.add_argument("--output", required=True, help="Output CSV path for metadata")
    args = parser.parse_args()

    article_refs = read_article_refs(args.articles_csv)
    metadata_records = fetch_metadata(article_refs)
    # Preserve order by title for some stability in diffs
    metadata_records.sort(key=lambda meta: meta.title.lower())
    write_metadata(args.output, metadata_records)


if __name__ == "__main__":
    main()
