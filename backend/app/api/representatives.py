"""
Representatives API endpoints
"""
import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_async_session
from app.services.geocodio import GeocodioService
from app.api.dependencies import get_current_active_user
from app.models.user import User, UserAddress
from app.models.geocoding import Representative
from sqlalchemy import select, and_, delete, update


router = APIRouter(prefix="/representatives", tags=["Representatives"])


# Request/Response schemas
class AddressLookup(BaseModel):
    """Address lookup request"""
    street_1: str = Field(..., min_length=1, description="Street address", alias="street")
    street_2: Optional[str] = Field(None, description="Apartment/Suite number")
    city: str = Field(..., min_length=1, description="City")
    state: str = Field(..., min_length=2, max_length=2, description="State abbreviation")
    zip_code: str = Field(..., min_length=5, max_length=10, description="ZIP code")
    save_as_primary: bool = Field(False, description="Save as user's primary address")

    class Config:
        populate_by_name = True  # Allow both 'street' and 'street_1'


class LocationLookup(BaseModel):
    """Location-based lookup request"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class RepresentativeResponse(BaseModel):
    """Representative information response"""
    name: str
    title: str
    office_type: str
    party: Optional[str]
    district: Optional[str]
    contact: dict
    social_media: dict
    offices: List[dict]
    photo_url: Optional[str]


class LookupResponse(BaseModel):
    """Complete lookup response"""
    address: str
    location: dict
    accuracy: Optional[float]
    accuracy_type: Optional[str]
    representatives: dict
    cached: bool = False
    cached_at: Optional[str] = None


@router.post("/lookup", response_model=LookupResponse)
async def lookup_representatives_by_address(
    address_data: AddressLookup,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Find all representatives for a given address

    This endpoint:
    - Geocodes the provided address
    - Returns federal senators and representatives
    - Returns state legislators
    - Caches results for 30 days to save API calls
    """
    geocodio = GeocodioService()

    # Build full street address
    street = address_data.street_1
    if address_data.street_2:
        street += f" {address_data.street_2}"

    # Get representatives
    result = await geocodio.geocode_address(
        db=db,
        street=street,
        city=address_data.city,
        state=address_data.state,
        zip_code=address_data.zip_code
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    # Save address if requested
    if address_data.save_as_primary:
        # TODO: Save address to user profile
        pass

    return LookupResponse(**result)


@router.post("/lookup/location", response_model=LookupResponse)
async def lookup_representatives_by_location(
    location_data: LocationLookup,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Find representatives by latitude/longitude

    Useful for mobile apps or map-based lookups
    """
    geocodio = GeocodioService()

    result = await geocodio.get_representatives_by_location(
        db=db,
        latitude=location_data.latitude,
        longitude=location_data.longitude
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return LookupResponse(**result)


@router.get("/search")
async def search_representatives(
    q: str = Query(..., min_length=2, description="Search query"),
    office_type: Optional[str] = Query(None, description="Filter by office type"),
    state: Optional[str] = Query(None, min_length=2, max_length=2, description="Filter by state"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Search for representatives by name or district

    This searches cached representative data only
    """
    # TODO: Implement representative search from cache
    return {
        "results": [],
        "query": q,
        "filters": {
            "office_type": office_type,
            "state": state
        }
    }


@router.get("/templates")
async def get_representative_templates(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get common representative templates for testing

    Returns pre-configured representatives for common scenarios
    """
    return {
        "templates": [
            {
                "id": "us_senator_ok_1",
                "name": "James Lankford",
                "title": "United States Senator",
                "state": "OK",
                "office_type": "federal_senate",
                "party": "Republican"
            },
            {
                "id": "us_senator_ok_2",
                "name": "Markwayne Mullin",
                "title": "United States Senator",
                "state": "OK",
                "office_type": "federal_senate",
                "party": "Republican"
            },
            {
                "id": "governor_ok",
                "name": "Kevin Stitt",
                "title": "Governor",
                "state": "OK",
                "office_type": "governor",
                "party": "Republican"
            }
        ]
    }


@router.get("/offices")
async def get_office_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of all office types and their descriptions
    """
    return {
        "federal": [
            {
                "type": "federal_senate",
                "title": "U.S. Senator",
                "description": "Member of the United States Senate",
                "term_length": "6 years"
            },
            {
                "type": "federal_house",
                "title": "U.S. Representative",
                "description": "Member of the U.S. House of Representatives",
                "term_length": "2 years"
            }
        ],
        "state": [
            {
                "type": "governor",
                "title": "Governor",
                "description": "Chief executive of the state",
                "term_length": "4 years"
            },
            {
                "type": "state_senate",
                "title": "State Senator",
                "description": "Member of the state senate",
                "term_length": "4 years"
            },
            {
                "type": "state_house",
                "title": "State Representative",
                "description": "Member of the state house",
                "term_length": "2 years"
            }
        ]
    }


@router.get("/cache/stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get cache statistics for monitoring

    Shows how many lookups are cached and cache hit rate
    """
    # TODO: Implement cache statistics
    return {
        "total_cached_addresses": 0,
        "cache_hit_rate": 0.0,
        "api_calls_saved": 0,
        "estimated_savings": "$0.00"
    }


class SaveRepresentativeRequest(BaseModel):
    """Request to save a representative"""
    # Data from Geocodio response
    name: str
    first_name: str
    last_name: str
    title: str
    office_type: str
    party: Optional[str]
    district: Optional[str] = None
    bioguide_id: Optional[str] = None
    contact: dict
    social_media: dict
    offices: List[dict]
    photo_url: Optional[str]
    references: Optional[dict] = None
    birthday: Optional[str] = None
    gender: Optional[str] = None


@router.post("/save")
async def save_representative(
    rep_data: SaveRepresentativeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Save a representative to user's profile for future letters
    """
    from datetime import timedelta
    from app.core.config import settings

    # Check if representative already exists by bioguide_id or name
    query = select(Representative)
    if rep_data.bioguide_id:
        query = query.where(Representative.bioguide_id == rep_data.bioguide_id)
    else:
        # Match by name and office type
        query = query.where(
            and_(
                Representative.full_name == rep_data.name,
                Representative.office_type == rep_data.office_type
            )
        )

    result = await db.execute(query)
    representative = result.scalar_one_or_none()

    if not representative:
        # Create new representative record
        representative = Representative(
            bioguide_id=rep_data.bioguide_id,
            full_name=rep_data.name,
            first_name=rep_data.first_name,
            last_name=rep_data.last_name,
            title=rep_data.title,
            office_type=rep_data.office_type,
            state="OK",  # TODO: Get from data or user
            district=rep_data.district,
            party=rep_data.party,
            offices=rep_data.offices,
            phone=rep_data.contact.get("phone"),
            fax=rep_data.contact.get("fax"),
            email=rep_data.contact.get("email"),
            website=rep_data.contact.get("website"),
            twitter=rep_data.social_media.get("twitter"),
            facebook=rep_data.social_media.get("facebook"),
            youtube=rep_data.social_media.get("youtube"),
            photo_url=rep_data.photo_url,
            data_source="geocodio",
            expires_at=datetime.utcnow() + timedelta(seconds=settings.representative_cache_ttl)
        )
        db.add(representative)
        await db.flush()

    # Load the saved_representatives relationship
    await db.refresh(current_user, ["saved_representatives"])

    # Check if already saved by user
    if representative not in current_user.saved_representatives:
        current_user.saved_representatives.append(representative)
        await db.commit()

        return {
            "message": f"Saved {rep_data.name}",
            "representative_id": str(representative.id)
        }
    else:
        return {
            "message": f"{rep_data.name} is already saved",
            "representative_id": str(representative.id)
        }


@router.get("/saved")
async def get_saved_representatives(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all representatives saved by the current user
    """
    await db.refresh(current_user, ["saved_representatives"])

    representatives = []
    for rep in current_user.saved_representatives:
        representatives.append({
            "id": str(rep.id),
            "name": rep.full_name,
            "first_name": rep.first_name,
            "last_name": rep.last_name,
            "title": rep.title,
            "office_type": rep.office_type,
            "party": rep.party,
            "district": rep.district,
            "contact": {
                "phone": rep.phone,
                "fax": rep.fax,
                "email": rep.email,
                "website": rep.website,
            },
            "social_media": {
                "twitter": rep.twitter,
                "facebook": rep.facebook,
                "youtube": rep.youtube,
            },
            "offices": rep.offices,
            "photo_url": rep.photo_url,
            "bioguide_id": rep.bioguide_id
        })

    return {"representatives": representatives}


@router.delete("/saved/{representative_id}")
async def remove_saved_representative(
    representative_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Remove a representative from user's saved list
    """
    # Get the representative
    result = await db.execute(
        select(Representative).where(Representative.id == uuid.UUID(representative_id))
    )
    representative = result.scalar_one_or_none()

    if not representative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Representative not found"
        )

    # Load the saved_representatives relationship
    await db.refresh(current_user, ["saved_representatives"])

    # Remove from user's saved list
    if representative in current_user.saved_representatives:
        current_user.saved_representatives.remove(representative)
        await db.commit()
        return {"message": f"Removed {representative.full_name}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Representative was not in your saved list"
        )


class SaveAddressRequest(BaseModel):
    """Request to save user address"""
    street: str = Field(..., min_length=1)
    street_2: Optional[str] = None
    city: str = Field(..., min_length=1)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)
    is_primary: bool = False


@router.post("/save-address")
async def save_user_address(
    address_data: SaveAddressRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Save user's address to their profile
    """
    # If setting as primary, unset other primary addresses
    if address_data.is_primary:
        await db.execute(
            update(UserAddress)
            .where(UserAddress.user_id == current_user.id)
            .values(is_primary=False)
        )

    # Create new address
    user_address = UserAddress(
        user_id=current_user.id,
        street_1=address_data.street,
        street_2=address_data.street_2,
        city=address_data.city,
        state=address_data.state,
        zip_code=address_data.zip_code,
        is_primary=address_data.is_primary
    )

    db.add(user_address)
    await db.commit()
    await db.refresh(user_address)

    return {
        "message": "Address saved successfully",
        "address_id": str(user_address.id),
        "address": user_address.full_address
    }


@router.get("/user-addresses")
async def get_user_addresses(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all addresses for the current user
    """
    result = await db.execute(
        select(UserAddress)
        .where(UserAddress.user_id == current_user.id)
        .order_by(UserAddress.is_primary.desc(), UserAddress.created_at.desc())
    )
    addresses = result.scalars().all()

    return {
        "addresses": [
            {
                "id": str(addr.id),
                "street_1": addr.street_1,
                "street_2": addr.street_2,
                "city": addr.city,
                "state": addr.state,
                "zip_code": addr.zip_code,
                "is_primary": addr.is_primary,
                "full_address": addr.full_address
            }
            for addr in addresses
        ]
    }


@router.delete("/user-addresses/{address_id}")
async def delete_user_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete a user's saved address
    """
    # Get the address
    result = await db.execute(
        select(UserAddress).where(
            and_(
                UserAddress.id == uuid.UUID(address_id),
                UserAddress.user_id == current_user.id
            )
        )
    )
    address = result.scalar_one_or_none()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    # Delete the address
    await db.delete(address)
    await db.commit()

    return {"message": "Address deleted successfully"}