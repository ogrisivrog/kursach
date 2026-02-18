from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Literal

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from .db import engine, get_db
from .models import Base, Item, Location, Inventory, Requirement
from .ingest import ingest_inventory_df
from .ingest_requirements import ingest_requirements_df

app = FastAPI(title="MTO Minimal API")

@app.on_event("startup")
def startup():
    # Пока создаём таблицы автоматически (позже заменим на миграции)
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}

# -------------------- import inventory --------------------

@app.post("/import/inventory")
async def import_inventory(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")

    stats = ingest_inventory_df(db, df)
    db.commit()
    return {"ok": True, **stats}

@app.post("/import/inventory-from-path")
def import_inventory_from_path(
    rel_path: str = Query(..., description="Путь относительно /app/data, например processed/inventory_normalized_aggregated.csv"),
    db: Session = Depends(get_db),
):
    safe_root = Path("/app/data").resolve()
    target = (safe_root / rel_path).resolve()

    if not str(target).startswith(str(safe_root)):
        raise HTTPException(status_code=400, detail="Bad path (outside /app/data)")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {rel_path}")
    if target.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    df = pd.read_csv(target, encoding="utf-8-sig")
    stats = ingest_inventory_df(db, df)
    db.commit()
    return {"ok": True, "path": rel_path, **stats}

# -------------------- import requirements --------------------

@app.post("/import/requirements")
async def import_requirements(
    file: UploadFile = File(...),
    replace: bool = Query(False, description="Если true — очищает requirements перед импортом"),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")

    stats = ingest_requirements_df(db, df, replace=replace)
    db.commit()
    return {"ok": True, **stats}

@app.post("/import/requirements-from-path")
def import_requirements_from_path(
    rel_path: str = Query(..., description="Путь относительно /app/data, например processed/requirements.csv"),
    replace: bool = Query(False, description="Если true — очищает requirements перед импортом"),
    db: Session = Depends(get_db),
):
    safe_root = Path("/app/data").resolve()
    target = (safe_root / rel_path).resolve()

    if not str(target).startswith(str(safe_root)):
        raise HTTPException(status_code=400, detail="Bad path (outside /app/data)")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {rel_path}")
    if target.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    df = pd.read_csv(target, encoding="utf-8-sig")
    stats = ingest_requirements_df(db, df, replace=replace)
    db.commit()
    return {"ok": True, "path": rel_path, **stats}

# -------------------- views --------------------

@app.get("/inventory")
def list_inventory(
    item: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            Item.name.label("item_name"),
            Location.name.label("location"),
            Inventory.qty_available.label("qty_available"),
        )
        .join(Inventory, Inventory.item_id == Item.id)
        .join(Location, Inventory.location_id == Location.id)
    )
    if item:
        q = q.filter(Item.name.ilike(f"%{item}%"))
    if location:
        q = q.filter(Location.name.ilike(f"%{location}%"))

    total = q.count()
    rows = q.order_by(Location.name.asc(), Item.name.asc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "rows": [{"item_name": r.item_name, "location": r.location, "qty_available": r.qty_available} for r in rows],
    }

@app.get("/inventory/summary")
def inventory_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Item.name.label("item_name"),
            func.sum(Inventory.qty_available).label("qty_total"),
        )
        .join(Inventory, Inventory.item_id == Item.id)
        .group_by(Item.name)
        .order_by(func.sum(Inventory.qty_available).desc(), Item.name.asc())
        .all()
    )
    return {"rows": [{"item_name": r.item_name, "qty_total": int(r.qty_total or 0)} for r in rows]}

@app.get("/requirements")
def list_requirements(
    discipline: Optional[str] = Query(None),
    item: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Requirement)
    if discipline:
        q = q.filter(Requirement.discipline.ilike(f"%{discipline}%"))
    if item:
        q = q.filter(Requirement.item_name.ilike(f"%{item}%"))

    total = q.count()
    rows = q.order_by(Requirement.discipline.asc().nulls_last(), Requirement.item_name.asc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "rows": [{"discipline": r.discipline, "lab": r.lab, "item_name": r.item_name, "qty_required": r.qty_required} for r in rows],
    }

@app.get("/requirements/summary")
def requirements_summary(
    by: Literal["item", "discipline"] = Query("item"),
    db: Session = Depends(get_db),
):
    if by == "item":
        rows = (
            db.query(
                Requirement.item_name.label("item_name"),
                func.sum(Requirement.qty_required).label("qty_required"),
            )
            .group_by(Requirement.item_name)
            .order_by(func.sum(Requirement.qty_required).desc(), Requirement.item_name.asc())
            .all()
        )
        return {"by": "item", "rows": [{"item_name": r.item_name, "qty_required": int(r.qty_required or 0)} for r in rows]}

    rows = (
        db.query(
            Requirement.discipline.label("discipline"),
            Requirement.item_name.label("item_name"),
            func.sum(Requirement.qty_required).label("qty_required"),
        )
        .group_by(Requirement.discipline, Requirement.item_name)
        .order_by(Requirement.discipline.asc().nulls_last(), func.sum(Requirement.qty_required).desc())
        .all()
    )
    return {"by": "discipline", "rows": [{"discipline": r.discipline, "item_name": r.item_name, "qty_required": int(r.qty_required or 0)} for r in rows]}

# -------------------- calc: coverage --------------------

@app.get("/calc/coverage")
def calc_coverage(
    only_deficit: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Минимальная версия: сопоставляем требования и наличие ПО ТОЧНОМУ item_name.
    Если названия отличаются ("ПК" vs "Персональный компьютер") — будет показывать дефицит.
    Позже добавим синонимы/нормализацию.
    """
    inv = (
        db.query(
            Item.name.label("item_name"),
            func.sum(Inventory.qty_available).label("qty_available"),
        )
        .join(Inventory, Inventory.item_id == Item.id)
        .group_by(Item.name)
        .all()
    )
    inv_map = {r.item_name: int(r.qty_available or 0) for r in inv}

    req = (
        db.query(
            Requirement.item_name.label("item_name"),
            func.sum(Requirement.qty_required).label("qty_required"),
        )
        .group_by(Requirement.item_name)
        .all()
    )

    rows = []
    for r in req:
        item_name = r.item_name
        qty_required = int(r.qty_required or 0)
        qty_available = inv_map.get(item_name, 0)
        deficit = max(0, qty_required - qty_available)
        if only_deficit and deficit == 0:
            continue
        rows.append(
            {
                "item_name": item_name,
                "qty_required": qty_required,
                "qty_available": qty_available,
                "deficit": deficit,
            }
        )

    rows.sort(key=lambda x: (-x["deficit"], x["item_name"]))
    return {"only_deficit": only_deficit, "rows": rows}

@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    items = db.query(func.count(Item.id)).scalar() or 0
    locations = db.query(func.count(Location.id)).scalar() or 0
    inv_rows = db.query(func.count(Inventory.id)).scalar() or 0
    qty_sum = db.query(func.coalesce(func.sum(Inventory.qty_available), 0)).scalar() or 0
    req_rows = db.query(func.count(Requirement.id)).scalar() or 0
    req_sum = db.query(func.coalesce(func.sum(Requirement.qty_required), 0)).scalar() or 0
    return {
        "items": int(items),
        "locations": int(locations),
        "inventory_rows": int(inv_rows),
        "qty_sum": int(qty_sum),
        "requirements_rows": int(req_rows),
        "requirements_sum": int(req_sum),
    }