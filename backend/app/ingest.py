from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from .models import Item, Location, Inventory

REQUIRED_COLS = {"item_name", "location", "qty_available"}

def _get_or_create_item(db: Session, name: str) -> Item:
    obj = db.query(Item).filter(Item.name == name).one_or_none()
    if obj:
        return obj
    obj = Item(name=name)
    db.add(obj)
    db.flush()  # get id
    return obj

def _get_or_create_location(db: Session, name: str) -> Location:
    obj = db.query(Location).filter(Location.name == name).one_or_none()
    if obj:
        return obj
    obj = Location(name=name)
    db.add(obj)
    db.flush()
    return obj

def ingest_inventory_df(db: Session, df: pd.DataFrame) -> dict:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    # Normalize minimal
    df = df.copy()
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["location"] = df["location"].astype(str).str.strip()
    df["qty_available"] = pd.to_numeric(df["qty_available"], errors="coerce").fillna(0).astype(int)
    df = df[(df["item_name"] != "") & (df["location"] != "")]

    # Cache to avoid repeated queries
    item_cache: dict[str, Item] = {}
    loc_cache: dict[str, Location] = {}
    updated = 0
    inserted = 0
    skipped = 0

    for row in df.itertuples(index=False):
        item_name = row.item_name
        loc_name = row.location
        qty = int(row.qty_available)
        if qty < 0:
            skipped += 1
            continue

        item = item_cache.get(item_name)
        if item is None:
            item = _get_or_create_item(db, item_name)
            item_cache[item_name] = item

        loc = loc_cache.get(loc_name)
        if loc is None:
            loc = _get_or_create_location(db, loc_name)
            loc_cache[loc_name] = loc

        inv = (
            db.query(Inventory)
            .filter(Inventory.item_id == item.id, Inventory.location_id == loc.id)
            .one_or_none()
        )
        if inv is None:
            inv = Inventory(item_id=item.id, location_id=loc.id, qty_available=qty)
            db.add(inv)
            inserted += 1
        else:
            inv.qty_available += qty  # accumulate
            updated += 1

    return {"inserted": inserted, "updated": updated, "skipped": skipped, "rows": int(len(df))}
