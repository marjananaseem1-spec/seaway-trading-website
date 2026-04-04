import json
import logging
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
_LOG_DIR = BASE_DIR / "instance"
_LOG_FILE = _LOG_DIR / "contact_submissions.log"


def _valid_email(addr: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", addr))


def _send_via_sendgrid(
    from_email: str,
    to_email: str,
    reply_to: str,
    subject: str,
    body: str,
) -> Tuple[bool, Optional[str]]:
    key = getattr(settings, "SENDGRID_API_KEY", "") or ""
    if not key:
        return False, "missing_api_key"
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "reply_to": {"email": reply_to},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=30)
        return True, None
    except urllib.error.HTTPError as exc:
        err = exc.read().decode(errors="replace") if exc.fp else str(exc)
        logger.error("SendGrid HTTP %s: %s", exc.code, err)
        return False, err
    except OSError as exc:
        logger.exception("SendGrid request failed")
        return False, str(exc)


def _send_contact_delivery(
    to_email: str,
    subject: str,
    body: str,
    customer_email: str,
) -> Tuple[bool, Optional[str]]:
    """Send to sales inbox: SendGrid API, else SMTP if configured."""
    if getattr(settings, "SENDGRID_API_KEY", ""):
        from_addr = getattr(settings, "SENDGRID_FROM_EMAIL", None) or settings.DEFAULT_FROM_EMAIL
        return _send_via_sendgrid(from_addr, to_email, customer_email, subject, body)

    if getattr(settings, "SMTP_ENABLED", False):
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            reply_to=[customer_email],
        )
        try:
            msg.send(fail_silently=False)
            return True, None
        except Exception:
            logger.exception("SMTP send failed")
            return False, "smtp_error"

    return False, "not_configured"


@ensure_csrf_cookie
def index(request):
    return render(request, "index.html")


@require_http_methods(["POST"])
def contact(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid request."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"ok": False, "error": "Invalid request."}, status=400)

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return JsonResponse({"ok": False, "error": "Please fill in all fields."}, status=400)
    if not _valid_email(email):
        return JsonResponse(
            {"ok": False, "error": "Please enter a valid email address."},
            status=400,
        )

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "name": name,
            "email": email,
            "message": message,
        },
        ensure_ascii=False,
    )
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

    to_email = getattr(settings, "CONTACT_FORM_TO", "sales@seawaytradingqatar.com")
    subject = f"[Seaway website] Quotation / enquiry from {name}"
    body = (
        f"New message via the website contact form.\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}\n\n"
        f"---\nReply directly to this customer using the email above.\n"
    )

    ok, err = _send_contact_delivery(to_email, subject, body, email)
    if not ok:
        if err == "not_configured":
            logger.error(
                "Contact form: no email provider (set SENDGRID_API_KEY or EMAIL_HOST on the server)"
            )
            return JsonResponse(
                {
                    "ok": False,
                    "error": (
                        "We could not send your message by email from this form yet. "
                        "Please write to sales@seawaytradingqatar.com or call the numbers "
                        "in the Contact section — we will help you from there."
                    ),
                },
                status=503,
            )
        logger.exception("Contact form: failed to send email to %s (%s)", to_email, err)
        return JsonResponse(
            {
                "ok": False,
                "error": "We could not send your message. Please email sales@seawaytradingqatar.com or call the numbers on the site.",
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "message": "Thank you — we’ll get back to you shortly.",
        }
    )
