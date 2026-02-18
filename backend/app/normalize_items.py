from __future__ import annotations

from pathlib import Path
import pandas as pd
import re


SYN_PATH = Path("/app/data/processed/synonyms.csv")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip()).lower()


def load_synonyms() -> dict[str, str]:
    """
    Загружает mapping variant->canonical из CSV.
    variant/canonical сравниваем в нижнем регистре.
    """
    if not SYN_PATH.exists():
        return {}

    df = pd.read_csv(SYN_PATH, encoding="utf-8-sig")
    if "variant" not in df.columns or "canonical" not in df.columns:
        return {}

    m = {}
    for v, c in zip(df["variant"], df["canonical"]):
        v2 = _norm(v)
        c2 = str(c).strip()
        if v2 and c2:
            m[v2] = c2
    return m


def canonicalize(name: str, syn: dict[str, str]) -> str:
    """
    Приводит название к "каноническому":
    1) сначала пробует synonyms.csv (точное совпадение после нормализации)
    2) затем срезает скобки и лишние хвосты
    3) затем простые правила по ключевым словам (на случай OCR/вариантов)
    """
    raw = str(name).strip()
    if not raw:
        return raw

    key = _norm(raw)
    if key in syn:
        return syn[key]

    # убираем "(...)" в конце/середине
    no_paren = re.sub(r"\([^)]*\)", "", raw).strip()
    key2 = _norm(no_paren)
    if key2 in syn:
        return syn[key2]

    low = key2

    if "персональн" in low and "компьютер" in low:
        return "Персональный компьютер"
    if "компьютер" in low and "преподав" in low:
        return "Компьютер преподавателя"
    if low.startswith("ибп") or "ибп" in low:
        return "ИБП"
    if "сервер" in low:
        return "Сервер учебный"

       # --- СЕТЕВОЕ / КАБЕЛИ ---
    # 1) СНАЧАЛА коммутаторы (важно: DGS = линейка коммутаторов D-Link)
    if "switch" in low or "коммут" in low or "baseline" in low:
        return "Коммутатор"
    if "dgs" in low:   # D-Link DGS-1100-24 и т.п.
        return "Коммутатор"

    # 2) ПОТОМ маршрутизаторы
    if ("маршрут" in low) or ("router" in low) or ("routerboard" in low) or ("mikrotik" in low) or ("cisco" in low):
        return "Маршрутизатор"
    # d-link иногда встречается и как маршрутизатор, и как коммутатор — DGS уже перехватили выше
    if "d-link" in low or "dlink" in low:
        return "Маршрутизатор"

    # патч-корды / кабели / тестеры (если появятся в инвентаре)
    if "патч" in low or "patch" in low or "patchcord" in low or "patch-cord" in low:
        return "Набор кабелей/патч-кордов"

    if ("тестер" in low or "tester" in low) and ("вит" in low or "twisted" in low or "кабель" in low or "cable" in low):
        return "Тестер витой пары"

    # --- СМАРТФОНЫ ---
    if "iphone" in low or "ios" in low:
        return "Смартфон iOS для тестирования"
    if "android" in low:
        return "Смартфон Android для тестирования"
    

    return no_paren