"""Exa.ai neural web search data source."""

from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class ExaSource(BaseDataSource):
    """Exa.ai neural/embeddings-based web search.

    Superior to keyword search for technical and specialized queries.
    Supports neural, keyword, and auto (hybrid) search modes.
    """

    BASE_URL = "https://api.exa.ai"

    def __init__(self, api_key: str):
        """Initialize Exa source.

        Args:
            api_key: Exa API key
        """
        super().__init__(
            name="exa",
            description="Neural web search for technical and specialized content",
        )
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        await super().initialize()

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
        await super().close()

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "auto",
        use_autoprompt: bool = True,
        include_text: bool = True,
        include_highlights: bool = True,
        start_published_date: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Execute a neural web search using Exa.

        Args:
            query: Search query (can be natural language)
            num_results: Number of results (1-100)
            search_type: "auto", "neural", or "keyword"
            use_autoprompt: Let Exa optimize query for neural search
            include_text: Include full text content
            include_highlights: Include relevant highlights
            start_published_date: Filter by date (YYYY-MM-DD)
            category: Filter by category (company, news, pdf, etc.)

        Returns:
            List of search results with content
        """
        if not self._client:
            raise RuntimeError("Exa source not initialized")

        payload: Dict[str, Any] = {
            "query": query,
            "numResults": min(num_results, 100),
            "type": search_type,
            "useAutoprompt": use_autoprompt,
            "contents": {
                "text": include_text,
                "highlights": include_highlights,
            },
        }

        if start_published_date:
            payload["startPublishedDate"] = start_published_date

        if category:
            payload["category"] = category

        try:
            response = await self._client.post(
                f"{self.BASE_URL}/search",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                result = {
                    "type": "web_result",
                    "source": "exa",
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0),
                    "published_date": item.get("publishedDate"),
                    "author": item.get("author"),
                }

                # Add text content if available
                if item.get("text"):
                    result["content"] = item["text"][:5000]  # Limit content size

                # Add highlights if available
                if item.get("highlights"):
                    result["highlights"] = item["highlights"]

                results.append(result)

            return results

        except httpx.HTTPError as e:
            print(f"Exa search error: {e}")
            return []

    async def find_similar(
        self,
        url: str,
        num_results: int = 10,
        exclude_source_domain: bool = True,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Find pages similar to a given URL.

        Args:
            url: URL to find similar content for
            num_results: Number of results
            exclude_source_domain: Exclude results from same domain

        Returns:
            List of similar pages
        """
        if not self._client:
            raise RuntimeError("Exa source not initialized")

        payload = {
            "url": url,
            "numResults": num_results,
            "excludeSourceDomain": exclude_source_domain,
            "contents": {
                "text": True,
                "highlights": True,
            },
        }

        try:
            response = await self._client.post(
                f"{self.BASE_URL}/findSimilar",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "type": "similar_page",
                    "source": "exa",
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0),
                    "content": item.get("text", "")[:5000],
                    "highlights": item.get("highlights", []),
                })

            return results

        except httpx.HTTPError as e:
            print(f"Exa find_similar error: {e}")
            return []

    async def get_contents(
        self,
        urls: List[str],
        include_text: bool = True,
        include_highlights: bool = False,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Get contents of specific URLs.

        Args:
            urls: List of URLs to fetch
            include_text: Include full text
            include_highlights: Include highlights

        Returns:
            List of page contents
        """
        if not self._client:
            raise RuntimeError("Exa source not initialized")

        payload = {
            "urls": urls[:10],  # Max 10 URLs per request
            "contents": {
                "text": include_text,
                "highlights": include_highlights,
            },
        }

        try:
            response = await self._client.post(
                f"{self.BASE_URL}/contents",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "type": "page_content",
                    "source": "exa",
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": item.get("text", ""),
                    "highlights": item.get("highlights", []),
                })

            return results

        except httpx.HTTPError as e:
            print(f"Exa get_contents error: {e}")
            return []
