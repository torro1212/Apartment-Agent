"""
Madlan scraper.

Strategy: Madlan uses Apollo GraphQL on their frontend. We hit the
public search results page and parse the embedded __NEXT_DATA__ JSON
which contains all listings. This is more stable than DOM scraping.
"""

import json
import re
import time
from typing import List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from config import (
    MIN_ROOMS, MAX_ROOMS, MIN_PRICE, MAX_PRICE,
    USER_AGENT, REQUEST_TIMEOUT, DELAY_BETWEEN_REQUESTS,
    SAFE_ROOM_KEYWORDS,
)
from storage import Listing


# Madlan area pages we care about
MADLAN_AREAS = [
    "נהריה",
    "כפר-ורדים",
    "מעלות-תרשיחא",
    "שלומי",
]


def _has_safe_room(text: str) -> bool:
    if not text:
        return False
    return any(kw in text for kw in SAFE_ROOM_KEYWORDS)


def _build_url(city: str, page: int = 1) -> str:
    """Build a Madlan rental search URL for a city."""
    encoded = quote(city)
    base = (
        f"https://www.madlan.co.il/for-rent/{encoded}-ישראל"
        f"?tracking_search_source=new_search"
        f"&minRooms={MIN_ROOMS}&maxRooms={MAX_ROOMS}"
        f"&minPrice={MIN_PRICE}&maxPrice={MAX_PRICE}"
    )
    if page > 1:
        base += f"&page={page}"
    return base


def _fetch_page(url: str) -> Optional[dict]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    next_data = soup.find("script", id="__NEXT_DATA__")
    if not next_data or not next_data.string:
        return None
    try:
        return json.loads(next_data.string)
    except json.JSONDecodeError:
        return None


def _walk_for_listings(obj, results: list, seen_ids: set):
    """Recursively walk Apollo cache for objects that look like listings."""
    if isinstance(obj, dict):
        # Heuristic: a listing has price + rooms + address-ish fields
        if (
            "price" in obj and "rooms" in obj
            and ("addressRecord" in obj or "address" in obj or "city" in obj)
        ):
            lid = obj.get("id") or obj.get("poiId")
            if lid and lid not in seen_ids:
                seen_ids.add(lid)
                results.append(obj)
        for v in obj.values():
            _walk_for_listings(v, results, seen_ids)
    elif isinstance(obj, list):
        for v in obj:
            _walk_for_listings(v, results, seen_ids)


def _parse_listing(raw: dict, city_hint: str) -> Optional[Listing]:
    try:
        price = raw.get("price")
        if isinstance(price, str):
            price = int("".join(c for c in price if c.isdigit()) or 0) or None

        rooms = raw.get("rooms")
        try:
            rooms = float(rooms) if rooms is not None else None
        except (ValueError, TypeError):
            rooms = None

        addr_record = raw.get("addressRecord") or {}
        street = addr_record.get("street") or raw.get("street") or ""
        neighborhood = addr_record.get("neighbourhood") or raw.get("neighborhood") or ""
        city = addr_record.get("city") or raw.get("city") or city_hint
        address = ", ".join(filter(None, [street, neighborhood, city]))

        title = raw.get("title") or f"{rooms} חדרים ב{city}" if rooms else city
        description = raw.get("description") or raw.get("listingType") or ""

        lid = raw.get("id") or raw.get("poiId")
        if not lid:
            return None
        url = f"https://www.madlan.co.il/listings/{lid}"

        return Listing(
            source="madlan",
            title=title,
            price=price,
            rooms=rooms,
            address=address,
            city=city,
            url=url,
            description=str(description)[:500],
            has_safe_room=_has_safe_room(f"{title} {description}"),
        )
    except Exception:
        return None


def fetch_madlan() -> List[Listing]:
    results: List[Listing] = []
    seen_urls = set()

    for city in MADLAN_AREAS:
        try:
            for page in range(1, 4):
                url = _build_url(city, page)
                data = _fetch_page(url)
                if not data:
                    break
                raw_listings = []
                seen_ids = set()
                _walk_for_listings(data, raw_listings, seen_ids)
                if not raw_listings:
                    break
                for raw in raw_listings:
                    listing = _parse_listing(raw, city)
                    if not listing:
                        continue
                    if listing.url in seen_urls:
                        continue
                    seen_urls.add(listing.url)
                    results.append(listing)
                time.sleep(DELAY_BETWEEN_REQUESTS)
        except requests.RequestException as e:
            print(f"[madlan] {city} request failed: {e}")
        except Exception as e:
            print(f"[madlan] {city} parse error: {e}")

    print(f"[madlan] found {len(results)} raw listings")
    return results
