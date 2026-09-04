from qdrant_client import models
from src.data.db.filter import FilterCondition, FilterGroup, Operator


def build_should_filter(match_list: list[dict]) -> models.Filter | None:
    if not match_list:
        return None

    should_conditions = []
    for match in match_list:
        must_conditions = [models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in match.items()]
        if must_conditions:
            should_conditions.append(models.Filter(must=must_conditions))

    if not should_conditions:
        return None

    return models.Filter(should=should_conditions)


def convert_filter(filter: FilterCondition | FilterGroup) -> models.Filter | None:
    if isinstance(filter, FilterCondition):
        field = filter.field
        op = filter.operator
        value = filter.value

        if op == Operator.EQ:
            return models.Filter(must=[models.FieldCondition(key=field, match=models.MatchValue(value=value))])
        elif op == Operator.GT:
            return models.Filter(must=[models.FieldCondition(key=field, range=models.Range(gt=value))])
        elif op == Operator.LT:
            return models.Filter(must=[models.FieldCondition(key=field, range=models.Range(lt=value))])
        elif op == Operator.GTE:
            return models.Filter(must=[models.FieldCondition(key=field, range=models.Range(gte=value))])
        elif op == Operator.LTE:
            return models.Filter(must=[models.FieldCondition(key=field, range=models.Range(lte=value))])
        elif op == Operator.NE:
            return models.Filter(must_not=[models.FieldCondition(key=field, match=models.MatchValue(value=value))])
        elif op == Operator.IN:
            if not isinstance(value, list):
                raise ValueError("IN operator requires a list")
            return models.Filter(must=[models.FieldCondition(key=field, match=models.MatchAny(any=value))])
        elif op == Operator.ISNULL:
            if value is True:
                return models.Filter(must=[models.FieldCondition(key=field, is_null=True)])
            else:
                return models.Filter(must_not=[models.FieldCondition(key=field, is_null=True)])
        elif op == Operator.LIKE:
            return models.Filter(must=[models.FieldCondition(key=field, match=models.MatchText(text=value))])
        elif op == Operator.ILIKE:
            return models.Filter(
                must=[models.FieldCondition(key=field, match=models.MatchText(text=value.lower()))])
        else:
            raise ValueError(f"Unsupported operator: {op}")

    elif isinstance(filter, FilterGroup):
        filters = [convert_filter(f) for f in filter.conditions if convert_filter(f) is not None]
        if not filters:
            return None

        if filter.operator == "AND":
            return models.Filter(must=[f for filter_obj in filters for f in filter_obj.must])
        else:
            return models.Filter(should=filters)
    else:
        raise TypeError(f"Unsupported condition type: {type(filter)}")
