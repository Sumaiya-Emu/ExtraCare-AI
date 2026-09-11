"""Shared, robust JSON-object extraction from LLM text output.

Used by every agent/tool that asks the configured LLM for structured JSON. A naive greedy
regex (\\{.*\\}) breaks the moment the model adds any trailing text containing
a brace; this does real bracket-depth matching instead, and ignores braces
that appear inside string literals.
"""
import json
from typing import Union


class JSONExtractionError(ValueError):
    """Raised when no balanced JSON object can be found in the model's output."""


def _normalize_message_content(content: Union[str, list, None]) -> str:
    """AIMessage.content is a plain string for most models, but some providers return a list of content-block dicts instead —
    e.g. [{"type": "text", "text": "...", "extras": {...}}]. Normalize both shapes
    to a plain string so every caller can keep treating it as text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


def extract_json_object(content: Union[str, list, None]) -> dict:
    text = _normalize_message_content(content)
    start = text.find("{")
    if start == -1:
        raise JSONExtractionError("No JSON object found in model output.")

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])

    raise JSONExtractionError("Unbalanced JSON object in model output.")
