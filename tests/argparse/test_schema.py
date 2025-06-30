# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse

from pycli_mcp.metadata.types.argparse import walk_commands


def test_basic() -> None:
    parser = argparse.ArgumentParser(prog="my-cli", description="My CLI")
    parser.add_argument("pos1", help="Positional 1")
    parser.add_argument("--opt1", required=True, help="Option 1")

    commands = list(walk_commands(parser, aggregate="none", name="my-cli"))
    metadata = commands[0]

    schema = metadata.schema.copy()
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


def test_types() -> None:
    parser = argparse.ArgumentParser(prog="my-cli")
    parser.add_argument("--my-int", type=int)
    parser.add_argument("--my-float", type=float)
    parser.add_argument("--my-bool", action="store_true")
    parser.add_argument("--my-list", action="append")
    parser.add_argument("--my-choice", choices=["a", "b"])

    commands = list(walk_commands(parser, aggregate="none", name="my-cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema == {
        "type": "object",
        "title": "my-cli",
        "description": "",
        "properties": {
            "my_int": {"title": "my_int", "description": "", "type": "integer", "default": None},
            "my_float": {"title": "my_float", "description": "", "type": "number", "default": None},
            "my_bool": {"title": "my_bool", "description": "", "type": "boolean", "default": False},
            "my_list": {
                "title": "my_list",
                "description": "",
                "type": "array",
                "items": {"type": "string"},
                "default": None,
            },
            "my_choice": {
                "title": "my_choice",
                "description": "",
                "type": "string",
                "enum": ["a", "b"],
                "default": None,
            },
        },
    }


def test_types_with_default() -> None:
    parser = argparse.ArgumentParser(prog="my-cli")
    parser.add_argument("--my-int", type=int, default=42)
    parser.add_argument("--my-float", type=float, default=9.81)
    parser.add_argument("--my-bool", action="store_true")
    parser.add_argument("--my-list", action="append")
    parser.add_argument("--my-choice", choices=["a", "b"], default="a")

    commands = list(walk_commands(parser, aggregate="none", name="my-cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema == {
        "type": "object",
        "title": "my-cli",
        "description": "",
        "properties": {
            "my_int": {"title": "my_int", "description": "", "type": "integer", "default": 42},
            "my_float": {"title": "my_float", "description": "", "type": "number", "default": 9.81},
            "my_bool": {"title": "my_bool", "description": "", "type": "boolean", "default": False},
            "my_list": {
                "title": "my_list",
                "description": "",
                "type": "array",
                "items": {"type": "string"},
                "default": None,
            },
            "my_choice": {
                "title": "my_choice",
                "description": "",
                "type": "string",
                "enum": ["a", "b"],
                "default": "a",
            },
        },
    }


def test_types_with_multiple_values() -> None:
    parser = argparse.ArgumentParser(prog="my-cli")
    parser.add_argument("--my-int", type=int, nargs="+")
    parser.add_argument("--my-float", type=float, nargs="+")
    parser.add_argument("--my-list", action="append")
    parser.add_argument("--my-choice", choices=["a", "b"], nargs="+")

    commands = list(walk_commands(parser, aggregate="none", name="my-cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema == {
        "type": "object",
        "title": "my-cli",
        "description": "",
        "properties": {
            "my_int": {
                "title": "my_int",
                "description": "",
                "type": "array",
                "items": {"type": "integer"},
                "default": None,
            },
            "my_float": {
                "title": "my_float",
                "description": "",
                "type": "array",
                "items": {"type": "number"},
                "default": None,
            },
            "my_list": {
                "title": "my_list",
                "description": "",
                "type": "array",
                "items": {"type": "string"},
                "default": None,
            },
            "my_choice": {
                "title": "my_choice",
                "description": "",
                "type": "array",
                "items": {"type": "string"},
                "default": None,
            },
        },
    }


def test_string_type() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--option", type=str, help="A string option")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["option"] == {
        "title": "option",
        "description": "A string option",
        "type": "string",
        "default": None,
    }
    assert metadata.options["option"].type == "option"
    assert not metadata.options["option"].required
    assert metadata.options["option"].flag_name == "--option"


def test_int_type() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--number", type=int, help="An integer option")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["number"] == {
        "title": "number",
        "description": "An integer option",
        "type": "integer",
        "default": None,
    }


def test_float_type() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--value", type=float, help="A float option")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["value"] == {
        "title": "value",
        "description": "A float option",
        "type": "number",
        "default": None,
    }


