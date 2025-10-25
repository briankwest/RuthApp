"""
Amazon SES email service for sending emails
"""
import logging
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import settings

logger = logging.getLogger(__name__)


class SESService:
    """
    Service for sending emails via Amazon SES
    """

    def __init__(self):
        """Initialize SES client"""
        self.ses_client = boto3.client(
            'ses',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.from_email = settings.ses_from_email
        self.from_name = settings.ses_from_name
        self.configuration_set = settings.ses_configuration_set

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Amazon SES

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            text_body: Plain text content of the email
            attachments: List of attachments (dict with 'filename' and 'content')
            cc_emails: List of CC recipients
            bcc_emails: List of BCC recipients
            reply_to: Reply-to email address

        Returns:
            Dictionary with message ID and status
        """
        try:
            # Create message container
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            if reply_to:
                msg['Reply-To'] = reply_to

            # Create message body
            msg_body = MIMEMultipart('alternative')

            # Add text part if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                msg_body.attach(text_part)

            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg_body.attach(html_part)

            msg.attach(msg_body)

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    att = MIMEApplication(attachment['content'])
                    att.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=attachment['filename']
                    )
                    msg.attach(att)

            # Prepare destination
            destination = {'ToAddresses': [to_email]}
            if cc_emails:
                destination['CcAddresses'] = cc_emails
            if bcc_emails:
                destination['BccAddresses'] = bcc_emails

            # Send email
            kwargs = {
                'Source': f"{self.from_name} <{self.from_email}>",
                'Destination': destination,
                'RawMessage': {'Data': msg.as_string()}
            }

            # Add configuration set if specified (for tracking)
            if self.configuration_set:
                kwargs['ConfigurationSetName'] = self.configuration_set

            response = self.ses_client.send_raw_email(**kwargs)

            logger.info(f"Email sent successfully to {to_email}, MessageId: {response['MessageId']}")

            return {
                'success': True,
                'message_id': response['MessageId'],
                'status': 'sent',
                'to': to_email,
                'subject': subject
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"SES ClientError: {error_code} - {error_message}")

            return {
                'success': False,
                'error': error_message,
                'error_code': error_code,
                'to': to_email,
                'subject': subject
            }

        except BotoCoreError as e:
            logger.error(f"SES BotoCoreError: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'to': to_email,
                'subject': subject
            }

        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'to': to_email,
                'subject': subject
            }

    async def send_letter_email(
        self,
        to_email: str,
        recipient_name: str,
        letter_subject: str,
        letter_content: str,
        pdf_attachment: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Send a letter via email with optional PDF attachment

        Args:
            to_email: Representative's email address
            recipient_name: Name of the representative
            letter_subject: Subject of the letter
            letter_content: Content of the letter
            pdf_attachment: PDF bytes to attach

        Returns:
            Dictionary with send status
        """
        # Format email subject
        subject = f"Constituent Letter: {letter_subject}"

        # Create HTML body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .letter {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
                .content {{ margin-top: 20px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="letter">
                <div class="header">
                    <h2>Constituent Letter</h2>
                    <p><strong>To:</strong> {recipient_name}</p>
                    <p><strong>Subject:</strong> {letter_subject}</p>
                </div>
                <div class="content">
                    {letter_content.replace(chr(10), '<br>')}
                </div>
                <div class="footer">
                    <p>This letter was sent via the Ruth civic engagement platform.</p>
                    <p>Please do not reply to this automated email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Create plain text body
        text_body = f"""
Constituent Letter

To: {recipient_name}
Subject: {letter_subject}

{letter_content}

---
This letter was sent via the Ruth civic engagement platform.
Please do not reply to this automated email.
        """

        # Prepare attachments if PDF is provided
        attachments = None
        if pdf_attachment:
            attachments = [{
                'filename': f'letter_{letter_subject.replace(" ", "_")[:30]}.pdf',
                'content': pdf_attachment
            }]

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            attachments=attachments
        )

    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_url: str
    ) -> Dict[str, Any]:
        """
        Send email verification link

        Args:
            to_email: User's email address
            user_name: User's name
            verification_url: Verification URL

        Returns:
            Dictionary with send status
        """
        subject = "Verify your Ruth Platform email address"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Welcome to Ruth Platform, {user_name}!</h2>
                <p>Please verify your email address by clicking the link below:</p>
                <p style="margin: 25px 0;">
                    <a href="{verification_url}"
                       style="background-color: #0066cc; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px;">
                        Verify Email Address
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="color: #666; font-size: 14px;">{verification_url}</p>
                <p>This link will expire in 7 days.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ccc;">
                <p style="color: #666; font-size: 12px;">
                    If you didn't create an account on Ruth Platform, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
Welcome to Ruth Platform, {user_name}!

Please verify your email address by clicking this link:
{verification_url}

This link will expire in 7 days.

If you didn't create an account on Ruth Platform, please ignore this email.
        """

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str
    ) -> Dict[str, Any]:
        """
        Send password reset email

        Args:
            to_email: User's email address
            user_name: User's name
            reset_url: Password reset URL

        Returns:
            Dictionary with send status
        """
        subject = "Reset your Ruth Platform password"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Password Reset Request</h2>
                <p>Hi {user_name},</p>
                <p>We received a request to reset your password. Click the link below to set a new password:</p>
                <p style="margin: 25px 0;">
                    <a href="{reset_url}"
                       style="background-color: #ff6b6b; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="color: #666; font-size: 14px;">{reset_url}</p>
                <p>This link will expire in 24 hours.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ccc;">
                <p style="color: #666; font-size: 12px;">
                    If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
Password Reset Request

Hi {user_name},

We received a request to reset your password. Click this link to set a new password:
{reset_url}

This link will expire in 24 hours.

If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
        """

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

    async def verify_email_address(self, email: str) -> bool:
        """
        Verify if an email address is verified in SES

        Args:
            email: Email address to verify

        Returns:
            True if verified, False otherwise
        """
        try:
            response = self.ses_client.get_identity_verification_attributes(
                Identities=[email]
            )

            verification_attrs = response.get('VerificationAttributes', {})
            email_attrs = verification_attrs.get(email, {})

            return email_attrs.get('VerificationStatus') == 'Success'

        except Exception as e:
            logger.error(f"Error verifying email address: {str(e)}")
            return False

    async def request_email_verification(self, email: str) -> bool:
        """
        Request SES to verify an email address (for sending from this address)

        Args:
            email: Email address to verify

        Returns:
            True if verification email sent, False otherwise
        """
        try:
            self.ses_client.verify_email_identity(EmailAddress=email)
            logger.info(f"Verification requested for email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error requesting email verification: {str(e)}")
            return False

    async def get_send_quota(self) -> Dict[str, Any]:
        """
        Get current SES sending quota

        Returns:
            Dictionary with quota information
        """
        try:
            response = self.ses_client.get_send_quota()
            return {
                'max_24_hour_send': response.get('Max24HourSend', 0),
                'max_send_rate': response.get('MaxSendRate', 0),
                'sent_last_24_hours': response.get('SentLast24Hours', 0)
            }
        except Exception as e:
            logger.error(f"Error getting send quota: {str(e)}")
            return {
                'max_24_hour_send': 0,
                'max_send_rate': 0,
                'sent_last_24_hours': 0
            }