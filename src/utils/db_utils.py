from src.data.db.filter import FilterCondition, FilterGroup


def validate_strings_exist(
    strings: str | list[str],
    context: str = "",
    max_errors: int = 20,
    return_str: bool = False,
) -> str | None:
    prefix = f"[{context}] " if context else ""
    if not strings:
        return f"{prefix}Argument cannot be empty"

    if isinstance(strings, list):
        error_lines = []
        for i, value in enumerate(strings):
            if not value:
                error_lines.append(f"Item {i}: string is empty.")
                if len(error_lines) >= max_errors:
                    error_lines.append("... (and more errors, truncated)")
                    break
        if error_lines:
            msg = f"{prefix}Validation errors for strings:\n" + "\n".join(error_lines)
            if return_str:
                return msg
            else:
                raise ValueError(msg)


def validate_dict_exist(
    data: dict | list[dict],
    context: str = "",
    max_errors: int = 20,
    return_str: bool = False,
) -> str | None:
    prefix = f"[{context}] " if context else ""
    if not data:
        return f"{prefix}Data cannot be empty."
    if isinstance(data, list):
        empty_indices = []
        for i, item in enumerate(data):
            if not item:
                empty_indices.append(i)
                if len(empty_indices) >= max_errors:
                    empty_indices.append("...")
                    break

        if empty_indices:
            if len(empty_indices) == 1:
                msg = f"{prefix}Item at index {empty_indices[0]} is empty."
            else:
                indices_str = ", ".join(str(i) for i in empty_indices if i != "...")
                msg = f"{prefix}Items at indices {indices_str} are empty."
                if "..." in empty_indices:
                    msg += " (and more errors, truncated)"

            if return_str:
                return msg
            else:
                raise ValueError(msg)


def validate_dict_contains_consistent_keys(
    data_list: list[dict],
    context: str = "",
    max_errors: int = 20,
    return_str: bool = False,
) -> str | None:
    prefix = f"[{context}] " if context else ""
    first_keys = set(data_list[0].keys())
    error_lines = []
    for i, data in enumerate(data_list[1:], start=1):
        current_keys = set(data.keys())
        if first_keys != current_keys:
            missing = first_keys - current_keys
            extra = current_keys - first_keys
            parts = []
            if missing:
                parts.append(f"missing keys: {sorted(missing)}")
            if extra:
                parts.append(f"extra keys: {sorted(extra)}")
            error_lines.append(f"[Item {i}] Inconsistent keys: " + ", ".join(parts))
            if len(error_lines) >= max_errors:
                error_lines.append("... (and more errors, truncated)")
                break

    if error_lines:
        msg = (
            f"{prefix}Inconsistent keys across dictionaries.\n"
            f"Expected keys (from first item): {sorted(first_keys)}\n" +
            "\n".join(error_lines)
        )
        if return_str:
            return msg
        else:
            raise ValueError(msg)


def validate_all_conflict_properties_in_properties(
    properties: dict | list[dict],
    conflict_properties: list[str],
    max_errors: int = 20,
    return_str: bool = False,
) -> str | None:
    error_lines = []
    if isinstance(properties, dict):
        for prop in conflict_properties:
            if prop not in properties:
                error_lines.append(f"Conflict property '{prop}' is missing in properties")
                if len(error_lines) >= max_errors:
                    error_lines.append("... (and more errors, truncated)")
                    break
            elif properties[prop] is None:
                error_lines.append(f"Conflict property '{prop}' is None")
                if len(error_lines) >= max_errors:
                    error_lines.append("... (and more errors, truncated)")
                    break

    else:
        for i, item in enumerate(properties):
            stop = False
            for prop in conflict_properties:
                if prop not in item:
                    error_lines.append(f"[Item {i}] Conflict property '{prop}' is missing")
                    if len(error_lines) >= max_errors:
                        error_lines.append("... (and more errors, truncated)")
                        stop = True
                        break
                elif item[prop] is None:
                    error_lines.append(f"[Item {i}] Conflict property '{prop}' is None")
                    if len(error_lines) >= max_errors:
                        error_lines.append("... (and more errors, truncated)")
                        stop = True
                        break
            if stop:
                break
    if error_lines:
        msg = (
            f"[Upsert properties] Validation errors for conflict properties.\n"
            f"Expected conflict properties: {sorted(conflict_properties)}\n" +
            "\n".join(error_lines)
        )
        if return_str:
            return msg
        else:
            raise ValueError(msg)


def validate_match_not_contains_duplicates(
    match: list[dict],
    max_errors: int = 20,
    return_str: bool = False,
) -> str | None:
    seen = {}
    duplicates = []
    for i, item in enumerate(match):
        key = frozenset(item.items())
        if key in seen:
            duplicates.append(f"index {i} duplicates index {seen[key]}")
            if len(duplicates) >= max_errors:
                duplicates.append("... (and more errors, truncated)")
                break
        else:
            seen[key] = i
    if duplicates:
        msg = f"[Match] Duplicate match conditions found: {', '.join(duplicates)}"
        if return_str:
            return msg
        else:
            raise ValueError(msg)


def validate_filter_exist(
    filter: FilterCondition | FilterGroup,
    max_errors: int = 20,
    return_str: bool = False,
) -> str | None:
    error_lines = []

    def collect(cond, path: str = ""):
        if isinstance(cond, FilterCondition):
            if not cond.field:
                error_lines.append(f"{path}Field name cannot be empty")
        elif isinstance(cond, FilterGroup):
            if not cond.conditions:
                error_lines.append(f"{path}Filter group cannot be empty")
            else:
                for i, sub in enumerate(cond.conditions):
                    collect(sub, f"{path}[{i}]")
        else:
            error_lines.append(f"{path}Unsupported condition type: {type(cond)}")

    collect(filter)
    if error_lines:
        if len(error_lines) > max_errors:
            msg = (
                "[Filter] Filter validation errors:\n" +
                "\n".join(error_lines[:max_errors]) +
                "... (and more errors, truncated)"
            )
        else:
            msg = (
                "[Filter] Filter validation errors:\n" +
                "\n".join(error_lines[:max_errors])
            )

        if return_str:
            return msg
        else:
            raise ValueError(msg)
