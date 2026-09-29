from .models import CostLine, MaterialTakeoff, PriceEntry, VarianceLine


def calculate_costs(
    takeoff: list[MaterialTakeoff], prices: dict[str, PriceEntry]
) -> list[CostLine]:
    lines = []
    for item in takeoff:
        price = prices.get(item.material)
        if price is None:
            continue
        if price.unit != item.unit:
            raise ValueError(
                f"Unit mismatch for {item.material}: {item.unit} vs {price.unit}"
            )
        lines.append(
            CostLine(
                material=item.material,
                quantity=item.final_quantity,
                unit=item.unit,
                unit_price=price.unit_price,
                estimated_cost=round(item.final_quantity * price.unit_price, 2),
                currency=price.currency,
            )
        )
    return lines


def calculate_variance(
    takeoff: list[MaterialTakeoff], actuals: dict[str, float], threshold_percent: float = 10.0
) -> list[VarianceLine]:
    result = []
    for item in takeoff:
        actual = actuals.get(item.material, 0.0)
        variance = actual - item.final_quantity
        variance_percent = None if item.final_quantity == 0 else variance / item.final_quantity * 100
        absolute_percent = abs(variance_percent or 0.0)
        status = "SIGNIFICANT VARIANCE" if absolute_percent > threshold_percent else "ON TRACK"
        result.append(
            VarianceLine(
                material=item.material,
                planned_quantity=item.final_quantity,
                actual_quantity=actual,
                variance=round(variance, 3),
                variance_percent=None if variance_percent is None else round(variance_percent, 2),
                unit=item.unit,
                status=status,
            )
        )
    return result
