"""USAspending.gov data source for federal contracts."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class USASpendingSource(BaseDataSource):
    """USAspending.gov API for federal contract data."""

    BASE_URL = "https://api.usaspending.gov/api/v2"

    def __init__(self):
        """Initialize USAspending source."""
        super().__init__(
            name="usaspending",
            description="US federal government contract awards and spending",
        )
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
        """Search federal contracts.

        Args:
            query: Search keywords
            filters: Additional filters (agency, naics, date_range, etc.)
            limit: Maximum results

        Returns:
            List of contract awards
        """
        if not self._client:
            raise RuntimeError("USAspending source not initialized")

        filters = filters or {}

        # Build search payload
        payload = {
            "filters": {
                "keywords": [query],
                "time_period": filters.get(
                    "time_period",
                    [
                        {
                            "start_date": (datetime.now() - timedelta(days=365 * 2)).strftime(
                                "%Y-%m-%d"
                            ),
                            "end_date": datetime.now().strftime("%Y-%m-%d"),
                        }
                    ],
                ),
            },
            "limit": limit,
            "page": 1,
        }

        # Add optional filters
        if filters.get("naics_codes"):
            payload["filters"]["naics_codes"] = filters["naics_codes"]

        if filters.get("agencies"):
            payload["filters"]["agencies"] = [
                {"type": "awarding", "tier": "toptier", "name": a}
                for a in filters["agencies"]
            ]

        if filters.get("recipient_name"):
            payload["filters"]["recipient_search_text"] = filters["recipient_name"]

        try:
            response = await self._client.post(
                f"{self.BASE_URL}/search/spending_by_award/",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for award in data.get("results", []):
                results.append(
                    {
                        "type": "federal_contract",
                        "award_id": award.get("generated_internal_id", ""),
                        "piid": award.get("Award ID", ""),
                        "description": award.get("Description", ""),
                        "recipient": award.get("Recipient Name", ""),
                        "awarding_agency": award.get("Awarding Agency", ""),
                        "awarding_sub_agency": award.get("Awarding Sub Agency", ""),
                        "award_amount": award.get("Award Amount", 0),
                        "start_date": award.get("Start Date", ""),
                        "end_date": award.get("End Date", ""),
                        "contract_type": award.get("Contract Award Type", ""),
                        "naics_code": award.get("NAICS Code", ""),
                        "naics_description": award.get("NAICS Description", ""),
                    }
                )

            return results

        except httpx.HTTPError as e:
            print(f"USAspending search error: {e}")
            return []

    async def get_recipient_profile(self, recipient_id: str) -> Dict[str, Any]:
        """Get detailed recipient (company) profile.

        Args:
            recipient_id: USAspending recipient ID

        Returns:
            Recipient profile data
        """
        if not self._client:
            raise RuntimeError("USAspending source not initialized")

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/recipient/{recipient_id}/",
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            print(f"USAspending recipient error: {e}")
            return {}

    async def get_award_details(self, award_id: str) -> Dict[str, Any]:
        """Get detailed award information.

        Args:
            award_id: Award internal ID

        Returns:
            Award details
        """
        if not self._client:
            raise RuntimeError("USAspending source not initialized")

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/awards/{award_id}/",
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            print(f"USAspending award error: {e}")
            return {}
