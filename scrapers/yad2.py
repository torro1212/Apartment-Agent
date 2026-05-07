"""
Yad2 scraper using curl_cffi to bypass ShieldSquare bot protection.
Fetches the rendered HTML page and extracts listings from __NEXT_DATA__.
"""

import json
import re
import time
from typing import List, Optional

from curl_cffi import requests as cf

from config import (
    MIN_ROOMS, MAX_ROOMS, MIN_PRICE, MAX_PRICE,
    YAD2_SEARCH_BASE, YAD2_MULTI_AREA, YAD2_MULTI_CITY,
    REQUEST_TIMEOUT, DELAY_BETWEEN_REQUESTS,
    SAFE_ROOM_KEYWORDS,
)
from storage import Listing

_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
}


def _has_safe_room(text: str) -> bool:
    if not text:
        return False
    return any(kw in text for kw in SAFE_ROOM_KEYWORDS)


def _safe_int(v) -> Optional[int]:
    try:
        return int(v) if v not in (None, "", "0") else None
    except (ValueError, TypeError):
        return None


def _safe_float(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _find_feed_items(obj, depth: int = 0) -> Optional[list]:
    """Walk __NEXT_DATA__ tree to find feed_items list."""
    if depth > 15:
        return None
    if isinstance(obj, dict):
        if "feed_items" in obj:
            items = obj["feed_items"]
            if isinstance(items, list) and items:
                return items
        for v in obj.values():
            res = _find_feed_items(v, depth + 1)
            if res is not None:
                return res
    elif isinstance(obj, list):
        for v in obj:
            res = _find_feed_items(v, depth + 1)
            if res is not None:
                return res
    return None


def _parse_item(item: dict) -> Optional[Listing]:
    try:
        if item.get("type") not in (None, "ad", ""):
            return None

        title = item.get("title") or item.get("row_1") or ""
        row2 = item.get("row_2") or ""
        row3 = item.get("row_3") or ""
        description = " | ".join(filter(None, [row2, row3, item.get("search_text", "")]))

        price_raw = item.get("price") or item.get("priceForSort") or ""
        price = _safe_int("".join(c for c in str(price_raw) if c.isdigit()))

        rooms = _safe_float(item.get("Rooms_text") or item.get("rooms"))

        city = item.get("city") or item.get("city_text") or ""
        neighborhood = item.get("neighborhood") or ""
        street = item.get("street") or item.get("address") or ""
        address = ", ".join(filter(None, [street, neighborhood, city]))

        listing_id = item.get("id") or item.get("link_token") or item.get("ad_number")
        if not listing_id:
            return None
        url = f"https://www.yad2.co.il/item/{listing_id}"

        full_text = f"{title} {description}"
        return Listing(
            source="yad2",
            title=title or "ללא כותרת",
            price=price,
            rooms=rooms,
            address=address,
            city=city,
            url=url,
            description=description[:500],
            has_safe_room=_has_safe_room(full_text),
        )
    except Exception:
        return None


def fetch_yad2() -> List[Listing]:
    results: List[Listing] = []
    seen_urls: set = set()

    try:
        for page in range(1, 6):
            params = {
                "maxPrice": MAX_PRICE,
                "minRooms": MIN_ROOMS,
                "multiArea": YAD2_MULTI_AREA,
                "multiCity": YAD2_MULTI_CITY,
            }
            if page > 1:
                params["page"] = page

            r = cf.get(
                YAD2_SEARCH_BASE,
                params=params,
                headers=_HEADERS,
                impersonate="chrome124",
                timeout=REQUEST_TIMEOUT,
            )

            if r.status_code != 200:
                print(f"[yad2] page {page}: HTTP {r.status_code}")
                break

            if "ShieldSquare" in r.text:
                print(f"[yad2] page {page}: captcha hit")
                break

            m = re.search(r'id="__NEXT_DATA__">(.+?)</script>', r.text)
            if not m:
                print(f"[yad2] page {page}: no __NEXT_DATA__")
                break

            data = json.loads(m.group(1))
            items = _find_feed_items(data)

            if not items:
                print(f"[yad2] page {page}: no feed_items")
                break

            added = 0
            for item in items:
                if not isinstance(item, dict):
                    continue
                listing = _parse_item(item)
                if listing and listing.url not in seen_urls:
                    seen_urls.add(listing.url)
                    results.append(listing)
                    added += 1

            print(f"[yad2] page {page}: {added} listings")
            if added == 0:
                break

            time.sleep(DELAY_BETWEEN_REQUESTS)

    except Exception as e:
        print(f"[yad2] error: {e}")

    print(f"[yad2] total: {len(results)} raw listings")
    return results
