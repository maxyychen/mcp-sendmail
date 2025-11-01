"""Email operations using SMTP."""
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import os
import base64

logger = logging.getLogger(__name__)


class EmailOperations:
    """Handles email sending operations via SMTP."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: Optional[bool] = None,
    ):
        """Initialize email operations.

        Args:
            smtp_host: SMTP server hostname (defaults to env SMTP_HOST or localhost)
            smtp_port: SMTP server port (defaults to env SMTP_PORT or 587)
            smtp_user: SMTP username (defaults to env SMTP_USER)
            smtp_password: SMTP password (defaults to env SMTP_PASSWORD)
            use_tls: Whether to use TLS encryption (auto-detected based on port if None)
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")

        # Auto-detect TLS based on port if not explicitly set
        if use_tls is None:
            # Port 25: Usually no TLS (plain SMTP or opportunistic TLS)
            # Port 587: Use TLS (STARTTLS)
            # Port 465: Use SSL (handled separately, but set to False here)
            self.use_tls = self.smtp_port not in [25, 465]
        else:
            self.use_tls = use_tls

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_addr: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            from_addr: Sender email address (defaults to SMTP_USER)
            cc: List of CC recipients
            bcc: List of BCC recipients
            html: Whether body is HTML (default: False for plain text)
            attachments: List of attachments with 'filename' and 'content' (base64 encoded)

        Returns:
            Dict with success status and message
        """
        try:
            from_addr = from_addr or self.smtp_user

            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_addr
            msg["To"] = to
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            # Attach body
            body_type = "html" if html else "plain"
            msg.attach(MIMEText(body, body_type))

            # Attach files if provided
            if attachments:
                for attachment in attachments:
                    filename = attachment.get("filename")
                    content = attachment.get("content")  # base64 encoded

                    if not filename or not content:
                        continue

                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(base64.b64decode(content))
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {filename}",
                    )
                    msg.attach(part)

            # Build recipient list
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send email
            self._send_smtp(msg, recipients)

            logger.info(f"Email sent successfully to {to}")
            return {
                "success": True,
                "message": f"Email sent successfully to {to}",
                "recipients": recipients,
            }

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        from_addr: Optional[str] = None,
        html: bool = False,
    ) -> Dict[str, Any]:
        """Send the same email to multiple recipients.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Email body content
            from_addr: Sender email address (defaults to SMTP_USER)
            html: Whether body is HTML (default: False)

        Returns:
            Dict with success status and results
        """
        results = []
        success_count = 0
        failed_count = 0

        for recipient in recipients:
            result = await self.send_email(
                to=recipient,
                subject=subject,
                body=body,
                from_addr=from_addr,
                html=html,
            )
            results.append({"recipient": recipient, "result": result})

            if result.get("success"):
                success_count += 1
            else:
                failed_count += 1

        return {
            "success": failed_count == 0,
            "total": len(recipients),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }

    async def send_template_email(
        self,
        to: str,
        subject: str,
        template: str,
        variables: Dict[str, str],
        from_addr: Optional[str] = None,
        html: bool = False,
    ) -> Dict[str, Any]:
        """Send an email using a template with variable substitution.

        Args:
            to: Recipient email address
            subject: Email subject
            template: Email template with {variable} placeholders
            variables: Dictionary of variable names and values to substitute
            from_addr: Sender email address (defaults to SMTP_USER)
            html: Whether template is HTML (default: False)

        Returns:
            Dict with success status and message
        """
        try:
            # Substitute variables in template
            body = template
            for key, value in variables.items():
                body = body.replace(f"{{{key}}}", value)

            # Send the email
            return await self.send_email(
                to=to,
                subject=subject,
                body=body,
                from_addr=from_addr,
                html=html,
            )

        except Exception as e:
            logger.error(f"Failed to send template email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]) -> None:
        """Send email via SMTP.

        Args:
            msg: The email message
            recipients: List of recipient addresses
        """
        if self.use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                if self.smtp_user and self.smtp_password:
                    try:
                        server.login(self.smtp_user, self.smtp_password)
                    except smtplib.SMTPAuthenticationError:
                        logger.warning("Authentication failed, continuing without auth")
                server.send_message(msg, to_addrs=recipients)
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    try:
                        server.login(self.smtp_user, self.smtp_password)
                    except (smtplib.SMTPAuthenticationError, smtplib.SMTPException) as e:
                        logger.warning(f"Authentication failed or not required: {e}, continuing without auth")
                server.send_message(msg, to_addrs=recipients)

    async def verify_connection(self) -> Dict[str, Any]:
        """Verify SMTP connection and credentials.

        Returns:
            Dict with success status and connection details
        """
        try:
            auth_used = False
            auth_message = ""

            if self.use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.starttls(context=context)
                    if self.smtp_user and self.smtp_password:
                        try:
                            server.login(self.smtp_user, self.smtp_password)
                            auth_used = True
                            auth_message = " (authenticated)"
                        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException) as e:
                            logger.warning(f"Authentication not required or failed: {e}")
                            auth_message = " (no authentication)"

                    return {
                        "success": True,
                        "message": f"SMTP connection verified successfully{auth_message}",
                        "server": self.smtp_host,
                        "port": self.smtp_port,
                        "tls": self.use_tls,
                        "authenticated": auth_used,
                    }
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    if self.smtp_user and self.smtp_password:
                        try:
                            server.login(self.smtp_user, self.smtp_password)
                            auth_used = True
                            auth_message = " (authenticated)"
                        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException) as e:
                            logger.warning(f"Authentication not required or failed: {e}")
                            auth_message = " (no authentication)"

                    return {
                        "success": True,
                        "message": f"SMTP connection verified successfully{auth_message}",
                        "server": self.smtp_host,
                        "port": self.smtp_port,
                        "tls": self.use_tls,
                        "authenticated": auth_used,
                    }

        except Exception as e:
            logger.error(f"SMTP connection failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "server": self.smtp_host,
                "port": self.smtp_port,
            }