def test_bool_flag() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose mode")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["verbose"] == {
        "title": "verbose",
        "description": "Enable verbose mode",
        "type": "boolean",
        "default": False,
    }
    assert metadata.options["verbose"].flag
    assert metadata.options["verbose"].flag_name == "--verbose"


def test_choices() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--mode", choices=["fast", "slow", "medium"], help="Select mode")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["mode"] == {
        "title": "mode",
        "description": "Select mode",
        "type": "string",
        "enum": ["fast", "slow", "medium"],
        "default": None,
    }


def test_positional_argument() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("filename", help="The input file")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["filename"] == {
        "title": "filename",
        "description": "The input file",
        "type": "string",
    }
    assert metadata.options["filename"].type == "positional"
    assert metadata.options["filename"].required


def test_optional_positional() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("files", nargs="*", help="Input files")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["files"] == {
        "title": "files",
        "description": "Input files",
        "type": "array",
        "items": {"type": "string"},
    }
    assert metadata.options["files"].type == "positional"
    assert metadata.options["files"].multiple


def test_required_option() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--config", required=True, help="Configuration file")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["config"] == {
        "title": "config",
        "description": "Configuration file",
        "type": "string",
    }
    assert metadata.options["config"].required
    assert "required" in metadata.schema
    assert "config" in metadata.schema["required"]


def test_default_value() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--port", type=int, default=8080, help="Port number")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["port"] == {
        "title": "port",
        "description": "Port number",
        "type": "integer",
        "default": 8080,
    }


def test_append_action() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--tag", action="append", help="Add a tag")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["tag"] == {
        "title": "tag",
        "description": "Add a tag",
        "type": "array",
        "items": {"type": "string"},
        "default": None,
    }
    assert metadata.options["tag"].multiple


def test_count_action() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["verbose"] == {
        "title": "verbose",
        "description": "Increase verbosity",
        "type": "integer",
        "default": 0,
    }


def test_multiple_values_nargs() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--items", nargs="+", help="One or more items")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.schema["properties"]["items"] == {
        "title": "items",
        "description": "One or more items",
        "type": "array",
        "items": {"type": "string"},
        "default": None,
    }
    assert metadata.options["items"].multiple


def test_short_and_long_flags() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("-f", "--file", help="Input file")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.options["file"].flag_name == "--file"  # Longest flag is used


def test_hidden_option() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--visible", help="Visible option")
    parser.add_argument("--hidden", help=argparse.SUPPRESS)

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert "visible" in metadata.schema["properties"]
    assert "hidden" not in metadata.schema["properties"]


def test_subcommand_with_options() -> None:
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")

    sub_parser = subparsers.add_parser("process", help="Process files")
    sub_parser.add_argument("input", help="Input file")
    sub_parser.add_argument("--output", "-o", required=True, help="Output file")
    sub_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    assert metadata.path == "cli process"
    assert "input" in metadata.schema["properties"]
    assert "output" in metadata.schema["properties"]
    assert "verbose" in metadata.schema["properties"]

    assert metadata.options["input"].type == "positional"
    assert metadata.options["output"].type == "option"
    assert metadata.options["output"].required
    assert metadata.options["verbose"].flag

    assert metadata.schema["required"] == ["input", "output"]


def test_custom_type() -> None:
    def port_type(value: str) -> int:
        port = int(value)
        if not 1 <= port <= 65535:
            msg = f"Port must be 1-65535, got {port}"
            raise argparse.ArgumentTypeError(msg)
        return port

    parser = argparse.ArgumentParser(prog="cli")
    parser.add_argument("--port", type=port_type, help="Port number (1-65535)")

    commands = list(walk_commands(parser, aggregate="none", name="cli"))
    assert len(commands) == 1, commands

    metadata = commands[0]
    # Custom types default to string
    assert metadata.schema["properties"]["port"] == {
        "title": "port",
        "description": "Port number (1-65535)",
        "type": "string",
        "default": None,
    }
