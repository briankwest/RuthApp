"""
Letter delivery API endpoints
Handles fax, email, and print delivery options
"""
import uuid
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.api.dependencies import get_current_active_user as get_current_user
from app.core.config import settings, derived_settings
from app.models.user import User
from app.models.letter import (
    Letter, LetterRecipient, DeliveryLog,
    LetterStatus, DeliveryMethod, DeliveryStatus
)
from app.models.geocoding import Representative
from app.services.fax import SignalWireFaxService
from app.services.ses import SESService
from app.services.pdf_generator import PDFService

router = APIRouter(prefix="/api/delivery", tags=["delivery"])


# ==================== Request/Response Models ====================

class DeliveryOptionsResponse(BaseModel):
    """Available delivery options for a recipient"""
    recipient_id: str
    recipient_name: str
    recipient_title: str
    available_methods: Dict[str, Any]


class SendFaxRequest(BaseModel):
    """Request to send fax"""
    recipient_id: str
    fax_number: Optional[str] = None  # Override if different from representative's


class SendEmailRequest(BaseModel):
    """Request to send email"""
    recipient_id: str
    email_address: Optional[EmailStr] = None  # Override if different from representative's


class DeliveryStatusResponse(BaseModel):
    """Delivery status response"""
    recipient_id: str
    recipient_name: str
    delivery_method: Optional[str]
    delivery_status: Optional[str]
    delivery_logs: List[Dict[str, Any]]


# ==================== Delivery Options Endpoints ====================

