from dataclasses import dataclass, field, asdict
from pathlib import Path
import requests
import subprocess
import json
from bs4 import BeautifulSoup, Tag
from http.cookiejar import MozillaCookieJar

from handymatt.bookmarks_getter import BookmarksGetter

from gwa_downloader.globals import __COOKIES__

# ======================================================================================================================
# region MISC
# ======================================================================================================================

def extract_id_and_title(url):
    p = url.split("/comments/")[-1]
    p = p.split("/")
    id_ = p[0]
    title = p[1].replace("_", " ").title()
    return id_, title

def fetch_reddit_url_soup(url: str) -> BeautifulSoup:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    jar = MozillaCookieJar(__COOKIES__)
    jar.load()
    
    url = url.replace('www.', 'old.')
    res = requests.get(url, cookies=jar, headers=headers)
    if res.status_code != 200:
        raise Exception(f"bad status code: {res.status_code}")
    soup = BeautifulSoup(res.content, 'html.parser')
    if 'over 18?' in soup.select_one('title').text: # type: ignore
        raise Exception("page not properly loaded, 'are you over 18?'")
    return soup

def extract_subreddit(url: str) -> str:
    if "reddit.com/r/" not in url.lower():
        return ""
    start = url.lower().find("/r/") + 3
    end = url.find("/", start)
    if end == -1:
        end = len(url)
    return url[start:end]

def standardize_reddit_url(url: str) -> str:
    url = 'https://www.reddit.com/r/' + url.split('/r/')[-1]
    return url.split('?')[0]

# def _copy_tree(src: str|Path, dst: str|Path) -> None:
#     src = Path(src); dst = Path(dst)
#     for path in src.rglob("*"):
#         if path.is_file():
#             rel = path.relative_to(src)
#             target = dst / rel
#             target.parent.mkdir(parents=True, exist_ok=True)
#             shutil.copy2(path, target)  # overwrites if exists

# ======================================================================================================================
# region POST ITEM
# ======================================================================================================================

@dataclass
class RedditComment():
    user: str
    date: str
    content: str
    upvotes: str
    replies: list["RedditComment"]=field(default_factory=list)

    def json(self) -> dict:
        for i, c in enumerate(self.replies):
            self.replies[i] = c.json() #type:ignore
        return asdict(self)

@dataclass
class GoneWildAudioPost():
    id_: str
    url: str
    subreddit: str
    author: str
    date_uploaded: str
    title_raw: str
    title: str # title with category and tags removed
    category: str # eg. [FF4M]
    tags: list[str]
    flair: str
    body_html: str # html so it contains links
    media_urls: list[str]
    upvotes: int=-1
    comments: list[RedditComment]=field(default_factory=list)

    user_data: dict=field(default_factory=dict)

    def json(self) -> dict:
        for i, c in enumerate(self.comments):
            self.comments[i] = c.json() #type:ignore
        return asdict(self)

def parse_int(value: str) -> int:
    value = value.strip().lower()
    multipliers = {
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000,
    }
    if value[-1] in multipliers:
        return int(float(value[:-1]) * multipliers[value[-1]])
    return int(value)

def _scrapePostInteractions(post: GoneWildAudioPost, siteTable: Tag) -> GoneWildAudioPost:
    post.upvotes = parse_int(siteTable.select('.score.unvoted')[0].text)
    post.comments = []
    return post

# ======================================================================================================================
# region METADATA
# ======================================================================================================================

def _split_raw_title(raw):
    """  """
    parts = raw.split('] ')
    category = parts[0].replace('[', '')
    rest = raw[len(category)+3:]
    parts = rest.replace(']', '').split(' [')
    title = parts[0]
    tags = parts[1:]
    return category, title, tags

def _getBodyAndMediaLinks(siteTable: Tag):
    """ pass this function the .siteTable element. it will extract description html and media links
    and add media-link class to media links """
    media_domains = [
        "soundgasm.net",
        "whyp.it",
    ]
    def _fromMediaDomain(x):
        for dom in media_domains:
            if dom in x: return True
        return False

    desc_el = siteTable.select('.md')[0]
    media_urls = []
    for a in desc_el.select('a[href]'):
        href = a['href']
        if _fromMediaDomain(href):
            media_urls.append(href)
            a['class'] = 'media-link'
    desc_html = desc_el.prettify()
    return desc_html, media_urls

# SCRAPE REDDIT POST
def parseGwaSoup(soup: BeautifulSoup):
    """  """
    siteTable = soup.select_one('#siteTable')
    if siteTable is None:
        raise Exception(f'unable to find .siteTable from old reddit')

    date_uploaded = siteTable.select('time')[0]["datetime"]
    assert isinstance(date_uploaded, str)
    date_uploaded = date_uploaded.split('+')[0].replace('T', ' ')
    title_raw = siteTable.select('a.title')[0].text
    category, title, tags = _split_raw_title(title_raw)

    body_html, media_urls = _getBodyAndMediaLinks(siteTable)

    # 
    post = GoneWildAudioPost(
        id_ = "",
        subreddit = "",
        url = "",
        author = siteTable.select('.author')[0].text,
        date_uploaded = date_uploaded,
        title_raw = title_raw,
        title = title,
        category = category,
        tags = tags,
        flair = siteTable.select('.linkflairlabel')[0].text,
        body_html = body_html,
        media_urls = media_urls,
    )

    # post interactions
    post = _scrapePostInteractions(post, siteTable)
    return post

# ======================================================================================================================
# region URL ITEM
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

def _get_tags_from_bm_location(location: str, target_folder: str) -> list[str]:
    end = location.split(target_folder)[-1]
    if end.endswith("/"):
        end = end[:-1]
    return [ t for t in end.split("/") if t != "" ]

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
