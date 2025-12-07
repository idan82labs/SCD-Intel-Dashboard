"""EPO (European Patent Office) data source."""

import base64
from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class EPOSource(BaseDataSource):
    """European Patent Office Open Patent Services API."""

    AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
    BASE_URL = "https://ops.epo.org/3.2/rest-services"

    def __init__(self, consumer_key: str, consumer_secret: str):
        """Initialize EPO source.

        Args:
            consumer_key: EPO API consumer key
            consumer_secret: EPO API consumer secret
        """
        super().__init__(
            name="epo",
            description="European Patent Office patent database",
        )
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self._client: httpx.AsyncClient | None = None
        self._access_token: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize HTTP client and authenticate."""
        self._client = httpx.AsyncClient(timeout=30.0)
        await self._authenticate()
        await super().initialize()

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
        await super().close()

    async def _authenticate(self) -> None:
        """Obtain access token from EPO."""
        if not self._client:
            return

        # Create Basic auth header
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        try:
            response = await self._client.post(
                self.AUTH_URL,
                headers={
                    "Authorization": f"Basic {encoded}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data.get("access_token")

        except httpx.HTTPError as e:
            print(f"EPO authentication error: {e}")
            self._access_token = None

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Search EPO patents.

        Args:
            query: Search keywords (CQL query)
            filters: Additional filters
            limit: Maximum results

        Returns:
            List of patents
        """
        if not self._client or not self._access_token:
            print("EPO source not authenticated")
            return []

        filters = filters or {}

        # Build CQL query
        cql_parts = []

        # Title/abstract search
        if query:
            cql_parts.append(f'txt="{query}"')

        # Applicant filter
        if filters.get("applicant"):
            cql_parts.append(f'pa="{filters["applicant"]}"')

        # CPC code filter
        if filters.get("cpc_code"):
            cql_parts.append(f'cpc="{filters["cpc_code"]}"')

        # Date filter
        if filters.get("date_from"):
            cql_parts.append(f'pd>={filters["date_from"]}')

        cql_query = " and ".join(cql_parts) if cql_parts else "txt=*"

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/published-data/search/biblio",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Accept": "application/json",
                },
                params={
                    "q": cql_query,
                    "Range": f"1-{min(limit, 100)}",
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []

            # Parse EPO response (complex nested structure)
            search_result = data.get("ops:world-patent-data", {}).get(
                "ops:biblio-search", {}
            )
            result_set = search_result.get("ops:search-result", {}).get(
                "exchange-documents", []
            )

            if not isinstance(result_set, list):
                result_set = [result_set]

            for doc in result_set[:limit]:
                exchange_doc = doc.get("exchange-document", {})
                biblio = exchange_doc.get("bibliographic-data", {})

                # Extract document ID
                doc_id = exchange_doc.get("@doc-number", "")
                country = exchange_doc.get("@country", "")

                # Extract title
                title_data = biblio.get("invention-title", {})
                if isinstance(title_data, list):
                    title = title_data[0].get("$", "") if title_data else ""
                else:
                    title = title_data.get("$", "")

                # Extract applicants
                applicants = []
                parties = biblio.get("parties", {}).get("applicants", {})
                applicant_list = parties.get("applicant", [])
                if not isinstance(applicant_list, list):
                    applicant_list = [applicant_list]
                for app in applicant_list:
                    name = app.get("applicant-name", {}).get("name", {}).get("$", "")
                    if name:
                        applicants.append(name)

                # Extract publication date
                pub_ref = biblio.get("publication-reference", {})
                doc_date = pub_ref.get("document-id", [{}])
                if isinstance(doc_date, list):
                    doc_date = doc_date[0]
                pub_date = doc_date.get("date", {}).get("$", "")

                results.append(
                    {
                        "type": "patent",
                        "patent_number": f"{country}{doc_id}",
                        "title": title,
                        "country": country,
                        "publication_date": pub_date,
                        "applicants": applicants,
                        "url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{country}{doc_id}",
                    }
                )

            return results

        except httpx.HTTPError as e:
            print(f"EPO search error: {e}")
            # Try to re-authenticate on 401
            if "401" in str(e):
                await self._authenticate()
            return []
