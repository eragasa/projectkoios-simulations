"""Typed Quantum ESPRESSO output title."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeControlCard,
)


class QeTitleCard(QeControlCard):
    """Represent one typed ``title`` assignment in ``&CONTROL``."""

    __slots__ = ("title",)

    title: str

    def __init__(self, title: str = " ") -> None:
        if type(title) is not str:
            raise TypeError("title must be a string")
        if "'" in title or "\n" in title or "\r" in title:
            raise ValueError("title must be unquoted and contain no line terminators")
        try:
            title.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("title must contain ASCII characters only") from error
        QeControlCard.__init__(self, lines=(f"title = '{title}'",))
        object.__setattr__(self, "title", title)

    def __setattr__(self, name: str, value: object) -> None:
        raise FrozenInstanceError(f"cannot assign to field {name!r}")
