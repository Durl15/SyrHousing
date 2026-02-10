"""
RSS feed adapter for grant discovery.
Fetches grants from Grants.gov and other RSS feeds.
"""

import feedparser
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from .base import GrantSourceAdapter

logger = logging.getLogger(__name__)


class RSSFeedAdapter(GrantSourceAdapter):
    """
    Adapter for discovering grants from RSS feeds.

    Primary source: Grants.gov RSS feeds
    - New opportunities feed
    - Modified opportunities feed
    - Category-specific feeds
    """

    # Grants.gov RSS feed URLs
    RSS_FEEDS = {
        "all_opportunities": "https://www.grants.gov/rss/GG_NewOpp.xml",
        "modified_opportunities": "https://www.grants.gov/rss/GG_ModOpp.xml",
        "by_category": "https://www.grants.gov/rss/GG_OppModByCategory.xml",
    }

    # Housing-related keywords for filtering
    HOUSING_KEYWORDS = [
        "housing", "homeowner", "home repair", "home improvement",
        "rehabilitation", "weatherization", "energy efficiency",
        "accessibility", "lead", "roof", "heating", "plumbing",
        "home ownership", "affordable housing", "community development",
        "neighborhood", "residential", "dwelling"
    ]

    def __init__(self, feed_urls: List[str] = None, days_back: int = 30):
        """
        Initialize RSS feed adapter.

        Args:
            feed_urls: List of RSS feed URLs (defaults to Grants.gov feeds)
            days_back: Only include entries from last N days (default 30)
        """
        self.feed_urls = feed_urls or [
            self.RSS_FEEDS["all_opportunities"],
            self.RSS_FEEDS["by_category"],
        ]
        self.days_back = days_back
        self.cutoff_date = datetime.now() - timedelta(days=days_back)

    def fetch_grants(self) -> List[Dict]:
        """
        Fetch grants from RSS feeds.

        Returns:
            List[Dict]: List of grant dictionaries with fields:
                - name: Grant title
                - source_url: Link to grant details
                - source_id: GUID/ID from feed
                - description: Summary text
                - published_date: Publication date
                - raw_entry: Full feed entry data
        """
        all_grants = []
        seen_links = set()

        for feed_url in self.feed_urls:
            try:
                logger.info(f"Fetching RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                if feed.bozo:
                    # Feed has errors but may still be usable
                    logger.warning(f"RSS feed has errors: {feed_url} - {feed.bozo_exception}")

                for entry in feed.entries:
                    # Deduplicate by link
                    link = entry.get("link", "")
                    if link in seen_links:
                        continue

                    # Check if entry is recent enough
                    published = self._parse_date(entry)
                    if published and published < self.cutoff_date:
                        continue  # Too old

                    # Filter for housing-related grants
                    if not self._is_housing_related(entry):
                        continue

                    # Extract grant data
                    grant = {
                        "name": entry.get("title", "Untitled Grant"),
                        "source_url": link,
                        "source_id": entry.get("id") or entry.get("guid") or link,
                        "description": self._get_description(entry),
                        "published_date": published.isoformat() if published else None,
                        "raw_entry": str(entry),
                    }

                    all_grants.append(grant)
                    seen_links.add(link)

                logger.info(f"Found {len(all_grants)} housing-related grants from {feed_url}")

            except Exception as e:
                logger.error(f"Failed to fetch RSS feed {feed_url}: {e}")
                continue

        logger.info(f"Total grants discovered from RSS feeds: {len(all_grants)}")
        return all_grants

    def get_source_type(self) -> str:
        """Return source type identifier."""
        return "rss_feed"

    def _parse_date(self, entry: Dict) -> datetime | None:
        """
        Parse publication date from RSS entry.

        Args:
            entry: feedparser entry dict

        Returns:
            datetime or None if parsing fails
        """
        # Try multiple date fields
        date_fields = ["published_parsed", "updated_parsed", "created_parsed"]

        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return datetime(*time_struct[:6])
                    except (TypeError, ValueError):
                        continue

        return None

    def _get_description(self, entry: Dict) -> str:
        """
        Extract description/summary from entry.

        Args:
            entry: feedparser entry dict

        Returns:
            str: Description text
        """
        # Try multiple description fields
        if hasattr(entry, "summary"):
            return entry.summary
        elif hasattr(entry, "description"):
            return entry.description
        elif hasattr(entry, "content"):
            if isinstance(entry.content, list) and len(entry.content) > 0:
                return entry.content[0].get("value", "")

        return ""

    def _is_housing_related(self, entry: Dict) -> bool:
        """
        Check if RSS entry is housing-related.

        Args:
            entry: feedparser entry dict

        Returns:
            bool: True if entry matches housing keywords
        """
        # Combine title and description for keyword search
        text = ""
        if hasattr(entry, "title"):
            text += entry.title.lower() + " "
        if hasattr(entry, "summary"):
            text += entry.summary.lower() + " "
        if hasattr(entry, "description"):
            text += entry.description.lower()

        # Check if any housing keyword is present
        for keyword in self.HOUSING_KEYWORDS:
            if keyword.lower() in text:
                return True

        return False
