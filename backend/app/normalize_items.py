from __future__ import annotations

from pathlib import Path
import pandas as pd
import re


_SYN_CANDIDATES = [
    Path("/app/data/processed/synonyms.csv"),          # docker (backend контейнер)
    Path("data/processed/synonyms.csv"),               # запуск из корня репо локально
    Path(__file__).resolve().parents[2] / "data" / "processed" / "synonyms.csv",  # запуск из backend/app
]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip()).lower()


def load_synonyms() -> dict[str, str]:
    """
    Загружает mapping variant->canonical из CSV.
    variant/canonical сравниваем в нижнем регистре.
    """
    syn_path = next((p for p in _SYN_CANDIDATES if p.exists()), None)
    if syn_path is None:
        return {}

    df = pd.read_csv(syn_path, encoding="utf-8-sig")
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

    # первичная чистка для поискового запроса
    raw = re.sub(r"\s+", " ", raw.replace("\xa0", " ")).strip()
    raw = raw.replace("«", '"').replace("»", '"')
    raw = re.sub(r'"+', '"', raw)
    raw = re.sub(r"\s*[,;]\s*", ", ", raw)
    raw = re.sub(r"\s*\.\s*", ". ", raw)
    raw = re.sub(r"\s+", " ", raw).strip(" ,;.")

    key = _norm(raw)
    if key in syn:
        return syn[key]

    # убираем "(...)" в конце/середине (для сопоставления по словарю и общим правилам)
    no_paren = re.sub(r"\([^)]*\)", "", raw).strip(" ,;.")
    key2 = _norm(no_paren)
    if key2 in syn:
        return syn[key2]

    low = key2

    # -------- мебель --------
    if ("комплект" in low or low.startswith("мебел")) and ("мебел" in low or "стол" in low or "стул" in low or "доск" in low):
        # если есть уточнение в скобках — обычно полезно для закупки, оставим тип скобок убранным, но нормализуем название
        return "Комплект учебной мебели"

    # -------- проекторы --------
    if "проектор" in low or "видеопроектор" in low or "диапроектор" in low:
        # диапроекторы оставим как отдельный класс (это не мультимедийный проектор)
        if "диапроектор" in low:
            # постараемся сохранить модель/бренд если есть
            return re.sub(r"\s+", " ", raw).strip()

        # аксессуары "для/к проектору" (экран, полотно, столик и т.п.) — это НЕ проектор
        if re.search(r"\b(для|к)\s+проектор[ауео]?\b", low) or re.search(r"\b(экран|полотно|креплен|кронштейн|штатив|столик)\b", low):
            return no_paren

        brand_fixes = {
            "panasonik": "panasonic",
            "sanio": "sanyo",
        }
        raw_fixed = raw
        for bad, good in brand_fixes.items():
            raw_fixed = re.sub(rf"\b{re.escape(bad)}\b", good, raw_fixed, flags=re.IGNORECASE)

        # достаём хвост после слова "проектор/видеопроектор" — там обычно бренд/модель
        m = re.search(
            r"(?:мультимед\.\s*)?(?:мультимедийный\s*)?(?:видео\s*)?(?:видеопроектор|проектор)\s*(.*)$",
            raw_fixed,
            flags=re.IGNORECASE,
        )
        tail = (m.group(1) if m else "").strip(" -–—:,.")
        tail = re.sub(r"^(?:мультимед\.\s*|мультимедийный\s*)+", "", tail, flags=re.IGNORECASE).strip(" -–—:,.")

        # если tail пустой — возвращаем единый канон
        if not tail:
            return "Мультимедийный проектор"

        # вычистим дубли типа "Panasonic Panasonic"
        tail = re.sub(r"\s+", " ", tail)
        tail = re.sub(r"^(panasonic|epson|sanyo|sony|benq|nec|acer|jvc)\s+\\1\\b", r"\\1", tail, flags=re.IGNORECASE)

        # финальный поисковый запрос: "Мультимедийный проектор <tail>"
        # но если в tail уже есть "ультракороткофокусный" / "короткофокусный" — сохраняем
        pretty_tail = tail
        # лёгкая капитализация брендов (модель оставляем как есть)
        pretty_tail = re.sub(r"\bpanasonic\b", "Panasonic", pretty_tail, flags=re.IGNORECASE)
        pretty_tail = re.sub(r"\bepson\b", "Epson", pretty_tail, flags=re.IGNORECASE)
        pretty_tail = re.sub(r"\bsanyo\b", "SANYO", pretty_tail, flags=re.IGNORECASE)
        pretty_tail = re.sub(r"\bsony\b", "Sony", pretty_tail, flags=re.IGNORECASE)
        pretty_tail = re.sub(r"\bbenq\b", "BenQ", pretty_tail, flags=re.IGNORECASE)
        pretty_tail = re.sub(r"\bnec\b", "NEC", pretty_tail, flags=re.IGNORECASE)
        pretty_tail = re.sub(r"\bacer\b", "Acer", pretty_tail, flags=re.IGNORECASE)
        pretty_tail = re.sub(r"\bjvc\b", "JVC", pretty_tail, flags=re.IGNORECASE)
        return f"Мультимедийный проектор {pretty_tail}".strip()

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