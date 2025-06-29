# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse

from pycli_mcp.metadata.types.argparse import walk_commands


def test_basic():
    parser = argparse.ArgumentParser(prog="my-cli", description="My CLI")
    parser.add_argument("pos1", help="Positional 1")
    parser.add_argument("--opt1", required=True, help="Option 1")

    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "my-cli"

    schema = metadata.schema
    if "required" in schema:
        schema["required"].sort()

    assert schema == {
        "type": "object",
        "title": "my-cli",
        "description": "My CLI",
        "properties": {
            "pos1": {"title": "pos1", "description": "Positional 1", "type": "string"},
            "opt1": {"title": "opt1", "description": "Option 1", "type": "string"},
        },
        "required": ["opt1", "pos1"],
    }


def test_types():
    parser = argparse.ArgumentParser(prog="my-cli")
    parser.add_argument("--my-int", type=int)
    parser.add_argument("--my-float", type=float)
    parser.add_argument("--my-bool", action="store_true")
    parser.add_argument("--my-list", action="append")
    parser.add_argument("--my-choice", choices=["a", "b"])

    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema == {
        "type": "object",
        "title": "my-cli",
        "description": "",
        "properties": {
            "my_int": {"title": "my_int", "description": None, "type": "integer", "default": None},
            "my_float": {"title": "my_float", "description": None, "type": "number", "default": None},
            "my_bool": {"title": "my_bool", "description": None, "type": "boolean", "default": False},
            "my_list": {
                "title": "my_list",
                "description": None,
                "type": "array",
                "items": {"type": "string"},
                "default": None,
            },
            "my_choice": {
                "title": "my_choice",
                "description": None,
                "type": "string",
                "enum": ["a", "b"],
                "default": None,
            },
        },
    }


def test_types_with_default():
    parser = argparse.ArgumentParser(prog="my-cli")
    parser.add_argument("--my-int", type=int, default=42)
    parser.add_argument("--my-float", type=float, default=9.81)
    parser.add_argument("--my-bool", action="store_true")
    parser.add_argument("--my-list", action="append")
    parser.add_argument("--my-choice", choices=["a", "b"], default="a")

    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema == {
        "type": "object",
        "title": "my-cli",
        "description": "",
        "properties": {
            "my_int": {"title": "my_int", "description": None, "type": "integer", "default": 42},
            "my_float": {"title": "my_float", "description": None, "type": "number", "default": 9.81},
            "my_bool": {"title": "my_bool", "description": None, "type": "boolean", "default": False},
            "my_list": {
                "title": "my_list",
                "description": None,
                "type": "array",
                "items": {"type": "string"},
                "default": None,
            },
            "my_choice": {
                "title": "my_choice",
                "description": None,
                "type": "string",
                "enum": ["a", "b"],
                "default": "a",
            },
        },
    }


def test_types_with_multiple_values():
    parser = argparse.ArgumentParser(prog="my-cli")
    parser.add_argument("--my-int", type=int, nargs="+")
    parser.add_argument("--my-float", type=float, nargs="+")
    parser.add_argument("--my-list", action="append")
    parser.add_argument("--my-choice", choices=["a", "b"], nargs="+")

    commands = list(walk_commands(parser, aggregate="none"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema == {
        "type": "object",
        "title": "my-cli",
        "description": "",
        "properties": {
            "my_int": {
                "title": "my_int",
                "description": None,
                "type": "array",
                "items": {"type": "integer"},
                "default": None,
            },
            "my_float": {
                "title": "my_float",
                "description": None,
                "type": "array",
                "items": {"type": "number"},
                "default": None,
            },
            "my_list": {
                "title": "my_list",
                "description": None,
                "type": "array",
                "items": {"type": "string"},
                "default": None,
            },
            "my_choice": {
                "title": "my_choice",
                "description": None,
                "type": "array",
                "items": {"type": "string", "enum": ["a", "b"]},
                "default": None,
            },
        },
    }
