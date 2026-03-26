"""
Address verification API.

Uses the US Census Geocoder (free, no API key required) to:
  - Validate a street address
  - Return the county it falls in
  - Flag whether it's within Onondaga County (FIPS 36067)
"""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/address", tags=["address"])

CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/geographies/address"
ONONDAGA_GEOID = "36067"
SERVICE_AREA_NAME = "Onondaga County, NY"


@router.get("/verify", summary="Verify address and check if it's in Onondaga County")
async def verify_address(
    street: str = Query(..., description="Street address, e.g. '123 Main St'"),
    city: str = Query(default="Syracuse", description="City"),
    state: str = Query(default="NY", description="State abbreviation"),
    zipcode: Optional[str] = Query(None, description="ZIP code (improves accuracy)"),
):
    params = {
        "street": street,
        "city": city,
        "state": state,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "86",   # Counties layer
        "format": "json",
    }
    if zipcode:
        params["zip"] = zipcode

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(CENSUS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="Address lookup timed out — try again.")
    except Exception as exc:
        logger.exception("Census geocoder request failed")
        raise HTTPException(status_code=503, detail=f"Address lookup unavailable: {exc}")

    matches = data.get("result", {}).get("addressMatches", [])
    if not matches:
        return {
            "found": False,
            "in_service_area": False,
            "county": None,
            "formatted_address": None,
            "message": "Address not found — check spelling or try adding a ZIP code.",
        }

    match = matches[0]
    counties = match.get("geographies", {}).get("Counties", [])
    county = counties[0] if counties else {}
    geoid = county.get("GEOID", "")
    county_name = county.get("NAME", "Unknown")
    in_service_area = geoid == ONONDAGA_GEOID

    return {
        "found": True,
        "formatted_address": match.get("matchedAddress", ""),
        "county": county_name,
        "county_geoid": geoid,
        "in_service_area": in_service_area,
        "lat": match.get("coordinates", {}).get("y"),
        "lon": match.get("coordinates", {}).get("x"),
        "message": (
            f"Verified in {SERVICE_AREA_NAME} — all programs available."
            if in_service_area
            else f"Address is in {county_name} County — some local Syracuse/Onondaga programs may not apply."
        ),
    }
