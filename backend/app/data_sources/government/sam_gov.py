"""SAM.gov data source for government opportunities."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class SAMGovSource(BaseDataSource):
    """SAM.gov API for government contract opportunities."""

    BASE_URL = "https://api.sam.gov/opportunities/v2"

    def __init__(self, api_key: str):
        """Initialize SAM.gov source.

        Args:
            api_key: SAM.gov API key
        """
        super().__init__(
            name="sam_gov",
            description="Active US government contract opportunities",
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
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Search contract opportunities.

        Args:
            query: Search keywords
            filters: Additional filters (naics, set_aside, etc.)
            limit: Maximum results

        Returns:
            List of opportunities
        """
        if not self._client:
            raise RuntimeError("SAM.gov source not initialized")

        filters = filters or {}

        # Build query parameters
        params = {
            "api_key": self.api_key,
            "q": query,
            "limit": limit,
            "postedFrom": filters.get(
                "posted_from",
                (datetime.now() - timedelta(days=90)).strftime("%m/%d/%Y"),
            ),
            "postedTo": filters.get(
                "posted_to",
                datetime.now().strftime("%m/%d/%Y"),
            ),
        }

        # Add optional filters
        if filters.get("naics"):
            params["naics"] = filters["naics"]

        if filters.get("set_aside"):
            params["typeOfSetAsideDescription"] = filters["set_aside"]

        if filters.get("notice_type"):
            params["ptype"] = filters["notice_type"]

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for opp in data.get("opportunitiesData", []):
                results.append(
                    {
                        "type": "contract_opportunity",
                        "notice_id": opp.get("noticeId", ""),
                        "title": opp.get("title", ""),
                        "description": opp.get("description", "")[:1000],
                        "solicitation_number": opp.get("solicitationNumber", ""),
                        "department": opp.get("fullParentPathName", ""),
                        "office": opp.get("officeAddress", {}).get("city", ""),
                        "posted_date": opp.get("postedDate", ""),
                        "response_deadline": opp.get("responseDeadLine", ""),
                        "naics_code": opp.get("naicsCode", ""),
                        "set_aside": opp.get("typeOfSetAsideDescription", ""),
                        "notice_type": opp.get("type", ""),
                        "url": opp.get("uiLink", ""),
                    }
                )

            return results

        except httpx.HTTPError as e:
            print(f"SAM.gov search error: {e}")
            return []

    async def get_opportunity_details(self, notice_id: str) -> Dict[str, Any]:
        """Get detailed opportunity information.

        Args:
            notice_id: SAM.gov notice ID

        Returns:
            Opportunity details
        """
        if not self._client:
            raise RuntimeError("SAM.gov source not initialized")

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search",
                params={
                    "api_key": self.api_key,
                    "noticeId": notice_id,
                },
            )
            response.raise_for_status()
            data = response.json()

            opportunities = data.get("opportunitiesData", [])
            return opportunities[0] if opportunities else {}

        except httpx.HTTPError as e:
            print(f"SAM.gov opportunity error: {e}")
            return {}
