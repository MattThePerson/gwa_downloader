""" misc helper functions """
import shutil
from pathlib import Path
import importlib.resources as resources

import gwa_downloader.frontend as frontend

def copy_frontend():
    target_dir = Path(".")
    source = resources.files(frontend)

    def copy_dir(src, dst):
        for item in src.iterdir():
            dest = dst / item.name
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                copy_dir(item, dest)
            else:
                with resources.as_file(item) as file_path:
                    shutil.copy(file_path, dest)

    copy_dir(source, target_dir)
    print(f"Copied frontend files to {target_dir}")

def extract_reddit_url_identifiers(url: str):
    """ given a url to a reddit post, extracts the subreddit, post id and title """
    sub = ""
    p = url.split("/comments/")[-1]
    p = p.split("/")
    id_ = p[0]
    title = p[1].replace("_", " ").title()
    return sub, id_, title

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
