from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from .models import Requirement

REQUIRED_COLS = {"item_name", "qty_required"}

def ingest_requirements_df(db: Session, df: pd.DataFrame, *, replace: bool = False) -> dict:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    df = df.copy()
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["qty_required"] = pd.to_numeric(df["qty_required"], errors="coerce").fillna(0).astype(int)

    if "discipline" in df.columns:
        df["discipline"] = df["discipline"].astype(str).str.strip()
        df.loc[df["discipline"] == "nan", "discipline"] = ""
    else:
        df["discipline"] = ""

    if "lab" in df.columns:
        df["lab"] = df["lab"].astype(str).str.strip()
        df.loc[df["lab"] == "nan", "lab"] = ""
    else:
        df["lab"] = ""

    df = df[(df["item_name"] != "") & (df["qty_required"] >= 0)]

    if replace:
        db.query(Requirement).delete()

    inserted = 0
    skipped = 0
    for row in df.itertuples(index=False):
        qty = int(row.qty_required)
        if qty == 0:
            skipped += 1
            continue
        db.add(
            Requirement(
                discipline=row.discipline or None,
                lab=row.lab or None,
                item_name=row.item_name,
                qty_required=qty,
            )
        )
        inserted += 1

    return {"inserted": inserted, "skipped": skipped, "rows": int(len(df)), "replace": bool(replace)}