import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

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

    try:
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            reply_to=[email],
        )
        msg.send(fail_silently=False)
    except Exception:
        logger.exception("Contact form: failed to send email to %s", to_email)
        return JsonResponse(
            {
                "ok": False,
                "error": "We could not send your message. Please email us directly at sales@seawaytradingqatar.com or call the numbers on the site.",
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "message": "Thank you — we’ll get back to you shortly.",
        }
    )
