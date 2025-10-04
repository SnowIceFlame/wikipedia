from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class ArticleRef:
    pageid: int
    title: str
    category: str  # provenance from the category crawl

@dataclass(frozen=True)
class ArticleMeta:
    pageid: int
    title: str
    shortdesc: str
    size_bytes: int
    word_count: int
    last_edit: date | None
    rev_id: int | None
    rev_url: str
    wikidata_id: str
    wikidata_url: str
    wikiprojects: list[str]
    quality: str | None  # e.g., "FA", "A", "GA", "B", "C", "Start", "Stub"

@dataclass(frozen=True)
class PageviewTotal:
    pageid: int
    title: str
    category: str
    yearly_views: int

