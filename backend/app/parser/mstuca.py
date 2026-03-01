from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import requests

from ..normalize_items import canonicalize, load_synonyms


URL_DEFAULT = "https://www.mstuca.ru/sveden/objects/index.php?sphrase_id=28124"
OUT_DEFAULT = Path("/app/data/processed/mstuca_items2_normalized.csv")


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=45)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def is_mtb_table(df: pd.DataFrame) -> bool:
    cols = [str(c).strip().lower() for c in df.columns]
    has_equipment = any("оснащ" in c for c in cols)
    has_address = any("адрес" in c for c in cols)
    has_name = any("наименование" in c for c in cols)
    return has_equipment and (has_address or has_name) and len(df.columns) >= 3


def normalize_table(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    mapping = {}
    for c in df.columns:
        cl = str(c).strip().lower()
        if "адрес" in cl:
            mapping[c] = "address"
        elif "наименование" in cl:
            mapping[c] = "room"
        elif "оснащ" in cl:
            mapping[c] = "equipment"

    df2 = df.rename(columns=mapping)
    if not {"equipment", "room"}.issubset(df2.columns):
        return None
    if "address" not in df2.columns:
        df2["address"] = ""
    return df2[["address", "room", "equipment"]].copy()


def load_mtb_frames(html: str) -> pd.DataFrame:
    tables = pd.read_html(html)  # requires lxml
    frames = []
    for t in tables:
        if is_mtb_table(t):
            nt = normalize_table(t)
            if nt is not None:
                frames.append(nt)
    if not frames:
        raise RuntimeError("Не нашёл таблицы с 'Оснащенность'. Возможно, изменилась разметка страницы.")
    return pd.concat(frames, ignore_index=True)


def segment_by_multiple_qty(chunk: str) -> List[str]:
    """
    Если в одном фрагменте несколько паттернов "... - 1 шт ... - 2 шт",
    пытаемся разбить на отдельные под-элементы.
    """
    qty_pat = re.compile(
        r"(.+?)(?:\s*[-–—]\s*|\s+)(\d+)\s*(шт\.?|шт|компл\.?|компл|ед\.?|ед|мест(а)?)\b",
        re.IGNORECASE,
    )
    matches = list(qty_pat.finditer(chunk))
    if len(matches) <= 1:
        return [chunk.strip()]

    segments = []
    last = 0
    for m in matches:
        seg = chunk[last : m.end()].strip(" ;,.\t")
        if seg:
            segments.append(seg)
        last = m.end()

    tail = chunk[last:].strip(" ;,.\t")
    if tail:
        segments.append(tail)
    return segments


def split_equipment_to_items(equipment: str) -> List[str]:
    if equipment is None:
        return []
    text = str(equipment).replace("\xa0", " ").strip()
    if text in {"-", "—", "–", ""}:
        return []

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[A-Za-zА-Яа-яЁё0-9])\.(?=[A-Za-zА-Яа-яЁё])", ". ", text)

    def split_top_level_commas(s: str) -> List[str]:
        out: List[str] = []
        buf: List[str] = []
        depth = 0

        def next_nonspace_is_letter(i: int) -> bool:
            j = i
            while j < len(s) and s[j].isspace():
                j += 1
            if j >= len(s):
                return False
            return bool(re.match(r"[A-Za-zА-Яа-яЁё]", s[j]))

        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")" and depth > 0:
                depth -= 1

            if ch == "," and depth == 0 and next_nonspace_is_letter(i + 1):
                seg = "".join(buf).strip(" \t;")
                if seg:
                    out.append(seg)
                buf = []
                continue

            buf.append(ch)

        tail = "".join(buf).strip(" \t;")
        if tail:
            out.append(tail)
        return out

    parts = re.split(r";|\n", text)

    items: List[str] = []
    for p in parts:
        p = p.strip(" ;,.\t")
        if not p:
            continue
        for sub in split_top_level_commas(p):
            sub = sub.strip(" ;,.\t")
            if not sub:
                continue
            for seg in segment_by_multiple_qty(sub):
                seg = seg.strip(" ;,.\t")
                if seg:
                    items.append(seg)
    return items


