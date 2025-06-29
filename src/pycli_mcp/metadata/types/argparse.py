# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import re
from typing import TYPE_CHECKING, Any, Literal

from pycli_mcp.metadata.interface import CommandMetadata

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


class ArgparseCommandMetadata(CommandMetadata):
    def __init__(self, *, path: str, schema: dict[str, Any], options: dict[str, ArgparseCommandOption]) -> None:
        super().__init__(path=path, schema=schema)

        self.__options = options

    @property
    def options(self) -> dict[str, ArgparseCommandOption]:
        return self.__options

    def construct(self, arguments: dict[str, Any] | None = None) -> list[str]:
        command = self.path.split()
        if not arguments:
            return command

        positional_args: list[str] = []
        optional_args: list[str] = []

        for option_name, value in arguments.items():
            option = self.options[option_name]
            if option.is_positional:
                if isinstance(value, list):
                    positional_args.extend(map(str, value))
                else:
                    positional_args.append(str(value))
            elif option.is_flag:
                if value:
                    optional_args.append(option.flag_name)
            elif isinstance(value, list):
                for v in value:
                    optional_args.extend((option.flag_name, str(v)))
            else:
                optional_args.extend((option.flag_name, str(value)))

        command.extend(optional_args)
        command.extend(positional_args)
        return command


class ArgparseCommandOption:
    __slots__ = ("__description", "__flag_name", "__is_flag", "__is_positional", "__required")

    def __init__(
        self,
        *,
        description: str,
        required: bool,
        flag_name: str = "",
        is_flag: bool = False,
        is_positional: bool = False,
    ) -> None:
        self.__description = description
        self.__required = required
        self.__flag_name = flag_name
        self.__is_flag = is_flag
        self.__is_positional = is_positional

    @property
    def description(self) -> str:
        return self.__description

    @property
    def required(self) -> bool:
        return self.__required

    @property
    def flag_name(self) -> str:
        return self.__flag_name

    @property
    def is_flag(self) -> bool:
        return self.__is_flag

    @property
    def is_positional(self) -> bool:
        return self.__is_positional


def get_parser_description(parser: argparse.ArgumentParser) -> str:
    return parser.description or ""


def get_longest_flag(flags: Sequence[str]) -> str:
    return sorted(flags, key=len)[-1]  # noqa: FURB192


def walk_parsers(
    parser: argparse.ArgumentParser,
    *,
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    _prog: str | None = None,
) -> Iterator[tuple[str, argparse.ArgumentParser]]:
    if name is None:
        name = parser.prog

    if _prog is None:
        name = name or parser.prog
        _prog = name

    subcommand_path = " ".join(name.split(" ")[1:])

    # Exclusion takes precedence
    if exclude and subcommand_path and re.search(exclude, subcommand_path):
        return

    # If it's the root command or matches the include pattern, yield it.
    if name == _prog or not include or re.search(include, subcommand_path):
        yield name, parser

    # Always recurse to check for deeper matches
    for action in parser._actions:  # noqa: SLF001
        if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
            for choice, subparser in action.choices.items():
                yield from walk_parsers(
                    subparser, name=f"{name} {choice}", include=include, exclude=exclude, _prog=_prog
                )


