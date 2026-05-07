"""
Email delivery with HTML formatting (RTL Hebrew).
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List

from config import (
    SMTP_SERVER, SMTP_PORT, EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO,
)
from storage import Listing


def _format_price(price) -> str:
    if price is None:
        return "—"
    return f"₪{price:,}"


def _format_rooms(rooms) -> str:
    if rooms is None:
        return "—"
    if rooms == int(rooms):
        return f"{int(rooms)}"
    return f"{rooms}"


def _format_location(l) -> str:
    """Show address+city, but avoid duplicating the city if already in address."""
    if l.address and l.city and l.city not in l.address:
        return f"{l.address}, {l.city}"
    return l.address or l.city or ""


def build_html(listings: List[Listing]) -> str:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    rows = []
    for l in sorted(listings, key=lambda x: (x.price or 999999)):
        safe_badge = "🛡️ ממ\"ד" if l.has_safe_room else ""
        source_badge = {
            "yad2": "<span style='background:#fde68a;padding:2px 8px;border-radius:4px;font-size:11px'>יד2</span>",
            "madlan": "<span style='background:#bfdbfe;padding:2px 8px;border-radius:4px;font-size:11px'>מדלן</span>",
        }.get(l.source, l.source)

        rows.append(f"""
        <div style='border:1px solid #e5e7eb;border-radius:8px;padding:14px;margin-bottom:12px;background:#fff'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px'>
            <strong style='font-size:16px'>{_format_price(l.price)} / חודש</strong>
            <div>{source_badge} {safe_badge}</div>
          </div>
          <div style='font-size:14px;color:#374151;margin-bottom:4px'>
            <strong>{_format_rooms(l.rooms)} חדרים</strong> · {_format_location(l)}
          </div>
          <div style='font-size:13px;color:#6b7280;margin-bottom:8px'>{l.title}</div>
          <a href='{l.url}' style='display:inline-block;background:#2563eb;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:13px'>צפה במודעה ←</a>
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html dir='rtl' lang='he'>
<head><meta charset='utf-8'></head>
<body style='font-family:-apple-system,Segoe UI,Arial,sans-serif;background:#f3f4f6;padding:20px;margin:0'>
  <div style='max-width:600px;margin:0 auto'>
    <div style='background:white;border-radius:12px;padding:20px;margin-bottom:16px'>
      <h2 style='margin:0 0 4px 0;color:#111827'>🏠 דירות חדשות באזור נהריה</h2>
      <div style='color:#6b7280;font-size:13px'>{timestamp} · {len(listings)} מודעות חדשות</div>
    </div>
    {''.join(rows)}
    <div style='text-align:center;color:#9ca3af;font-size:11px;margin-top:20px'>
      Apartment Search Agent · רץ אוטומטית פעמיים ביום
    </div>
  </div>
</body></html>"""
    return html


def send_email(listings: List[Listing]) -> bool:
    if not listings:
        print("[email] no new listings, skipping send")
        return True

    if not (EMAIL_FROM and EMAIL_PASSWORD and EMAIL_TO):
        print("[email] credentials not configured, skipping send")
        print(f"[email] would have sent {len(listings)} listings")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏠 {len(listings)} דירות חדשות באזור נהריה"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    html = build_html(listings)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"[email] sent {len(listings)} listings to {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"[email] send failed: {e}")
        return False
