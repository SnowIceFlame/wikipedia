import csv
from pathlib import Path
from typing import Iterable

from .types import ArticleRef, PageviewTotal, ArticleMeta


def read_article_refs(path: str | Path) -> list[ArticleRef]:
    article_refs: list[ArticleRef] = []
    with open(path, newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            article_refs.append(
                ArticleRef(
                    pageid=int(row["pageid"]),
                    title=row["title"],
                    category=row.get("category", ""),
                )
            )
    return article_refs


def write_views(path: str | Path, rows: Iterable[PageviewTotal]) -> None:
    with open(path, "w", newline="") as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(["pageid", "title", "category", "yearly_views"])
        for record in rows:
            writer.writerow(
                [record.pageid, record.title, record.category, record.yearly_views]
            )


def write_metadata(path: str | Path, rows: Iterable[ArticleMeta]) -> None:
    with open(path, "w", newline="") as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(
            [
                "pageid",
                "title",
                "shortdesc",
                "size_bytes",
                "word_count",
                "quality",
                "last_edit",
                "wikiprojects",
                "rev_id",
                "rev_url",
                "wikidata_id",
                "wikidata_url",
            ]
        )
        for meta in rows:
            writer.writerow(
                [
                    meta.pageid,
                    meta.title,
                    meta.shortdesc,
                    meta.size_bytes,
                    meta.word_count,
                    meta.quality or "",
                    meta.last_edit.isoformat() if meta.last_edit else "",
                    "; ".join(meta.wikiprojects),
                    meta.rev_id or "",
                    meta.rev_url,
                    meta.wikidata_id,
                    meta.wikidata_url,
                ]
            )
