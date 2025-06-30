# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse

from pycli_mcp.metadata.types.argparse import walk_commands


def create_filter_test_parser() -> argparse.ArgumentParser:
    """Return a parser with nested sub-parsers used for filter tests."""

    parser = argparse.ArgumentParser(prog="my-cli")
    subparsers = parser.add_subparsers(dest="command")

    # Root-level sub-command
    parser_subc1 = subparsers.add_parser("subc-1")
    parser_subc1.add_argument("pos1")

    # Nested group with its own sub-command
    parser_subg1 = subparsers.add_parser("subg-1")
    subg1_subparsers = parser_subg1.add_subparsers(dest="subcommand")
    parser_subc2 = subg1_subparsers.add_parser("subc-2")
    parser_subc2.add_argument("pos1")

    return parser


def test_no_commands() -> None:
    parser = argparse.ArgumentParser(prog="cli")

    # Parser with no subcommands should still yield one command
    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": "",
        "properties": {},
        "title": "cli",
        "type": "object",
    }
    assert not metadata.options


def test_root_command() -> None:
    parser = argparse.ArgumentParser(
        prog="cli",
        description="""

            text
                nested

        """,
    )

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
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


def test_nested_commands() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("subc-1")

    subg_1_parser = subparsers.add_parser("subg-1")
    subg_1_subparsers = subg_1_parser.add_subparsers(dest="subcommand")
    subg_1_subparsers.add_parser("subc-2")

    commands = sorted(walk_commands(parser, aggregate="none", name="cli"), key=lambda m: m.path)
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


def test_options() -> None:
    parser = argparse.ArgumentParser(prog="my-cli", description="A test parser.")
    parser.add_argument("pos1", help="Positional argument 1")
    parser.add_argument("--foo", "-f", help="Optional argument foo")
    parser.add_argument("--bar", action="store_true", help="A boolean flag")
    parser.add_argument("--baz", type=int, choices=[1, 2, 3], help="An integer choice")

    commands = list(walk_commands(parser, aggregate="none", name="my-cli"))
    assert len(commands) == 1
    metadata = commands[0]

    schema = metadata.schema.copy()
    if "required" in schema:
        schema["required"].sort()

    assert schema == {
        "type": "object",
        "title": "my-cli",
        "description": "A test parser.",
        "properties": {
            "pos1": {"title": "pos1", "description": "Positional argument 1", "type": "string"},
            "foo": {
                "title": "foo",
                "description": "Optional argument foo",
                "type": "string",
                "default": None,
            },
            "bar": {"title": "bar", "description": "A boolean flag", "type": "boolean", "default": False},
            "baz": {
                "title": "baz",
                "description": "An integer choice",
                "type": "integer",
                "enum": [1, 2, 3],
                "default": None,
            },
        },
        "required": ["pos1"],
    }

    # Option helper assertions -------------------------------------------
    assert metadata.options["pos1"].type == "positional"
    assert metadata.options["foo"].type == "option"
    assert metadata.options["foo"].flag_name == "--foo"
    assert metadata.options["bar"].flag


def test_subparsers() -> None:
    parser = argparse.ArgumentParser(prog="my-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_foo = subparsers.add_parser("foo", description="foo subcommand")
    parser_foo.add_argument("pos1", help="Positional argument 1")

    parser_bar = subparsers.add_parser("bar", description="bar subcommand")
    parser_bar.add_argument("--baz", action="store_true")

    commands = sorted(walk_commands(parser, aggregate="none", name="my-cli"), key=lambda m: m.path)
    assert len(commands) == 2, commands  # Only leaf commands, not the root

    bar_meta, foo_meta = commands

    # Foo schema ---------------------------------------------------------
    foo_schema = foo_meta.schema.copy()
    if "required" in foo_schema:
        foo_schema["required"].sort()

    assert foo_schema == {
        "type": "object",
        "title": "my-cli foo",
        "description": "foo subcommand",
        "properties": {"pos1": {"title": "pos1", "description": "Positional argument 1", "type": "string"}},
        "required": ["pos1"],
    }

    # Bar schema ---------------------------------------------------------
    bar_schema = bar_meta.schema.copy()
    if "required" in bar_schema:
        bar_schema["required"].sort()

    assert bar_schema == {
        "type": "object",
        "title": "my-cli bar",
        "description": "bar subcommand",
        "properties": {"baz": {"title": "baz", "description": "", "type": "boolean", "default": False}},
    }


def test_include_filter() -> None:
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="none", name="my-cli", include=r"^subc-1$"))
    assert len(commands) == 1  # Only included
    paths = {cmd.path for cmd in commands}
    assert "my-cli subc-1" in paths


