import re
from datetime import datetime
from .clients import mw_get
from .types import ArticleMeta

# Highest-to-lowest precedence
QUALITY_ORDER: list[str] = ["FA", "FL", "A", "GA", "B", "C", "Start", "Stub", "List"]

# Strict pattern that mirrors common talk-page categories like:
# "Category:FA-Class articles", "Category:A-Class Foo articles", etc.
QUALITY_PATTERN = re.compile(
    r"^Category:(FA|FL|A|GA|B|C|Start|Stub|List)-Class\b",  # anchored to Category: and -Class
)

def extract_quality(categories: list[dict]) -> str | None:
    """
    Given the 'categories' array from a Talk page query (each item has 'title'),
    return the single best assessment per QUALITY_ORDER, or None if not present.
    After PIQA passed, this should be irrelevant since projects should not have
    separate rankings, but do it anyway just in case.
    """
    found: set[str] = set()
    for category in categories:
        title = category.get("title", "")
        match = QUALITY_PATTERN.search(title)
        if match:
            found.add(match.group(1))  # already in canonical case (e.g., "Start", "FA", ...)
    for grade in QUALITY_ORDER:
        if grade in found:
            return grade
    return None

def extract_wikiprojects(categories: list[dict]) -> list[str]:
    projects: set[str] = set()
    for category in categories:
        title = category.get("title", "")
        match = re.search(r"^Category:WikiProject (.+?) articles$", title)
        if match:
            projects.add(match.group(1))
    return sorted(projects)

def fetch_article_meta(title: str, session) -> ArticleMeta:
    # Base article
    article_data = mw_get({
        "action": "query",
        "prop": "revisions|info|extracts|pageprops",
        "titles": title,
        "rvprop": "ids|timestamp",
        "explaintext": 1,
        "inprop": "url",
    }, session)
    page_data = next(iter(article_data["query"]["pages"].values()))
    pageid = int(page_data["pageid"])

    extract_text = page_data.get("extract", "") or ""
    revision_info = page_data.get("revisions", [])
    rev_id = revision_info[0]["revid"] if revision_info else None
    last_edit = (
        datetime.strptime(revision_info[0]["timestamp"], "%Y-%m-%dT%H:%M:%SZ").date()
        if revision_info else None
    )
    wikidata_id = page_data.get("pageprops", {}).get("wikibase_item", "") or ""
    wikidata_url = f"https://www.wikidata.org/wiki/{wikidata_id}" if wikidata_id else ""
    size_bytes = page_data.get("length", 0)
    word_count = len(extract_text.split())
    rev_url = (
        f"https://en.wikipedia.org/w/index.php?title={title.replace(' ', '_')}&oldid={rev_id}"
        if rev_id else ""
    )
    shortdesc = page_data.get("pageprops", {}).get("wikibase-shortdesc", "") or ""

    # Talk page categories (for quality & projects)
    talk_data = mw_get({
        "action": "query",
        "prop": "categories",
        "titles": f"Talk:{title}",
        "cllimit": "max",
    }, session)
    talk_page = next(iter(talk_data["query"]["pages"].values()))
    talk_categories: list[dict] = talk_page.get("categories", []) if "categories" in talk_page else []

    quality = extract_quality(talk_categories)
    wikiprojects = extract_wikiprojects(talk_categories)

    return ArticleMeta(
        pageid=pageid,
        title=page_data["title"],
        shortdesc=shortdesc,
        size_bytes=size_bytes,
        word_count=word_count,
        last_edit=last_edit,
        rev_id=rev_id,
        rev_url=rev_url,
        wikidata_id=wikidata_id,
        wikidata_url=wikidata_url,
        wikiprojects=wikiprojects,
        quality=quality,
    )
