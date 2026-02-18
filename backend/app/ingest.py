from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from .models import Item, Location, Inventory, SoftwareInventory, SoftwareRequirement
from .normalize_software import canonicalize_software


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
    required = {"item_name", "location", "qty_available"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    df = df.copy()
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["location"] = df["location"].astype(str).str.strip()
    df["qty_available"] = pd.to_numeric(df["qty_available"], errors="coerce").fillna(0).astype(int)

    # агрегируем на всякий случай
    df = (
        df[(df["item_name"] != "") & (df["location"] != "")]
        .groupby(["item_name", "location"], as_index=False)["qty_available"]
        .sum()
    )

    inserted = 0
    updated = 0
    skipped = 0

    for row in df.itertuples(index=False):
        item_name = row.item_name
        location_name = row.location
        qty = int(row.qty_available)

        item = db.query(Item).filter(Item.name == item_name).one_or_none()
        if not item:
            item = Item(name=item_name)
            db.add(item)
            db.flush()

        loc = db.query(Location).filter(Location.name == location_name).one_or_none()
        if not loc:
            loc = Location(name=location_name)
            db.add(loc)
            db.flush()

        inv = (
            db.query(Inventory)
            .filter(Inventory.item_id == item.id, Inventory.location_id == loc.id)
            .one_or_none()
        )

        if inv:
            inv.qty_available = qty
            updated += 1
        else:
            db.add(Inventory(item_id=item.id, location_id=loc.id, qty_available=qty))
            inserted += 1

    return {"inserted": inserted, "updated": updated, "skipped": skipped, "rows": int(len(df))}


def ingest_software_inventory_df(db: Session, df: pd.DataFrame) -> dict:
    required = {"software_name", "seats_available", "location"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    df = df.copy()
    df["software_name"] = df["software_name"].astype(str).map(canonicalize_software)
    df["location"] = df["location"].astype(str).str.strip()
    df["seats_available"] = pd.to_numeric(df["seats_available"], errors="coerce").fillna(0).astype(int)

    # агрегируем на всякий случай
    df = (
        df[(df["software_name"] != "") & (df["location"] != "")]
        .groupby(["software_name", "location"], as_index=False)["seats_available"]
        .sum()
    )

    inserted, updated = 0, 0
    for r in df.itertuples(index=False):
        row = (
            db.query(SoftwareInventory)
            .filter(SoftwareInventory.software_name == r.software_name,
                    SoftwareInventory.location == r.location)
            .one_or_none()
        )
        if row:
            row.seats_available = int(r.seats_available)  # ВАЖНО: перезапись, не +=
            updated += 1
        else:
            db.add(SoftwareInventory(
                software_name=r.software_name,
                location=r.location,
                seats_available=int(r.seats_available),
            ))
            inserted += 1

    return {"rows": int(len(df)), "inserted": inserted, "updated": updated, "skipped": 0}


def ingest_software_requirements_df(db: Session, df: pd.DataFrame, *, replace: bool = False) -> dict:
    required = {"software_name", "seats_required", "discipline", "lab"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    if replace:
        db.query(SoftwareRequirement).delete()

    df = df.copy()
    df["software_name"] = df["software_name"].astype(str).map(canonicalize_software)
    df["discipline"] = df["discipline"].astype(str).str.strip()
    df["lab"] = df["lab"].astype(str).str.strip()
    df["seats_required"] = pd.to_numeric(df["seats_required"], errors="coerce").fillna(0).astype(int)

    df = df[(df["software_name"] != "") & (df["discipline"] != "") & (df["lab"] != "")]

    inserted = 0
    for r in df.itertuples(index=False):
        db.add(SoftwareRequirement(
            software_name=r.software_name,
            seats_required=int(r.seats_required),
            discipline=r.discipline,
            lab=r.lab,
        ))
        inserted += 1

    return {"rows": int(len(df)), "inserted": inserted, "skipped": 0, "replace": replace}