def test_exclude_filter() -> None:
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="none", name="my-cli", exclude=r"^subg-1"))
    assert len(commands) == 1
    paths = {cmd.path for cmd in commands}
    assert "my-cli subc-1" in paths


def test_exclude_filter_override() -> None:
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="none", name="my-cli", include=r"^subc-1$", exclude=r"^subc-1$"))
    assert len(commands) == 0  # All excluded


def test_aggregate_group() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")

    subc_1_parser = subparsers.add_parser("subc-1")
    subc_1_parser.add_argument("--foo", help="foo help")
    subc_1_parser.add_argument("--bar", help="bar\n\nhelp")
    subc_1_parser.add_argument("--baz", help="baz help")

    subg_1_parser = subparsers.add_parser("subg-1")
    subg_1_subparsers = subg_1_parser.add_subparsers(dest="subcommand")
    subg_1_subparsers.add_parser("subc-2")

    commands = list(walk_commands(parser, aggregate="group", name="cli"))
    assert len(commands) == 2, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": """\
Usage: cli SUBCOMMAND [ARGS]...

# Available subcommands

## subc-1

Usage: cli subc-1 [-h] [--foo FOO] [--bar BAR] [--baz BAZ]

Options:
--foo VALUE  foo help
--bar VALUE  bar

help
--baz VALUE  baz help
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

Usage: cli subg-1 subc-2 [-h]
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
    parser = argparse.ArgumentParser(prog="cli", description="foo bar baz")
    parser.add_argument("--foo", help="foo help")
    parser.add_argument("--bar", help="bar\n\nhelp")
    parser.add_argument("--baz", help="baz help")

    commands = list(walk_commands(parser, aggregate="group", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": """\
Usage: cli [-h] [--foo FOO] [--bar BAR] [--baz BAZ]

foo bar baz

Options:
--foo VALUE  foo help
--bar VALUE  bar

help
--baz VALUE  baz help
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
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="verbose help")
    subparsers = parser.add_subparsers(dest="command")

    subc_1_parser = subparsers.add_parser("subc-1")
    subc_1_parser.add_argument("--foo", help="foo help")
    subc_1_parser.add_argument("--bar", help="bar\n\nhelp")
    subc_1_parser.add_argument("--baz", help="baz help")

    subg_1_parser = subparsers.add_parser("subg-1")
    subg_1_subparsers = subg_1_parser.add_subparsers(dest="subcommand")
    subg_1_subparsers.add_parser("subc-2")

    commands = list(walk_commands(parser, aggregate="root", name="cli"))
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

Usage: cli subc-1 [-h] [--foo FOO] [--bar BAR] [--baz BAZ]

Options:
--foo VALUE  foo help
--bar VALUE  bar

help
--baz VALUE  baz help

## cli subg-1 subc-2

Usage: cli subg-1 subc-2 [-h]
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
    parser = argparse.ArgumentParser(prog="cli", description="foo bar baz")
    parser.add_argument("--foo", help="foo help")
    parser.add_argument("--bar", help="bar\n\nhelp")
    parser.add_argument("--baz", help="baz help")

    commands = list(walk_commands(parser, aggregate="root", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli"
    assert metadata.schema == {
        "description": """\
## cli

Usage: cli [-h] [--foo FOO] [--bar BAR] [--baz BAZ]

foo bar baz

Options:
--foo VALUE  foo help
--bar VALUE  bar

help
--baz VALUE  baz help
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
