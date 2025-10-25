"""
Google Address Validation API service for parsing and normalizing addresses
"""
import logging
from typing import Dict, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleAddressValidator:
    """Service for validating and parsing addresses using Google Address Validation API"""

    def __init__(self):
        self.api_key = settings.google_maps_api_key
        self.base_url = "https://addressvalidation.googleapis.com/v1:validateAddress"

    async def validate_and_parse_address(self, address_string: str) -> Optional[Dict]:
        """
        Validate and parse an address using Google's Address Validation API

        Args:
            address_string: Full address string to parse

        Returns:
            Dictionary with parsed address components or None if validation fails

        Example return:
            {
                'street_1': '351 Cannon House Office Building',
                'street_2': None,
                'city': 'Washington',
                'state': 'DC',
                'zip': '20515-3602',
                'formatted_address': '351 Cannon House Office Building, Washington, DC 20515-3602, USA'
            }
        """
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json={
                        "address": {
                            "addressLines": [address_string]
                        }
                    },
                    timeout=10.0
                )

                if response.status_code != 200:
                    logger.error(f"Google Address API error: {response.status_code} - {response.text}")
                    return None

                data = response.json()

                # Extract result
                result = data.get('result', {})
                address = result.get('address', {})
                postal_address = address.get('postalAddress', {})

                if not postal_address:
                    logger.warning(f"No postal address found for: {address_string}")
                    return None

                # Extract address components
                address_lines = postal_address.get('addressLines', [])
                locality = postal_address.get('locality', '')  # City
                administrative_area = postal_address.get('administrativeArea', '')  # State
                postal_code = postal_address.get('postalCode', '')  # ZIP

                # Parse address lines (typically 1-2 lines for street address)
                street_1 = address_lines[0] if len(address_lines) > 0 else ''
                street_2 = address_lines[1] if len(address_lines) > 1 else None

                # Get formatted address from addressComponents for full format
                formatted_address = address.get('formattedAddress', address_string)

                return {
                    'street_1': street_1,
                    'street_2': street_2,
                    'city': locality,
                    'state': administrative_area,
                    'zip': postal_code,
                    'formatted_address': formatted_address
                }

        except httpx.TimeoutException:
            logger.error(f"Timeout validating address: {address_string}")
            return None
        except Exception as e:
            logger.error(f"Error validating address '{address_string}': {e}")
            return None


async def parse_office_address_with_google(
    street_1: str,
    city: str = "",
    state: str = "",
    zip_code: str = ""
) -> Dict[str, Optional[str]]:
    """
    Parse office address using Google Address Validation API

    Args:
        street_1: Street address (may contain full address)
        city: City name (optional, for context)
        state: State abbreviation (optional, for context)
        zip_code: ZIP code (optional, for context)

    Returns:
        Dictionary with cleaned address components
    """
    validator = GoogleAddressValidator()

    # If we have all components, use them; otherwise parse the full street_1
    if city and state:
        full_address = f"{street_1}, {city}, {state} {zip_code}".strip()
    else:
        full_address = street_1

    result = await validator.validate_and_parse_address(full_address)

    if result:
        return {
            'street_1': result['street_1'],
            'street_2': result['street_2'],
            'city': result['city'],
            'state': result['state'],
            'zip': result['zip']
        }

    # Fallback: return original if Google API fails
    logger.warning(f"Google API failed for '{full_address}', using original values")
    return {
        'street_1': street_1,
        'street_2': None,
        'city': city,
        'state': state,
        'zip': zip_code
    }
