#!/usr/bin/env python3
"""
Test script for Amazon SES email functionality
Sends test verification and password reset emails to brian@bkw.org
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.email_service import email_service
import secrets
from datetime import datetime


def test_verification_email():
    """Test sending a verification email"""
    print("\n" + "="*60)
    print("Testing Email Verification Email")
    print("="*60)

    test_token = secrets.token_urlsafe(32)
    test_email = "brian@bkw.org"
    test_name = "Brian"

    print(f"Sending verification email to: {test_email}")
    print(f"Test token: {test_token}")
    print(f"Test name: {test_name}")

    try:
        result = email_service.send_verification_email(
            to_email=test_email,
            verification_token=test_token,
            user_name=test_name
        )

        print("\n✅ SUCCESS!")
        print(f"Message ID: {result['message_id']}")
        print(f"Sent to: {result['to']}")
        return True

    except Exception as e:
        print("\n❌ FAILED!")
        print(f"Error: {str(e)}")
        return False


def test_password_reset_email():
    """Test sending a password reset email"""
    print("\n" + "="*60)
    print("Testing Password Reset Email")
    print("="*60)

    test_token = secrets.token_urlsafe(32)
    test_email = "brian@bkw.org"
    test_name = "Brian"

    print(f"Sending password reset email to: {test_email}")
    print(f"Test token: {test_token}")
    print(f"Test name: {test_name}")

    try:
        result = email_service.send_password_reset_email(
            to_email=test_email,
            reset_token=test_token,
            user_name=test_name
        )

        print("\n✅ SUCCESS!")
        print(f"Message ID: {result['message_id']}")
        print(f"Sent to: {result['to']}")
        return True

    except Exception as e:
        print("\n❌ FAILED!")
        print(f"Error: {str(e)}")
        return False


def test_basic_email():
    """Test sending a basic email"""
    print("\n" + "="*60)
    print("Testing Basic Email Sending")
    print("="*60)

    test_email = "brian@bkw.org"

    print(f"Sending basic test email to: {test_email}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SES Test Email</h1>
            <p>This is a test email from the Ruth Platform backend.</p>
            <p>If you're reading this, Amazon SES is configured correctly!</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    SES Test Email

    This is a test email from the Ruth Platform backend.
    If you're reading this, Amazon SES is configured correctly!

    Timestamp: {timestamp}
    """

    try:
        result = email_service.send_email(
            to_email=test_email,
            subject="Ruth Platform - SES Test Email",
            html_body=html_body,
            text_body=text_body
        )

        print("\n✅ SUCCESS!")
        print(f"Message ID: {result['message_id']}")
        print(f"Sent to: {result['to']}")
        return True

    except Exception as e:
        print("\n❌ FAILED!")
        print(f"Error: {str(e)}")
        return False


def main():
    """Run all email tests"""
    print("\n" + "="*60)
    print("Ruth Platform - Amazon SES Email Test Suite")
    print("="*60)
    print(f"Target email: brian@bkw.org")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Basic email
    results.append(("Basic Email", test_basic_email()))

    # Test 2: Verification email
    results.append(("Verification Email", test_verification_email()))

    # Test 3: Password reset email
    results.append(("Password Reset Email", test_password_reset_email()))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")

    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)

    print("\n" + "-"*60)
    print(f"Total: {total_passed}/{total_tests} tests passed")
    print("="*60)

    if total_passed == total_tests:
        print("\n🎉 All tests passed! SES is configured correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Check the error messages above.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
