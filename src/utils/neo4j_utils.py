from src.data.db.filter import FilterCondition, FilterGroup, Operator


def escape_identifier(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def convert_filter(filter: FilterCondition | FilterGroup, alias: str = "n") -> tuple[str, dict]:
    def process(filter: FilterCondition | FilterGroup) -> tuple[str, dict]:
        if isinstance(filter, FilterCondition):
            field = filter.field
            safe_field = escape_identifier(field)
            op = filter.operator
            value = filter.value

            param_name = f"filter_{len(params)}"

            if op == Operator.EQ:
                return f"{alias}.`{safe_field}` = ${param_name}", {param_name: value}
            elif op == Operator.GT:
                return f"{alias}.`{safe_field}` > ${param_name}", {param_name: value}
            elif op == Operator.LT:
                return f"{alias}.`{safe_field}` < ${param_name}", {param_name: value}
            elif op == Operator.GTE:
                return f"{alias}.`{safe_field}` >= ${param_name}", {param_name: value}
            elif op == Operator.LTE:
                return f"{alias}.`{safe_field}` <= ${param_name}", {param_name: value}
            elif op == Operator.NE:
                return f"{alias}.`{safe_field}` <> ${param_name}", {param_name: value}
            elif op == Operator.IN:
                if not isinstance(value, list) or not value:
                    raise ValueError(f"IN operator requires a non-empty list for field '{field}'")
                return f"{alias}.`{safe_field}` IN ${param_name}", {param_name: value}
            elif op == Operator.ISNULL:
                if value is True:
                    return f"{alias}.`{safe_field}` IS NULL", {}
                else:
                    return f"{alias}.`{safe_field}` IS NOT NULL", {}
            elif op == Operator.LIKE:
                return f"{alias}.`{safe_field}` CONTAINS ${param_name}", {param_name: value}
            elif op == Operator.ILIKE:
                return f"toLower({alias}.`{safe_field}`) CONTAINS toLower(${param_name})", {param_name: value}
            else:
                raise ValueError(f"Unsupported operator: {op}")

        elif isinstance(filter, FilterGroup):
            if not filter.conditions:
                return "", {}

            sub_parts = []
            all_params = {}
            for sub_cond in filter.conditions:
                sub_str, sub_params = process(sub_cond)
                if sub_str:
                    sub_parts.append(sub_str)
                    all_params.update(sub_params)

            if not sub_parts:
                return "", {}

            if filter.operator == "AND":
                combined = " AND ".join(sub_parts)
            else:
                combined = " OR ".join(sub_parts)

            if len(sub_parts) > 1:
                return f"({combined})", all_params
            else:
                return combined, all_params
        else:
            raise TypeError(f"Unsupported condition type: {type(filter)}")

    where_clause, params = process(filter)
    return where_clause, params
