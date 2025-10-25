"""
Geocod.io API integration service with caching
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
from app.models.geocoding import GeocodingCache, Representative

logger = logging.getLogger(__name__)


class GeocodioService:
    """
    Service for interacting with Geocod.io API with intelligent caching
    """

    def __init__(self):
        self.api_key = settings.geocodio_api_key
        self.base_url = f"https://api.geocod.io/v{settings.geocodio_version}"
        self.timeout = httpx.Timeout(30.0)

    async def geocode_address(
        self,
        db: AsyncSession,
        street: str,
        city: str,
        state: str,
        zip_code: str,
        include_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Geocode an address and get representative information

        Args:
            db: Database session
            street: Street address
            city: City name
            state: State abbreviation
            zip_code: ZIP code
            include_fields: Additional fields to include (cd, stateleg, etc.)

        Returns:
            Geocoding results with representatives
        """
        # Generate cache key
        cache_key = GeocodingCache.generate_address_hash(street, city, state, zip_code)

        # Check cache first
        cached_result = await self._get_cached_result(db, cache_key)
        if cached_result:
            logger.info(f"Cache hit for address: {cache_key}")
            return cached_result

        # Prepare address for API
        full_address = f"{street}, {city}, {state} {zip_code}"

        # Default fields to include
        if include_fields is None:
            include_fields = [
                "cd",  # Congressional district
                "stateleg",  # State legislative districts
                "census",  # Census data
            ]

        # Make API request
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "api_key": self.api_key,
                    "fields": ",".join(include_fields),
                }

                response = await client.get(
                    f"{self.base_url}/geocode",
                    params={**params, "q": full_address}
                )
                response.raise_for_status()

                data = response.json()

                # Full format returns results array
                if not data.get("results"):
                    logger.warning(f"No results for address: {full_address}")
                    return {"error": "Address not found"}

                result = data["results"][0]

                # Extract representative information
                representatives = await self._extract_representatives(result)

                # Cache the result
                await self._cache_result(
                    db=db,
                    cache_key=cache_key,
                    full_address=full_address,
                    result=result,
                    representatives=representatives
                )

                return {
                    "address": result.get("formatted_address", full_address),
                    "location": result.get("location", {}),
                    "accuracy": result.get("accuracy", 0),
                    "accuracy_type": result.get("accuracy_type", "unknown"),
                    "congressional_district": result.get("fields", {}).get("congressional_districts", []),
                    "state_legislative_districts": result.get("fields", {}).get("state_legislative_districts", []),
                    "representatives": representatives,
                    "cached": False
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"Geocod.io API error: {e}")
            return {"error": f"API error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return {"error": str(e)}

    async def get_representatives_by_location(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Get representatives for a specific lat/lng coordinate
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "api_key": self.api_key,
                    "fields": "cd,stateleg",
                }

                response = await client.get(
                    f"{self.base_url}/reverse",
                    params={**params, "q": f"{latitude},{longitude}"}
                )
                response.raise_for_status()

                data = response.json()

                if not data.get("results"):
                    return {"error": "Location not found"}

                result = data["results"][0]
                representatives = await self._extract_representatives(result)

                return {
                    "location": {"lat": latitude, "lng": longitude},
                    "address": result.get("formatted_address", ""),
                    "representatives": representatives,
                }

        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            return {"error": str(e)}

    async def _extract_representatives(self, geocoding_result: Dict) -> Dict[str, List[Dict]]:
        """
        Extract representative information from Geocod.io result
        """
        representatives = {
            "federal": {
                "senators": [],
                "representatives": []
            },
            "state": {
                "senators": [],
                "representatives": [],
                "governor": None
            }
        }

        fields = geocoding_result.get("fields", {})

        # Congressional districts
        cd_data = fields.get("congressional_districts", [])
        if cd_data and len(cd_data) > 0:
            district = cd_data[0]

            # Current congress members
            if "current_legislators" in district:
                for legislator in district.get("current_legislators", []):
                    if legislator.get("type") == "senator":
                        representatives["federal"]["senators"].append(
                            self._format_federal_legislator(legislator, "senator")
                        )
                    elif legislator.get("type") == "representative":
                        representatives["federal"]["representatives"].append(
                            self._format_federal_legislator(legislator, "representative")
                        )

        # State legislative districts
        state_leg = fields.get("state_legislative_districts", {})
        if state_leg:
            # State senate
            if "senate" in state_leg:
                for district in state_leg["senate"]:
                    if "current_legislators" in district:
                        for legislator in district["current_legislators"]:
                            representatives["state"]["senators"].append(
                                self._format_state_legislator(legislator, "state_senator")
                            )

            # State house
            if "house" in state_leg:
                for district in state_leg["house"]:
                    if "current_legislators" in district:
                        for legislator in district["current_legislators"]:
                            representatives["state"]["representatives"].append(
                                self._format_state_legislator(legislator, "state_representative")
                            )

        return representatives

    def _format_federal_legislator(self, legislator: Dict, office_type: str) -> Dict:
        """
        Format federal legislator information
        """
        bio = legislator.get("bio", {})
        contact = legislator.get("contact", {})
        social = legislator.get("social", {})
        references = legislator.get("references", {})

        # Format offices
        offices = []

        # DC Office
        if contact.get("address"):
            offices.append({
                "name": "Washington Office",
                "type": "dc",
                "street_1": contact.get("address", ""),
                "city": "Washington",
                "state": "DC",
                "zip": contact.get("office_zip", ""),
                "phone": contact.get("phone", ""),
                "fax": contact.get("fax", "")
            })

        # Build display name
        first_name = bio.get("first_name", "")
        last_name = bio.get("last_name", "")
        display_name = f"{first_name} {last_name}".strip() if first_name or last_name else "Unknown"

        return {
            "name": display_name,
            "first_name": first_name,
            "last_name": last_name,
            "title": "U.S. Senator" if office_type == "senator" else "U.S. Representative",
            "party": bio.get("party", ""),
            "office_type": f"federal_{office_type}",
            "bioguide_id": references.get("bioguide_id", ""),
            "birthday": bio.get("birthday", ""),
            "gender": bio.get("gender", ""),
            "contact": {
                "phone": contact.get("phone", ""),
                "fax": contact.get("fax", ""),
                "website": contact.get("url", ""),
                "contact_form": contact.get("contact_form", "")
            },
            "social_media": {
                "twitter": social.get("twitter", ""),
                "facebook": social.get("facebook", ""),
                "youtube": social.get("youtube", ""),
                "youtube_id": social.get("youtube_id", "")
            },
            "references": {
                "bioguide_id": references.get("bioguide_id", ""),
                "govtrack_id": references.get("govtrack_id", ""),
                "opensecrets_id": references.get("opensecrets_id", ""),
                "votesmart_id": references.get("votesmart_id", ""),
                "ballotpedia_id": references.get("ballotpedia_id", ""),
                "wikipedia_id": references.get("wikipedia_id", "")
            },
            "offices": offices,
            "photo_url": bio.get("photo_url", "")
        }

    def _format_state_legislator(self, legislator: Dict, office_type: str) -> Dict:
        """
        Format state legislator information
        """
        bio = legislator.get("bio", {})
        contact = legislator.get("contact", {})
        social = legislator.get("social", {})
        references = legislator.get("references", {})

        # Format offices
        offices = []

        # Capitol office - check for address field (used by Open States data)
        if contact.get("address"):
            offices.append({
                "name": "Capitol Office",
                "type": "capitol",
                "street_1": contact.get("address", ""),
                "city": "Oklahoma City",
                "state": "OK",
                "zip": "",
                "phone": contact.get("phone", ""),
                "fax": ""
            })

        # District office
        if contact.get("district_address"):
            offices.append({
                "name": "District Office",
                "type": "district",
                "street_1": contact.get("district_address", ""),
                "city": contact.get("district_city", ""),
                "state": "OK",
                "zip": contact.get("district_zip", ""),
                "phone": contact.get("district_phone", ""),
                "fax": contact.get("district_fax", "")
            })

        # Build display name
        first_name = bio.get("first_name", "")
        last_name = bio.get("last_name", "")
        display_name = f"{first_name} {last_name}".strip() if first_name or last_name else "Unknown"

        return {
            "name": display_name,
            "first_name": first_name,
            "last_name": last_name,
            "title": "State Senator" if "senator" in office_type else "State Representative",
            "party": bio.get("party", ""),
            "office_type": office_type,
            "district": bio.get("district", ""),
            "birthday": bio.get("birthday", ""),
            "gender": bio.get("gender", ""),
            "contact": {
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "website": contact.get("url", "")
            },
            "social_media": {
                "twitter": social.get("twitter", ""),
                "facebook": social.get("facebook", ""),
                "youtube": social.get("youtube", ""),
                "youtube_id": social.get("youtube_id", "")
            },
            "references": {
                "votesmart_id": references.get("votesmart_id", ""),
                "ballotpedia_id": references.get("ballotpedia_id", ""),
                "wikipedia_id": references.get("wikipedia_id", ""),
                "openstates_id": references.get("openstates_id", "")
            },
            "offices": offices,
            "photo_url": bio.get("photo_url", "")
        }

    async def _get_cached_result(
        self,
        db: AsyncSession,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached geocoding result if exists and not expired
        """
        stmt = select(GeocodingCache).where(
            and_(
                GeocodingCache.address_hash == cache_key,
                GeocodingCache.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        cached = result.scalar_one_or_none()

        if cached:
            return {
                "address": cached.formatted_address or cached.full_address,
                "location": {
                    "lat": cached.latitude,
                    "lng": cached.longitude
                },
                "accuracy": cached.accuracy,
                "accuracy_type": cached.accuracy_type,
                "congressional_district": cached.congressional_district,
                "state_legislative_districts": cached.state_legislative_districts,
                "representatives": cached.representatives or {},
                "cached": True,
                "cached_at": cached.created_at.isoformat()
            }

        return None

    async def _cache_result(
        self,
        db: AsyncSession,
        cache_key: str,
        full_address: str,
        result: Dict,
        representatives: Dict
    ):
        """
        Cache geocoding result
        """
        try:
            location = result.get("location", {})
            fields = result.get("fields", {})

            # Extract districts
            cd = fields.get("congressional_districts", [])
            state_leg = fields.get("state_legislative_districts", {})

            cache_entry = GeocodingCache(
                address_hash=cache_key,
                full_address=full_address,
                latitude=location.get("lat"),
                longitude=location.get("lng"),
                formatted_address=result.get("formatted_address"),
                accuracy=result.get("accuracy"),
                accuracy_type=result.get("accuracy_type"),
                geocodio_response=result,
                congressional_district=cd[0].get("district_number") if cd else None,
                state_legislative_districts={
                    "house": state_leg.get("house", [{}])[0].get("district_number") if state_leg.get("house") else None,
                    "senate": state_leg.get("senate", [{}])[0].get("district_number") if state_leg.get("senate") else None
                },
                representatives=representatives,
                expires_at=datetime.utcnow() + timedelta(seconds=settings.geocoding_cache_ttl)
            )

            db.add(cache_entry)
            await db.commit()

            logger.info(f"Cached geocoding result for: {cache_key}")

        except Exception as e:
            logger.error(f"Error caching result: {e}")
            await db.rollback()