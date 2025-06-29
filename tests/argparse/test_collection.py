# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse

from pycli_mcp.metadata.types.argparse import walk_commands


def test_no_options():
    parser = argparse.ArgumentParser(prog="my-cli")
    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 1
    metadata = commands[0]
    assert metadata.path == "my-cli"
    assert not metadata.options
    assert metadata.schema == {
        "type": "object",
        "title": "my-cli",
        "description": "",
        "properties": {},
    }


def test_options():
    parser = argparse.ArgumentParser(prog="my-cli", description="A test parser.")
    parser.add_argument("pos1", help="Positional argument 1")
    parser.add_argument("--foo", "-f", help="Optional argument foo")
    parser.add_argument("--bar", action="store_true", help="A boolean flag")
    parser.add_argument("--baz", type=int, choices=[1, 2, 3], help="An integer choice")

    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 1
    metadata = commands[0]

    assert metadata.path == "my-cli"

    schema = metadata.schema
    if "required" in schema:
        schema["required"].sort()

    assert schema == {
        "type": "object",
        "title": "my-cli",
        "description": "A test parser.",
        "properties": {
            "pos1": {"title": "pos1", "description": "Positional argument 1", "type": "string"},
            "foo": {"title": "foo", "description": "Optional argument foo", "type": "string", "default": None},
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

    assert "pos1" in metadata.options
    assert metadata.options["pos1"].is_positional
    assert "foo" in metadata.options
    assert not metadata.options["foo"].is_positional
    assert metadata.options["foo"].flag_name == "--foo"
    assert "bar" in metadata.options
    assert metadata.options["bar"].is_flag


def test_subparsers():
    parser = argparse.ArgumentParser(prog="my-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    parser_foo = subparsers.add_parser("foo", description="foo subcommand")
    parser_foo.add_argument("pos1", help="Positional argument 1")

    parser_bar = subparsers.add_parser("bar", description="bar subcommand")
    parser_bar.add_argument("--baz", action="store_true")

    commands = sorted(walk_commands(parser, aggregate="none"), key=lambda m: m.path)
    assert len(commands) == 3

    root_meta, bar_meta, foo_meta = commands

    schema = root_meta.schema
    if "required" in schema:
        schema["required"].sort()

    assert schema == {
        "type": "object",
        "title": "my-cli",
        "description": "",
        "properties": {
            "command": {
                "title": "command",
                "description": None,
                "type": "string",
                "enum": ["foo", "bar"],
            },
        },
        "required": ["command"],
    }

    schema = foo_meta.schema
    if "required" in schema:
        schema["required"].sort()

    assert schema == {
        "type": "object",
        "title": "my-cli foo",
        "description": "foo subcommand",
        "properties": {"pos1": {"title": "pos1", "description": "Positional argument 1", "type": "string"}},
        "required": ["pos1"],
    }

    schema = bar_meta.schema
    if "required" in schema:
        schema["required"].sort()

    assert schema == {
        "type": "object",
        "title": "my-cli bar",
        "description": "bar subcommand",
        "properties": {
            "baz": {"title": "baz", "description": None, "type": "boolean", "default": False},
        },
    }


def create_filter_test_parser():
    parser = argparse.ArgumentParser(prog="my-cli")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("subc-1")

    subg_1 = subparsers.add_parser("subg-1")
    subg_1_subparsers = subg_1.add_subparsers(dest="subcommand")
    subg_1_subparsers.add_parser("subc-2")

    return parser


def test_include_filter():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="none", include=r"^subc-1$"))
    assert len(commands) == 2
    paths = {cmd.path for cmd in commands}
    assert "my-cli" in paths
    assert "my-cli subc-1" in paths


def test_exclude_filter():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="none", exclude=r"^subg-1"))
    assert len(commands) == 2
    paths = {cmd.path for cmd in commands}
    assert "my-cli" in paths
    assert "my-cli subc-1" in paths


def test_exclude_filter_override():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="none", include=r"^subc-1$", exclude=r"^subc-1$"))
    assert len(commands) == 1
    assert commands[0].path == "my-cli"


def test_aggregate_group():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="group"))
    assert len(commands) == 2

    command_map = {cmd.path: cmd for cmd in commands}
    assert "my-cli" in command_map
    assert "my-cli subg-1" in command_map

    root_group = command_map["my-cli"]
    assert root_group.schema["properties"]["subcommand"]["enum"] == ["subc-1", "subg-1"]

    sub_group = command_map["my-cli subg-1"]
    assert sub_group.schema["properties"]["subcommand"]["enum"] == ["subc-2"]


def test_aggregate_root():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="root"))
    assert len(commands) == 1
    command = commands[0]
    assert command.path == "my-cli"
    assert "usage: my-cli" in command.schema["description"].lower()
    assert "my-cli subc-1" in command.schema["description"]
    assert "my-cli subg-1" in command.schema["description"]
    assert "my-cli subg-1 subc-2" in command.schema["description"]


def test_aggregate_root_include():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="root", include=r"subc-1$"))
    assert len(commands) == 1
    command = commands[0]
    assert command.path == "my-cli"
    assert "usage: my-cli" in command.schema["description"].lower()
    assert "my-cli subc-1" in command.schema["description"]
    assert "my-cli subg-1" not in command.schema["description"]
    assert "my-cli subg-1 subc-2" not in command.schema["description"]


def test_aggregate_root_exclude():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="root", exclude=r"^subg-1"))
    assert len(commands) == 1
    command = commands[0]
    assert command.path == "my-cli"
    assert "usage: my-cli" in command.schema["description"].lower()
    assert "my-cli subc-1" in command.schema["description"]
    assert "my-cli subg-1" not in command.schema["description"]
    assert "my-cli subg-1 subc-2" not in command.schema["description"]


def test_aggregate_group_include():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="group", include=r"subc-1$"))
    assert len(commands) == 1
    command = commands[0]
    assert command.path == "my-cli"
    assert command.schema["properties"]["subcommand"]["enum"] == ["subc-1"]


def test_aggregate_group_exclude():
    parser = create_filter_test_parser()
    commands = list(walk_commands(parser, aggregate="group", exclude=r"^subg-1"))
    assert len(commands) == 1
    command = commands[0]
    assert command.path == "my-cli"
    assert command.schema["properties"]["subcommand"]["enum"] == ["subc-1"]
