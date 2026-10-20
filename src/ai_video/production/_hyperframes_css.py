"""Pure normalization of generated HyperFrames CSS for exact source audit.

This parser neither executes CSS nor grants source acceptance; the caller still
compares the complete normalized model against reconstructed compiler output.
"""
from __future__ import annotations

import re


def _split_css_rules(css: str) -> tuple[tuple[str, str], ...]:
    rules: list[tuple[str, str]] = []
    cursor = 0
    length = len(css)
    while cursor < length:
        while cursor < length and css[cursor].isspace():
            cursor += 1
        if cursor == length:
            break
        opening = css.find("{", cursor)
        if opening < 0:
            raise ValueError("CSS contains an unterminated rule.")
        header = css[cursor:opening].strip()
        if not header:
            raise ValueError("CSS contains an empty rule header.")
        depth = 1
        end = opening + 1
        while end < length and depth:
            if css[end] == "{":
                depth += 1
            elif css[end] == "}":
                depth -= 1
            end += 1
        if depth:
            raise ValueError("CSS contains an unterminated rule body.")
        rules.append((header, css[opening + 1 : end - 1]))
        cursor = end
    return tuple(rules)


def _parse_declarations(body: str) -> tuple[tuple[str, str], ...]:
    declarations: list[tuple[str, str]] = []
    # Generated url(data:font/...;base64,...) contains a semicolon inside url().
    # All declarations remain compared against the exact compiler output.
    for item in re.split(r";(?![^()]*\))", body):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError("CSS contains an invalid declaration.")
        name, value = item.split(":", 1)
        declarations.append((name.strip().lower(), value.strip()))
    if len({name for name, _ in declarations}) != len(declarations):
        raise ValueError("CSS contains a duplicate declaration.")
    return tuple(declarations)


def parse_css_model(styles: list[str]) -> tuple[object, ...]:
    model: list[object] = []
    for css in styles:
        if re.search(r"(?i)(?<![-\w])@import\b", css):
            raise ValueError("CSS imports are not allowed in HyperFrames source.")
        for header, body in _split_css_rules(css):
            if header.lower().startswith("@keyframes "):
                name = header.split(maxsplit=1)[1]
                stops = tuple(
                    (stop_header.replace(" ", ""), _parse_declarations(stop_body))
                    for stop_header, stop_body in _split_css_rules(body)
                )
                model.append(("keyframes", name, stops))
            else:
                model.append(("rule", header.replace(" ", ""), _parse_declarations(body)))
    return tuple(model)
