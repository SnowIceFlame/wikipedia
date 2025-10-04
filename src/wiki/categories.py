from collections import deque
from .clients import mw_get

def fetch_category_members(category_title: str, member_type: str, session) -> list[dict]:
    if not category_title.startswith("Category:"):
        category_title = f"Category:{category_title}"
    members: list[dict] = []
    continue_token: str | None = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmlimit": "max",
            "cmtype": member_type,
        }
        if continue_token:
            params["cmcontinue"] = continue_token
        payload = mw_get(params, session)
        members.extend(payload["query"]["categorymembers"])
        continue_token = payload.get("continue", {}).get("cmcontinue")
        if not continue_token:
            break
    return members


def crawl_category(root_category: str, max_depth: int, exclude: set[str] | None, session) -> tuple[dict[int, tuple[str, str]], set[str]]:
    """
    Returns:
      articles: {pageid: (title, source_category_without_prefix)}
      visited_categories: set of visited category titles (with 'Category:' prefix)
    """
    exclude = exclude or set()
    if not root_category.startswith("Category:"):
        root_category = f"Category:{root_category}"

    queue = deque([(root_category, 0)])
    visited_categories: set[str] = set()
    articles: dict[int, tuple[str, str]] = {}

    while queue:
        category_title, depth = queue.popleft()
        if category_title in visited_categories:
            continue
        visited_categories.add(category_title)

        for item in fetch_category_members(category_title, "page", session):
            articles[item["pageid"]] = (item["title"], category_title.removeprefix("Category:"))

        if depth < max_depth:
            for subcat in fetch_category_members(category_title, "subcat", session):
                sub_title = subcat["title"]
                if sub_title not in visited_categories and sub_title not in exclude:
                    queue.append((sub_title, depth + 1))

    return articles, visited_categories

