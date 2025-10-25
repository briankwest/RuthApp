"""
Update recipient addresses in existing letter records
This script updates the recipient_address field for all LetterRecipient records
by fetching the current address from the Representative model.
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
from app.models.letter import LetterRecipient
from app.models.geocoding import Representative

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def update_recipient_addresses():
    """Update recipient addresses in all letter recipient records"""
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
            # Get all letter recipients
            result = await db.execute(select(LetterRecipient))
            recipients = result.scalars().all()

            if not recipients:
                logger.info("No letter recipients found")
                return

            logger.info(f"Found {len(recipients)} letter recipients to update")

            success_count = 0
            error_count = 0
            no_match_count = 0

            for i, recipient in enumerate(recipients, 1):
                try:
                    logger.info(f"Processing {i}/{len(recipients)}: {recipient.recipient_name}")

                    # Try to find matching representative
                    rep_result = await db.execute(
                        select(Representative).where(
                            Representative.full_name.ilike(f"%{recipient.recipient_name}%")
                        ).limit(1)
                    )
                    rep = rep_result.scalar_one_or_none()

                    if not rep:
                        logger.warning(f"  ⚠ No representative found for {recipient.recipient_name}")
                        no_match_count += 1
                        continue

                    # Get updated address from representative
                    updated_address = rep.address

                    # Compare and update if different
                    current_address = recipient.recipient_address
                    if current_address.get('street_1') != updated_address.get('street_1'):
                        logger.info(f"  ↻ Updating address for {recipient.recipient_name}")
                        logger.info(f"    Old: {current_address.get('street_1', 'EMPTY')}")
                        logger.info(f"    New: {updated_address.get('street_1', 'EMPTY')}")

                        recipient.recipient_address = updated_address
                        success_count += 1
                    else:
                        logger.info(f"  ✓ Address already correct for {recipient.recipient_name}")
                        success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"  ✗ Error updating {recipient.recipient_name}: {e}")

            # Commit all changes
            await db.commit()

            logger.info("=" * 60)
            logger.info(f"Update complete!")
            logger.info(f"  Updated: {success_count}")
            logger.info(f"  No match: {no_match_count}")
            logger.info(f"  Errors: {error_count}")
            logger.info(f"  Total: {len(recipients)}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Fatal error during address update: {e}")
            raise

        finally:
            await engine.dispose()


async def main():
    """Main entry point"""
    logger.info("Starting recipient address update...")
    await update_recipient_addresses()


if __name__ == '__main__':
    asyncio.run(main())
