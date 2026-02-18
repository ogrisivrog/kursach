# backend/app/normalize_software.py
from __future__ import annotations

import re

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())

def canonicalize_software(name: str) -> str:
    """
    Минимальная нормализация ПО под твой проект.
    Можно расширять правилами/синонимами.
    """
    raw = str(name).strip()
    if not raw:
        return raw

    low = _norm(raw)

    # VS Code
    if "visual studio code" in low or low == "vscode" or "vs code" in low:
        return "VS Code"

    # Python
    if low.startswith("python") or "python 3" in low:
        return "Python"

    # PostgreSQL
    if "postgresql" in low or low == "postgres" or low.startswith("postgres"):
        return "PostgreSQL"

    # Docker
    if low.startswith("docker") or "docker desktop" in low:
        return "Docker"

    # Wireshark
    if "wireshark" in low:
        return "Wireshark"

    # дефолт: как есть (с нормальными пробелами)
    return re.sub(r"\s+", " ", raw).strip()