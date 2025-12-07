"""RSS feed aggregator data source."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

import httpx

from app.data_sources.base import BaseDataSource


# Default RSS feeds for various industries
DEFAULT_FEEDS = {
    "tech": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
    ],
    "defense": [
        "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
        "https://breakingdefense.com/feed/",
    ],
    "business": [
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://www.reuters.com/rssFeed/businessNews",
    ],
    "patents": [
        "https://www.patentlyapple.com/feed/",
    ],
}


class RSSSource(BaseDataSource):
    """RSS feed aggregator for news monitoring."""

    def __init__(self, custom_feeds: Optional[Dict[str, List[str]]] = None):
        """Initialize RSS source.

        Args:
            custom_feeds: Dictionary of category -> feed URLs
        """
        super().__init__(
            name="rss",
            description="RSS feed aggregator for industry news",
        )
        self.feeds = custom_feeds or DEFAULT_FEEDS
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(timeout=15.0)
        await super().initialize()

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
        await super().close()

    async def search(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        max_results: int = 20,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Search RSS feeds for matching articles.

        Args:
            query: Search keywords (will filter results)
            categories: Feed categories to search (default: all)
            max_results: Maximum results to return

        Returns:
            List of matching articles
        """
        if not FEEDPARSER_AVAILABLE:
            print("RSS source disabled: feedparser not installed")
            return []

        if not self._client:
            raise RuntimeError("RSS source not initialized")

        # Determine which feeds to query
        categories = categories or list(self.feeds.keys())
        feed_urls = []
        for cat in categories:
            if cat in self.feeds:
                feed_urls.extend(self.feeds[cat])

        # Fetch all feeds concurrently
        tasks = [self._fetch_feed(url) for url in feed_urls]
        all_entries = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and filter results
        results = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        for entries in all_entries:
            if isinstance(entries, Exception):
                continue

            for entry in entries:
                # Check if any query term matches title or summary
                title = entry.get("title", "").lower()
                summary = entry.get("summary", "").lower()

                if any(term in title or term in summary for term in query_terms):
                    results.append(entry)

        # Sort by date (newest first) and limit
        results.sort(key=lambda x: x.get("published", ""), reverse=True)
        return results[:max_results]

    async def _fetch_feed(self, url: str) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed.

        Args:
            url: Feed URL

        Returns:
            List of feed entries
        """
        if not FEEDPARSER_AVAILABLE:
            return []

        try:
            response = await self._client.get(url)
            response.raise_for_status()

            # Parse feed
            feed = feedparser.parse(response.text)
            source = urlparse(url).netloc

            entries = []
            for entry in feed.entries[:50]:  # Limit per feed
                published = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6]).isoformat()

                entries.append(
                    {
                        "type": "rss_article",
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "summary": entry.get("summary", "")[:500],
                        "published": published,
                        "source": source,
                        "author": entry.get("author", ""),
                    }
                )

            return entries

        except Exception as e:
            print(f"RSS fetch error for {url}: {e}")
            return []
