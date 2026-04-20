from typing import List, Optional
from pydantic import BaseModel, field_validator


class Vehicle(BaseModel):
    vehicle_id: int
    title: Optional[str]
    created_tms: Optional[int]
    changed_tms: Optional[int]
    year: Optional[int]
    first_registration_tms_B: Optional[int]
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
    @field_validator("equipments", mode="before")
    @classmethod
    def normalize_equipments(cls, v):
        if v is None:
            return []

        # case 1: already list
        if isinstance(v, list):
            return v

        # case 2: dict like {"item": ...}
        if isinstance(v, dict):
            items = v.get("item")
            if isinstance(items, list):
                return items
            if isinstance(items, str):
                return [items]
            return []

        # case 3: single string
        if isinstance(v, str):
            return [v]
        return []

    @field_validator("photos", mode="before")
    @classmethod
    def normalize_photos(cls, v):
        if v is None:
            return []

        if isinstance(v, list):
            return v

        if isinstance(v, dict):
            items = v.get("item")
            if isinstance(items, list):
                return items
            if isinstance(items, str):
                return [items]
            return []

        if isinstance(v, str):
            return [v]

        return []