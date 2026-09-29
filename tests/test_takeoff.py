from app.models import BuildingElement
from app.takeoff import apply_wastage, calculate_takeoff, default_rules


def test_apply_wastage():
    assert apply_wastage(4000, 5) == 4200


def test_calculate_takeoff():
    items = calculate_takeoff(
        [BuildingElement(element_type="block_wall", quantity=60, unit="m2")],
        default_rules(),
        {"blocks": 5, "cement": 5, "sand": 5},
    )
    blocks = next(item for item in items if item.material == "blocks")
    assert blocks.planned_quantity == 600
    assert blocks.final_quantity == 630
