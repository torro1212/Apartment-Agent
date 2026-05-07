"""
Listing data model + dedup storage.
Listings are uniquely identified by a content hash so that re-listed
properties (new URL but same address+price+rooms) are still deduped.
"""

import hashlib
import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import List, Optional

from config import SEEN_LISTINGS_FILE, MAX_AGE_DAYS


@dataclass
class Listing:
    source: str               # "yad2" / "madlan"
    title: str
    price: Optional[int]
    rooms: Optional[float]
    address: str
    city: str
    url: str
    description: str = ""
    has_safe_room: bool = False
    found_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def content_hash(self) -> str:
        """
        Hash that survives URL changes / re-listings.
        Same address + price + rooms = same listing.
        """
        key = f"{self.city}|{self.address}|{self.price}|{self.rooms}".lower()
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    def url_hash(self) -> str:
        return hashlib.sha256(self.url.encode("utf-8")).hexdigest()[:16]


class SeenStore:
    """Tracks listings we've already alerted on."""

    def __init__(self, path: str = SEEN_LISTINGS_FILE):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self):
        # purge old entries
        cutoff = (datetime.utcnow() - timedelta(days=MAX_AGE_DAYS)).isoformat()
        self.data = {
            k: v for k, v in self.data.items()
            if v.get("found_at", "9999") > cutoff
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def is_new(self, listing: Listing) -> bool:
        return (
            listing.url_hash() not in self.data
            and listing.content_hash() not in self.data
        )

    def mark_seen(self, listing: Listing):
        record = asdict(listing)
        self.data[listing.url_hash()] = record
        self.data[listing.content_hash()] = record

    def filter_new(self, listings: List[Listing]) -> List[Listing]:
        new = []
        for l in listings:
            if self.is_new(l):
                new.append(l)
                self.mark_seen(l)
        return new
