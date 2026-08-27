"""SMTP 발송 — HTML + 평문 multipart/alternative (FR-7, NFR-5).

자격증명은 전부 환경변수(GitHub Secrets)로 받는다(NFR-6).
재시도는 하지 않는다 — 실패는 워크플로 실패로 드러낸다(NFR-4).
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

DEFAULT_TO = "benrico@handong.ac.kr"
DEFAULT_HOST = "smtp.gmail.com"
DEFAULT_PORT = 465  # SMTPS


def build_message(subject: str, text: str, html: str, sender: str, to: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(text)                       # 평문 대체본
    msg.add_alternative(html, subtype="html")   # HTML 본문
    return msg


def send(msg: EmailMessage) -> None:
    host = os.environ.get("SMTP_HOST", DEFAULT_HOST)
    port = int(os.environ.get("SMTP_PORT", str(DEFAULT_PORT)))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    if not user or not password:
        raise RuntimeError("SMTP_USER / SMTP_PASS 가 설정되지 않았다")
    with smtplib.SMTP_SSL(host, port, timeout=60) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
