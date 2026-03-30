import argparse
from dataclasses import dataclass, fields
from pathlib import Path
from datetime import datetime

from gwa_downloader import (
    url,
    io,
    reddit_post,
    media_down,
    helpers,
    constants,
)

# ======================================================================================================================
# region Main
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

def main(url_items: list[url.URLItem], args: MainArgs):
    """  """

    offline_site_path = Path('.').resolve()
    DATA_DIR = offline_site_path / "data"
    POSTS_DIR = offline_site_path / "pages"
    
    # print urls
    if args.list_urls:
        for i in url_items:
            print(i.url)
        return
        
    # --------------------------------------------------------------------------
    # STEP 1: scrape metadata
    # --------------------------------------------------------------------------

    if not args.only_site:
        for idx, i in enumerate(url_items):
            print("[{}/{}] \"{}\"".format(idx+1, len(url_items), i.url))
            
            # variables
            _, id_, _ = helpers.extract_reddit_url_identifiers(i.url)
            post_data_file = DATA_DIR / f"{id_}.json"
            post_interactions_file = DATA_DIR / f"{id_}-interact.json"

            # scrape
            post_data, post_inter = reddit_post.scrape_reddit_post_data(id_, i.url, i.tags, i.date_added)

            # interactions
            io.write_json(post_inter.json(), post_interactions_file)
            if args.only_update_interactions:
                print('only scraped interactions, continuing')
                continue

            # post data
            if not post_data_file.exists():
                print('writing post data')
                io.write_json(post_data.json(), post_data_file)

            # skip media download
            if args.no_media_download:
                print('skipping media download')
                continue
            
            # [3/3] download media
            post_data.body_html, down_count = media_down.download_media_urls_from_post_body(
                post_data.body_html,
                id_,
                offline_site_path,
            )

            # update data_file
            if down_count > 0:
                io.write_json(post_data.json(), post_data_file)

    # --------------------------------------------------------------------------
    # STEP 2: create offline site
    # --------------------------------------------------------------------------

    if not args.no_site:

        # save post overview data into `data/_general.json`
        ...

        # copy site template files
        print('copying site_template')
        # helpers.copy_frontend()

        # download jquery (if using)
        ...

    # END MAIN
        
# ======================================================================================================================
# region CLI
# ======================================================================================================================

def get_url_items(args: argparse.Namespace) -> tuple[list[url.URLItem], int]:

    # get urls
    url_items = []
    if args.url:
        url_items = [
            url.URLItem(
                url = args.url,
                date_added = str(datetime.now()).split('.')[0],
            )
        ]
    elif args.bookmarks:
        url_items = url.get_reddit_urls_from_bookmarks(
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

# cli
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
    constants.__COOKIES__ = args.cookies
    if not Path(args.cookies).exists():
        print('\nerror: please ensure cookies.txt exists in the current directory')
        exit(1)
    
    # main
    print()
    main(
        url_items=url_items,
        args=MainArgs.from_dict(vars(args)),
    )
    print()
