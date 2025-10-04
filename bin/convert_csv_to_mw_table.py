import argparse
import csv
from pathlib import Path

""" 
python3 bin/convert_csv_to_mw_table.py "video game" vg_artists_2024_2025_combined.csv:50 vg_companies_2024_2025_combined.csv vg_terms_2024_2025_combined.csv:100 vg_chars_2024_2025_combined.csv vg_composers_2024_2025_combined.csv:100 vg_programmers_2024_2025_combined.csv:75 vg_writers_2024_2025_combined.csv:75

python3 bin/convert_csv_to_mw_table.py "video game" vg_games_2024_2025_combined.csv  --group-by-category-year --output WP_VG_games.txt
"""

def parse_input_specs(specs, default_limit: int | None) -> list[tuple[Path, int | None]]:
    """
    Accepts inputs like:
      file.csv
      file.csv:150
    Returns list of (Path, limit or None).
    """
    parsed: list[tuple[Path, int | None]] = []
    for spec in specs:
        if ":" in spec:
            path_str, limit_str = spec.rsplit(":", 1)
            path = Path(path_str)
            try:
                limit = int(limit_str)
            except ValueError:
                raise SystemExit(f"Invalid limit in input spec: {spec!r}")
            parsed.append((path, limit))
        else:
            parsed.append((Path(spec), default_limit))
    return parsed


def derive_output_path(wikiproject: str, explicit_output: str | None) -> Path:
    if explicit_output:
        return Path(explicit_output)
    safe = wikiproject.replace(" ", "_")
    return Path(f"WP_{safe}.txt")



def format_quality_cell(quality: str | None, wikiproject: str) -> str:
    """
    If quality is present (e.g., 'GA', 'FA', 'B', 'C', 'Start', 'Stub', 'A'),
    return {{QUALITY-Class|category=Category:QUALITY-Class <WIKIPROJECT> articles}}
    Otherwise return empty string (blank cell).
    """
    if not quality:
        return ""
    grade = quality.strip()
    return f"{{{{{grade}-Class|category=Category:{grade}-Class {wikiproject} articles}}}}"


def write_table_header(lines: list[str], caption: str) -> None:
    lines.append("{{Table alignment}}")
    lines.append('{| class="wikitable sortable col1right col2right col5right "')
    lines.append(f"|+ {caption}")
    lines.append("|-")
    lines.append("!Rank")
    lines.append("!Views")
    lines.append("!Article")
    lines.append("!Quality")
    lines.append("!Words")
    lines.append("!Description")


def write_table_row(
    lines: list[str],
    rank: str,
    title: str,
    views: str,
    quality_cell: str,
    word_count: str,
    description: str,
) -> None:
    lines.append("|-")
    lines.append(f"| {rank}")
    lines.append(f"| {views}")
    lines.append(f"| [[{title}]]")
    lines.append(f"| {quality_cell}")
    lines.append(f"| {word_count}")
    lines.append(f"| {description[:85]}") # truncate long descriptions


def parse_category_year(category: str) -> int | None:
    """
    Extract a 4-digit leading year from a category like '2021 video games'.
    Returns int year or None if unparseable/missing.
    """
    category = (category or "").strip()
    if len(category) >= 4 and category[:4].isdigit():
        year = int(category[:4])
        if 1000 <= year <= 2100:
            return year
    return None


def year_bucket_name(year: int | None) -> str:
    if year is None:
        return "Unparseable"
    if year < 1980:
        return "Pre-1980"
    if 1980 <= year <= 1989:
        return "1980–1989"
    if 1990 <= year <= 1999:
        return "1990–1999"
    if 2000 <= year <= 2009:
        return "2000–2009"
    if 2010 <= year <= 2019:
        return "2010–2019"
    return "2020–2029"  # catch-all for 2020–2029 (and anything 2020+ up to 2029)

