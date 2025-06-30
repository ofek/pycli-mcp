# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import click

from pycli_mcp.metadata.types.click import walk_commands


def test_no_commands() -> None:
    @click.group()
    def cli() -> None:
        pass

    assert not list(walk_commands(cli, aggregate="none"))


def test_root_command() -> None:
    @click.command()
    def cli() -> None:
        # fmt: off
        """

            text
                nested

        """
        # fmt: on

    commands = list(walk_commands(cli, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "text\n    nested",
        "properties": {},
        "title": "cli",
        "type": "object",
    }
    assert not metadata.options


def test_dynamic() -> None:
    from pycli_mcp.metadata.query import walk_commands

    def func() -> click.Command:
        @click.command()
        def cli() -> None:
            # fmt: off
            """

                text
                    nested

            """
            # fmt: on

        return cli

    commands = list(walk_commands(func, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "text\n    nested",
        "properties": {},
        "title": "cli",
        "type": "object",
    }


def test_nested_commands() -> None:
    @click.group()
    def cli() -> None:
        pass

    @cli.command()
    def subc_1() -> None:
        pass

    @cli.group()
    def subg_1() -> None:
        pass

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = sorted(walk_commands(cli, aggregate="none"), key=lambda m: m.path)
    assert len(commands) == 2, commands

    metadata1 = commands[0]
    assert metadata1.path == "cli subc-1"
    assert metadata1.schema == {
        "description": "",
        "properties": {},
        "title": "cli subc-1",
        "type": "object",
    }
    assert not metadata1.options

    metadata2 = commands[1]
    assert metadata2.path == "cli subg-1 subc-2"
    assert metadata2.schema == {
        "description": "",
        "properties": {},
        "title": "cli subg-1 subc-2",
        "type": "object",
    }
    assert not metadata2.options


def test_name_overrides() -> None:
    @click.group(name="cmd")
    def cli() -> None:
        pass

    @cli.command(name="foo")
    def subc_1() -> None:
        pass

    @cli.group(name="bar")
    def subg_1() -> None:
        pass

    @subg_1.command(name="baz")
    def subc_2() -> None:
        pass

    commands = sorted(walk_commands(cli, aggregate="none"), key=lambda m: m.path)
    assert len(commands) == 2, commands

    metadata1 = commands[0]
    assert metadata1.path == "cmd bar baz"
    assert metadata1.schema == {
        "description": "",
        "properties": {},
        "title": "cmd bar baz",
        "type": "object",
    }
    assert not metadata1.options

    metadata2 = commands[1]
    assert metadata2.path == "cmd foo"
    assert metadata2.schema == {
        "description": "",
        "properties": {},
        "title": "cmd foo",
        "type": "object",
    }
    assert not metadata2.options


def test_hidden_command() -> None:
    @click.group()
    def cli() -> None:
        pass

    @cli.command(hidden=True)
    def subc_1() -> None:
        pass

    @cli.group()
    def subg_1() -> None:
        pass

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli subg-1 subc-2"
    assert metadata.schema == {
        "description": "",
        "properties": {},
        "title": "cli subg-1 subc-2",
        "type": "object",
    }
    assert not metadata.options


def test_hidden_group() -> None:
    @click.group()
    def cli() -> None:
        pass

    @cli.command()
    def subc_1() -> None:
        pass

    @cli.group(hidden=True)
    def subg_1() -> None:
        pass

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli subc-1"
    assert metadata.schema == {
        "description": "",
        "properties": {},
        "title": "cli subc-1",
        "type": "object",
    }
    assert not metadata.options


def test_include_filter() -> None:
    @click.group()
    def cli() -> None:
        pass

    @cli.command()
    def subc_1() -> None:
        pass

    @cli.group()
    def subg_1() -> None:
        pass

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none", include=r"^subc-1$"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli subc-1"
    assert metadata.schema == {
        "description": "",
        "properties": {},
        "title": "cli subc-1",
        "type": "object",
    }
    assert not metadata.options


def test_exclude_filter() -> None:
    @click.group()
    def cli() -> None:
        pass

    @cli.command()
    def subc_1() -> None:
        pass

    @cli.group()
    def subg_1() -> None:
        pass

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none", exclude=r"^subg-1"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli subc-1"
    assert metadata.schema == {
        "description": "",
        "properties": {},
        "title": "cli subc-1",
        "type": "object",
    }
    assert not metadata.options


def test_exclude_filter_override() -> None:
    @click.group()
    def cli() -> None:
        pass

    @cli.command()
    def subc_1() -> None:
        pass

    @cli.group()
    def subg_1() -> None:
        pass

    @subg_1.command()
    def subc_2() -> None:
        pass

    assert not list(walk_commands(cli, aggregate="none", include=r"^subc-1$", exclude=r"^subc-1"))


def test_aggregate_group() -> None:
    @click.group()
    def cli() -> None:
        pass

    @cli.command()
    @click.option("--foo", help="foo help")
    @click.option("--bar", help="bar\n\nhelp")
    @click.option("--baz", help="baz help")
    def subc_1(*, foo: str | None, bar: str | None, baz: str | None) -> None:
        pass

    @cli.group()
    def subg_1() -> None:
        pass

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(cli, aggregate="group"))
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
    assert metadata.schema == {
        "description": """\
Usage: cli subg-1 SUBCOMMAND [ARGS]...

# Available subcommands

## subc-2

Usage: cli subg-1 subc-2 [OPTIONS]
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
                "enum": ["subc-2"],
                "title": "subcommand",
                "description": "The subcommand to execute",
            },
        },
        "title": "cli subg-1",
        "type": "object",
    }


def test_aggregate_group_only_root_command() -> None:
    @click.command()
    @click.option("--foo", help="foo help")
    @click.option("--bar", help="bar\n\nhelp")
    @click.option("--baz", help="baz help")
    def cli(*, foo: str | None, bar: str | None, baz: str | None) -> None:
        """
        foo bar baz
        """

    commands = list(walk_commands(cli, aggregate="group"))
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
    @click.group()
    @click.option("--verbose", "-v", count=True, help="verbose help")
    def cli(*, verbose: int) -> None:
        pass

    @cli.command()
    @click.option("--foo", help="foo help")
    @click.option("--bar", help="bar\n\nhelp")
    @click.option("--baz", help="baz help")
    def subc_1(*, foo: str | None, bar: str | None, baz: str | None) -> None:
        pass

    @cli.group()
    def subg_1() -> None:
        pass

    @subg_1.command()
    def subc_2() -> None:
        pass

    commands = list(walk_commands(cli, aggregate="root"))
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
    @click.command()
    @click.option("--foo", help="foo help")
    @click.option("--bar", help="bar\n\nhelp")
    @click.option("--baz", help="baz help")
    def cli(*, foo: str | None, bar: str | None, baz: str | None) -> None:
        """
        foo bar baz
        """

    commands = list(walk_commands(cli, aggregate="root"))
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
