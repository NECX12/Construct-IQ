from typing import Any

from pydantic import BaseModel, Field


class Measurement(BaseModel):
    value: float
    unit: str = "m"
    source: str = "user_entered"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    review_required: bool = False


class Room(BaseModel):
    name: str
    length_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None
    area_m2: float | None = None


class BuildingElement(BaseModel):
    element_type: str
    quantity: float
    unit: str
    dimensions: dict[str, float] = Field(default_factory=dict)
    source: str = "user_entered"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class DrawingExtraction(BaseModel):
    filename: str
    drawing_type: str = "unknown"
    rooms: list[Room] = Field(default_factory=list)
    doors: int = 0
    windows: int = 0
    building_elements: list[BuildingElement] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AIElement(BaseModel):
    element_type: str
    quantity: float
    unit: str
    source: str = "ai_extracted"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AIExtractionResponse(BaseModel):
    drawing_type: str = "unknown"
    rooms: list[Room] = Field(default_factory=list)
    doors: int = Field(default=0, ge=0)
    windows: int = Field(default=0, ge=0)
    building_elements: list[AIElement] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SiteLogEntry(BaseModel):
    date: str
    activity: str
    material: str | None = None
    quantity: float | None = None
    unit: str | None = None
    workers: int | None = None
    notes: str | None = None


class MaterialRule(BaseModel):
    material: str
    consumption_rate: float = Field(gt=0)
    unit: str


class MaterialTakeoff(BaseModel):
    material: str
    planned_quantity: float
    unit: str
    wastage_percent: float = Field(default=0.0, ge=0.0)
    final_quantity: float
    source_elements: list[str] = Field(default_factory=list)


class PriceEntry(BaseModel):
    material: str
    unit: str
    unit_price: float = Field(ge=0)
    currency: str = "NGN"


class CostLine(BaseModel):
    material: str
    quantity: float
    unit: str
    unit_price: float
    estimated_cost: float
    currency: str


class VarianceLine(BaseModel):
    material: str
    planned_quantity: float
    actual_quantity: float
    variance: float
    variance_percent: float | None
    unit: str
    status: str


class ProjectState(BaseModel):
    name: str = "Untitled project"
    project_type: str = "Residential"
    location: str = ""
    currency: str = "NGN"
    assumptions: dict[str, Any] = Field(default_factory=dict)
    extraction: DrawingExtraction | None = None
    takeoff: list[MaterialTakeoff] = Field(default_factory=list)
    costs: list[CostLine] = Field(default_factory=list)
    site_logs: list[SiteLogEntry] = Field(default_factory=list)
    variance: list[VarianceLine] = Field(default_factory=list)
