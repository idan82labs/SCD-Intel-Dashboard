"""UN Comtrade data source for international trade statistics."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.data_sources.base import BaseDataSource


class UNComtradeSource(BaseDataSource):
    """UN Comtrade API for international trade data.

    Uses the public preview API which allows up to 500 records without auth.
    For larger queries, a subscription key is required.
    """

    BASE_URL = "https://comtradeapi.un.org/public/v1/preview"
    DATA_URL = "https://comtradeapi.un.org/data/v1/get"

    # HS codes relevant to infrared/thermal imaging equipment
    RELEVANT_HS_CODES = {
        "9013": "Optical devices and instruments",
        "901380": "Other optical devices, appliances and instruments",
        "9027": "Instruments for physical/chemical analysis",
        "902780": "Other instruments for physical analysis",
        "8525": "TV cameras, digital cameras, video recorders",
        "852580": "TV cameras, digital cameras",
        "9031": "Measuring/checking instruments",
        "903180": "Other measuring/checking instruments",
    }

    # Key trading countries for thermal imaging
    KEY_REPORTERS = {
        "156": "China",
        "276": "Germany",
        "250": "France",
        "826": "United Kingdom",
        "840": "United States",
        "392": "Japan",
        "410": "South Korea",
        "376": "Israel",
    }

    def __init__(self, subscription_key: Optional[str] = None):
        """Initialize UN Comtrade source.

        Args:
            subscription_key: Optional API key for extended access
        """
        super().__init__(
            name="un_comtrade",
            description="UN Comtrade international trade statistics",
        )
        self._subscription_key = subscription_key
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        headers = {"Accept": "application/json"}
        if self._subscription_key:
            headers["Ocp-Apim-Subscription-Key"] = self._subscription_key

        self._client = httpx.AsyncClient(timeout=60.0, headers=headers)
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
        limit: int = 100,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Search trade data.

        Args:
            query: Search term (mapped to HS codes or partner countries)
            filters: Filters (reporter_code, partner_code, hs_code, year)
            limit: Maximum results (max 500 for preview API)

        Returns:
            List of trade flow records
        """
        if not self._client:
            raise RuntimeError("UN Comtrade source not initialized")

        filters = filters or {}

        # Map query to HS codes if it matches our keywords
        hs_codes = filters.get("hs_codes", [])
        if not hs_codes:
            query_lower = query.lower()
            for code, desc in self.RELEVANT_HS_CODES.items():
                if any(term in query_lower for term in ["infrared", "thermal", "optical", "detector", "sensor"]):
                    hs_codes.append(code)
                    break
            if not hs_codes:
                hs_codes = ["9013"]  # Default to optical devices

        # Get trade data
        results = []
        for hs_code in hs_codes[:3]:  # Limit to 3 codes per search
            trade_data = await self._get_trade_data(
                hs_code=hs_code,
                reporter_code=filters.get("reporter_code"),
                partner_code=filters.get("partner_code"),
                year=filters.get("year", datetime.now().year - 1),
                flow_code=filters.get("flow_code", "X"),  # Exports by default
                limit=min(limit, 500),
            )
            results.extend(trade_data)

        return results[:limit]

    async def _get_trade_data(
        self,
        hs_code: str,
        reporter_code: Optional[str],
        partner_code: Optional[str],
        year: int,
        flow_code: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get trade data from Comtrade API."""
        if not self._client:
            return []

        try:
            # Use preview endpoint (no auth required, 500 record limit)
            params = {
                "cmdCode": hs_code,
                "flowCode": flow_code,
                "period": str(year),
                "maxRecords": limit,
                "format": "json",
                "includeDesc": "true",
            }

            if reporter_code:
                params["reporterCode"] = reporter_code
            if partner_code:
                params["partnerCode"] = partner_code

            response = await self._client.get(
                f"{self.BASE_URL}/C/A/HS",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for record in data.get("data", []):
                results.append({
                    "type": "trade_flow",
                    "source": "un_comtrade",
                    "year": record.get("period"),
                    "reporter_code": record.get("reporterCode"),
                    "reporter": record.get("reporterDesc", ""),
                    "partner_code": record.get("partnerCode"),
                    "partner": record.get("partnerDesc", ""),
                    "flow_code": record.get("flowCode"),
                    "flow": record.get("flowDesc", ""),
                    "hs_code": record.get("cmdCode"),
                    "hs_description": record.get("cmdDesc", ""),
                    "trade_value_usd": record.get("primaryValue"),
                    "quantity": record.get("qty"),
                    "quantity_unit": record.get("qtyUnitAbbr", ""),
                    "net_weight_kg": record.get("netWgt"),
                })

            return results

        except httpx.HTTPError as e:
            print(f"UN Comtrade API error: {e}")
            return []

    async def get_china_exports(
        self,
        hs_code: str = "9013",
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get Chinese exports for specific HS code.

        Useful for tracking Chinese thermal imaging equipment exports.

        Args:
            hs_code: HS commodity code
            year: Year (defaults to previous year)

        Returns:
            List of export records
        """
        if year is None:
            year = datetime.now().year - 1

        return await self._get_trade_data(
            hs_code=hs_code,
            reporter_code="156",  # China
            partner_code=None,
            year=year,
            flow_code="X",  # Exports
            limit=500,
        )

    async def get_bilateral_trade(
        self,
        reporter_code: str,
        partner_code: str,
        hs_code: str = "9013",
        years: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Get bilateral trade data between two countries.

        Args:
            reporter_code: Reporting country code
            partner_code: Partner country code
            hs_code: HS commodity code
            years: List of years to query

        Returns:
            List of trade records
        """
        if years is None:
            current_year = datetime.now().year
            years = [current_year - 1, current_year - 2]

        results = []
        for year in years:
            data = await self._get_trade_data(
                hs_code=hs_code,
                reporter_code=reporter_code,
                partner_code=partner_code,
                year=year,
                flow_code="M,X",  # Both imports and exports
                limit=100,
            )
            results.extend(data)

        return results
