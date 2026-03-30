from datetime import datetime
import requests
from bs4 import BeautifulSoup, Tag
from http.cookiejar import MozillaCookieJar

from gwa_downloader import constants, struct, helpers

# ======================================================================================================================
# region MISC
# ======================================================================================================================

def _fetch_reddit_url_soup(url: str) -> BeautifulSoup:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    jar = MozillaCookieJar(constants.__COOKIES__)
    jar.load()
    
    url = url.replace('www.', 'old.')
    res = requests.get(url, cookies=jar, headers=headers)
    if res.status_code != 200:
        raise Exception(f"bad status code: {res.status_code}")
    soup = BeautifulSoup(res.content, 'html.parser')
    if 'over 18?' in soup.select_one('title').text: # type: ignore
        raise Exception("page not properly loaded, 'are you over 18?'")
    return soup

def _extract_subreddit(url: str) -> str:
    if "reddit.com/r/" not in url.lower():
        return ""
    start = url.lower().find("/r/") + 3
    end = url.find("/", start)
    if end == -1:
        end = len(url)
    return url[start:end]

def _standardize_reddit_url(url: str) -> str:
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
def _parseGwaSoup(soup: BeautifulSoup) -> tuple[struct.RedditPostData, struct.RedditPostInteractions]:
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

    # post
    post = struct.RedditPostData(
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

    # inter
    inter = struct.RedditPostInteractions(
        upvotes = helpers.parse_int(siteTable.select('.score.unvoted')[0].text),
        date_scraped = str(datetime.now()).split('.')[0],
        comments = [],
    )

    # post interactions
    return post, inter

# ======================================================================================================================
# region Public
# ======================================================================================================================

def scrape_reddit_post_data(id_: str, url: str, tags: list[str], date_added: str) -> tuple[struct.RedditPostData, struct.RedditPostInteractions]:
    """  """
    soup = _fetch_reddit_url_soup(url)
    post, inter = _parseGwaSoup(soup)

    # hydrate post
    post.id_ = id_
    post.subreddit = _extract_subreddit(url)
    post.url = _standardize_reddit_url(url)

    # hydrate interactions
    inter.user_tags = tags
    inter.date_added = date_added

    return post, inter
