"""Base class for all data sources."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseDataSource(ABC):
    """Abstract base class for all data sources."""

    def __init__(self, name: str, description: str = ""):
        """Initialize the data source.

        Args:
            name: Unique identifier for this source
            description: Human-readable description
        """
        self.name = name
        self.description = description
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the data source (e.g., authenticate, test connection)."""
        self._initialized = True

    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Execute a search query against this data source.

        Args:
            query: Search query string or structured query
            **kwargs: Additional source-specific parameters

        Returns:
            List of result dictionaries
        """
        pass

    async def close(self) -> None:
        """Clean up resources."""
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the source is initialized."""
        return self._initialized

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
