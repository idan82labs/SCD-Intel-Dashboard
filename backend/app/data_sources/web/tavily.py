"""Tavily web search data source."""

from typing import Any, Dict, List

import httpx

from app.data_sources.base import BaseDataSource


class TavilySource(BaseDataSource):
    """Tavily AI-powered web search."""

    BASE_URL = "https://api.tavily.com"

    def __init__(self, api_key: str):
        """Initialize Tavily source.

        Args:
            api_key: Tavily API key
        """
        super().__init__(
            name="tavily",
            description="AI-powered web search for current information",
        )
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(timeout=30.0)
        await super().initialize()

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
        await super().close()

    async def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 10,
        include_answer: bool = True,
        include_raw_content: bool = False,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Execute a web search using Tavily.

        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            max_results: Maximum number of results
            include_answer: Include AI-generated answer
            include_raw_content: Include full page content

        Returns:
            List of search results
        """
        if not self._client:
            raise RuntimeError("Tavily source not initialized")

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
        }

        try:
            response = await self._client.post(
                f"{self.BASE_URL}/search",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            results = []

            # Add AI answer if available
            if include_answer and data.get("answer"):
                results.append(
                    {
                        "type": "ai_answer",
                        "content": data["answer"],
                        "query": query,
                    }
                )

            # Add search results
            for item in data.get("results", []):
                results.append(
                    {
                        "type": "web_result",
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                        "score": item.get("score", 0),
                        "published_date": item.get("published_date"),
                    }
                )

            return results

        except httpx.HTTPError as e:
            print(f"Tavily search error: {e}")
            return []
