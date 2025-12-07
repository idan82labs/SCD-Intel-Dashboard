"""Canada Open Government and CanadaBuys data source."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class CanadaGovSource(BaseDataSource):
    """Canada Open Government and CanadaBuys API for Canadian procurement.

    Uses CKAN API for Open Government data and CanadaBuys for tenders.
    No API key required for read operations.
    """

    CKAN_URL = "https://open.canada.ca/data/api/3"
    BUYANDSELL_URL = "https://buyandsell.gc.ca/procurement-data/api"

    # GSIN codes relevant to defense/optics (Government Supply Classification)
    DEFENSE_GSIN = [
        "N58",   # Communication and detection equipment
        "N66",   # Instruments and laboratory equipment
        "N67",   # Photographic equipment
    ]

    def __init__(self):
        """Initialize Canada Gov source."""
        super().__init__(
            name="canada_gov",
            description="Canadian government procurement and open data",
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
        """Search Canadian government data.

        Args:
            query: Search keywords
            filters: Optional filters (gsin, date_range, organization)
            limit: Maximum results

        Returns:
            List of procurement/data records
        """
        if not self._client:
            raise RuntimeError("Canada Gov source not initialized")

        results = []

        # Search contracts data
        contract_results = await self._search_contracts(query, filters, limit)
        results.extend(contract_results)

        # Search CKAN datasets
        dataset_results = await self._search_datasets(query, filters, limit // 2)
        results.extend(dataset_results)

        return results[:limit]

    async def _search_contracts(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search Canadian government contracts via Open Data."""
        if not self._client:
            return []

        filters = filters or {}

        try:
            # Search proactive disclosure contracts dataset
            params = {
                "q": query,
                "rows": limit,
                "sort": "metadata_modified desc",
            }

            # Add organization filter if provided
            if filters.get("organization"):
                params["fq"] = f"organization:{filters['organization']}"

            response = await self._client.get(
                f"{self.CKAN_URL}/action/package_search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            if data.get("success"):
                for package in data.get("result", {}).get("results", []):
                    # Filter for contract-related datasets
                    title_lower = package.get("title", "").lower()
                    if any(term in title_lower for term in ["contract", "procurement", "tender", "award"]):
                        results.append({
                            "type": "canada_dataset",
                            "source": "canada_gov",
                            "id": package.get("id", ""),
                            "title": package.get("title", ""),
                            "organization": package.get("organization", {}).get("title", ""),
                            "description": package.get("notes", "")[:500],
                            "created": package.get("metadata_created", ""),
                            "modified": package.get("metadata_modified", ""),
                            "num_resources": package.get("num_resources", 0),
                            "url": f"https://open.canada.ca/data/en/dataset/{package.get('id', '')}",
                        })

            return results

        except httpx.HTTPError as e:
            print(f"Canada CKAN search error: {e}")
            return []

    async def _search_datasets(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search general datasets in Open Canada."""
        if not self._client:
            return []

        try:
            # Add defense/optics related terms
            search_query = f"{query} (defense OR defence OR optical OR infrared OR military)"

            params = {
                "q": search_query,
                "rows": limit,
                "sort": "score desc",
            }

            response = await self._client.get(
                f"{self.CKAN_URL}/action/package_search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            if data.get("success"):
                for package in data.get("result", {}).get("results", []):
                    results.append({
                        "type": "canada_dataset",
                        "source": "canada_gov",
                        "id": package.get("id", ""),
                        "title": package.get("title", ""),
                        "organization": package.get("organization", {}).get("title", ""),
                        "description": package.get("notes", "")[:500] if package.get("notes") else "",
                        "keywords": package.get("tags", []),
                        "created": package.get("metadata_created", ""),
                        "modified": package.get("metadata_modified", ""),
                        "url": f"https://open.canada.ca/data/en/dataset/{package.get('id', '')}",
                    })

            return results

        except httpx.HTTPError as e:
            print(f"Canada datasets search error: {e}")
            return []

    async def get_contracts_by_vendor(
        self,
        vendor_name: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search contracts by vendor name.

        Args:
            vendor_name: Company/vendor name to search
            limit: Maximum results

        Returns:
            List of contract records
        """
        return await self._search_contracts(
            query=vendor_name,
            filters=None,
            limit=limit,
        )

    async def get_defense_datasets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get datasets from National Defence.

        Returns:
            List of DND-related datasets
        """
        if not self._client:
            raise RuntimeError("Canada Gov source not initialized")

        try:
            params = {
                "fq": "organization:dnd-mdn",  # Department of National Defence
                "rows": limit,
                "sort": "metadata_modified desc",
            }

            response = await self._client.get(
                f"{self.CKAN_URL}/action/package_search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            if data.get("success"):
                for package in data.get("result", {}).get("results", []):
                    results.append({
                        "type": "canada_dataset",
                        "source": "canada_gov",
                        "id": package.get("id", ""),
                        "title": package.get("title", ""),
                        "organization": "Department of National Defence",
                        "description": package.get("notes", "")[:500] if package.get("notes") else "",
                        "created": package.get("metadata_created", ""),
                        "modified": package.get("metadata_modified", ""),
                        "url": f"https://open.canada.ca/data/en/dataset/{package.get('id', '')}",
                    })

            return results

        except httpx.HTTPError as e:
            print(f"Canada DND datasets error: {e}")
            return []
