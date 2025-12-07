"""USPTO patent data source."""

from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class USPTOSource(BaseDataSource):
    """USPTO Patent Database API."""

    # PatentsView API
    BASE_URL = "https://api.patentsview.org/patents/query"

    def __init__(self):
        """Initialize USPTO source."""
        super().__init__(
            name="uspto",
            description="US Patent and Trademark Office patent database",
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
        """Search USPTO patents.

        Args:
            query: Search keywords (searches title and abstract)
            filters: Additional filters (assignee, date_range, cpc_code)
            limit: Maximum results

        Returns:
            List of patents
        """
        if not self._client:
            raise RuntimeError("USPTO source not initialized")

        filters = filters or {}

        # Build query
        query_conditions = [{"_text_any": {"patent_title": query}}]

        # Add optional filters
        if filters.get("assignee"):
            query_conditions.append(
                {"_contains": {"assignee_organization": filters["assignee"]}}
            )

        if filters.get("cpc_code"):
            query_conditions.append(
                {"_begins": {"cpc_subgroup_id": filters["cpc_code"]}}
            )

        if filters.get("date_from"):
            query_conditions.append(
                {"_gte": {"patent_date": filters["date_from"]}}
            )

        # Build payload
        payload = {
            "q": {"_and": query_conditions} if len(query_conditions) > 1 else query_conditions[0],
            "f": [
                "patent_number",
                "patent_title",
                "patent_abstract",
                "patent_date",
                "patent_type",
                "assignee_organization",
                "assignee_country",
                "inventor_first_name",
                "inventor_last_name",
                "cpc_group_id",
                "cpc_group_title",
            ],
            "o": {"per_page": limit},
            "s": [{"patent_date": "desc"}],
        }

        try:
            response = await self._client.post(
                self.BASE_URL,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for patent in data.get("patents", []):
                # Extract assignees
                assignees = [
                    a.get("assignee_organization", "Unknown")
                    for a in patent.get("assignees", [])
                ]

                # Extract inventors
                inventors = [
                    f"{i.get('inventor_first_name', '')} {i.get('inventor_last_name', '')}".strip()
                    for i in patent.get("inventors", [])
                ]

                # Extract CPC codes
                cpc_codes = [
                    {
                        "code": c.get("cpc_group_id", ""),
                        "title": c.get("cpc_group_title", ""),
                    }
                    for c in patent.get("cpcs", [])[:5]
                ]

                results.append(
                    {
                        "type": "patent",
                        "patent_number": patent.get("patent_number", ""),
                        "title": patent.get("patent_title", ""),
                        "abstract": patent.get("patent_abstract", "")[:500],
                        "date": patent.get("patent_date", ""),
                        "patent_type": patent.get("patent_type", ""),
                        "assignees": assignees,
                        "inventors": inventors,
                        "cpc_codes": cpc_codes,
                        "url": f"https://patents.google.com/patent/US{patent.get('patent_number', '')}",
                    }
                )

            return results

        except httpx.HTTPError as e:
            print(f"USPTO search error: {e}")
            return []

    async def get_patent_details(self, patent_number: str) -> Dict[str, Any]:
        """Get detailed patent information.

        Args:
            patent_number: USPTO patent number

        Returns:
            Patent details
        """
        if not self._client:
            raise RuntimeError("USPTO source not initialized")

        payload = {
            "q": {"patent_number": patent_number},
            "f": [
                "patent_number",
                "patent_title",
                "patent_abstract",
                "patent_date",
                "patent_type",
                "assignee_organization",
                "assignee_country",
                "inventor_first_name",
                "inventor_last_name",
                "inventor_city",
                "inventor_country",
                "cpc_group_id",
                "cpc_group_title",
                "cited_patent_number",
                "citedby_patent_number",
            ],
        }

        try:
            response = await self._client.post(
                self.BASE_URL,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            patents = data.get("patents", [])
            return patents[0] if patents else {}

        except httpx.HTTPError as e:
            print(f"USPTO patent detail error: {e}")
            return {}

    async def get_assignee_patents(
        self, assignee: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all patents for an assignee.

        Args:
            assignee: Organization name
            limit: Maximum results

        Returns:
            List of patents
        """
        return await self.search(
            query="",
            filters={"assignee": assignee},
            limit=limit,
        )
