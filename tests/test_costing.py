from app.costing import calculate_costs, calculate_variance
from app.models import MaterialTakeoff, PriceEntry


def test_costing_and_variance():
    takeoff = [MaterialTakeoff(material="blocks", planned_quantity=600, unit="pcs", final_quantity=630)]
    costs = calculate_costs(takeoff, {"blocks": PriceEntry(material="blocks", unit="pcs", unit_price=750)})
    assert costs[0].estimated_cost == 472500
    variance = calculate_variance(takeoff, {"blocks": 700})
    assert variance[0].variance == 70
    assert variance[0].status == "SIGNIFICANT VARIANCE"
