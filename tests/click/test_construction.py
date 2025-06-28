# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import click

from pycli_mcp.metadata.query import walk_commands


def test_root_no_options() -> None:
    @click.command()
    def cli() -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({}) == ["cli"]


def test_nested_no_options() -> None:
    @click.group()
    def cli() -> None:
        pass

    @cli.command()
    def sub() -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({}) == ["cli", "sub"]


def test_options() -> None:
    @click.command()
    @click.option("--string", "-s")
    @click.option("--integer", "-i", type=int)
    @click.option("--number", "-n", type=float)
    @click.option("--flag", "-f", is_flag=True)
    @click.option("--choice", "-c", type=click.Choice(["bar", "baz"]))
    @click.option("--multiple", "-m", multiple=True)
    @click.option("--container", "-t", type=(str, str))
    @click.option("--multi-container", "-mt", type=(str, str), multiple=True)
    @click.option("--unused-option", "-u")
    def cli(
        *,
        string: str | None,
        integer: int | None,
        number: float | None,
        flag: bool,
        choice: str | None,
        multiple: tuple[str, ...] | None,
        container: tuple[str, str] | None,
        multi_container: tuple[tuple[str, str], ...] | None,
        unused_option: str | None,
    ) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({
        "string": "foo",
        "integer": 1,
        "number": 1.0,
        "flag": True,
        "choice": "bar",
        "multiple": ["m2", "m1"],
        "container": ["t2", "t1"],
        "multi_container": [["mc2", "mc1"], ["mc4", "mc3"]],
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
        "--container",
        "t2",
        "t1",
        "--multi-container",
        "mc2",
        "mc1",
        "--multi-container",
        "mc4",
        "mc3",
    ]


def test_arguments() -> None:
    @click.command()
    @click.argument("arg")
    @click.argument("args", nargs=-1)
    def cli(*, arg: str, args: tuple[str, ...] | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({
        "arg": "a1",
        "args": ["a2", "a3"],
    }) == ["cli", "--", "a1", "a2", "a3"]


def test_placement() -> None:
    @click.command()
    @click.argument("args", nargs=-1, required=True)
    @click.option("--option", "-o")
    def cli(*, args: tuple[str, ...], option: str | None) -> None:
        pass

    commands = list(walk_commands(cli, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.construct({
        "args": ["a1", "a2"],
        "option": "o1",
    }) == ["cli", "--option", "o1", "--", "a1", "a2"]
