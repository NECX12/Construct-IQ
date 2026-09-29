import io
import json

import pandas as pd

from .models import CostLine, MaterialTakeoff, VarianceLine


def takeoff_dataframe(items: list[MaterialTakeoff]) -> pd.DataFrame:
    return pd.DataFrame([item.model_dump() for item in items])


def costs_dataframe(items: list[CostLine]) -> pd.DataFrame:
    return pd.DataFrame([item.model_dump() for item in items])


def variance_dataframe(items: list[VarianceLine]) -> pd.DataFrame:
    return pd.DataFrame([item.model_dump() for item in items])


def json_report(takeoff: list[MaterialTakeoff], costs: list[CostLine], variance: list[VarianceLine]) -> bytes:
    payload = {
        "takeoff": [item.model_dump() for item in takeoff],
        "costs": [item.model_dump() for item in costs],
        "variance": [item.model_dump() for item in variance],
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def excel_report(takeoff: list[MaterialTakeoff], costs: list[CostLine], variance: list[VarianceLine]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        takeoff_dataframe(takeoff).to_excel(writer, index=False, sheet_name="Takeoff")
        costs_dataframe(costs).to_excel(writer, index=False, sheet_name="Costs")
        variance_dataframe(variance).to_excel(writer, index=False, sheet_name="Variance")
    return output.getvalue()
