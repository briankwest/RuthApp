"""
Address parsing utility for cleaning and normalizing addresses from Geocodio API
"""
import re
from typing import Dict, Optional


def parse_office_address(street_1: str, city: str = "", state: str = "", zip_code: str = "") -> Dict[str, Optional[str]]:
    """
    Parse office address that may have city/state/zip embedded in street_1

    Examples:
        "Room 250, 2300 N. Lincoln Blvd., Oklahoma City, OK 73105"
        -> street_1="Room 250", street_2="2300 N. Lincoln Blvd.", city="Oklahoma City", state="OK", zip="73105"

        "351 Cannon House Office Building Washington DC 20515-3602"
        -> street_1="351 Cannon House Office Building", city="Washington", state="DC", zip="20515-3602"

    Args:
        street_1: The street address (may contain full address)
        city: City name (if already separate)
        state: State abbreviation (if already separate)
        zip_code: ZIP code (if already separate)

    Returns:
        Dictionary with cleaned address components
    """
    # If we already have city, state, and zip separate, check if they're embedded in street_1
    if city and state:
        # Try to find city, state in street_1
        pattern = rf',?\s*{re.escape(city)},?\s*{re.escape(state)}\s*(\d{{5}}(-\d{{4}})?)?'
        match = re.search(pattern, street_1, re.IGNORECASE)

        if match:
            # Extract the embedded zip if present
            embedded_zip = match.group(1)
            if embedded_zip and not zip_code:
                zip_code = embedded_zip

            # Remove city, state, zip from street_1
            clean_street = street_1[:match.start()].strip().rstrip(',').strip()

            # Try to split into street_1 and street_2 on comma
            parts = [p.strip() for p in clean_street.split(',') if p.strip()]

            return {
                'street_1': parts[0] if parts else clean_street,
                'street_2': parts[1] if len(parts) > 1 else None,
                'city': city,
                'state': state,
                'zip': zip_code
            }

    # Try to parse generic US address format: "street, city, STATE ZIP"
    # Pattern: anything, followed by comma, city name, comma, STATE abbreviation, optional ZIP
    pattern = r'^(.+?),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)?$'
    match = re.match(pattern, street_1)

    if match:
        street_part = match.group(1).strip()
        parsed_city = match.group(2).strip()
        parsed_state = match.group(3).strip()
        parsed_zip = match.group(4) if match.group(4) else ""

        # Split street part on comma for street_1 and street_2
        street_parts = [p.strip() for p in street_part.split(',') if p.strip()]

        return {
            'street_1': street_parts[0] if street_parts else street_part,
            'street_2': street_parts[1] if len(street_parts) > 1 else None,
            'city': parsed_city,
            'state': parsed_state,
            'zip': parsed_zip
        }

    # Try pattern without commas: "street city STATE ZIP"
    # This handles "351 Cannon House Office Building Washington DC 20515-3602"
    pattern = r'^(.+?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)?$'
    match = re.match(pattern, street_1)

    if match:
        street_part = match.group(1).strip()
        parsed_city = match.group(2).strip()
        parsed_state = match.group(3).strip()
        parsed_zip = match.group(4) if match.group(4) else ""

        return {
            'street_1': street_part,
            'street_2': None,
            'city': parsed_city,
            'state': parsed_state,
            'zip': parsed_zip
        }

    # If no pattern matches, return as-is
    return {
        'street_1': street_1,
        'street_2': None,
        'city': city,
        'state': state,
        'zip': zip_code
    }


def clean_office_data(office: Dict) -> Dict:
    """
    Clean office data from Geocodio API response

    Args:
        office: Office dict with potentially embedded address in street_1

    Returns:
        Cleaned office dict with properly separated address components
    """
    street_1 = office.get('street_1', '')
    city = office.get('city', '')
    state = office.get('state', '')
    zip_code = office.get('zip', '')

    parsed = parse_office_address(street_1, city, state, zip_code)

    # Update office with parsed values
    office_clean = office.copy()
    office_clean['street_1'] = parsed['street_1']
    office_clean['street_2'] = parsed['street_2'] or office.get('street_2')
    office_clean['city'] = parsed['city']
    office_clean['state'] = parsed['state']
    office_clean['zip'] = parsed['zip']

    return office_clean
