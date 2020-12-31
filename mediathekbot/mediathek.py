import logging
import feedparser
from urllib.parse import quote
from typing import Tuple, Generator
from time import mktime
from datetime import datetime

log = logging.getLogger('rich')

FEED_URL = 'https://mediathekviewweb.de/feed?query={}'


def query_feed(query: str) -> Generator[Tuple, None, None]:
    """
    This method should return a list of tuples
    """
    log.debug('Fetching feed for "%s"', query)

    feed = feedparser.parse(FEED_URL.format(quote(query)))

    for entry in feed['entries']:
        entry_id = entry['id']
        title = entry['title']
        author = entry['author']
        duration = entry['duration']
        summary = entry['summary']
        video_url = entry['link']
        website_url = entry['websiteurl']
        published = datetime.fromtimestamp(mktime(entry['published_parsed']))
        yield (entry_id, title, author, duration, summary, video_url, website_url, published)
