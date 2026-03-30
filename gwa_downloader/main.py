import argparse
from dataclasses import dataclass, fields
from bs4 import BeautifulSoup
import os
from pathlib import Path
import json
from datetime import datetime

from gwa_downloader.globals import __COOKIES__
from gwa_downloader import lib

# ======================================================================================================================
# region MAIN
# ======================================================================================================================

@dataclass
class MainArgs:
    list_urls: bool=False
    only_update_interactions: bool=False
    redo_scraping: bool=False
    no_media_download: bool=False
    no_site: bool=False
    only_site: bool=False

    @staticmethod
    def from_dict(d: dict) -> "MainArgs":
        valid_keys = { f.name for f in fields(MainArgs) }
        filtered = { k: v for k, v in d.items() if k in valid_keys }
        return MainArgs(**filtered)

def main(url_items: list[lib.URLItem], args: MainArgs):

    offline_site_path = Path('.').resolve()
    DATA_DIR = offline_site_path / "data"
    POSTS_DIR = offline_site_path / "pages"
    
    # print urls
    if args.list_urls:
        for i in url_items:
            # print(i.date_added, i.name[:80])
            print(i.url[:30], i.tags)
    
    return
    
    # --------------------------------------------------------------------------
    # STEP 1: scrape metadata
    # --------------------------------------------------------------------------

    if True: # TODO: ???
        for idx, i in enumerate(url_items):
            print("[{}/{}] \"{}\"".format(idx+1, len(url_items), i.url))
            id_, _ = lib.extract_id_and_title(i.url)
            savepath = DATA_DIR / f"{id_}.json"

            if os.path.exists(savepath) and not args.redo_scraping:
                print('metadata already exists, continuing')
                continue
            
            print('requesting post soup')
            soup = lib.fetch_reddit_url_soup(i.url)
            post = lib.parseGwaSoup(soup)
            post.id_ = id_
            post.subreddit = lib.extract_subreddit(i.url)
            post.url = lib.standardize_reddit_url(i.url)

            # add user data
            post.user_data = {
                "user_tags": i.tags,
                "date_added": i.date_added,
                "date_last_scraped": str(datetime.now()).split('.')[0],
            }

            print('saving metadata to:', savepath)
            with open(savepath, 'w') as f:
                json.dump(post.json(), f, indent=4)

    # --------------------------------------------------------------------------
    # STEP 2: download media
    # --------------------------------------------------------------------------

    if not args.no_media_download:
        metadata_files = sorted(DATA_DIR.glob('*.json'))
        for idx, file in enumerate(metadata_files):
            id_ = file.stem
            print('[{}/{}] checking media for id: {}'.format(idx+1, len(metadata_files), id_))

            # check media exists
            post_media_dir = offline_site_path / "media" / id_
            if any(post_media_dir.glob('*')):
                print('media exists for post, continuing')
                continue

            # get soup and a_els
            with open(file, 'r') as f:
                post_data = json.load(f)
            soup = BeautifulSoup(post_data['body_html'], 'html.parser')
            a_els_to_handle = soup.select('a.media-link:not([data-something])')
            a_els_handled = 0

            # handle media download
            for a_idx, a_el in enumerate(a_els_to_handle):
                href = str(a_el.get("href", ""))
                assert href != ""
                ytdlp_data = lib.getUrlData(str(href))
                assert isinstance(ytdlp_data, dict) and len(ytdlp_data) != 0
                media_id, media_title, extractor, ext = ytdlp_data['id'], ytdlp_data['title'], ytdlp_data['extractor'], ytdlp_data['ext']

                # 
                savepath_rel = Path("media") / id_ / f"[{extractor}] [{media_id}] {media_title}.{ext}"
                savepath = offline_site_path / savepath_rel
                print('  ({}/{}) media: "{}"'.format(a_idx+1, len(a_els_to_handle), savepath))
                if savepath.exists():
                    print('media already exists')
                else:
                    try:
                        lib.downloadMedia(href, savepath)
                    except Exception as e:
                        print('oh no, something went boo boo')
                    a_el["data-local-media-src"] = str(savepath_rel)
                    a_els_handled += 1
            
            # save updates to data
            if a_els_handled > 0:
                post_data["body_html"] = soup.prettify()
                with open(file, 'w') as f:
                    json.dump(post_data, f, indent=4)
            
    # --------------------------------------------------------------------------
    # STEP 3: create offline site
    # --------------------------------------------------------------------------

    if not args.no_site:

        # copy site template files
        print('copying site_template')
        # _copy_tree("./site_template", offline_site_path)

        # download jquery (if using)
        ...

        # create post html files
        with open('post_template.html', 'r') as f:
            post_template = ''.join(f.readlines())
        
        postsData = {}
        for file in DATA_DIR.glob('*.json'):
            id_ = file.stem
            print('id:', id_)
            savepath = POSTS_DIR / f"{id_}.html"
            savepath.parent.mkdir(exist_ok=True)
            with open(file, 'r') as f:
                data = json.load(f)
            json_str = json.dumps(data, indent=4)
            post_template = post_template.replace("/*STARTREPLACE*/{}/*ENDREPLACE*/", json_str)
            with open(savepath, 'w') as f:
                f.write(post_template)
            
            # save to postData
            del data["comments"]; del data["body_html"]
            postsData[id_] = data

        # create home page data
        savepath = offline_site_path / "home-page-data.js"
        with open(savepath, 'w') as f:
            f.write(f"const posts = {json.dumps(postsData, indent=4)};\n")

    # END MAIN
        
