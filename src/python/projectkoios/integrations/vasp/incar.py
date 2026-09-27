"""Immutable VASP INCAR records with bounded generic syntax handling."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MAX_INCAR_BYTES = 10_000_000
_TAG = re.compile(r"[A-Z][A-Z0-9_]*(?:/[A-Z0-9_]+)*")
_BLOCK_NAME = re.compile(r"[A-Z0-9_]+")
INCAR_DOCUMENTATION_URL = "https://vasp.at/wiki/INCAR"
INCAR_TAG_DOCUMENTATION_URL = "https://vasp.at/wiki/Category:INCAR_tag"


class IncarSyntaxError(ValueError):
    """Report malformed or unsupported INCAR syntax."""


@dataclass(frozen=True, slots=True)
class IncarAssignment:
    """Represent one normalized INCAR tag and its lexical value."""

    tag: str
    value: str

    def __post_init__(self) -> None:
        if type(self.tag) is not str or not _TAG.fullmatch(self.tag):
            raise ValueError("INCAR tag must be normalized uppercase tag syntax")
        if type(self.value) is not str:
            raise TypeError("INCAR value must be a string")
        if not self.value or self.value != self.value.strip():
            raise ValueError("INCAR value must be nonempty and stripped")
        if "\r" in self.value or "\t" in self.value:
            raise ValueError("INCAR value must not contain carriage returns or tabs")


@dataclass(frozen=True, slots=True)
class IncarFile:
    """Represent ordered INCAR assignments without applying VASP defaults."""

    assignments: tuple[IncarAssignment, ...]

    def __post_init__(self) -> None:
        if type(self.assignments) is not tuple:
            raise TypeError("INCAR assignments must be a tuple")
        if any(
            type(assignment) is not IncarAssignment for assignment in self.assignments
        ):
            raise TypeError("INCAR assignments must contain IncarAssignment values")


@dataclass(frozen=True, slots=True)
class IncarParser:
    """Parse bounded INCAR text without maintaining a version-fragile tag whitelist."""

    def parse(self, text: str) -> IncarFile:
        """Parse generic official INCAR syntax into normalized assignments."""
        if type(text) is not str:
            raise TypeError("INCAR text must be a string")
        try:
            encoded = text.encode("ascii")
        except UnicodeEncodeError as error:
            raise IncarSyntaxError(
                "INCAR text must contain plain ASCII only"
            ) from error
        if len(encoded) > _MAX_INCAR_BYTES:
            raise IncarSyntaxError("INCAR text exceeds the byte limit")
        if "\r" in text:
            raise IncarSyntaxError("INCAR text must use Unix line endings")
        if "\t" in text:
            raise IncarSyntaxError("INCAR text must not contain tabs")

        tokens = _tokenize(text)
        prefixes: list[str] = []
        assignments: list[IncarAssignment] = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token == "}":
                if not prefixes:
                    raise IncarSyntaxError("INCAR contains an unmatched closing brace")
                prefixes.pop()
                index += 1
                continue
            if token == "{":
                raise IncarSyntaxError("INCAR block is missing its name")
            if index + 1 < len(tokens) and tokens[index + 1] == "{":
                block_name = token.strip().upper()
                if not _BLOCK_NAME.fullmatch(block_name):
                    raise IncarSyntaxError("INCAR block name is invalid")
                prefixes.append(block_name)
                index += 2
                continue
            if "=" not in token:
                index += 1
                continue
            raw_tag, raw_value = token.split("=", 1)
            tag = raw_tag.strip().upper()
            value = raw_value.strip()
            if prefixes:
                tag = "/".join((*prefixes, tag))
            try:
                assignment = IncarAssignment(tag=tag, value=value)
            except (TypeError, ValueError) as error:
                raise IncarSyntaxError(
                    f"invalid INCAR assignment for {tag!r}"
                ) from error
            assignments.append(assignment)
            index += 1

        if prefixes:
            raise IncarSyntaxError("INCAR contains an unterminated nested-tag block")
        return IncarFile(assignments=tuple(assignments))


@dataclass(frozen=True, slots=True)
class IncarWriter:
    """Render normalized INCAR assignments using direct tag syntax."""

    def render(self, input_file: IncarFile) -> str:
        """Return deterministic INCAR text with one assignment per statement."""
        if type(input_file) is not IncarFile:
            raise TypeError("input_file must be an IncarFile")
        if not input_file.assignments:
            return ""
        return "".join(
            f"{assignment.tag} = {assignment.value}\n"
            for assignment in input_file.assignments
        )


def _tokenize(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    buffer: list[str] = []
    quote: str | None = None
    index = 0

    def flush() -> None:
        token = "".join(buffer).strip()
        buffer.clear()
        if token:
            tokens.append(token)

    while index < len(text):
        character = text[index]
        if quote is not None:
            buffer.append(character)
            if character == quote:
                quote = None
            index += 1
            continue
        if character in {'"', "'"}:
            quote = character
            buffer.append(character)
            index += 1
            continue
        if character in {"#", "!"}:
            while index < len(text) and text[index] != "\n":
                index += 1
            continue
        if character == "\\":
            cursor = index + 1
            while cursor < len(text) and text[cursor] == " ":
                cursor += 1
            if cursor < len(text) and text[cursor] == "\n":
                if cursor != index + 1:
                    raise IncarSyntaxError(
                        "INCAR continuation backslash must end the physical line"
                    )
                while buffer and buffer[-1] == " ":
                    buffer.pop()
                buffer.append(" ")
                index = cursor + 1
                while index < len(text) and text[index] == " ":
                    index += 1
                continue
            buffer.append(character)
            index += 1
            continue
        if character in {";", "\n"}:
            flush()
            index += 1
            continue
        if character in {"{", "}"}:
            flush()
            tokens.append(character)
            index += 1
            continue
        buffer.append(character)
        index += 1

    if quote is not None:
        raise IncarSyntaxError("INCAR contains an unterminated quoted value")
    flush()
    return tuple(tokens)
