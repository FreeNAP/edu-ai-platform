"""SMTP 邮件发送。未配置 SMTP 时只写日志（开发/演示环境）。"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from ..config import settings

logger = logging.getLogger("edu.mail")


def send_mail(to: str, subject: str, body: str) -> bool:
    if not settings.smtp_enabled:
        logger.warning("SMTP 未配置，邮件未发送：to=%s subject=%s", to, subject)
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("智慧教育平台", settings.smtp_from))
    msg["To"] = to
    msg.set_content(body)
    try:
        if settings.smtp_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=ssl.create_default_context(), timeout=15) as s:
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as s:
                s.starttls(context=ssl.create_default_context())
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_password)
                s.send_message(msg)
        return True
    except Exception:
        logger.exception("邮件发送失败 to=%s", to)
        return False
