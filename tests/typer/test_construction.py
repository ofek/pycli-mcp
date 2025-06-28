# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

from enum import Enum

import typer

from pycli_mcp.metadata.query import walk_commands


class Choices(str, Enum):
    BAR = "bar"
    BAZ = "baz"


def test_root_no_options() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli() -> None:
        pass

    commands = list(walk_commands(app, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({}) == ["cli"]


def test_nested_no_options() -> None:
    app = typer.Typer(name="cli", add_completion=False)
    subg = typer.Typer(add_completion=False)
    app.add_typer(subg, name="subg")

    @subg.command()
    def subc() -> None:
        pass

    commands = list(walk_commands(app, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({}) == ["cli", "subg", "subc"]


def test_options() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(
        *,
        string: str | None = typer.Option(None, "--string", "-s"),
        integer: int | None = typer.Option(None, "--integer", "-i"),
        number: float | None = typer.Option(None, "--number", "-n"),
        flag: bool = typer.Option(False, "--flag", "-f"),
        choice: Choices | None = typer.Option(None, "--choice", "-c"),
        multiple: list[str] | None = typer.Option(None, "--multiple", "-m"),
        unused_option: str | None = typer.Option(None, "--unused-option", "-u"),
    ) -> None:
        pass

    commands = list(walk_commands(app, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({
        "string": "foo",
        "integer": 1,
        "number": 1.0,
        "flag": True,
        "choice": "bar",
        "multiple": ["m2", "m1"],
    }) == [
        "cli",
        "--flag",
        "--string",
        "foo",
        "--integer",
        "1",
        "--number",
        "1.0",
        "--choice",
        "bar",
        "--multiple",
        "m2",
        "--multiple",
        "m1",
    ]


def test_arguments() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, arg: str, args: list[str] | None = typer.Argument(None)) -> None:
        pass

    commands = list(walk_commands(app, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({
        "arg": "a1",
        "args": ["a2", "a3"],
    }) == ["cli", "--", "a1", "a2", "a3"]


def test_placement() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(
        *,
        args: list[str] = typer.Argument(...),
        option: str | None = typer.Option(None, "--option", "-o"),
    ) -> None:
        pass

    commands = list(walk_commands(app, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({
        "args": ["a1", "a2"],
        "option": "o1",
    }) == ["cli", "--option", "o1", "--", "a1", "a2"]
