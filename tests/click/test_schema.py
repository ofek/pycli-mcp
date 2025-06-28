# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import click

from pycli_mcp.metadata.types.click import walk_commands


def test_no_help_text() -> None:
    @click.command()
    @click.option("--foo", is_flag=True)
    def cli(*, foo: bool) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.option("--foo", is_flag=True, help="foo help")
    def cli(*, foo: bool) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.option("--foo", help="foo help")
    def cli(*, foo: str | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.option("--foo", type=int, help="foo help")
    def cli(*, foo: int | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.option("--foo", type=float, help="foo help")
    def cli(*, foo: float | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.option("--foo", type=click.Choice(["bar", "baz"]), help="foo help")
    def cli(*, foo: str | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.option("--foo", type=click.Path(), help="foo help")
    def cli(*, foo: str | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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


def test_file() -> None:
    @click.command()
    @click.option("--foo", type=click.File(), help="foo help")
    def cli(*, foo: str | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.option("--foo", multiple=True, help="foo help")
    @click.option("--bar", type=int, multiple=True, help="bar help")
    @click.option("--baz", type=float, multiple=True, help="baz help")
    def cli(*, foo: tuple[str, ...] | None, bar: tuple[int, ...] | None, baz: tuple[float, ...] | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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


def test_container() -> None:
    @click.command()
    @click.option("--foo", type=(str, str), help="foo help")
    def cli(*, foo: tuple[str, str] | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_multi_container() -> None:
    @click.command()
    @click.option("--foo", type=(str, str), multiple=True, help="foo help")
    def cli(*, foo: tuple[tuple[str, str], ...] | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
                "type": "array",
                "items": {"type": "array", "items": {"type": "string"}},
            },
        },
        "title": "cli",
        "type": "object",
    }
    assert sorted(metadata.options) == ["foo"]


def test_required_option() -> None:
    @click.command()
    @click.option("--foo", required=True, help="foo help")
    def cli(*, foo: str) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.argument("arg")
    def cli(*, arg: str) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.argument("arg", required=False)
    def cli(*, arg: str | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.argument("args", nargs=-1)
    def cli(*, args: tuple[str, ...] | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
    @click.command()
    @click.argument("args", nargs=-1, required=True)
    def cli(*, args: tuple[str, ...]) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
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
