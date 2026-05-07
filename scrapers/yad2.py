"""
Yad2 scraper.

Strategy: Yad2 has an internal JSON API used by their own frontend
(https://gw.yad2.co.il/feed-search-legacy/realestate/rent).
We hit it directly with realistic headers. Falls back to nothing if blocked
(use a paid proxy in that case - see README).
"""

import time
from typing import List, Optional

import requests

from config import (
    MIN_ROOMS, MAX_ROOMS, MIN_PRICE, MAX_PRICE,
    YAD2_AREA_CODE, NAHARIYA_AREA_CITIES,
    USER_AGENT, REQUEST_TIMEOUT, DELAY_BETWEEN_REQUESTS,
    SAFE_ROOM_KEYWORDS,
)
from storage import Listing


YAD2_API = "https://gw.yad2.co.il/feed-search-legacy/realestate/rent"


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
        return float(v) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


def _build_params(city_code: Optional[int] = None) -> dict:
    """Build Yad2 API query params."""
    params = {
        "rooms": f"{MIN_ROOMS}-{MAX_ROOMS}",
        "price": f"{MIN_PRICE}-{MAX_PRICE}",
        "forceLdLoad": "true",
    }
    if city_code:
        params["city"] = city_code
    else:
        # search the whole Western Galilee area
        params["area"] = YAD2_AREA_CODE
    return params


def _fetch_page(params: dict, page: int = 1) -> dict:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
        "Referer": "https://www.yad2.co.il/realestate/rent",
        "Origin": "https://www.yad2.co.il",
    }
    p = dict(params)
    p["page"] = page
    r = requests.get(YAD2_API, params=p, headers=headers, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _parse_item(item: dict) -> Optional[Listing]:
    """Parse one Yad2 feed item into a Listing."""
    try:
        # Yad2 feed items have many possible shapes; we defensively pull fields
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
        has_safe = _has_safe_room(full_text)

        return Listing(
            source="yad2",
            title=title or "ללא כותרת",
            price=price,
            rooms=rooms,
            address=address,
            city=city,
            url=url,
            description=description[:500],
            has_safe_room=has_safe,
        )
    except Exception:
        return None


def fetch_yad2() -> List[Listing]:
    """Fetch all matching listings from Yad2 across the Western Galilee."""
    results: List[Listing] = []
    seen_ids = set()

    # Strategy: one broad area search (Western Galilee) covers all towns,
    # then we filter by city name if needed.
    params = _build_params(city_code=None)

    try:
        for page in range(1, 6):  # up to 5 pages = ~150 listings
            data = _fetch_page(params, page=page)
            feed = data.get("data", {}).get("feed", {})
            items = feed.get("feed_items", []) or data.get("feed", {}).get("feed_items", [])
            if not items:
                break
            for item in items:
                if item.get("type") and item["type"] != "ad":
                    continue
                listing = _parse_item(item)
                if not listing:
                    continue
                if listing.url in seen_ids:
                    continue
                seen_ids.add(listing.url)
                results.append(listing)
            time.sleep(DELAY_BETWEEN_REQUESTS)
    except requests.RequestException as e:
        print(f"[yad2] request failed: {e}")
    except Exception as e:
        print(f"[yad2] parse error: {e}")

    print(f"[yad2] found {len(results)} raw listings")
    return results