@router.get("/letters/{letter_id}/delivery-options", response_model=List[DeliveryOptionsResponse])
async def get_delivery_options(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available delivery methods for each recipient"""
    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get all recipients
    result = await db.execute(
        select(LetterRecipient).where(LetterRecipient.letter_id == letter.id)
    )
    recipients = result.scalars().all()

    options_list = []

    for recipient in recipients:
        # Try to find representative data for contact info
        available_methods = {
            'print': True,  # Always available
            'fax': False,
            'email': False,
            'fax_number': None,
            'email_address': None
        }

        # Try to get representative by name matching
        # This is a best-effort lookup
        result = await db.execute(
            select(Representative).where(
                Representative.full_name.ilike(f"%{recipient.recipient_name}%")
            ).limit(1)
        )
        rep = result.scalar_one_or_none()

        if rep:
            available_methods = rep.get_available_delivery_methods()
        else:
            # Check if contact info is in recipient address
            if recipient.recipient_address.get('fax'):
                available_methods['fax'] = True
                available_methods['fax_number'] = recipient.recipient_address['fax']
            if recipient.recipient_address.get('email'):
                available_methods['email'] = True
                available_methods['email_address'] = recipient.recipient_address['email']

        options_list.append(
            DeliveryOptionsResponse(
                recipient_id=str(recipient.id),
                recipient_name=recipient.recipient_name,
                recipient_title=recipient.recipient_title,
                available_methods=available_methods
            )
        )

    return options_list


@router.get("/letters/{letter_id}/recipients/{recipient_id}/delivery-options")
async def get_recipient_delivery_options(
    letter_id: str,
    recipient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available delivery methods for a specific recipient"""
    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get the recipient
    result = await db.execute(
        select(LetterRecipient).where(
            and_(
                LetterRecipient.id == uuid.UUID(recipient_id),
                LetterRecipient.letter_id == letter.id
            )
        )
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    # Get available methods
    available_methods = {
        'print': True,
        'fax': False,
        'email': False,
        'fax_number': None,
        'email_address': None
    }

    # Try to get representative data
    result = await db.execute(
        select(Representative).where(
            Representative.full_name.ilike(f"%{recipient.recipient_name}%")
        ).limit(1)
    )
    rep = result.scalar_one_or_none()

    if rep:
        available_methods = rep.get_available_delivery_methods()
    else:
        # Check recipient address for contact info
        if recipient.recipient_address.get('fax'):
            available_methods['fax'] = True
            available_methods['fax_number'] = recipient.recipient_address['fax']
        if recipient.recipient_address.get('email'):
            available_methods['email'] = True
            available_methods['email_address'] = recipient.recipient_address['email']

    # Add service availability info
    return {
        'recipient_id': str(recipient.id),
        'recipient_name': recipient.recipient_name,
        'recipient_title': recipient.recipient_title,
        'available_methods': available_methods,
        'pdf_generated': recipient.pdf_generated,
        'services_configured': {
            'fax': derived_settings.enable_fax,
            'email': derived_settings.enable_email
        }
    }


# ==================== Fax Delivery Endpoints ====================

@router.post("/letters/{letter_id}/recipients/{recipient_id}/send-fax")
async def send_fax(
    letter_id: str,
    recipient_id: str,
    fax_number: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send letter via fax to a recipient"""
    # Check if fax is configured
    if not derived_settings.enable_fax:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fax service is not configured"
        )

    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get the recipient
    result = await db.execute(
        select(LetterRecipient).where(
            and_(
                LetterRecipient.id == uuid.UUID(recipient_id),
                LetterRecipient.letter_id == letter.id
            )
        )
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    # Check if PDF is generated
    if not recipient.pdf_generated or not recipient.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF must be generated before sending fax. Call /generate-pdf first."
        )

    # Determine fax number
    target_fax = fax_number
    if not target_fax:
        # Try to get from representative
        result = await db.execute(
            select(Representative).where(
                Representative.full_name.ilike(f"%{recipient.recipient_name}%")
            ).limit(1)
        )
        rep = result.scalar_one_or_none()

        if rep and rep.fax:
            target_fax = rep.fax
        elif recipient.recipient_address.get('fax'):
            target_fax = recipient.recipient_address['fax']

    if not target_fax:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fax number available for this recipient. Please provide one."
        )

    # Validate fax number
    fax_service = SignalWireFaxService()
    if not fax_service.validate_fax_number(target_fax):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid fax number format"
        )

    # TODO: Create publicly accessible URL for PDF
    # For now, we'll need to implement PDF serving endpoint or use S3
    # This is a placeholder - you'll need to adapt based on your infrastructure

    # Option 1: If you have a public endpoint to serve PDFs
    pdf_url = f"{settings.cors_origins[0]}/api/pdfs/{recipient.id}.pdf"

    # Option 2: Upload to S3 and use that URL (if S3 is configured)
    # if derived_settings.enable_s3:
    #     pdf_url = await upload_to_s3(recipient.pdf_path)

    # Send fax
    result = await fax_service.send_fax(
        to_number=target_fax,
        pdf_url=pdf_url,
        recipient_name=recipient.recipient_name
    )

    # Create delivery log
    delivery_log = DeliveryLog(
        id=uuid.uuid4(),
        letter_recipient_id=recipient.id,
        delivery_method=DeliveryMethod.FAX,
        delivery_status=DeliveryStatus.PROCESSING if result['success'] else DeliveryStatus.FAILED,
        fax_number=target_fax,
        fax_sid=result.get('fax_sid'),
        delivery_details=result,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow() if not result['success'] else None,
        error_message=result.get('error') if not result['success'] else None
    )

    db.add(delivery_log)

    # Update recipient status
    if result['success']:
        recipient.delivery_method = DeliveryMethod.FAX
        recipient.delivery_status = DeliveryStatus.PROCESSING
    else:
        recipient.delivery_status = DeliveryStatus.FAILED

    await db.commit()
    await db.refresh(delivery_log)

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fax sending failed: {result.get('error')}"
        )

    return {
        'success': True,
        'message': 'Fax queued for delivery',
        'fax_sid': result.get('fax_sid'),
        'delivery_log_id': str(delivery_log.id),
        'to': target_fax,
        'status': result.get('status')
    }


@router.get("/fax/{fax_sid}/status")
async def get_fax_status(
    fax_sid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the status of a sent fax"""
    # Find delivery log
    result = await db.execute(
        select(DeliveryLog).where(DeliveryLog.fax_sid == fax_sid)
    )
    delivery_log = result.scalar_one_or_none()

    if not delivery_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fax not found"
        )

    # Verify user owns this letter
    result = await db.execute(
        select(LetterRecipient).where(LetterRecipient.id == delivery_log.letter_recipient_id)
    )
    recipient = result.scalar_one_or_none()

    if recipient:
        result = await db.execute(
            select(Letter).where(Letter.id == recipient.letter_id)
        )
        letter = result.scalar_one_or_none()

        if not letter or letter.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    # Get updated status from SignalWire
    fax_service = SignalWireFaxService()
    status_result = await fax_service.get_fax_status(fax_sid)

    if status_result['success']:
        # Update delivery log
        from app.services.fax import FaxStatus

        delivery_log.delivery_status = FaxStatus.to_delivery_status(status_result['status'])
        delivery_log.delivery_details = status_result

        if status_result['status'] in ['delivered', 'received']:
            delivery_log.completed_at = datetime.utcnow()
            delivery_log.pages_sent = str(status_result.get('num_pages', ''))

            # Update recipient status
            if recipient:
                recipient.delivery_status = DeliveryStatus.DELIVERED
        elif status_result['status'] in ['failed', 'no-answer', 'busy', 'canceled']:
            delivery_log.completed_at = datetime.utcnow()
            delivery_log.error_message = f"Fax {status_result['status']}"

            if recipient:
                recipient.delivery_status = DeliveryStatus.FAILED

        await db.commit()

    return {
        'fax_sid': fax_sid,
        'status': status_result.get('status'),
        'to': status_result.get('to'),
        'from': status_result.get('from'),
        'num_pages': status_result.get('num_pages'),
        'duration': status_result.get('duration'),
        'price': status_result.get('price'),
        'price_unit': status_result.get('price_unit'),
        'date_created': status_result.get('date_created'),
        'date_updated': status_result.get('date_updated')
    }


# ==================== Email Delivery Endpoints ====================

@router.post("/letters/{letter_id}/recipients/{recipient_id}/send-email")
async def send_email(
    letter_id: str,
    recipient_id: str,
    email_address: Optional[EmailStr] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send letter via email to a recipient"""
    # Check if email is configured
    if not derived_settings.enable_email:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured"
        )

    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get the recipient
    result = await db.execute(
        select(LetterRecipient).where(
            and_(
                LetterRecipient.id == uuid.UUID(recipient_id),
                LetterRecipient.letter_id == letter.id
            )
        )
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    # Check if PDF is generated
    if not recipient.pdf_generated or not recipient.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF must be generated before sending email. Call /generate-pdf first."
        )

    # Determine email address
    target_email = email_address
    if not target_email:
        # Try to get from representative
        result = await db.execute(
            select(Representative).where(
                Representative.full_name.ilike(f"%{recipient.recipient_name}%")
            ).limit(1)
        )
        rep = result.scalar_one_or_none()

        if rep and rep.email:
            target_email = rep.email
        elif recipient.recipient_address.get('email'):
            target_email = recipient.recipient_address['email']

    if not target_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email address available for this recipient. Please provide one."
        )

    # Read PDF file
    if not os.path.exists(recipient.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF file not found. Please regenerate the PDF."
        )

    with open(recipient.pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    # Send email via SES
    ses_service = SESService()
    result = await ses_service.send_letter_email(
        to_email=target_email,
        recipient_name=recipient.recipient_name,
        letter_subject=recipient.personalized_subject or letter.subject,
        letter_content=recipient.personalized_content,
        pdf_attachment=pdf_bytes
    )

    # Create delivery log
    delivery_log = DeliveryLog(
        id=uuid.uuid4(),
        letter_recipient_id=recipient.id,
        delivery_method=DeliveryMethod.EMAIL,
        delivery_status=DeliveryStatus.SENT if result['success'] else DeliveryStatus.FAILED,
        email_address=target_email,
        email_message_id=result.get('message_id'),
        delivery_details=result,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        error_message=result.get('error') if not result['success'] else None
    )

    db.add(delivery_log)

    # Update recipient status
    if result['success']:
        recipient.delivery_method = DeliveryMethod.EMAIL
        recipient.delivery_status = DeliveryStatus.SENT
    else:
        recipient.delivery_status = DeliveryStatus.FAILED

    await db.commit()
    await db.refresh(delivery_log)

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email sending failed: {result.get('error')}"
        )

    return {
        'success': True,
        'message': 'Email sent successfully',
        'message_id': result.get('message_id'),
        'delivery_log_id': str(delivery_log.id),
        'to': target_email,
        'subject': result.get('subject')
    }


# ==================== Delivery Status Endpoints ====================

@router.get("/letters/{letter_id}/delivery-status", response_model=List[DeliveryStatusResponse])
async def get_letter_delivery_status(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get delivery status for all recipients of a letter"""
    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get all recipients
    result = await db.execute(
        select(LetterRecipient).where(LetterRecipient.letter_id == letter.id)
    )
    recipients = result.scalars().all()

    status_list = []

    for recipient in recipients:
        # Get delivery logs
        result = await db.execute(
            select(DeliveryLog)
            .where(DeliveryLog.letter_recipient_id == recipient.id)
            .order_by(DeliveryLog.started_at.desc())
        )
        logs = result.scalars().all()

        status_list.append(
            DeliveryStatusResponse(
                recipient_id=str(recipient.id),
                recipient_name=recipient.recipient_name,
                delivery_method=recipient.delivery_method.value if recipient.delivery_method else None,
                delivery_status=recipient.delivery_status.value if recipient.delivery_status else None,
                delivery_logs=[
                    {
                        'id': str(log.id),
                        'method': log.delivery_method.value,
                        'status': log.delivery_status.value,
                        'started_at': log.started_at.isoformat() if log.started_at else None,
                        'completed_at': log.completed_at.isoformat() if log.completed_at else None,
                        'error_message': log.error_message,
                        'fax_sid': log.fax_sid,
                        'email_message_id': log.email_message_id
                    }
                    for log in logs
                ]
            )
        )

    return status_list


@router.get("/letters/{letter_id}/recipients/{recipient_id}/delivery-status")
async def get_recipient_delivery_status(
    letter_id: str,
    recipient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get delivery status for a specific recipient"""
    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get the recipient
    result = await db.execute(
        select(LetterRecipient).where(
            and_(
                LetterRecipient.id == uuid.UUID(recipient_id),
                LetterRecipient.letter_id == letter.id
            )
        )
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    # Get delivery logs
    result = await db.execute(
        select(DeliveryLog)
        .where(DeliveryLog.letter_recipient_id == recipient.id)
        .order_by(DeliveryLog.started_at.desc())
    )
    logs = result.scalars().all()

    return {
        'recipient_id': str(recipient.id),
        'recipient_name': recipient.recipient_name,
        'delivery_method': recipient.delivery_method.value if recipient.delivery_method else None,
        'delivery_status': recipient.delivery_status.value if recipient.delivery_status else None,
        'delivery_logs': [
            {
                'id': str(log.id),
                'method': log.delivery_method.value,
                'status': log.delivery_status.value,
                'started_at': log.started_at.isoformat() if log.started_at else None,
                'completed_at': log.completed_at.isoformat() if log.completed_at else None,
                'error_message': log.error_message,
                'fax_sid': log.fax_sid,
                'fax_number': log.fax_number,
                'email_message_id': log.email_message_id,
                'email_address': log.email_address,
                'pages_sent': log.pages_sent,
                'retry_count': log.retry_count
            }
            for log in logs
        ]
    }