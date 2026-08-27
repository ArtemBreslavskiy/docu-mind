from pydantic import BaseModel, validator
from typing import Any, Literal
from enum import Enum


class Operator(str, Enum):
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    NE = "ne"
    IN = "in"
    ISNULL = "isnull"
    LIKE = "like"
    ILIKE = "ilike"


class FilterCondition(BaseModel):
    field: str
    operator: Operator = Operator.EQ
    value: Any

    @validator("value")
    def validate_value(cls, v, values):
        op = values.get("operator")
        if op == Operator.IN and not isinstance(v, list):
            raise ValueError("IN operator requires a list")
        if op == Operator.IN and not v:
            raise ValueError("IN operator requires non-empty list")
        return v


class FilterGroup(BaseModel):
    operator: Literal["AND", "OR"] = "AND"
    conditions: list[FilterCondition | "FilterGroup"] = []