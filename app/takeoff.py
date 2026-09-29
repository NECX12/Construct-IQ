from collections import defaultdict

from .models import BuildingElement, MaterialRule, MaterialTakeoff


def calculate_area(length_m: float, width_m: float) -> float:
    if length_m < 0 or width_m < 0:
        raise ValueError("Dimensions cannot be negative")
    return length_m * width_m


def calculate_wall_area(length_m: float, height_m: float) -> float:
    if length_m < 0 or height_m < 0:
        raise ValueError("Dimensions cannot be negative")
    return length_m * height_m


def apply_wastage(quantity: float, wastage_percent: float) -> float:
    if quantity < 0 or wastage_percent < 0:
        raise ValueError("Quantity and wastage cannot be negative")
    return quantity * (1 + wastage_percent / 100)


def calculate_takeoff(
    elements: list[BuildingElement],
    rules: dict[str, list[MaterialRule]],
    wastage_percent: dict[str, float] | None = None,
) -> list[MaterialTakeoff]:
    wastage_percent = wastage_percent or {}
    totals: dict[str, float] = defaultdict(float)
    units: dict[str, str] = {}
    sources: dict[str, list[str]] = defaultdict(list)

    for element in elements:
        if element.quantity < 0:
            raise ValueError(f"Negative quantity for {element.element_type}")
        for rule in rules.get(element.element_type, []):
            totals[rule.material] += element.quantity * rule.consumption_rate
            units[rule.material] = rule.unit
            sources[rule.material].append(element.element_type)

    return [
        MaterialTakeoff(
            material=material,
            planned_quantity=round(quantity, 3),
            unit=units[material],
            wastage_percent=wastage_percent.get(material, 0.0),
            final_quantity=round(apply_wastage(quantity, wastage_percent.get(material, 0.0)), 3),
            source_elements=sorted(set(sources[material])),
        )
        for material, quantity in sorted(totals.items())
    ]


def default_rules() -> dict[str, list[MaterialRule]]:
    return {
        "block_wall": [
            MaterialRule(material="blocks", consumption_rate=10.0, unit="pcs"),
            MaterialRule(material="cement", consumption_rate=0.15, unit="bag"),
            MaterialRule(material="sand", consumption_rate=0.02, unit="m3"),
        ],
        "floor_area": [
            MaterialRule(material="tiles", consumption_rate=1.0, unit="m2"),
        ],
    }