def extract_name_qty(item: str) -> Tuple[str, Optional[int]]:
    s = item.strip()

    m = re.search(r"(\d+)\s*(шт\.?|шт|компл\.?|компл|ед\.?|ед)\b", s, flags=re.IGNORECASE)
    qty = None
    if m:
        qty = int(m.group(1))
        s = re.sub(r"[-–—]?\s*" + re.escape(m.group(0)), "", s, flags=re.IGNORECASE).strip()

    m2 = re.search(r"[:\-]\s*(\d+)\s*$", s)
    if qty is None and m2:
        tail_num = int(m2.group(1))
        if re.search(r"\bмест\b|рабочих мест|место инструктора", s, flags=re.IGNORECASE):
            qty = tail_num
            s = re.sub(r"[:\-]\s*" + re.escape(m2.group(1)) + r"\s*$", "", s).strip()

    s = re.sub(r"\s+", " ", s).strip(" -–—;,.")
    return s, qty


def build_inventory_rows(df: pd.DataFrame, keep_capacity: bool) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        address = str(r.get("address", "")).strip()
        room = str(r.get("room", "")).strip()
        equipment = r.get("equipment", "")

        if not room:
            continue

        location = f"{address} | {room}" if address else room

        for raw_item in split_equipment_to_items(equipment):
            name, qty = extract_name_qty(raw_item)
            if not name:
                continue
            if not keep_capacity and re.search(r"\bмест\b|рабочих мест|место инструктора", name, flags=re.IGNORECASE):
                continue
            rows.append(
                {
                    "item_name": name,
                    "location": location,
                    "qty_available": "" if qty is None else qty,
                }
            )

    return pd.DataFrame(rows, columns=["item_name", "location", "qty_available"])


def parse_and_normalize_to_csv(
    url: str = URL_DEFAULT,
    out_path: Path = OUT_DEFAULT,
    keep_capacity: bool = False,
) -> Path:
    html = fetch_html(url)
    rooms_df = load_mtb_frames(html)
    inv_df = build_inventory_rows(rooms_df, keep_capacity=keep_capacity)

    syn = load_synonyms()
    inv_df["canonical_item_name"] = inv_df["item_name"].astype(str).map(lambda s: canonicalize(s, syn))
    inv_df["search_query"] = inv_df["canonical_item_name"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    inv_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return out_path


def parse_on_startup() -> Optional[Path]:
    """
    Вызывается на старте приложения. Управление через env:
    - MTSUCA_PARSE_ON_STARTUP: "1"/"0" (default: "1")
    - MTSUCA_URL: URL страницы (default: URL_DEFAULT)
    - MTSUCA_KEEP_CAPACITY: "1"/"0" (default: "0")
    - MTSUCA_OUT: путь к выходному CSV (default: OUT_DEFAULT)
    """
    if os.getenv("MTSUCA_PARSE_ON_STARTUP", "1") not in {"1", "true", "True", "yes", "YES"}:
        return None

    url = os.getenv("MTSUCA_URL", URL_DEFAULT)
    keep_capacity = os.getenv("MTSUCA_KEEP_CAPACITY", "0") in {"1", "true", "True", "yes", "YES"}
    out_path = Path(os.getenv("MTSUCA_OUT", str(OUT_DEFAULT)))

    # По умолчанию — генерируем файл только если его ещё нет.
    # Заглушка: при необходимости можно обновлять раз в неделю, сравнивая mtime файла с текущей датой.
    # Например: if out_path.exists() and (time.time() - out_path.stat().st_mtime) < 7*24*3600: return out_path
    if out_path.exists():
        return out_path

    # Не валим весь бэкенд, если сайт недоступен
    try:
        return parse_and_normalize_to_csv(url=url, out_path=out_path, keep_capacity=keep_capacity)
    except Exception as e:
        print(f"[parser:mstuca] parse failed: {e}")
        return None