def walk_commands_no_aggregation(
    command: argparse.ArgumentParser,
    *,
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    strict_types: bool = False,
) -> Iterator[ArgparseCommandMetadata]:
    for path, parser in walk_parsers(command, name=name, include=include, exclude=exclude):
        properties: dict[str, Any] = {}
        options: dict[str, ArgparseCommandOption] = {}

        for action in parser._actions:  # noqa: SLF001
            if isinstance(action, (argparse._HelpAction, argparse._VersionAction)):  # noqa: SLF001
                continue

            prop: dict[str, Any] = {"title": action.dest, "description": action.help}

            is_positional = not action.option_strings
            option_name = action.dest
            flag_name = ""
            if not is_positional:
                flag_name = get_longest_flag(action.option_strings)

            option_data: dict[str, Any] = {
                "description": action.help or "",
                "required": action.required,
                "flag_name": flag_name,
                "is_positional": is_positional,
            }

            if isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):  # noqa: SLF001
                prop["type"] = "boolean"
                option_data["is_flag"] = True
            elif action.nargs in {"?", "*", "+"} or isinstance(action, argparse._AppendAction):  # noqa: SLF001
                prop["type"] = "array"
                prop["items"] = {}
                if action.type is int:
                    prop["items"]["type"] = "integer"
                elif action.type is float:
                    prop["items"]["type"] = "number"
                else:
                    prop["items"]["type"] = "string"
                if action.choices:
                    prop["items"]["enum"] = list(action.choices)
            elif action.type is int:
                prop["type"] = "integer"
                if action.choices:
                    prop["enum"] = list(action.choices)
            elif action.type is float:
                prop["type"] = "number"
                if action.choices:
                    prop["enum"] = list(action.choices)
            elif strict_types:
                msg = f"Unknown type: {action.type}"
                raise ValueError(msg)
            else:
                prop["type"] = "string"
                if action.choices:
                    prop["enum"] = list(action.choices)

            if not action.required or (action.default is not None and action.default != argparse.SUPPRESS):
                prop["default"] = action.default

            properties[option_name] = prop
            options[option_name] = ArgparseCommandOption(**option_data)

        schema = {
            "type": "object",
            "properties": properties,
            "title": path,
            "description": get_parser_description(parser),
        }
        required = [option_name for option_name, option in options.items() if option.required]
        if required:
            schema["required"] = required

        yield ArgparseCommandMetadata(path=path, schema=schema, options=options)


def walk_commands_group_aggregation(
    command: argparse.ArgumentParser,
    *,
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
) -> Iterator[ArgparseCommandMetadata]:
    filtered_paths_and_parsers = list(walk_parsers(command, name=name, include=include, exclude=exclude))

    groups: dict[str, dict[str, argparse.ArgumentParser]] = {}
    for path, parser in filtered_paths_and_parsers:
        if " " not in path:
            continue

        parent_path = " ".join(path.split(" ")[:-1])
        command_name = path.split(" ")[-1]

        groups.setdefault(parent_path, {})[command_name] = parser

    for group_path, commands in groups.items():
        description = f"""\
Usage: {group_path} SUBCOMMAND [ARGS]...

# Available subcommands
"""
        for command_name, parser in commands.items():
            description += f"""
## {command_name}

{parser.format_help()}
"""

        yield ArgparseCommandMetadata(
            path=group_path,
            schema={
                "type": "object",
                "properties": {
                    "subcommand": {
                        "type": "string",
                        "enum": list(commands.keys()),
                        "title": "subcommand",
                        "description": "The subcommand to execute",
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "title": "args",
                        "description": "The arguments to pass to the subcommand",
                    },
                },
                "title": group_path,
                "description": description.lstrip(),
            },
            options={
                "subcommand": ArgparseCommandOption(
                    is_positional=True,
                    required=True,
                    description="The subcommand to execute",
                ),
                "args": ArgparseCommandOption(
                    is_positional=True,
                    required=False,
                    description="The arguments to pass to the subcommand",
                ),
            },
        )


def walk_commands_root_aggregation(
    command: argparse.ArgumentParser,
    *,
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
) -> Iterator[ArgparseCommandMetadata]:
    prog = name or command.prog
    filtered_paths_and_parsers = list(walk_parsers(command, name=name, include=include, exclude=exclude))

    description = ""
    for _, parser in filtered_paths_and_parsers:
        description += f"""
## {parser.prog}

{parser.format_help()}
"""

    yield ArgparseCommandMetadata(
        path=prog,
        schema={
            "type": "object",
            "properties": {
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "title": "args",
                    "description": "The arguments to pass to the root command",
                },
            },
            "title": prog,
            "description": description.lstrip(),
        },
        options={
            "args": ArgparseCommandOption(
                is_positional=True,
                required=False,
                description="The arguments to pass to the root command",
            ),
        },
    )


def walk_commands(
    command: argparse.ArgumentParser,
    *,
    aggregate: Literal["root", "group", "none"],
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    strict_types: bool = False,
) -> Iterator[ArgparseCommandMetadata]:
    if aggregate == "root":
        yield from walk_commands_root_aggregation(
            command,
            name=name,
            include=include,
            exclude=exclude,
        )
    elif aggregate == "group":
        yield from walk_commands_group_aggregation(
            command,
            name=name,
            include=include,
            exclude=exclude,
        )
    elif aggregate == "none":
        yield from walk_commands_no_aggregation(
            command,
            name=name,
            include=include,
            exclude=exclude,
            strict_types=strict_types,
        )
    else:
        msg = f"Invalid aggregate value: {aggregate}"
        raise ValueError(msg)
