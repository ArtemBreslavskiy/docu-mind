from sqlalchemy import or_, and_, Table
from typing import Any
from src.data.db.filter import FilterCondition, FilterGroup, Operator


def convert_filter(table: Table, filter: FilterCondition | FilterGroup) -> Any:
    if isinstance(filter, FilterCondition):
        column = table.c.get(filter.field)
        if column is None:
            raise ValueError(f"Column '{filter.field}' not found in table '{table.name}'")
        op = filter.operator
        value = filter.value
        if op == Operator.EQ:
            return column == value
        elif op == Operator.GT:
            return column > value
        elif op == Operator.LT:
            return column < value
        elif op == Operator.GTE:
            return column >= value
        elif op == Operator.LTE:
            return column <= value
        elif op == Operator.NE:
            return column != value
        elif op == Operator.IN:
            if not isinstance(value, list) or not value:
                raise ValueError("IN operator requires a non-empty list")
            return column.in_(value)
        elif op == Operator.ISNULL:
            return column.is_(None) if value is True else column.isnot(None)
        elif op == Operator.LIKE:
            return column.like(value)
        elif op == Operator.ILIKE:
            return column.ilike(value)
        else:
            raise ValueError(f"Unsupported operator: {op}")

    elif isinstance(filter, FilterGroup):
        if not filter.conditions:
            return True
        sub_conditions = [convert_filter(table, f) for f in filter.conditions]
        if filter.operator == "AND":
            return and_(*sub_conditions)
        else:
            return or_(*sub_conditions)
    else:
        raise TypeError(f"Unsupported condition type: {type(filter)}")
