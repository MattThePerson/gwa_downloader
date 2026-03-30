# r/GoneWildAudio downloader

A python (PyPi) package for downloading posts from r/GoneWildAudio and creating an offline site for exploring/listening. 

## Installation

It's recommended to install via pipx (`pipx install gwa-down`). If you don't want to get pipx, just use pip. 

NOTE: If you still have no clue what to do, see the *Installation for noobs* section at the end xD

## Basic usage

1. Open a terminal and navigate to an empty folder of your choice.
2. Give `gwa-down` url(s) to download (eg. `gwa-down --url [URL]`). See `CLI options` section for more info.
3. This will scrape the post metadata and download any media files for the urls. Afterwards, the folder contain an index.html file and you can serve it, eg. using `python3 -m http.server`.
    - Additionally a `site_noserver/` folder will be created which does not need a server, just open `site_noserver/index.html` in a browser.

## CLI Options

```sh

# url selection
--url # url (or id) to download
--file
--bookmarks # [chrome|brave|firefox]
--browser-profile # default=Default

# feed selection (upcoming)
--feed # [top|best|hot|new]
--sort # [all|year|month]
--limit

# managing options
--tag # append, user tags added to handled urls (will overwrite existing tags)
--update-comments-only # skips download and

# other options
--cookies # default=cookies.txt
--cookies-from-browser # uses yt-dlp to save the cookies

# dev other options
--no-download
--no-site
--no-site-noserver

```

## Other

### Upcoming features

- ability to fetch posts by feed
- ability to rescrape only comments/upvotes
- site that doesn't require a server

### Instalation for noobs

To use this package, you need:

1. A terminal
2. Python

If needed, find a tutorial on how to use a terminal and install python.

Then, you should install the `gwa-down` package using `pip install gwa-down`. You can ensure the installation worked by typing `gwa-down --version` into the terminal (it should print the version, else it failed).



