# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import typer

from pycli_mcp.metadata.query import walk_commands


def test_root_command() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli() -> None:
        # fmt: off
        """

            text
                nested

        """
        # fmt: on

    commands = list(walk_commands(app, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "text\nnested",
        "properties": {},
        "title": "cli",
        "type": "object",
    }


def test_nested_commands() -> None:
    app = typer.Typer(name="cli", add_completion=False)

    @app.command()
    def subc_1() -> None:
        pass

    subg_1 = typer.Typer(add_completion=False)
    app.add_typer(subg_1, name="subg-1")

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = sorted(walk_commands(app, aggregate="none"), key=lambda m: m.path)
    assert len(commands) == 2, commands

    metadata1 = commands[0]
    assert metadata1.path == "cli subc-1"
    assert metadata1.schema == {
        "description": "",
        "properties": {},
        "title": "cli subc-1",
        "type": "object",
    }

    metadata2 = commands[1]
    assert metadata2.path == "cli subg-1 subc-2"
    assert metadata2.schema == {
        "description": "",
        "properties": {},
        "title": "cli subg-1 subc-2",
        "type": "object",
    }


def test_hidden_command() -> None:
    app = typer.Typer(name="cli", add_completion=False)

    @app.command(hidden=True)
    def subc_1() -> None:
        pass

    subg_1 = typer.Typer(add_completion=False)
    app.add_typer(subg_1, name="subg-1")

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(app, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli subg-1 subc-2"
    assert metadata.schema == {
        "description": "",
        "properties": {},
        "title": "cli subg-1 subc-2",
        "type": "object",
    }


def test_include_filter() -> None:
    app = typer.Typer(name="cli", add_completion=False)

    @app.command()
    def subc_1() -> None:
        pass

    subg_1 = typer.Typer(add_completion=False)
    app.add_typer(subg_1, name="subg-1")

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(app, aggregate="none", include=r"^subc-1$"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli subc-1"
    assert metadata.schema == {
        "description": "",
        "properties": {},
        "title": "cli subc-1",
        "type": "object",
    }


def test_exclude_filter() -> None:
    app = typer.Typer(name="cli", add_completion=False)

    @app.command()
    def subc_1() -> None:
        pass

    subg_1 = typer.Typer(add_completion=False)
    app.add_typer(subg_1, name="subg-1")

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(app, aggregate="none", exclude=r"^subg-1"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli subc-1"
    assert metadata.schema == {
        "description": "",
        "properties": {},
        "title": "cli subc-1",
        "type": "object",
    }


def test_exclude_filter_override() -> None:
    app = typer.Typer(name="cli", add_completion=False)

    @app.command()
    def subc_1() -> None:
        pass

    subg_1 = typer.Typer(add_completion=False)
    app.add_typer(subg_1, name="subg-1")

    @subg_1.command()
    def subc_2() -> None:
        pass

    assert not list(walk_commands(app, aggregate="none", include=r"^subc-1$", exclude=r"^subc-1"))


def test_aggregate_group() -> None:
    app = typer.Typer(name="cli", add_completion=False)

    @app.command()
    def subc_1(
        *,
        foo: str | None = typer.Option(None, "--foo", help="foo help"),
        bar: str | None = typer.Option(None, "--bar", help="bar\n\nhelp"),
        baz: str | None = typer.Option(None, "--baz", help="baz help"),
    ) -> None:
        pass

    subg_1 = typer.Typer(add_completion=False)
    app.add_typer(subg_1, name="subg-1")

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(app, aggregate="group"))
    assert len(commands) == 2, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": """\
Usage: cli SUBCOMMAND [ARGS]...

# Available subcommands

## subc-1

Usage: cli subc-1 [OPTIONS]

Options:
--foo TEXT  foo help
--bar TEXT  bar

            help
--baz TEXT  baz help
""",
        "properties": {
            "args": {
                "type": "array",
                "items": {
                    "type": "string",
                },
                "title": "args",
                "description": "The arguments to pass to the subcommand",
            },
            "subcommand": {
                "type": "string",
                "enum": ["subc-1"],
                "title": "subcommand",
                "description": "The subcommand to execute",
            },
        },
        "title": "cli",
        "type": "object",
    }

    metadata = commands[1]
    assert metadata.path == "cli subg-1"
    assert metadata.schema["properties"] == {
        "args": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "title": "args",
            "description": "The arguments to pass to the subcommand",
        },
        "subcommand": {
            "type": "string",
            "enum": ["subc-2"],
            "title": "subcommand",
            "description": "The subcommand to execute",
        },
    }


def test_aggregate_group_only_root_command() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(
        *,
        foo: str | None = typer.Option(None, "--foo", help="foo help"),
        bar: str | None = typer.Option(None, "--bar", help="bar\n\nhelp"),
        baz: str | None = typer.Option(None, "--baz", help="baz help"),
    ) -> None:
        """
        foo bar baz
        """

    commands = list(walk_commands(app, aggregate="group"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": """\
Usage: cli [OPTIONS]

foo bar baz

Options:
--foo TEXT  foo help
--bar TEXT  bar

            help
--baz TEXT  baz help
""",
        "properties": {
            "args": {
                "type": "array",
                "items": {
                    "type": "string",
                },
                "title": "args",
                "description": "The arguments to pass to the command",
            },
        },
        "title": "cli",
        "type": "object",
    }


def test_aggregate_root() -> None:
    app = typer.Typer(name="cli", add_completion=False)

    @app.callback()
    def callback(
        *,
        verbose: int = typer.Option(0, "--verbose", "-v", count=True, show_default=False, help="verbose help"),
    ) -> None:
        pass

    @app.command()
    def subc_1(
        *,
        foo: str | None = typer.Option(None, "--foo", help="foo help"),
        bar: str | None = typer.Option(None, "--bar", help="bar\n\nhelp"),
        baz: str | None = typer.Option(None, "--baz", help="baz help"),
    ) -> None:
        pass

    subg_1 = typer.Typer(add_completion=False)
    app.add_typer(subg_1, name="subg-1")

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(app, aggregate="root"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": """\
# cli

Usage: cli [OPTIONS] SUBCOMMAND [ARGS]...

Options:
-v, --verbose  verbose help

## cli subc-1

Usage: cli subc-1 [OPTIONS]

Options:
--foo TEXT  foo help
--bar TEXT  bar

            help
--baz TEXT  baz help

## cli subg-1 subc-2

Usage: cli subg-1 subc-2 [OPTIONS]
""",
        "properties": {
            "args": {
                "type": "array",
                "items": {
                    "type": "string",
                },
                "title": "args",
                "description": "The arguments to pass to the root command",
            },
        },
        "title": "cli",
        "type": "object",
    }


def test_aggregate_root_no_subcommands() -> None:
    app = typer.Typer(add_completion=False)

    @app.command()
    def cli(
        *,
        foo: str | None = typer.Option(None, "--foo", help="foo help"),
        bar: str | None = typer.Option(None, "--bar", help="bar\n\nhelp"),
        baz: str | None = typer.Option(None, "--baz", help="baz help"),
    ) -> None:
        """
        foo bar baz
        """

    commands = list(walk_commands(app, aggregate="root"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": """\
## cli

Usage: cli [OPTIONS]

foo bar baz

Options:
--foo TEXT  foo help
--bar TEXT  bar

            help
--baz TEXT  baz help
""",
        "properties": {
            "args": {
                "type": "array",
                "items": {
                    "type": "string",
                },
                "title": "args",
                "description": "The arguments to pass to the root command",
            },
        },
        "title": "cli",
        "type": "object",
    }
