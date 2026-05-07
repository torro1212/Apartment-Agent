"""
Apartment Search Agent - Configuration
======================================
All search criteria and settings in one place.
Edit this file to tune the search.
"""

# ===== SEARCH CRITERIA =====
MIN_ROOMS = 3
MAX_ROOMS = 6
MAX_PRICE = 7500
MIN_PRICE = 1500  # filter out obvious junk listings

# ממ"ד / מרחב מוגן required
REQUIRE_SAFE_ROOM = True
SAFE_ROOM_KEYWORDS = ["ממ\"ד", "ממד", "מרחב מוגן", "מקלט פרטי"]

# ===== GEOGRAPHIC AREA =====
# Nahariya + surrounding moshavim/kibbutzim within ~15km
# Yad2 city codes (verified from Yad2 URL params)
NAHARIYA_AREA_CITIES = {
    "נהריה": 9700,
    "כפר ורדים": 1296,
    "מעלות-תרשיחא": 1063,
    "שלומי": 1292,
    "ראש הנקרה": None,  # kibbutz - search via free text
    "יחיעם": None,
    "כברי": None,
    "געתון": None,
    "לוחמי הגטאות": None,
    "אילון": None,
    "מצובה": None,
    "חניתה": None,
    "אדמית": None,
    "גשר הזיו": None,
    "סער": None,
    "שבי ציון": None,
    "רגבה": None,
    "בן עמי": None,
    "בוסתן הגליל": None,
    "עמקה": None,
    "כליל": None,
}

# Free-text fallback for places without Yad2 city codes
FREE_TEXT_LOCATIONS = [
    name for name, code in NAHARIYA_AREA_CITIES.items() if code is None
]

# Yad2 saved-search base URL (coastal north area — from your browser)
YAD2_SEARCH_BASE = "https://www.yad2.co.il/realestate/rent/coastal-north"
YAD2_MULTI_AREA = "68"
YAD2_MULTI_CITY = "9100,0674"

# ===== EMAIL =====
import os
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")  # Gmail App Password
EMAIL_TO = os.environ.get("EMAIL_TO", "")

# ===== STORAGE =====
SEEN_LISTINGS_FILE = "seen_listings.json"
MAX_AGE_DAYS = 30  # forget listings older than this (in case they re-list)

# ===== SCRAPING =====
REQUEST_TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)
DELAY_BETWEEN_REQUESTS = 3  # seconds, be polite
