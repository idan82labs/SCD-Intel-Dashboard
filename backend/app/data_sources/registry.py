"""Central registry for all data sources."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.config import settings
from app.data_sources.base import BaseDataSource


@dataclass
class SourceCapability:
    """Describes what a data source can provide."""

    name: str
    description: str
    query_types: List[str] = field(default_factory=list)
    data_types: List[str] = field(default_factory=list)


class DataSourceRegistry:
    """Central registry for all data sources."""

    def __init__(self):
        """Initialize the registry."""
        self._sources: Dict[str, BaseDataSource] = {}
        self._capabilities: Dict[str, SourceCapability] = {}

    async def initialize(self) -> None:
        """Initialize all data sources."""
        # Import sources here to avoid circular imports
        from app.data_sources.web.tavily import TavilySource
        from app.data_sources.web.rss import RSSSource
        from app.data_sources.government.usaspending import USASpendingSource
        from app.data_sources.government.sam_gov import SAMGovSource
        from app.data_sources.government.eu_ted import EUTEDSource
        from app.data_sources.government.canada_buys import CanadaGovSource
        from app.data_sources.patents.uspto import USPTOSource
        from app.data_sources.patents.epo import EPOSource
        from app.data_sources.company.sec_edgar import SECEdgarSource
        from app.data_sources.trade.un_comtrade import UNComtradeSource

        # Web sources
        if settings.TAVILY_API_KEY:
            self._register_source(
                "web_search",
                TavilySource(settings.TAVILY_API_KEY),
                SourceCapability(
                    name="web_search",
                    description="Real-time web search for current information, news, and general research",
                    query_types=["keyword", "question", "topic"],
                    data_types=["articles", "web_pages", "news"],
                ),
            )

        self._register_source(
            "rss_news",
            RSSSource(),
            SourceCapability(
                name="rss_news",
                description="Aggregated news from industry RSS feeds",
                query_types=["keyword", "topic", "company"],
                data_types=["news_articles"],
            ),
        )

        # Government sources
        self._register_source(
            "usaspending",
            USASpendingSource(),
            SourceCapability(
                name="usaspending",
                description="US federal government contract awards and spending data",
                query_types=["keyword", "company", "naics_code", "date_range"],
                data_types=["contracts", "awards", "spending"],
            ),
        )

        if settings.SAM_GOV_API_KEY:
            self._register_source(
                "sam_gov",
                SAMGovSource(settings.SAM_GOV_API_KEY),
                SourceCapability(
                    name="sam_gov",
                    description="Active US government contract opportunities and solicitations",
                    query_types=["keyword", "naics_code", "date_range"],
                    data_types=["opportunities", "solicitations"],
                ),
            )

        # Patent sources
        self._register_source(
            "uspto",
            USPTOSource(),
            SourceCapability(
                name="uspto",
                description="US patent database - patents, applications, assignees",
                query_types=["keyword", "cpc_code", "assignee", "date_range"],
                data_types=["patents", "applications", "inventors"],
            ),
        )

        if settings.EPO_CONSUMER_KEY and settings.EPO_CONSUMER_SECRET:
            self._register_source(
                "epo",
                EPOSource(settings.EPO_CONSUMER_KEY, settings.EPO_CONSUMER_SECRET),
                SourceCapability(
                    name="epo",
                    description="European Patent Office - European patent filings",
                    query_types=["keyword", "cpc_code", "applicant", "date_range"],
                    data_types=["patents", "applications"],
                ),
            )

        # Company/Financial sources
        self._register_source(
            "sec_edgar",
            SECEdgarSource(settings.SEC_EDGAR_CONTACT_EMAIL),
            SourceCapability(
                name="sec_edgar",
                description="SEC EDGAR filings - 10-K, 10-Q, 8-K for public companies",
                query_types=["company", "ticker", "keyword"],
                data_types=["filings", "financials", "disclosures"],
            ),
        )

        # International Government sources
        self._register_source(
            "eu_ted",
            EUTEDSource(),
            SourceCapability(
                name="eu_ted",
                description="EU TED - European public procurement notices and tenders",
                query_types=["keyword", "cpv_code", "country"],
                data_types=["tenders", "contracts", "awards"],
            ),
        )

        self._register_source(
            "canada_gov",
            CanadaGovSource(),
            SourceCapability(
                name="canada_gov",
                description="Canadian government procurement and open data",
                query_types=["keyword", "organization", "vendor"],
                data_types=["contracts", "datasets", "tenders"],
            ),
        )

        # Trade data sources
        self._register_source(
            "un_comtrade",
            UNComtradeSource(settings.UN_COMTRADE_KEY),
            SourceCapability(
                name="un_comtrade",
                description="UN Comtrade - International trade statistics by HS code",
                query_types=["hs_code", "country", "year"],
                data_types=["trade_flows", "exports", "imports"],
            ),
        )

        # Initialize all registered sources
        for source in self._sources.values():
            await source.initialize()

        print(f"Initialized {len(self._sources)} data sources: {list(self._sources.keys())}")

    def _register_source(
        self, name: str, source: BaseDataSource, capability: SourceCapability
    ) -> None:
        """Register a data source with its capabilities."""
        self._sources[name] = source
        self._capabilities[name] = capability

    def get_source(self, name: str) -> Optional[BaseDataSource]:
        """Get a data source by name."""
        return self._sources.get(name)

    def list_sources(self) -> List[SourceCapability]:
        """List all available sources with their capabilities."""
        return list(self._capabilities.values())

    def list_source_names(self) -> List[str]:
        """List all source names."""
        return list(self._sources.keys())

    async def close(self) -> None:
        """Close all data sources."""
        for source in self._sources.values():
            await source.close()
        print("All data sources closed")
