# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse

from pycli_mcp.metadata.types.argparse import walk_commands


def test_no_arguments() -> None:
    parser = argparse.ArgumentParser(prog="cli")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct() == ["cli"]


def test_single_option() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--name")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"name": "foo"}) == ["cli", "--name", "foo"]


def test_short_option() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("-n", "--name")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    # Should use the long form
    assert metadata.construct({"name": "foo"}) == ["cli", "--name", "foo"]


def test_boolean_flag() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--verbose", action="store_true")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"verbose": True}) == ["cli", "--verbose"]
    assert metadata.construct({"verbose": False}) == ["cli"]


def test_positional_argument() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("filename")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"filename": "test.txt"}) == ["cli", "test.txt"]


def test_multiple_positionals() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("source")
    parser.add_argument("dest")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"source": "input.txt", "dest": "output.txt"}) == ["cli", "input.txt", "output.txt"]


def test_options_and_positionals() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--output", "-o")
    parser.add_argument("filename")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"verbose": True, "output": "out.txt", "filename": "in.txt"}) == [
        "cli",
        "--verbose",
        "--output",
        "out.txt",
        "in.txt",
    ]


def test_list_positional() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("files", nargs="*")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"files": ["a.txt", "b.txt", "c.txt"]}) == ["cli", "a.txt", "b.txt", "c.txt"]


def test_multiple_values_option() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--tags", nargs="+")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"tags": ["tag1", "tag2", "tag3"]}) == [
        "cli",
        "--tags",
        "tag1",
        "--tags",
        "tag2",
        "--tags",
        "tag3",
    ]


def test_subcommand() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")

    sub_parser = subparsers.add_parser("process")
    sub_parser.add_argument("--verbose", action="store_true")
    sub_parser.add_argument("input")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"verbose": True, "input": "file.txt"}) == ["cli", "process", "--verbose", "file.txt"]


def test_aggregate_group_subcommand() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("sub1")
    subparsers.add_parser("sub2")

    commands = list(walk_commands(parser, aggregate="group", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"subcommand": "sub1", "args": ["--verbose", "file.txt"]}) == [
        "cli",
        "sub1",
        "--verbose",
        "file.txt",
    ]


def test_aggregate_root() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--verbose", action="store_true")

    commands = list(walk_commands(parser, aggregate="root", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"args": ["--verbose", "sub", "arg1", "arg2"]}) == [
        "cli",
        "--verbose",
        "sub",
        "arg1",
        "arg2",
    ]


def test_integer_conversion() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--port", type=int)
    parser.add_argument("--count", type=int)

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    metadata = commands[0]

    assert metadata.construct({"port": 8080, "count": 42}) == ["cli", "--port", "8080", "--count", "42"]
