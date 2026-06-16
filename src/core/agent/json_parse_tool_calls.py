import json
import re
import uuid
from typing import Any


def parse_tool_calls_from_text(text: str) -> list[dict[str, Any]]:
    if not text:
        return []

    tool_calls = []

    markdown_json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
    if markdown_json_match:
        try:
            data = json.loads(markdown_json_match.group(1))
            if isinstance(data, list):
                for item in data:
                    if "name" in item and "arguments" in item:
                        tool_calls.append(_make_tool_call(item["name"], item["arguments"]))

            elif isinstance(data, dict):
                if "name" in data and "arguments" in data:
                    tool_calls.append(_make_tool_call(data["name"], data["arguments"]))

        except (json.JSONDecodeError, TypeError, KeyError):
            pass

    if not tool_calls:
        javascript_match = re.search(r'```(?:javascript|js)\s*\n(.*?)\n```', text, re.DOTALL)
        if javascript_match:
            js_code = javascript_match.group(1)
            for match in re.finditer(r'(\w+)\(([^)]*)\)', js_code):
                tool_name = match.group(1)
                args_str = match.group(2)
                args_dict = {}
                positional = re.findall(r'"([^"]*)"', args_str)
                named = dict(re.findall(r'(\w+)\s*=\s*("[^"]*"|\d+)', args_str))
                if positional:
                    args_dict["query"] = positional[0]
                if len(positional) > 1:
                    try:
                        args_dict["k"] = int(positional[1])
                    except ValueError:
                        pass
                for key, val in named.items():
                    if val.startswith('"'):
                        val = val.strip('"')
                    else:
                        val = int(val) if val.isdigit() else val
                    args_dict[key] = val
                if args_dict:
                    tool_calls.append(_make_tool_call(tool_name, args_dict))

    if not tool_calls:
        json_objects = re.findall(
            r'\{[^{}]*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{[^{}]+\})[^{}]*\}',
            text
        )
        for tool_name, args_str in json_objects:
            try:
                args = json.loads(args_str)
                tool_calls.append(_make_tool_call(tool_name, args))
            except (json.JSONDecodeError, TypeError, KeyError):
                continue

    if not tool_calls:
        func_match = re.findall(r'(\w+)\(([^)]*)\)', text)
        for tool_name, args_str in func_match:
            args_dict = {}
            for arg in re.findall(r'(\w+)\s*=\s*"([^"]*)"', args_str):
                args_dict[arg[0]] = arg[1]
            for arg in re.findall(r'(\w+)\s*=\s*(\d+)', args_str):
                if arg[0] not in args_dict:
                    args_dict[arg[0]] = int(arg[1])
            if args_dict:
                tool_calls.append(_make_tool_call(tool_name, args_dict))

    return tool_calls


def _make_tool_call(name: str, arguments: dict) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "args": arguments
    }