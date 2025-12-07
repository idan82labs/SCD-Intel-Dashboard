"""EU TED (Tenders Electronic Daily) data source for European procurement."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class EUTEDSource(BaseDataSource):
    """EU TED API for European public procurement notices.

    No API key required for search operations.
    Documentation: https://api.ted.europa.eu/swagger
    """

    BASE_URL = "https://api.ted.europa.eu/v3"

    # CPV codes relevant to defense/infrared optics
    DEFENSE_CPV_CODES = [
        "35000000",  # Security, fire-fighting, police and defence equipment
        "35300000",  # Weapons, ammunition and associated parts
        "35600000",  # Ordnance and defence equipment
        "38000000",  # Laboratory, optical and precision equipment
        "38300000",  # Measuring instruments
        "38600000",  # Optical instruments
        "38630000",  # Optical instruments (subsection)
        "38636000",  # Optical specialized instruments
    ]

    def __init__(self):
        """Initialize EU TED source."""
        super().__init__(
            name="eu_ted",
            description="European public procurement notices from TED",
        )
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json"},
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
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Search TED notices.

        Args:
            query: Search keywords
            filters: Optional filters (cpv_codes, countries, date_range)
            limit: Maximum results

        Returns:
            List of procurement notices
        """
        if not self._client:
            raise RuntimeError("EU TED source not initialized")

        filters = filters or {}

        # Build query string
        query_parts = [f'"{query}"']

        # Add CPV codes filter
        cpv_codes = filters.get("cpv_codes", self.DEFENSE_CPV_CODES[:3])
        if cpv_codes:
            cpv_query = " OR ".join([f"cpv:{code}" for code in cpv_codes])
            query_parts.append(f"({cpv_query})")

        # Add country filter
        countries = filters.get("countries", [])
        if countries:
            country_query = " OR ".join([f"country:{c}" for c in countries])
            query_parts.append(f"({country_query})")

        # Date range
        start_date = filters.get(
            "start_date",
            (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        )
        end_date = filters.get("end_date", datetime.now().strftime("%Y-%m-%d"))

        try:
            # Use the notice search endpoint
            search_body = {
                "query": " AND ".join(query_parts),
                "fields": [
                    "notice-id",
                    "title",
                    "buyer-name",
                    "buyer-country",
                    "publication-date",
                    "cpv-code",
                    "estimated-value",
                    "currency",
                    "notice-type",
                    "deadline-receipt-tenders",
                ],
                "pageSize": min(limit, 100),
                "page": 1,
                "sortField": "publication-date",
                "sortOrder": "desc",
            }

            response = await self._client.post(
                f"{self.BASE_URL}/notices/search",
                json=search_body,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            notices = data.get("notices", [])

            for notice in notices[:limit]:
                results.append({
                    "type": "eu_procurement",
                    "source": "eu_ted",
                    "notice_id": notice.get("notice-id", ""),
                    "title": notice.get("title", ""),
                    "buyer_name": notice.get("buyer-name", ""),
                    "buyer_country": notice.get("buyer-country", ""),
                    "publication_date": notice.get("publication-date", ""),
                    "cpv_code": notice.get("cpv-code", ""),
                    "estimated_value": notice.get("estimated-value"),
                    "currency": notice.get("currency", "EUR"),
                    "notice_type": notice.get("notice-type", ""),
                    "deadline": notice.get("deadline-receipt-tenders", ""),
                    "url": f"https://ted.europa.eu/notice/{notice.get('notice-id', '')}",
                })

            return results

        except httpx.HTTPError as e:
            print(f"EU TED search error: {e}")
            # Fallback to simpler search endpoint
            return await self._fallback_search(query, limit)

    async def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback search using simpler API endpoint."""
        if not self._client:
            return []

        try:
            params = {
                "q": query,
                "scope": "3",  # All notices
                "size": limit,
            }

            response = await self._client.get(
                f"{self.BASE_URL}/notices",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for notice in data.get("results", data.get("notices", []))[:limit]:
                results.append({
                    "type": "eu_procurement",
                    "source": "eu_ted",
                    "notice_id": notice.get("noticeId", notice.get("id", "")),
                    "title": notice.get("title", notice.get("content", {}).get("title", "")),
                    "buyer_name": notice.get("buyerName", ""),
                    "buyer_country": notice.get("buyerCountry", ""),
                    "publication_date": notice.get("publicationDate", ""),
                    "cpv_code": notice.get("cpvCode", ""),
                    "notice_type": notice.get("noticeType", ""),
                    "url": f"https://ted.europa.eu/notice/{notice.get('noticeId', notice.get('id', ''))}",
                })

            return results

        except httpx.HTTPError as e:
            print(f"EU TED fallback search error: {e}")
            return []

    async def get_notice_details(self, notice_id: str) -> Dict[str, Any]:
        """Get detailed notice information.

        Args:
            notice_id: TED notice ID

        Returns:
            Full notice details
        """
        if not self._client:
            raise RuntimeError("EU TED source not initialized")

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/notices/{notice_id}",
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            print(f"EU TED notice details error: {e}")
            return {}
