from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Vehicle(BaseModel):
    vehicle_id: int
    title: Optional[str]
    created_tms: Optional[int]
    changed_tms: Optional[int]
    year: Optional[int]
    first_registration_tms: Optional[int]
    carmaker: Optional[str]
    model: Optional[str]
    energy: Optional[str]
    motorisation: Optional[str]
    transmission: Optional[str]
    finishing: Optional[str]
    color: Optional[str]
    doors: Optional[int]
    seats: Optional[int]
    power: Optional[int]
    co2: Optional[float]
    critair: Optional[int]
    drive_mode: Optional[str]
    mileage: Optional[int]
    body_j2: Optional[str] = None
    price: Optional[float] = None
    equipments: List[str] = []
    photos: List[str] = []

    # --- PRE VALIDATION (runs before parsing) ---
    @field_validator("*", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        return None if v == "" else v

    # --- STRUCTURE NORMALIZATION ---
    @field_validator("photos", mode="before")
    @classmethod
    def normalize_photos(cls, v):
        if isinstance(v, dict):
            return v.get("item", [])
        return v or []

    @field_validator("equipments", mode="before")
    @classmethod
    def normalize_equipments(cls, v):
        if isinstance(v, dict):
            return v.get("item", [])
        return v or []