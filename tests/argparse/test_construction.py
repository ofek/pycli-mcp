# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse

from pycli_mcp.metadata.types.argparse import walk_commands


def test_basic():
    parser = argparse.ArgumentParser(prog="my-cli")
    parser.add_argument("pos1")
    parser.add_argument("--foo", "-f")
    parser.add_argument("--bar", action="store_true")

    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    command = metadata.construct({
        "pos1": "val1",
        "foo": "val2",
        "bar": True,
    })
    assert command == ["my-cli", "--foo", "val2", "--bar", "val1"]


def test_list_option():
    parser = argparse.ArgumentParser(prog="my-cli")
    parser.add_argument("--foo", action="append")

    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    command = metadata.construct({
        "foo": ["a", "b"],
    })
    assert command == ["my-cli", "--foo", "a", "--foo", "b"]


def test_subparser():
    parser = argparse.ArgumentParser(prog="my-cli")
    subparsers = parser.add_subparsers(dest="command")
    parser_foo = subparsers.add_parser("foo")
    parser_foo.add_argument("pos1")

    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 2, commands

    metadata = commands[1]
    command = metadata.construct({
        "pos1": "val1",
    })
    assert command == ["my-cli", "foo", "val1"]
