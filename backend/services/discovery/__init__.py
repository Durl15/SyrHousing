"""
Grant discovery service package.
Automated discovery of grants from multiple sources (APIs, RSS feeds, web scraping).
"""

from .discovery_service import run_discovery

__all__ = ["run_discovery"]
