from dataclasses import dataclass, field

from handymatt.bookmarks_getter import BookmarksGetter

@dataclass
class URLItem:
    url: str
    date_added: str
    tags: list[str]=field(default_factory=list)
    name: str=""

def _get_tags_from_string(x: str) -> list[str]:
    tags = []
    parts = x.split(' #')
    i = len(parts)-1
    while i > 0:
        p = parts[i]
        if " " in p or p == "":
            break
        tags.append(p)
        i -= 1
    return tags

def _url_is_from_subreddit(url: str) -> bool:
    subreddits = [
        "r/GoneWildAudio",
    ]
    url = url.lower()
    for sub in subreddits:
        if sub.lower() in url:
            return True
    return False

def get_reddit_urls_from_bookmarks(browser="brave", profile="Default") -> list[URLItem]:
    bm_getter = BookmarksGetter(browser=browser.lower(), profile=profile)
    books = bm_getter.get_bookmarks(domain="reddit.com")
    books = [ bm for bm in books if "/comments/" in bm.url and _url_is_from_subreddit(bm.url) ]
    return [
        URLItem(
            url=b.url,
            date_added=b.date_added,
            tags=_get_tags_from_string(b.name),
            name=b.name,
        )
        for b in books
    ]
