"""Render bounded, deterministic native ``epw.x`` input."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_ASSIGNMENT_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\([1-9][0-9]*\))?\Z")
_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
type QeEpwInputScalar = bool | int | float | str


@dataclass(frozen=True, slots=True)
class QeEpwInputAssignment:
    """Declare one typed ``&inputepw`` namelist assignment."""

    name: str
    value: QeEpwInputScalar

    def __post_init__(self) -> None:
        if type(self.name) is not str or _ASSIGNMENT_NAME.fullmatch(self.name) is None:
            raise ValueError("name must be a safe EPW namelist variable")
        if type(self.value) is bool or type(self.value) is int:
            return
        if type(self.value) is float:
            if not math.isfinite(self.value):
                raise ValueError("floating-point values must be finite")
            return
        if type(self.value) is str:
            try:
                self.value.encode("ascii")
            except UnicodeEncodeError as error:
                raise ValueError("string values must be ASCII") from error
            if any(character in self.value for character in ("\0", "\n", "\r")):
                raise ValueError("string values must not contain control newlines")
            return
        raise TypeError("value must be a bool, int, float, or string")


@dataclass(frozen=True, slots=True)
class QeEpwInputConfiguration:
    """Declare provider-native EPW input without selecting scientific policy."""

    assignments: tuple[QeEpwInputAssignment, ...]
    input_filename: str = "epw.in"
    title: str = "--"

    def __post_init__(self) -> None:
        if type(self.assignments) is not tuple or not self.assignments:
            raise ValueError("assignments must be a nonempty tuple")
        if any(type(item) is not QeEpwInputAssignment for item in self.assignments):
            raise TypeError("assignments must contain QeEpwInputAssignment records")
        normalized_names = tuple(item.name.casefold() for item in self.assignments)
        if len(normalized_names) != len(set(normalized_names)):
            raise ValueError("assignment names must be unique")
        by_name = {item.name.casefold(): item for item in self.assignments}
        for required in ("prefix", "outdir"):
            if required not in by_name or type(by_name[required].value) is not str:
                raise ValueError(f"{required} must be declared as a string")
        if (
            type(self.input_filename) is not str
            or _FILENAME.fullmatch(self.input_filename) is None
        ):
            raise ValueError("input_filename must be a safe basename")
        if (
            type(self.title) is not str
            or not self.title
            or self.title != self.title.strip()
        ):
            raise ValueError("title must be nonempty and stripped")
        try:
            self.title.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("title must be ASCII") from error
        if any(character in self.title for character in ("\0", "\n", "\r")):
            raise ValueError("title must not contain control newlines")


@dataclass(frozen=True, slots=True)
class QeEpwRenderedInput:
    """Represent one deterministic, newline-terminated EPW input document."""

    filename: str
    text: str

    def __post_init__(self) -> None:
        if type(self.filename) is not str or _FILENAME.fullmatch(self.filename) is None:
            raise ValueError("filename must be a safe basename")
        if type(self.text) is not str or not self.text.endswith("\n"):
            raise ValueError("text must be a newline-terminated string")
        try:
            self.text.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("text must be ASCII") from error


@dataclass(frozen=True, slots=True)
class QeEpwInputRenderer:
    """Render explicit assignments in caller-provided deterministic order."""

    def render(self, configuration: QeEpwInputConfiguration) -> QeEpwRenderedInput:
        """Return native ``&inputepw`` text without filesystem or process effects."""
        if type(configuration) is not QeEpwInputConfiguration:
            raise TypeError("configuration must be a QeEpwInputConfiguration")
        lines = [configuration.title, "&inputepw"]
        lines.extend(
            f"  {assignment.name} = {_format_value(assignment.value)}"
            for assignment in configuration.assignments
        )
        lines.append("/")
        return QeEpwRenderedInput(
            filename=configuration.input_filename,
            text="\n".join(lines) + "\n",
        )


def _format_value(value: QeEpwInputScalar) -> str:
    if type(value) is bool:
        return ".true." if value else ".false."
    if type(value) is int:
        return str(value)
    if type(value) is float:
        return repr(value)
    if type(value) is str:
        return "'" + value.replace("'", "''") + "'"
    raise TypeError("unsupported EPW input value")
