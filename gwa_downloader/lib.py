from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import json

from handymatt.bookmarks_getter import BookmarksGetter

# ======================================================================================================================
# region MISC
# ======================================================================================================================

def extract_id_and_title(url):
    p = url.split("/comments/")[-1]
    p = p.split("/")
    id_ = p[0]
    title = p[1].replace("_", " ").title()
    return id_, title

# ======================================================================================================================
# region Media Download
# ======================================================================================================================

def getUrlData(url: str) -> dict:
    """  """
    cmd = [
        "yt-dlp",
        "--dump-json", url,
        "--verbose",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise subprocess.SubprocessError(f"yt-dlp failed with exit code: {result.returncode}\nstderr: {result.stderr}")
    data = json.loads(result.stdout)
    assert isinstance(data, dict) and len(data) > 0
    return data

def downloadMedia(url: str, savepath: Path):
    """ downloads media from url into folder """
    savepath.parent.mkdir(exist_ok=True, parents=True)
    cmd = [
        "yt-dlp",
        url,
        "-o", savepath,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise Exception(f"stderr from subprocess ({r.returncode}):\n{r.stderr}")

# ======================================================================================================================
# region URL ITEM
# ======================================================================================================================

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

def _url_from_subreddit(url: str) -> bool:
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
    books = [ bm for bm in books if "/comments/" in bm.url and _url_from_subreddit(bm.url) ]
    return [
        URLItem(
            url=b.url,
            date_added=b.date_added,
            tags=_get_tags_from_string(b.name),
            name=b.name,
        )
        for b in books
    ]
