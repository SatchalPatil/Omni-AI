import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from typing import List, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()
logger.info("Loaded .env file for email utils")

def send_email(to_email: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> bool:
    """
    Sends an email using Gmail's SMTP server with support for attachments.
    Phase 3: Email sending function for email automation.

    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
        attachments (Optional[List[str]]): List of file paths to attach (e.g., PDF reports)

    Returns:
        bool: True if successful, False otherwise

    Raises:
        ValueError: If email format is invalid or required credentials are missing
        Exception: If email sending fails due to SMTP or other errors
    """
    logger.info(f"[EmailUtils] Phase 3 - Sending email to: {to_email}")
    logger.info(f"[EmailUtils] Subject: {subject[:50]}...")
    
    # Validate inputs
    if not to_email or not subject or not body:
        logger.error("[EmailUtils] Missing required fields")
        raise ValueError("to_email, subject, and body are required")
    
    # Email format validation (basic check)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, to_email):
        raise ValueError(f"Invalid email format: {to_email}")

    # SMTP configuration from .env (with fallbacks for demo)
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))  # Use 587 for TLS, 465 for SSL
    smtp_user = os.getenv('SMTP_USER', 'autoemail22@gmail.com')
    smtp_password = os.getenv('SMTP_PASSWORD', 'wufr haao cpmg ksaw')  # Use App Password for Gmail

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be set in .env")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach files if provided
    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)
            else:
                logger.warning(f"Attachment not found: {file_path}")

    try:
        logger.info(f"[EmailUtils] Connecting to SMTP server {smtp_server}:{smtp_port}...")
        # Use TLS for security
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable TLS
            logger.info("[EmailUtils] TLS enabled, logging in...")
            server.login(smtp_user, smtp_password)
            logger.info("[EmailUtils] Login successful, sending email...")
            server.sendmail(smtp_user, to_email, msg.as_string())
        logger.info(f"[EmailUtils] ✅ Email sent successfully to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("[EmailUtils] ❌ SMTP Authentication failed. Check email credentials in .env.")
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"[EmailUtils] ❌ Recipient refused: {to_email}")
        return False
    except smtplib.SMTPServerDisconnected:
        logger.error("[EmailUtils] ❌ SMTP server disconnected")
        return False
    except Exception as e:
        logger.error(f"[EmailUtils] ❌ Unexpected error sending email: {str(e)}")
        return False

if __name__ == '__main__':
    # Test email sending
    test_to = 'satchalpatil04@gmail.com'
    test_subject = 'Test Email from AI Workspace'
    test_body = 'This is a test email sent from the AI Automation Workspace.'
    test_attachments = ['reports/sample_report.pdf'] if os.path.exists('reports/sample_report.pdf') else None
    
    success = send_email(test_to, test_subject, test_body, test_attachments)
    logger.info(f"Test email sent: {success}")