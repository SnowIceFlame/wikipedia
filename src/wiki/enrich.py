from .types import PageviewTotal, ArticleMeta, ArticleRef
from .pageviews import get_yearly_total_views
from .mw import fetch_article_meta
from .clients import mw_session


def compute_yearly_views(
    articles: list[ArticleRef], start: str, end: str
) -> list[PageviewTotal]:
    """
    For each article, compute the total views across [start, end) (monthly granularity).
    Returns a list of PageviewTotal records.
    """
    session = mw_session()
    results: list[PageviewTotal] = []
    for article in articles:
        total_views = get_yearly_total_views(session, article.title, start, end)
        results.append(
            PageviewTotal(
                pageid=article.pageid,
                title=article.title,
                category=article.category,
                yearly_views=total_views,
            )
        )
    return results


def fetch_metadata(articles: list[ArticleRef]) -> list[ArticleMeta]:
    """
    For each article, fetch ArticleMeta using the MediaWiki API and Talk-page categories.
    """
    session = mw_session()
    metadata_records: list[ArticleMeta] = []
    for article in articles:
        metadata_records.append(fetch_article_meta(article.title, session))
    return metadata_records
