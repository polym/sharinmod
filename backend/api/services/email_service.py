"""
Email service for sending transactional emails via SMTP
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from api.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an email via SMTP.

    Returns True on success, False if SMTP is not configured or an error occurs.
    Failure is non-fatal: callers should log/handle gracefully.
    """
    if not settings.SMTP_HOST:
        logger.warning("[Email] SMTP_HOST is not configured. Email not sent to %s.", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
        logger.info("[Email] Sent '%s' to %s", subject, to_email)
        return True
    except Exception as exc:
        logger.error("[Email] Failed to send '%s' to %s: %s", subject, to_email, exc)
        return False


def send_verification_email(to_email: str, verification_link: str) -> bool:
    """Send an email verification link to a newly registered user."""
    subject = "验证您的 SharinMod 账户邮箱"
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h2>欢迎注册 SharinMod！</h2>
      <p>请点击以下链接验证您的邮箱地址：</p>
      <p>
        <a href="{verification_link}" style="display:inline-block;padding:10px 20px;background:#4F46E5;color:#fff;text-decoration:none;border-radius:6px;">
          验证邮箱
        </a>
      </p>
      <p>或复制以下链接到浏览器：<br><a href="{verification_link}">{verification_link}</a></p>
      <p style="color:#888;">此链接将在 24 小时后失效。</p>
    </div>
    """
    return send_email(to_email, subject, html_body)
