""" media downloading using yt-dlp """
from pathlib import Path
import subprocess
import json
from bs4 import BeautifulSoup

# ======================================================================================================================
# region Private
# ======================================================================================================================

def _get_ytdlp_metadata(url: str) -> dict:
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

def _downloadMedia(url: str, savepath: Path):
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
# region Public
# ======================================================================================================================

def download_media_urls_from_post_body(body_html: str, id_: str, path: Path) -> tuple[str, int]:
    soup = BeautifulSoup(body_html, 'html.parser')
    a_els_to_handle = soup.select('a.media-link:not([data-local-media-src])')
    a_els_handled = 0
    
    # handle media download
    for a_idx, a_el in enumerate(a_els_to_handle):
        href = str(a_el.get("href", ""))
        assert href != ""
        ytdlp_data = _get_ytdlp_metadata(str(href))
        assert isinstance(ytdlp_data, dict) and len(ytdlp_data) != 0

        # determine savepath
        media_id = ytdlp_data['id']
        media_title = ytdlp_data['title']
        extractor = ytdlp_data['extractor']
        ext = ytdlp_data['ext']
        savepath_rel = Path("media") / id_ / f"[{extractor}] [{media_id}] {media_title}.{ext}"
        savepath = path / savepath_rel

        print('  ({}/{}) media: "{}"'.format(a_idx+1, len(a_els_to_handle), savepath))

        if savepath.exists():
            print('media already exists')
            continue

        # download
        try:
            _downloadMedia(href, savepath)
        except Exception as e:
            print('oh no, something went boo boo')
        a_el["data-local-media-src"] = str(savepath_rel)
        a_els_handled += 1

    return soup.prettify(), a_els_handled
