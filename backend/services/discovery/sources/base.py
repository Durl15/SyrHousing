"""
Base abstract class for grant source adapters.
All source adapters must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class GrantSourceAdapter(ABC):
    """
    Abstract base class for grant discovery sources.

    Each source adapter (RSS, API, web scraping) implements this interface
    to provide a consistent way to fetch grants from different sources.
    """

    @abstractmethod
    def fetch_grants(self) -> List[Dict]:
        """
        Fetch grants from the source.

        Returns:
            List[Dict]: List of raw grant data dictionaries.
                       Each dict should contain at least 'name' and 'source_url'.

        Raises:
            Exception: If source is unavailable or fetch fails.
        """
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        """
        Return the source type identifier.

        Returns:
            str: Source type (e.g., "rss_feed", "grants_gov_api", "web_scrape")
        """
        pass

    def get_source_name(self) -> str:
        """
        Return human-readable source name (optional override).

        Returns:
            str: Display name for the source
        """
        return self.get_source_type().replace("_", " ").title()
