"""SEC EDGAR data source for company filings and financial data."""

from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class SECEdgarSource(BaseDataSource):
    """SEC EDGAR API for company filings and financial data.

    No API key required. Uses data.sec.gov for company submissions
    and efts.sec.gov for full-text search.
    """

    SUBMISSIONS_URL = "https://data.sec.gov/submissions"
    SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
    COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

    # Common defense/infrared competitors CIKs (zero-padded to 10 digits)
    KNOWN_CIKS = {
        "teledyne": "0000096885",
        "l3harris": "0000202058",
        "bae systems": "0000916076",
        "leonardo drs": "0001833756",
        "flir": "0000354908",
        "raytheon": "0000101829",
        "northrop grumman": "0001133421",
        "lockheed martin": "0000936468",
        "general dynamics": "0000040533",
    }

    def __init__(self, contact_email: str = "research@example.com"):
        """Initialize SEC EDGAR source.

        Args:
            contact_email: Email for User-Agent header (required by SEC)
        """
        super().__init__(
            name="sec_edgar",
            description="SEC EDGAR filings and financial data for public companies",
        )
        self._contact_email = contact_email
        self._client: httpx.AsyncClient | None = None
        self._ticker_map: Dict[str, str] = {}

    async def initialize(self) -> None:
        """Initialize HTTP client and load ticker mappings."""
        headers = {
            "User-Agent": f"CI-Research-Platform {self._contact_email}",
            "Accept": "application/json",
        }
        self._client = httpx.AsyncClient(timeout=30.0, headers=headers)
        await self._load_ticker_map()
        await super().initialize()

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
        await super().close()

    async def _load_ticker_map(self) -> None:
        """Load company ticker to CIK mapping."""
        if not self._client:
            return
        try:
            response = await self._client.get(self.COMPANY_TICKERS_URL)
            response.raise_for_status()
            data = response.json()
            for entry in data.values():
                ticker = entry.get("ticker", "").lower()
                cik = str(entry.get("cik_str", "")).zfill(10)
                if ticker:
                    self._ticker_map[ticker] = cik
        except httpx.HTTPError as e:
            print(f"Failed to load SEC ticker map: {e}")

    def _get_cik(self, identifier: str) -> Optional[str]:
        """Get CIK from company name or ticker."""
        identifier_lower = identifier.lower()

        # Check known CIKs first
        for name, cik in self.KNOWN_CIKS.items():
            if name in identifier_lower or identifier_lower in name:
                return cik

        # Check ticker map
        if identifier_lower in self._ticker_map:
            return self._ticker_map[identifier_lower]

        return None

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Search SEC filings using full-text search.

        Args:
            query: Search keywords (company name, topic, etc.)
            filters: Optional filters (form_types, date_range)
            limit: Maximum results

        Returns:
            List of filing records
        """
        if not self._client:
            raise RuntimeError("SEC EDGAR source not initialized")

        filters = filters or {}
        results = []

        # Try to get company-specific filings first
        cik = self._get_cik(query)
        if cik:
            company_results = await self._get_company_filings(cik, filters, limit)
            results.extend(company_results)

        # Also do full-text search
        search_results = await self._full_text_search(query, filters, limit)
        results.extend(search_results)

        # Dedupe by accession number
        seen = set()
        unique_results = []
        for r in results:
            acc = r.get("accession_number", "")
            if acc and acc not in seen:
                seen.add(acc)
                unique_results.append(r)

        return unique_results[:limit]

    async def _get_company_filings(
        self,
        cik: str,
        filters: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get filings for a specific company by CIK."""
        if not self._client:
            return []

        try:
            url = f"{self.SUBMISSIONS_URL}/CIK{cik}.json"
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()

            company_name = data.get("name", "")
            ticker = data.get("tickers", [""])[0] if data.get("tickers") else ""
            filings = data.get("filings", {}).get("recent", {})

            results = []
            form_types = filters.get("form_types", [])

            # Combine filing data
            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            accessions = filings.get("accessionNumber", [])
            descriptions = filings.get("primaryDocument", [])
            doc_descriptions = filings.get("primaryDocDescription", [])

            for i in range(min(len(forms), limit * 2)):  # Get extra to filter
                form = forms[i] if i < len(forms) else ""

                # Filter by form type if specified
                if form_types and form not in form_types:
                    continue

                accession = accessions[i] if i < len(accessions) else ""
                filing_date = dates[i] if i < len(dates) else ""
                doc = descriptions[i] if i < len(descriptions) else ""
                doc_desc = doc_descriptions[i] if i < len(doc_descriptions) else ""

                results.append({
                    "type": "sec_filing",
                    "source": "sec_edgar",
                    "company_name": company_name,
                    "ticker": ticker,
                    "cik": cik,
                    "form_type": form,
                    "filing_date": filing_date,
                    "accession_number": accession.replace("-", ""),
                    "description": doc_desc or doc,
                    "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{doc}",
                })

                if len(results) >= limit:
                    break

            return results

        except httpx.HTTPError as e:
            print(f"SEC company filings error: {e}")
            return []

    async def _full_text_search(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Perform full-text search across SEC filings."""
        if not self._client:
            return []

        try:
            params = {
                "q": query,
                "dateRange": "custom",
                "startdt": filters.get("start_date", "2020-01-01"),
                "enddt": filters.get("end_date", "2025-12-31"),
            }

            if filters.get("form_types"):
                params["forms"] = ",".join(filters["form_types"])

            response = await self._client.get(self.SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            hits = data.get("hits", {}).get("hits", [])

            for hit in hits[:limit]:
                source = hit.get("_source", {})
                results.append({
                    "type": "sec_filing",
                    "source": "sec_edgar",
                    "company_name": source.get("display_names", [""])[0],
                    "ticker": source.get("tickers", [""])[0] if source.get("tickers") else "",
                    "cik": source.get("ciks", [""])[0] if source.get("ciks") else "",
                    "form_type": source.get("form", ""),
                    "filing_date": source.get("file_date", ""),
                    "accession_number": source.get("adsh", ""),
                    "description": source.get("file_description", ""),
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&filenum={source.get('file_num', '')}",
                })

            return results

        except httpx.HTTPError as e:
            print(f"SEC full-text search error: {e}")
            return []

    async def get_company_facts(self, cik: str) -> Dict[str, Any]:
        """Get XBRL company facts (financial data).

        Args:
            cik: Company CIK (zero-padded to 10 digits)

        Returns:
            Company financial facts from XBRL filings
        """
        if not self._client:
            raise RuntimeError("SEC EDGAR source not initialized")

        try:
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"SEC company facts error: {e}")
            return {}
