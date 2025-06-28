# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CommandMetadata(ABC):
    def __init__(self, *, path: str, schema: dict[str, Any]) -> None:
        self.__path = path
        self.__schema = schema

    @property
    def path(self) -> str:
        return self.__path

    @property
    def schema(self) -> dict[str, Any]:
        return self.__schema

    @abstractmethod
    def construct(self, arguments: dict[str, Any] | None = None) -> list[str]: ...
