"""
Regenerate all PDFs in the database with updated format
This script will regenerate all existing PDFs to include full recipient addresses
and apply any other PDF formatting improvements.
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
from app.models.user import User, UserAddress
from app.services.pdf_generator import PDFService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def regenerate_all_pdfs(include_email: bool = False, include_phone: bool = False):
    """
    Regenerate all PDFs in the database

    Args:
        include_email: Whether to include email in return address
        include_phone: Whether to include phone in return address
    """
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
            # Get all letter recipients that have PDFs generated
            result = await db.execute(
                select(LetterRecipient).where(LetterRecipient.pdf_generated == True)
            )
            recipients = result.scalars().all()

            if not recipients:
                logger.info("No PDFs found to regenerate")
                return

            logger.info(f"Found {len(recipients)} PDFs to regenerate")

            pdf_service = PDFService()
            success_count = 0
            error_count = 0

            for i, recipient in enumerate(recipients, 1):
                try:
                    # Get the user who created this letter
                    # We need to navigate: recipient -> letter -> user
                    from app.models.letter import Letter
                    letter_result = await db.execute(
                        select(Letter).where(Letter.id == recipient.letter_id)
                    )
                    letter = letter_result.scalar_one_or_none()

                    if not letter:
                        logger.warning(f"Letter not found for recipient {recipient.id}")
                        error_count += 1
                        continue

                    # Get user
                    user_result = await db.execute(
                        select(User).where(User.id == letter.user_id)
                    )
                    user = user_result.scalar_one_or_none()

                    if not user:
                        logger.warning(f"User not found for letter {letter.id}")
                        error_count += 1
                        continue

                    # Get user's primary address
                    address_result = await db.execute(
                        select(UserAddress)
                        .where(UserAddress.user_id == user.id)
                        .order_by(UserAddress.is_primary.desc(), UserAddress.created_at.desc())
                    )
                    addresses = address_result.scalars().all()

                    sender_street_1 = ""
                    sender_street_2 = None
                    sender_city = ""
                    sender_state = ""
                    sender_zip = ""

                    if addresses:
                        primary_address = addresses[0]
                        sender_street_1 = primary_address.street_1
                        sender_street_2 = primary_address.street_2
                        sender_city = primary_address.city
                        sender_state = primary_address.state
                        sender_zip = primary_address.zip_code

                    logger.info(f"Regenerating PDF {i}/{len(recipients)}: {recipient.recipient_name}")

                    # Regenerate PDF
                    result = await pdf_service.generate_pdf_for_recipient(
                        letter_recipient=recipient,
                        sender_name=user.full_name,
                        sender_street_1=sender_street_1,
                        sender_street_2=sender_street_2,
                        sender_city=sender_city,
                        sender_state=sender_state,
                        sender_zip=sender_zip,
                        sender_email=user.email,
                        sender_phone=user.phone,
                        include_email=include_email,
                        include_phone=include_phone
                    )

                    if result['success']:
                        success_count += 1
                        logger.info(f"  ✓ Successfully regenerated PDF for {recipient.recipient_name}")
                    else:
                        error_count += 1
                        logger.error(f"  ✗ Failed to regenerate PDF for {recipient.recipient_name}: {result.get('error')}")

                except Exception as e:
                    error_count += 1
                    logger.error(f"  ✗ Error regenerating PDF for recipient {recipient.id}: {e}")

            logger.info("=" * 60)
            logger.info(f"Regeneration complete!")
            logger.info(f"  Success: {success_count}")
            logger.info(f"  Errors: {error_count}")
            logger.info(f"  Total: {len(recipients)}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Fatal error during PDF regeneration: {e}")
            raise

        finally:
            await engine.dispose()


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Regenerate all PDFs in the database')
    parser.add_argument(
        '--include-email',
        action='store_true',
        help='Include email addresses in return address'
    )
    parser.add_argument(
        '--include-phone',
        action='store_true',
        help='Include phone numbers in return address'
    )

    args = parser.parse_args()

    logger.info("Starting PDF regeneration...")
    logger.info(f"Options: include_email={args.include_email}, include_phone={args.include_phone}")

    await regenerate_all_pdfs(
        include_email=args.include_email,
        include_phone=args.include_phone
    )


if __name__ == '__main__':
    asyncio.run(main())
