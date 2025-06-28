# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer
from typer.main import get_command

from pycli_mcp.metadata.types.click import walk_commands


class Choices(str, Enum):
    BAR = "bar"
    BAZ = "baz"


def test_no_help_text() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, foo: bool = False) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "foo": {
                "default": False,
                "title": "foo",
                "type": "boolean",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert len(metadata.options) == 1


def test_boolean() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, foo: bool = typer.Option(False, help="foo help")) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "foo": {
                "default": False,
                "description": "foo help",
                "title": "foo",
                "type": "boolean",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_string() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, foo: str | None = typer.Option(None, help="foo help")) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "foo": {
                "default": None,
                "description": "foo help",
                "title": "foo",
                "type": "string",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_integer() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, foo: int | None = typer.Option(None, help="foo help")) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "foo": {
                "default": None,
                "description": "foo help",
                "title": "foo",
                "type": "integer",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_float() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, foo: float | None = typer.Option(None, help="foo help")) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "foo": {
                "default": None,
                "description": "foo help",
                "title": "foo",
                "type": "number",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_choice() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, foo: Choices | None = typer.Option(None, help="foo help")) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "foo": {
                "default": None,
                "description": "foo help",
                "enum": ["bar", "baz"],
                "title": "foo",
                "type": "string",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_path() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, foo: Path | None = typer.Option(None, help="foo help")) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "foo": {
                "default": None,
                "description": "foo help",
                "title": "foo",
                "type": "string",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_multiple_allowed() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(
        *,
        foo: list[str] | None = typer.Option(None, help="foo help"),
        bar: list[int] | None = typer.Option(None, help="bar help"),
        baz: list[float] | None = typer.Option(None, help="baz help"),
    ) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "bar": {
                "default": None,
                "description": "bar help",
                "items": {"type": "integer"},
                "title": "bar",
                "type": "array",
            },
            "baz": {
                "default": None,
                "description": "baz help",
                "items": {"type": "number"},
                "title": "baz",
                "type": "array",
            },
            "foo": {
                "default": None,
                "description": "foo help",
                "items": {"type": "string"},
                "title": "foo",
                "type": "array",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["bar", "baz", "foo"]


def test_required_option() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, foo: str = typer.Option(..., help="foo help")) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "foo": {
                "description": "foo help",
                "title": "foo",
                "type": "string",
            },
        },
        "required": ["foo"],
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_argument() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, arg: str) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "arg": {
                "title": "arg",
                "type": "string",
            },
        },
        "required": ["arg"],
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["arg"]


def test_optional_argument() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, arg: str | None = None) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "arg": {
                "default": None,
                "title": "arg",
                "type": "string",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["arg"]


def test_arbitrary_arguments() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, args: list[str] | None = None) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "args": {
                "default": None,
                "items": {"type": "string"},
                "title": "args",
                "type": "array",
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["args"]


def test_arbitrary_arguments_required() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(*, args: list[str]) -> None:
        pass

    commands = list(walk_commands(get_command(app), aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {
            "args": {
                "items": {"type": "string"},
                "title": "args",
                "type": "array",
            },
        },
        "required": ["args"],
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["args"]
