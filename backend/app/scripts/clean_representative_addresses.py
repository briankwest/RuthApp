"""
Clean representative addresses using Google Address Validation API
This script parses embedded city/state/zip from street_1 fields
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.geocoding import Representative
from app.utils.google_address import parse_office_address_with_google

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def clean_representative_addresses():
    """Clean all representative addresses using Google Address Validation API"""
    # Create async engine
    engine = create_async_engine(
        settings.async_database_url,
        echo=False
    )

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        try:
            # Get all representatives
            result = await db.execute(select(Representative))
            representatives = result.scalars().all()

            if not representatives:
                logger.info("No representatives found")
                return

            logger.info(f"Found {len(representatives)} representatives to process")

            success_count = 0
            error_count = 0
            skipped_count = 0

            for i, rep in enumerate(representatives, 1):
                try:
                    logger.info(f"Processing {i}/{len(representatives)}: {rep.full_name}")

                    if not rep.offices:
                        logger.warning(f"  ⚠ No offices for {rep.full_name}")
                        skipped_count += 1
                        continue

                    # Clean each office
                    updated_offices = []
                    for office in rep.offices:
                        street_1 = office.get('street_1', '')
                        city = office.get('city', '')
                        state = office.get('state', '')
                        zip_code = office.get('zip', '')

                        if not street_1:
                            updated_offices.append(office)
                            continue

                        logger.info(f"  Parsing office: {office.get('name', 'Unknown')}")
                        logger.info(f"    Original: {street_1}")

                        # Parse address using Google API
                        parsed = await parse_office_address_with_google(
                            street_1, city, state, zip_code
                        )

                        # Update office with parsed values
                        updated_office = office.copy()
                        updated_office['street_1'] = parsed['street_1']
                        updated_office['street_2'] = parsed['street_2']
                        updated_office['city'] = parsed['city']
                        updated_office['state'] = parsed['state']
                        updated_office['zip'] = parsed['zip']

                        logger.info(f"    Cleaned:")
                        logger.info(f"      street_1: {parsed['street_1']}")
                        if parsed['street_2']:
                            logger.info(f"      street_2: {parsed['street_2']}")
                        logger.info(f"      city: {parsed['city']}, {parsed['state']} {parsed['zip']}")

                        updated_offices.append(updated_office)

                    # Update representative with cleaned offices
                    rep.offices = updated_offices
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"  ✗ Error processing {rep.full_name}: {e}")

            # Commit all changes
            await db.commit()

            logger.info("=" * 60)
            logger.info(f"Address cleaning complete!")
            logger.info(f"  Success: {success_count}")
            logger.info(f"  Skipped: {skipped_count}")
            logger.info(f"  Errors: {error_count}")
            logger.info(f"  Total: {len(representatives)}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Fatal error during address cleaning: {e}")
            raise

        finally:
            await engine.dispose()


async def main():
    """Main entry point"""
    logger.info("Starting representative address cleaning...")
    logger.info("Using Google Address Validation API")
    await clean_representative_addresses()


if __name__ == '__main__':
    asyncio.run(main())
