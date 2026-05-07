"""
Apartment Search Agent - main entry point.

Run this twice daily via GitHub Actions cron:
  python main.py
"""

import sys
from typing import List

from config import (
    MIN_ROOMS, MAX_ROOMS, MAX_PRICE,
    NAHARIYA_AREA_CITIES,
)
from storage import Listing, SeenStore
from scrapers.yad2 import fetch_yad2
from scrapers.madlan import fetch_madlan
from emailer import send_email


VALID_CITIES_LOWER = {c.lower() for c in NAHARIYA_AREA_CITIES.keys()}


def _city_matches(listing_city: str) -> bool:
    """Check if the listing is in our target area."""
    if not listing_city:
        return False
    lc = listing_city.strip().lower()
    for target in VALID_CITIES_LOWER:
        if target in lc or lc in target:
            return True
    return False


def filter_listings(listings: List[Listing]) -> List[Listing]:
    """Apply all hard filters (rooms, price, area). Safe-room is shown as a
    badge but not enforced as a filter, since most listings don't expose the
    field reliably and we'd lose too many real candidates."""
    out = []
    for l in listings:
        if l.rooms is not None and not (MIN_ROOMS <= l.rooms <= MAX_ROOMS):
            continue
        if l.price is not None and l.price > MAX_PRICE:
            continue
        if not _city_matches(l.city):
            continue
        out.append(l)
    return out


def main() -> int:
    print("=" * 60)
    print(f"Apartment Search Agent: rooms {MIN_ROOMS}-{MAX_ROOMS}, max ₪{MAX_PRICE}")
    print("=" * 60)

    all_listings: List[Listing] = []

    print("\n→ Fetching Yad2...")
    try:
        all_listings.extend(fetch_yad2())
    except Exception as e:
        print(f"  Yad2 failed entirely: {e}")

    print("\n→ Fetching Madlan...")
    try:
        all_listings.extend(fetch_madlan())
    except Exception as e:
        print(f"  Madlan failed entirely: {e}")

    print(f"\n→ Total raw listings: {len(all_listings)}")

    filtered = filter_listings(all_listings)
    print(f"→ After area + price + rooms filter: {len(filtered)}")

    store = SeenStore()
    new_listings = store.filter_new(filtered)
    print(f"→ New (not seen before): {len(new_listings)}")

    if new_listings:
        print("\nNew listings:")
        for l in new_listings:
            price = f"₪{l.price:,}" if l.price else "?"
            rooms = l.rooms if l.rooms else "?"
            print(f"  [{l.source}] {price} · {rooms}ח · {l.city} · {l.url}")

    send_email(new_listings)
    store.save()

    print("\n✓ Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
