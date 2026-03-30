from dataclasses import dataclass, asdict, field

@dataclass
class JSONifiable():
    def json(self) -> dict:
        return asdict(self)

@dataclass
class RedditComment(JSONifiable):
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
class RedditPostData(JSONifiable):
    id_: str
    url: str
    subreddit: str
    author: str
    date_uploaded: str
    title_raw: str
    title: str # title with category and tags removed
    category: str # eg. [F4M]
    tags: list[str] # tags from title (eg. [Tag])
    flair: str
    body_html: str # html so it contains links
    media_urls: list[str]

@dataclass
class RedditPostInteractions(JSONifiable):
    date_scraped: str
    upvotes: int=-1
    comments: list[dict]=field(default_factory=list)
    # user_data: dict=field(default_factory=dict)
    user_tags: list[str]=field(default_factory=list)
    date_added: str=""
