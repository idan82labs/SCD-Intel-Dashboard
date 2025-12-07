"""Espacenet patent search (EPO public interface, no API key required)."""

from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx

from app.data_sources.base import BaseDataSource


class EspacenetSource(BaseDataSource):
    """Espacenet public patent search - no API key required.

    Uses EPO's public Espacenet interface for worldwide patent search.
    Covers 130+ million patent documents from 100+ countries.
    """

    BASE_URL = "https://worldwide.espacenet.com"
    SEARCH_API = "https://worldwide.espacenet.com/3.2/rest-services/published-data/search"

    # CPC codes relevant to infrared/thermal imaging
    IR_CPC_CODES = {
        "G01J5": "Radiation pyrometry - infrared detectors",
        "G02B23": "Telescopes, periscopes, thermal imaging",
        "H01L27/146": "Infrared radiation sensitive devices",
        "H01L31/09": "Infrared sensitive semiconductor devices",
        "G08B13/194": "Infrared intrusion detection",
        "F41G3": "Aiming or sighting devices for weapons",
        "F41G7": "Direction control systems for guided munitions",
    }

    def __init__(self):
        """Initialize Espacenet source."""
        super().__init__(
            name="espacenet",
            description="European/worldwide patent search via Espacenet",
        )
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "User-Agent": "CI-Research-Platform/1.0",
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
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Search Espacenet patents.

        Args:
            query: Search keywords
            filters: Optional filters (applicant, cpc_code, date_from)
            limit: Maximum results

        Returns:
            List of patent records
        """
        if not self._client:
            raise RuntimeError("Espacenet source not initialized")

        filters = filters or {}

        # Build search query parts
        query_parts = []

        if query:
            query_parts.append(f'txt="{query}"')

        if filters.get("applicant"):
            query_parts.append(f'pa="{filters["applicant"]}"')

        if filters.get("cpc_code"):
            query_parts.append(f'cpc="{filters["cpc_code"]}"')

        if filters.get("date_from"):
            query_parts.append(f'pd>={filters["date_from"]}')

        search_query = " AND ".join(query_parts) if query_parts else f'txt="{query}"'

        try:
            # Use the Open Patent Services public endpoint
            params = {
                "q": search_query,
                "Range": f"1-{min(limit, 100)}",
            }

            response = await self._client.get(
                f"{self.BASE_URL}/3.2/rest-services/published-data/search/biblio",
                params=params,
            )

            if response.status_code == 200:
                return self._parse_ops_response(response.json(), limit)

            # Fallback: search via web scraping approach
            return await self._web_search(query, filters, limit)

        except httpx.HTTPError as e:
            print(f"Espacenet search error: {e}")
            return await self._web_search(query, filters, limit)

    async def _web_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Fallback web-based search using Espacenet's JSON API."""
        if not self._client:
            return []

        filters = filters or {}

        try:
            # Build Espacenet query format
            search_terms = []
            if query:
                search_terms.append(f'txt all "{query}"')
            if filters.get("applicant"):
                search_terms.append(f'pa all "{filters["applicant"]}"')
            if filters.get("cpc_code"):
                search_terms.append(f'cpc all "{filters["cpc_code"]}"')

            full_query = " AND ".join(search_terms) if search_terms else query

            # Espacenet's internal search API
            response = await self._client.get(
                f"{self.BASE_URL}/searchResults",
                params={
                    "q": full_query,
                    "lang": "en",
                    "format": "json",
                },
            )

            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            hits = data.get("results", data.get("hits", []))
            if isinstance(hits, dict):
                hits = hits.get("hits", [])

            for hit in hits[:limit]:
                doc = hit.get("_source", hit)
                results.append({
                    "type": "patent",
                    "source": "espacenet",
                    "patent_number": doc.get("publication_number", doc.get("pn", "")),
                    "title": doc.get("title", doc.get("ti", "")),
                    "applicants": doc.get("applicants", []),
                    "publication_date": doc.get("publication_date", doc.get("pd", "")),
                    "abstract": doc.get("abstract", "")[:500],
                    "url": f"{self.BASE_URL}/patent/search?q=pn%3D{doc.get('publication_number', '')}",
                })

            return results

        except Exception as e:
            print(f"Espacenet web search error: {e}")
            return []

    def _parse_ops_response(
        self,
        data: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Parse OPS API response format."""
        results = []

        try:
            search_result = data.get("ops:world-patent-data", {}).get(
                "ops:biblio-search", {}
            )
            result_set = search_result.get("ops:search-result", {}).get(
                "exchange-documents", []
            )

            if not isinstance(result_set, list):
                result_set = [result_set] if result_set else []

            for doc in result_set[:limit]:
                exchange_doc = doc.get("exchange-document", {})
                biblio = exchange_doc.get("bibliographic-data", {})

                doc_id = exchange_doc.get("@doc-number", "")
                country = exchange_doc.get("@country", "")

                # Extract title
                title_data = biblio.get("invention-title", {})
                if isinstance(title_data, list):
                    title = title_data[0].get("$", "") if title_data else ""
                else:
                    title = title_data.get("$", "") if isinstance(title_data, dict) else str(title_data)

                # Extract applicants
                applicants = []
                parties = biblio.get("parties", {}).get("applicants", {})
                applicant_list = parties.get("applicant", [])
                if not isinstance(applicant_list, list):
                    applicant_list = [applicant_list] if applicant_list else []
                for app in applicant_list:
                    if isinstance(app, dict):
                        name = app.get("applicant-name", {}).get("name", {}).get("$", "")
                        if name:
                            applicants.append(name)

                # Extract publication date
                pub_ref = biblio.get("publication-reference", {})
                doc_date = pub_ref.get("document-id", [{}])
                if isinstance(doc_date, list):
                    doc_date = doc_date[0] if doc_date else {}
                pub_date = doc_date.get("date", {}).get("$", "") if isinstance(doc_date, dict) else ""

                patent_num = f"{country}{doc_id}"
                results.append({
                    "type": "patent",
                    "source": "espacenet",
                    "patent_number": patent_num,
                    "title": title,
                    "country": country,
                    "publication_date": pub_date,
                    "applicants": applicants,
                    "url": f"{self.BASE_URL}/patent/search?q=pn%3D{patent_num}",
                })

        except Exception as e:
            print(f"Error parsing OPS response: {e}")

        return results

    async def search_by_applicant(
        self,
        applicant: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search patents by applicant/company name.

        Args:
            applicant: Company or applicant name
            limit: Maximum results

        Returns:
            List of patents for that applicant
        """
        return await self.search(
            query="",
            filters={"applicant": applicant},
            limit=limit,
        )

    async def search_ir_patents(
        self,
        query: str = "infrared detector",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search infrared/thermal imaging related patents.

        Uses relevant CPC codes for infrared technology.

        Args:
            query: Additional search terms
            limit: Maximum results

        Returns:
            List of IR-related patents
        """
        results = []

        # Search with IR-specific CPC codes
        for cpc_code in list(self.IR_CPC_CODES.keys())[:3]:
            cpc_results = await self.search(
                query=query,
                filters={"cpc_code": cpc_code},
                limit=limit // 3,
            )
            results.extend(cpc_results)

        return results[:limit]
