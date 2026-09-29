import re
from datetime import datetime

from .models import SiteLogEntry


MATERIAL_PATTERN = re.compile(
    r"^\s*(?P<material>[A-Za-z][A-Za-z ]*?)\s*[-:]\s*"
    r"(?P<quantity>\d+(?:\.\d+)?)\s+(?P<unit>[A-Za-z0-9]+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_site_log(text: str) -> list[SiteLogEntry]:
    date_match = re.search(r"Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
    date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
    activity_match = re.search(r"Activity\s*:\s*(.+)", text, re.IGNORECASE)
    activity = activity_match.group(1).strip() if activity_match else "Unspecified"
    workers_match = re.search(r"Workers\s*:\s*(\d+)", text, re.IGNORECASE)
    workers = int(workers_match.group(1)) if workers_match else None
    entries = []
    for match in MATERIAL_PATTERN.finditer(text):
        entries.append(
            SiteLogEntry(
                date=date,
                activity=activity,
                material=match.group("material").strip().lower(),
                quantity=float(match.group("quantity")),
                unit=match.group("unit").strip().lower(),
                workers=workers,
            )
        )
    return entries


def aggregate_actuals(entries: list[SiteLogEntry]) -> dict[str, float]:
    actuals: dict[str, float] = {}
    for entry in entries:
        if entry.material and entry.quantity is not None:
            actuals[entry.material] = actuals.get(entry.material, 0.0) + entry.quantity
    return actuals