def grouped_limits_for_bucket(bucket: str) -> int | None:
    """
    Limits per bucket:
      - Pre-1980: 20
      - each decade (1980–1989 ... 2020–2029): 150
      - Unparseable: None (no limit)
    """
    if bucket == "Pre-1980":
        return 20
    if bucket == "Unparseable":
        return None
    return 150


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")
    with open(path, newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def numeric_views(value: str) -> int:
    try:
        return int(value)
    except Exception:
        return 0

def render_grouped_section(
    section_title: str,
    caption: str,
    wikiproject: str,
    rows: list[dict[str, str]],
) -> list[str]:
    """
    One file → one section, with subsections per time-bucket.
    Rows within each bucket are sorted by yearly_views desc, then title.
    """
    lines: list[str] = []
    lines.append(f"== {section_title} ==")

    # bucket rows
    buckets: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        category = (row.get("category") or "").strip()
        year = parse_category_year(category)
        bucket = year_bucket_name(year)
        buckets.setdefault(bucket, []).append(row)

    # deterministic order of buckets
    bucket_order = ["Pre-1980", "1980–1989", "1990–1999", "2000–2009", "2010–2019", "2020–2029", "Unparseable"]

    for bucket in bucket_order:
        bucket_rows = buckets.get(bucket, [])
        if not bucket_rows:
            continue

        # sort by views desc, then title
        bucket_rows.sort(key=lambda r: (-numeric_views(r.get("yearly_views") or "0"), (r.get("title") or "").lower()))

        # apply per-bucket limits
        limit = grouped_limits_for_bucket(bucket)
        if limit is not None:
            bucket_rows = bucket_rows[:limit]

        # subsection and table
        lines.append(f"=== {bucket} ===")
        write_table_header(lines, caption=caption)

        for row in bucket_rows:
            title = (row.get("title") or "").strip()
            if not title:
                continue
            quality_cell = format_quality_cell((row.get("quality") or "").strip(), wikiproject=wikiproject)
            write_table_row(
                lines=lines,
                rank=(row.get("rank") or "").strip(),
                title=title,
                views=(row.get("yearly_views") or "").strip(),
                quality_cell=quality_cell,
                word_count=(row.get("word_count") or "").strip(),
                description=(row.get("shortdesc") or "").strip(),
            )

        lines.append("|}")
        lines.append("")
    return lines

def process_one_csv(
    section_title: str,
    wikiproject: str,
    caption: str,
    limit: int | None,
    rows: list[dict[str, str]],
) -> list[str]:
    """
    Returns the wikitext lines for one section + table built from the CSV.
    Expects columns:
      rank,pageid,title,category,yearly_views,shortdesc,word_count,quality
    """
    
    lines: list[str] = []
    lines.append(f"== {section_title} ==")

    write_table_header(lines, caption=caption)
    count = 0

    for row in rows:
        title = row.get("title", "").strip()
        if not title:
            continue  # skip malformed rows

        rank = row.get("rank", "").strip()
        views = row.get("yearly_views", "").strip()
        word_count = row.get("word_count", "").strip()
        description = row.get("shortdesc", "").strip()
        quality = row.get("quality", "").strip()

        quality_cell = format_quality_cell(quality, wikiproject=wikiproject)

        write_table_row(
            lines=lines,
            rank=rank,
            title=title,
            views=views,
            quality_cell=quality_cell,
            word_count=word_count,
            description=description,
        )

        count += 1
        if limit is not None and count >= limit:
            break

    lines.append("|}")
    lines.append("")  # blank line after table
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert one or more combined CSVs to a MediaWiki table text file. "
            "Each input CSV becomes a section with a wikitable."
        )
    )
    parser.add_argument(
        "wikiproject",
        help='WikiProject name used in the quality template category, e.g. "video game" or "Spain".',
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help='Input CSV(s). Per-file limits via "path.csv:150". '
             "CSV must have: rank,pageid,title,category,yearly_views,shortdesc,word_count,quality",
    )
    parser.add_argument(
        "--default-limit",
        type=int,
        default=150,
        help="If provided, apply this limit to any input that does not specify its own :N.",
    )
    parser.add_argument(
        "--caption",
        default="[[:Category:REPLACE_ME]]",
        help='Table caption text (default: "[[:Category:REPLACE_ME]]").',
    )
    parser.add_argument(
        "--group-by-category-year",
        action="store_true",
        help=(
            "Group rows by year bucket derived from the beginning of the `category` field "
            "(Pre-1980 top 10; decade buckets top 150; Unparseable no limit). "
            "Per-file :N limits are ignored in this mode."
        ),
    )
    parser.add_argument(
        "--output",
        help="Output path. If omitted, writes to WP_<WikiProject>.txt (spaces replaced with underscores).",
    )
    args = parser.parse_args()

    output_path = derive_output_path(args.wikiproject, args.output)
    input_specs = parse_input_specs(args.inputs, default_limit=args.default_limit)

    all_lines: list[str] = []
    for path, limit in input_specs:
        section_title = path.stem
        rows = read_rows(path)
        if args.group_by_category_year:
            section_lines = render_grouped_section(
                section_title=section_title,
                caption=args.caption,
                wikiproject=args.wikiproject,
                rows=rows,
            )
        else:
            section_lines = process_one_csv(
                section_title=section_title,
                wikiproject=args.wikiproject,
                caption=args.caption,
                limit=limit,
                rows=rows,
            )
        all_lines.extend(section_lines)

    output_path.write_text("\n".join(all_lines), encoding="utf-8")
    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