# ======================================================================================================================
# region CLI
# ======================================================================================================================

def get_url_items(args: argparse.Namespace) -> tuple[list[lib.URLItem], int]:

    # get urls
    url_items = []
    if args.url:
        url_items = [
            lib.URLItem(
                url = args.url,
                date_added = str(datetime.now()).split('.')[0],
            )
        ]
    elif args.bookmarks:
        url_items = lib.get_reddit_urls_from_bookmarks(
            browser=args.bookmarks,
            profile=args.browser_profile,
        )
    elif args.file:
        raise NotImplementedError("no file reading yet")
    elif args.feed:
        raise NotImplementedError("no feed getting yet")
    elif not args.only_site:
        print("please provide some urls with --url or --file or --bookmarks\n")
        return url_items, 1

    # add user tags
    if args.tag != []:
        for i in url_items:
            i.tags.extend(args.tag)
    
    # urls check
    if not args.only_site:
        if len(url_items) == 0:
            print("no urls fetched")
            exit(0)
        print(f'fetched {len(url_items)} urls')
    
    return url_items, 0

# CLI
def cli():

    # argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", "-u", help="Give single url to download. Can also give id of post")
    parser.add_argument("--file", "-f", help="file from which to read urls") # TODO: implement
    parser.add_argument("--bookmarks", "-b", help="Give browser to get bookmarks from")
    parser.add_argument("--browser-profile", default="Default", help="Give the browser profile name")
    
    # feed select # TODO: implement
    parser.add_argument("--feed", default="best", choices=["best", "top", "new"], help="")
    parser.add_argument("--feed-sort", default="all", choices=["all", "year", "month"], help="")
    parser.add_argument("--feed-limit", type=int, help="")
    
    # managing options
    parser.add_argument("--tag", action='append', default=[], help="Give list of tags add to posts")
    parser.add_argument("--redo", action="store_true", help="Redo scraping and downloading for existing posts")
    parser.add_argument("--update-comments-only", action="store_true", help="Redo scraping of interactions only") # TODO: implement

    # other options
    parser.add_argument("--cookies", default="cookies.txt", help="Give name of cookies.txt file to use")
    parser.add_argument("--cookies-from-browser", help="Give name of browser to get cookies from (will download)") # TODO: implement

    # dev options
    parser.add_argument("--no-media", action="store_true", help="Skip downloading of media")
    parser.add_argument("--no-site", action="store_true", help="Skip copying/creation of offline site")
    parser.add_argument("--only-site", action="store_true", help="Only create site from existing data")
    parser.add_argument("--list-urls", action="store_true", help="")
    # parser.add_argument("--no-scrape", action="store_true", help="")

    args = parser.parse_args()

    # SPLASH ❤️
    print('\nWelcome to r/GoneWildAudio downloader! ❤️\n')

    # get url items
    url_items, ret_code = get_url_items(args)
    if ret_code != 0:
        exit(0)
    
    # cookies
    if args.cookies_from_browser:
        raise NotImplementedError("not cookies from browser")
    __COOKIES__ = args.cookies
    
    # main
    print()
    main(
        url_items=url_items,
        args=MainArgs.from_dict(vars(args)),
    )
    print()
