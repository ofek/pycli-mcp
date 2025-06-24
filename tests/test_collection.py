# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import click

from click_mcp_server.metadata import walk_commands


def test_no_commands() -> None:
    @click.group()
    def cli() -> None:
        pass

    assert not list(walk_commands(cli))


def test_root_command() -> None:
    @click.command()
    def cli() -> None:
        # fmt: off
        """

            text
                nested

        """
        # fmt: on

    commands = list(walk_commands(cli))
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

    commands = sorted(walk_commands(cli), key=lambda m: m.path)
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

    commands = sorted(walk_commands(cli), key=lambda m: m.path)
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

    commands = list(walk_commands(cli))
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

    commands = list(walk_commands(cli))
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

    commands = list(walk_commands(cli, include=r"^subc-1$"))
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

    commands = list(walk_commands(cli, exclude=r"^subg-1"))
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

    assert not list(walk_commands(cli, include=r"^subc-1$", exclude=r"^subc-1"))
