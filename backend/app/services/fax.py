"""
SignalWire Fax Service
Handles fax delivery of letters to representatives
"""
import logging
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class SignalWireFaxService:
    """Service for sending faxes via SignalWire API"""

    def __init__(self):
        self.project_id = settings.signalwire_project_id
        self.token = settings.signalwire_token
        self.space_url = settings.signalwire_space_url
        self.from_number = settings.signalwire_fax_from

        # Validate configuration
        if not all([self.project_id, self.token, self.space_url, self.from_number]):
            logger.warning("SignalWire fax service not fully configured")

        # Construct base URL
        self.base_url = f"https://{self.space_url}/api/laml/2010-04-01"
        self.auth = (self.project_id, self.token)

    def is_configured(self) -> bool:
        """Check if SignalWire is properly configured"""
        return all([self.project_id, self.token, self.space_url, self.from_number])

    async def send_fax(self,
                      to_number: str,
                      pdf_url: str,
                      recipient_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a fax via SignalWire

        Args:
            to_number: Destination fax number (E.164 format recommended)
            pdf_url: Publicly accessible URL to the PDF file
            recipient_name: Optional name of recipient for logging

        Returns:
            Dictionary with send status and details
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'SignalWire fax service not configured',
                'error_code': 'NOT_CONFIGURED'
            }

        try:
            # Clean phone number (remove spaces, dashes, parentheses)
            to_number_cleaned = to_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

            # Ensure it starts with + for E.164 format
            if not to_number_cleaned.startswith('+'):
                # Assume US number if not in international format
                if len(to_number_cleaned) == 10:
                    to_number_cleaned = f"+1{to_number_cleaned}"
                elif len(to_number_cleaned) == 11 and to_number_cleaned.startswith('1'):
                    to_number_cleaned = f"+{to_number_cleaned}"
                else:
                    to_number_cleaned = f"+{to_number_cleaned}"

            logger.info(f"Sending fax to {to_number_cleaned} (recipient: {recipient_name})")

            # Prepare fax data
            fax_data = {
                'From': self.from_number,
                'To': to_number_cleaned,
                'MediaUrl': pdf_url,
                'Quality': 'fine',  # Options: standard, fine, superfine
                'StatusCallback': None,  # TODO: Add webhook URL for status updates
            }

            # Send fax via SignalWire API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/Accounts/{self.project_id}/Faxes.json",
                    auth=self.auth,
                    data=fax_data
                )

            if response.status_code == 201:
                # Fax queued successfully
                fax_response = response.json()

                logger.info(f"Fax queued successfully. SID: {fax_response.get('sid')}")

                return {
                    'success': True,
                    'fax_sid': fax_response.get('sid'),
                    'status': fax_response.get('status'),
                    'to': fax_response.get('to'),
                    'from': fax_response.get('from'),
                    'direction': fax_response.get('direction'),
                    'num_pages': fax_response.get('num_pages'),
                    'date_created': fax_response.get('date_created'),
                    'price': fax_response.get('price'),
                    'price_unit': fax_response.get('price_unit'),
                    'message': 'Fax queued for delivery'
                }
            else:
                # Error occurred
                error_data = response.json() if response.text else {}
                error_message = error_data.get('message', 'Unknown error')
                error_code = error_data.get('code', response.status_code)

                logger.error(f"SignalWire fax error {error_code}: {error_message}")

                return {
                    'success': False,
                    'error': error_message,
                    'error_code': str(error_code),
                    'status_code': response.status_code
                }

        except httpx.TimeoutException:
            logger.error("Timeout sending fax to SignalWire")
            return {
                'success': False,
                'error': 'Request timeout',
                'error_code': 'TIMEOUT'
            }
        except httpx.RequestError as e:
            logger.error(f"Network error sending fax: {e}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'error_code': 'NETWORK_ERROR'
            }
        except Exception as e:
            logger.error(f"Unexpected error sending fax: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UNKNOWN_ERROR'
            }

    async def get_fax_status(self, fax_sid: str) -> Dict[str, Any]:
        """
        Get the status of a sent fax

        Args:
            fax_sid: The SignalWire fax SID

        Returns:
            Dictionary with fax status information
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'SignalWire fax service not configured'
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/Accounts/{self.project_id}/Faxes/{fax_sid}.json",
                    auth=self.auth
                )

            if response.status_code == 200:
                fax_data = response.json()

                return {
                    'success': True,
                    'sid': fax_data.get('sid'),
                    'status': fax_data.get('status'),
                    'to': fax_data.get('to'),
                    'from': fax_data.get('from'),
                    'num_pages': fax_data.get('num_pages'),
                    'duration': fax_data.get('duration'),
                    'quality': fax_data.get('quality'),
                    'price': fax_data.get('price'),
                    'price_unit': fax_data.get('price_unit'),
                    'date_created': fax_data.get('date_created'),
                    'date_updated': fax_data.get('date_updated')
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'error_code': error_data.get('code', response.status_code)
                }

        except Exception as e:
            logger.error(f"Error getting fax status: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def cancel_fax(self, fax_sid: str) -> Dict[str, Any]:
        """
        Cancel a queued fax

        Args:
            fax_sid: The SignalWire fax SID

        Returns:
            Dictionary with cancellation status
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'SignalWire fax service not configured'
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/Accounts/{self.project_id}/Faxes/{fax_sid}.json",
                    auth=self.auth,
                    data={'Status': 'canceled'}
                )

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Fax cancelled successfully'
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error')
                }

        except Exception as e:
            logger.error(f"Error cancelling fax: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def validate_fax_number(self, fax_number: str) -> bool:
        """
        Basic validation of fax number format

        Args:
            fax_number: Phone number to validate

        Returns:
            True if number appears valid
        """
        if not fax_number:
            return False

        # Remove common formatting characters
        cleaned = fax_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')

        # Check if it's all digits
        if not cleaned.isdigit():
            return False

        # Check length (10 digits for US, 11 for US with country code, up to 15 for international)
        if len(cleaned) < 10 or len(cleaned) > 15:
            return False

        return True

    async def estimate_pages(self, pdf_path: str) -> Optional[int]:
        """
        Estimate number of pages in PDF (for cost estimation)

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages or None if error
        """
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            logger.warning(f"Could not count PDF pages: {e}")
            return None

    def estimate_cost(self, num_pages: int, is_international: bool = False) -> Dict[str, Any]:
        """
        Estimate fax cost based on pages

        Note: SignalWire pricing varies. This is an estimate.
        Check current pricing at: https://signalwire.com/pricing

        Args:
            num_pages: Number of pages
            is_international: Whether it's an international fax

        Returns:
            Cost estimate information
        """
        # Approximate SignalWire pricing (as of 2024)
        # US/Canada: ~$0.01-0.02 per page
        # International: varies widely by country

        if is_international:
            cost_per_page = 0.05  # Conservative estimate
            note = "International pricing varies by country"
        else:
            cost_per_page = 0.015  # US/Canada estimate
            note = "US/Canada domestic rate"

        estimated_cost = num_pages * cost_per_page

        return {
            'num_pages': num_pages,
            'cost_per_page': cost_per_page,
            'estimated_total': estimated_cost,
            'currency': 'USD',
            'note': note,
            'disclaimer': 'This is an estimate. Actual costs may vary.'
        }


# Status constants for fax delivery
class FaxStatus:
    """SignalWire fax status values"""
    QUEUED = "queued"
    PROCESSING = "processing"
    SENDING = "sending"
    DELIVERED = "delivered"
    RECEIVING = "receiving"
    RECEIVED = "received"
    NO_ANSWER = "no-answer"
    BUSY = "busy"
    FAILED = "failed"
    CANCELED = "canceled"

    # Mapping to our delivery status
    @staticmethod
    def to_delivery_status(signalwire_status: str) -> str:
        """Convert SignalWire status to our DeliveryStatus enum"""
        from app.models.letter import DeliveryStatus

        status_map = {
            FaxStatus.QUEUED: DeliveryStatus.PROCESSING,
            FaxStatus.PROCESSING: DeliveryStatus.PROCESSING,
            FaxStatus.SENDING: DeliveryStatus.PROCESSING,
            FaxStatus.DELIVERED: DeliveryStatus.DELIVERED,
            FaxStatus.RECEIVED: DeliveryStatus.DELIVERED,
            FaxStatus.NO_ANSWER: DeliveryStatus.FAILED,
            FaxStatus.BUSY: DeliveryStatus.FAILED,
            FaxStatus.FAILED: DeliveryStatus.FAILED,
            FaxStatus.CANCELED: DeliveryStatus.CANCELLED,
        }

        return status_map.get(signalwire_status, DeliveryStatus.PENDING)