"""
Email service for sending emails via Amazon SES
"""
import boto3
import logging
from typing import Optional, List
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Amazon SES"""

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

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> dict:
        """
        Send an email via Amazon SES

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML version of email body
            text_body: Plain text version of email body (optional)
            reply_to: Reply-to email address (optional)

        Returns:
            dict: Response from SES containing message ID

        Raises:
            Exception: If email sending fails
        """
        try:
            # Build the sender
            if self.from_name:
                sender = f"{self.from_name} <{self.from_email}>"
            else:
                sender = self.from_email

            # Build message
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                }
            }

            # Add text body if provided
            if text_body:
                message['Body']['Text'] = {'Data': text_body, 'Charset': 'UTF-8'}

            # Prepare send parameters
            send_params = {
                'Source': sender,
                'Destination': {'ToAddresses': [to_email]},
                'Message': message
            }

            # Add reply-to if provided
            if reply_to:
                send_params['ReplyToAddresses'] = [reply_to]

            # Add configuration set if configured
            if self.configuration_set:
                send_params['ConfigurationSetName'] = self.configuration_set

            # Send email
            response = self.ses_client.send_email(**send_params)

            logger.info(f"Email sent successfully to {to_email}. Message ID: {response['MessageId']}")
            return {
                'success': True,
                'message_id': response['MessageId'],
                'to': to_email
            }

        except ClientError as e:
            error_msg = e.response['Error']['Message']
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            raise Exception(f"Email sending failed: {error_msg}")

        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
            raise

    def send_verification_email(self, to_email: str, verification_token: str, user_name: str) -> dict:
        """
        Send email verification email

        Args:
            to_email: User's email address
            verification_token: Email verification token
            user_name: User's first name

        Returns:
            dict: Response from send_email
        """
        # Build verification URL
        base_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:3000"
        verification_url = f"{base_url}/verify-email?token={verification_token}"

        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Ruth!</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>Thank you for registering with Ruth, your civic empowerment platform!</p>
                    <p>Please verify your email address by clicking the button below:</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #2563eb;">{verification_url}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account with Ruth, please ignore this email.</p>
                    <p>Best regards,<br>The Ruth Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 Ruth Platform. All rights reserved.</p>
                    <p>Raise Up The Heard</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        text_body = f"""
        Welcome to Ruth!

        Hello {user_name},

        Thank you for registering with Ruth, your civic empowerment platform!

        Please verify your email address by visiting this link:
        {verification_url}

        This link will expire in 24 hours.

        If you didn't create an account with Ruth, please ignore this email.

        Best regards,
        The Ruth Team

        Raise Up The Heard
        """

        return self.send_email(
            to_email=to_email,
            subject="Verify Your Email Address - Ruth Platform",
            html_body=html_body,
            text_body=text_body
        )

    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> dict:
        """
        Send password reset email

        Args:
            to_email: User's email address
            reset_token: Password reset token
            user_name: User's first name

        Returns:
            dict: Response from send_email
        """
        # Build reset URL
        base_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:3000"
        reset_url = f"{base_url}/reset-password?token={reset_token}"

        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #dc2626;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
                .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>We received a request to reset your password for your Ruth account.</p>
                    <p>Click the button below to reset your password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #2563eb;">{reset_url}</p>
                    <div class="warning">
                        <p><strong>Security Note:</strong></p>
                        <ul>
                            <li>This link will expire in 1 hour</li>
                            <li>If you didn't request this password reset, please ignore this email</li>
                            <li>Your password won't change until you create a new one via the link above</li>
                        </ul>
                    </div>
                    <p>Best regards,<br>The Ruth Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 Ruth Platform. All rights reserved.</p>
                    <p>Raise Up The Heard</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        text_body = f"""
        Password Reset Request

        Hello {user_name},

        We received a request to reset your password for your Ruth account.

        Click the link below to reset your password:
        {reset_url}

        SECURITY NOTE:
        - This link will expire in 1 hour
        - If you didn't request this password reset, please ignore this email
        - Your password won't change until you create a new one via the link above

        Best regards,
        The Ruth Team

        Raise Up The Heard
        """

        return self.send_email(
            to_email=to_email,
            subject="Reset Your Password - Ruth Platform",
            html_body=html_body,
            text_body=text_body
        )


# Create singleton instance
email_service = EmailService()
