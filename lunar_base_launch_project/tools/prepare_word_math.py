r"""Prepare the mathematical model Markdown for Pandoc DOCX conversion.

Pandoc's DOCX writer converts a useful subset of TeX math to Word OMML.  The
source document is written in readable Markdown and uses some old TeX idioms
(``\rm`` and ``\over``) that are fine for humans but weak for OMML conversion.
This script normalizes only math code blocks and leaves the source document
unchanged.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


MATH_BLOCK = re.compile(r"```math\r?\n(.*?)\r?\n```", re.DOTALL)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_word_math.py SOURCE.md OUTPUT.md")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    text = source.read_text(encoding="utf-8")

    def repl(match: re.Match[str]) -> str:
        body = normalize_math(match.group(1))
        return "$$\n" + body.strip() + "\n$$"

    output.write_text(MATH_BLOCK.sub(repl, text), encoding="utf-8")


def normalize_math(value: str) -> str:
    value = replace_rm(value)
    value = replace_over(value)
    return value


def replace_rm(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        body = match.group(1).replace(r"\ ", " ").strip()
        return r"{\mathrm{" + body + r"}}"

    return re.sub(r"\{\\rm\s+([^{}]+)\}", repl, value)


def replace_over(value: str) -> str:
    while r"\over" in value:
        pos = value.find(r"\over")
        start = find_fraction_start(value, pos)
        end = find_fraction_end(value, pos + len(r"\over"))
        if start is None or end is None:
            break
        numerator = value[start + 1 : pos].strip()
        denominator = value[pos + len(r"\over") : end].strip()
        replacement = r"{\frac{" + numerator + "}{" + denominator + "}}"
        value = value[:start] + replacement + value[end + 1 :]
    return value


def find_fraction_start(value: str, over_pos: int) -> int | None:
    depth = 0
    for idx in range(over_pos - 1, -1, -1):
        char = value[idx]
        if char == "}":
            depth += 1
        elif char == "{":
            if depth == 0:
                return idx
            depth -= 1
    return None


def find_fraction_end(value: str, idx: int) -> int | None:
    depth = 0
    while idx < len(value):
        char = value[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            if depth == 0:
                return idx
            depth -= 1
        idx += 1
    return None


if __name__ == "__main__":
    main()
