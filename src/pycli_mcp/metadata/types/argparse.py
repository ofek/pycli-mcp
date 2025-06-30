# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import inspect
import re
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from pycli_mcp.metadata.interface import CommandMetadata

if TYPE_CHECKING:
    from collections.abc import Iterator


class ArgparseCommandOptionKwargs(TypedDict, total=False):
    type: Literal["positional", "option"]
    required: bool
    description: str
    multiple: bool
    flag: bool
    flag_name: str


class ArgparseCommandMetadata(CommandMetadata):
    def __init__(self, *, path: str, schema: dict[str, Any], options: dict[str, ArgparseCommandOption]) -> None:
        super().__init__(path=path, schema=schema)

        self.__options = options

    @property
    def options(self) -> dict[str, ArgparseCommandOption]:
        return self.__options

    def construct(self, arguments: dict[str, Any] | None = None) -> list[str]:
        command = self.path.split()
        if arguments and self.options:
            args: list[Any] = []
            opts: list[Any] = []
            flags: list[str] = []
            for option_name, value in arguments.items():
                option = self.options[option_name]
                if option.type == "positional":
                    if isinstance(value, list):
                        args.extend(value)
                    else:
                        args.append(value)
                    continue

                if option.flag:
                    if value:
                        flags.append(option.flag_name)
                elif option.multiple:
                    for v in value:
                        opts.extend((option.flag_name, v))
                else:
                    opts.extend((option.flag_name, value))

            command.extend(flags)
            command.extend(map(str, opts))
            command.extend(map(str, args))

        return command


class ArgparseCommandOption:
    __slots__ = ("__description", "__flag", "__flag_name", "__multiple", "__required", "__type")

    def __init__(
        self,
        *,
        type: Literal["positional", "option"],  # noqa: A002
        required: bool,
        description: str,
        multiple: bool = False,
        flag: bool = False,
        flag_name: str = "",
    ) -> None:
        self.__type = type
        self.__required = required
        self.__description = description
        self.__multiple = multiple
        self.__flag = flag
        self.__flag_name = flag_name

    @property
    def type(self) -> Literal["positional", "option"]:
        return self.__type

    @property
    def required(self) -> bool:
        return self.__required

    @property
    def description(self) -> str:
        return self.__description

    @property
    def multiple(self) -> bool:
        return self.__multiple

    @property
    def flag(self) -> bool:
        return self.__flag

    @property
    def flag_name(self) -> str:
        return self.__flag_name


def get_longest_flag(flags: list[str]) -> str:
    if not flags:
        return ""
    return sorted(flags, key=len)[-1]  # noqa: FURB192


def get_parser_description(parser: argparse.ArgumentParser) -> str:
    if parser.description:
        return inspect.cleandoc(parser.description).strip()
    return ""


def get_parser_options_block(parser: argparse.ArgumentParser) -> str:
    lines: list[str] = []

    # Get all actions except help and subparsers
    for action in parser._actions:
        if action.help == argparse.SUPPRESS or action.dest == "help" or isinstance(action, argparse._SubParsersAction):
            continue

        # Build option string
        option_strings = list(action.option_strings) if action.option_strings else []
        if not option_strings and action.dest != argparse.SUPPRESS:
            # Positional argument
            option_strings = [action.dest]

        if not option_strings:
            continue

        opt_str = ", ".join(option_strings)

        # Add metavar for non-flag options
        if hasattr(action, "metavar") and action.metavar:
            opt_str += f" {action.metavar}"
        elif (
            not isinstance(action, argparse._StoreTrueAction)
            and not isinstance(action, argparse._StoreFalseAction)
            and not isinstance(action, argparse._CountAction)
        ):
            if hasattr(action, "type") and action.type:
                type_name = getattr(action.type, "__name__", "VALUE").upper()
                opt_str += f" {type_name}"
            else:
                opt_str += " VALUE"

        # Add help text
        help_text = action.help or ""
        if help_text:
            lines.append(f"{opt_str}  {help_text}")
        else:
            lines.append(opt_str)

    return "\n".join(lines)


def get_parser_full_usage(parser: argparse.ArgumentParser, name: str) -> str:
    # Format usage - temporarily override prog to use our name
    original_prog = parser.prog
    try:
        parser.prog = name
        usage = parser.format_usage().strip()
        if usage.startswith("usage: "):
            usage = usage[7:]
        usage = f"Usage: {usage}"
    finally:
        parser.prog = original_prog

    if description := get_parser_description(parser):
        usage += f"\n\n{description}"

    if options := get_parser_options_block(parser):
        usage += f"\n\nOptions:\n{options}"

    return usage


def walk_parser_tree(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    parent_path: str = "",
) -> Iterator[tuple[str, argparse.ArgumentParser]]:
    """Walk through parser tree including subparsers."""
    # Check if this parser has subparsers
    subparsers_action = None
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparsers_action = action
            break

    if not subparsers_action:
        # This is a leaf parser
        command_path = f"{parent_path} {name}".strip() if parent_path else name
        subcommand_path = " ".join(command_path.split()[1:]) if parent_path else ""

        if exclude is not None and subcommand_path and re.search(exclude, subcommand_path):
            return
        if include is not None and subcommand_path and not re.search(include, subcommand_path):
            return

        yield (command_path, parser)
        return

    # This parser has subparsers, iterate through them
    current_path = f"{parent_path} {name}".strip() if parent_path else name
    for subcommand_name, subparser in subparsers_action.choices.items():
        yield from walk_parser_tree(
            subparser,
            name=subcommand_name,
            include=include,
            exclude=exclude,
            parent_path=current_path,
        )


def walk_commands_no_aggregation(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    strict_types: bool = False,
) -> Iterator[ArgparseCommandMetadata]:
    for command_path, subparser in walk_parser_tree(parser, name=name, include=include, exclude=exclude):
        properties: dict[str, Any] = {}
        options: dict[str, ArgparseCommandOption] = {}

        # Process all actions
        for action in subparser._actions:
            if action.help == argparse.SUPPRESS or action.dest == "help":
                continue

            # Determine if this is a positional or optional argument
            is_positional = not action.option_strings

            option_name: str
            option_data: ArgparseCommandOptionKwargs
            if is_positional:
                option_name = action.dest
                option_data = {
                    "type": "positional",
                    "required": action.required if hasattr(action, "required") else True,
                    "multiple": action.nargs in {"*", "+"} if hasattr(action, "nargs") else False,
                }
            else:
                flag_name = get_longest_flag(list(action.option_strings))
                option_name = action.dest.replace("-", "_")
                option_data = {
                    "type": "option",
                    "required": action.required,
                    "multiple": action.nargs in {"*", "+"} if hasattr(action, "nargs") else False,
                    "flag_name": flag_name,
                }

            prop: dict[str, Any] = {"title": option_name}
            prop["description"] = action.help or ""

            # Determine type
            if isinstance(action, (argparse._StoreConstAction, argparse._StoreTrueAction, argparse._StoreFalseAction)):
                option_data["flag"] = True
                prop["type"] = "boolean"
            elif isinstance(action, argparse._CountAction):
                prop["type"] = "integer"
            elif isinstance(action, argparse._AppendAction):
                option_data["multiple"] = True
                prop["type"] = "array"
                prop["items"] = {"type": "string"}
            elif hasattr(action, "type") and action.type:
                if action.type is int:
                    if option_data.get("multiple"):
                        prop["type"] = "array"
                        prop["items"] = {"type": "integer"}
                    else:
                        prop["type"] = "integer"
                elif action.type is float:
                    if option_data.get("multiple"):
                        prop["type"] = "array"
                        prop["items"] = {"type": "number"}
                    else:
                        prop["type"] = "number"
                # Default to string for other types
                elif option_data.get("multiple"):
                    prop["type"] = "array"
                    prop["items"] = {"type": "string"}
                else:
                    prop["type"] = "string"
                # Add choices if present (after type determination)
                if hasattr(action, "choices") and action.choices and not option_data.get("multiple"):
                    prop["enum"] = list(action.choices)
            elif hasattr(action, "choices") and action.choices:
                if option_data.get("multiple"):
                    prop["type"] = "array"
                    prop["items"] = {"type": "string"}
                else:
                    prop["type"] = "string"
                    prop["enum"] = list(action.choices)
            # Default to string
            elif option_data.get("multiple"):
                prop["type"] = "array"
                prop["items"] = {"type": "string"}
            elif strict_types:
                msg = f"Unknown type: {action.type}"
                raise ValueError(msg)
            else:
                prop["type"] = "string"

            # Set default value
            if hasattr(action, "default") and action.default is not None and action.default != argparse.SUPPRESS:
                prop["default"] = action.default
            elif not option_data["required"] and not is_positional:
                prop["default"] = None

            properties[option_name] = prop
            option_data["description"] = prop.get("description", "")
            options[option_name] = ArgparseCommandOption(**option_data)

        schema = {
            "type": "object",
            "properties": properties,
            "title": command_path,
            "description": get_parser_description(subparser),
        }
        required = sorted([option_name for option_name, option in options.items() if option.required])
        if required:
            schema["required"] = required

        yield ArgparseCommandMetadata(path=command_path, schema=schema, options=options)


def walk_commands_group_aggregation(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
) -> Iterator[ArgparseCommandMetadata]:
    groups: dict[str, dict[str, tuple[str, argparse.ArgumentParser]]] = {}

    for command_path, subparser in walk_parser_tree(parser, name=name, include=include, exclude=exclude):
        parts = command_path.split()
        if len(parts) == 1:
            # Root command
            groups.setdefault(name, {})[""] = (command_path, subparser)
        else:
            # Group by parent path
            group_path = " ".join(parts[:-1])
            command_name = parts[-1]
            groups.setdefault(group_path, {})[command_name] = (command_path, subparser)

    for group_path, commands in groups.items():
        # Root is a command rather than a group
        if "" in commands:
            command_path, subparser = commands[""]
            yield ArgparseCommandMetadata(
                path=group_path,
                schema={
                    "type": "object",
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
                    "title": group_path,
                    "description": f"{get_parser_full_usage(subparser, name)}\n",
                },
                options={
                    "args": ArgparseCommandOption(
                        type="positional",
                        required=False,
                        description="The arguments to pass to the command",
                    ),
                },
            )
            continue

        description = f"""\
Usage: {group_path} SUBCOMMAND [ARGS]...

# Available subcommands
"""
        for command_name, (command_path, subparser) in commands.items():
            description += f"""
## {command_name}

{get_parser_full_usage(subparser, command_path)}
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
                        "items": {
                            "type": "string",
                        },
                        "title": "args",
                        "description": "The arguments to pass to the subcommand",
                    },
                },
                "title": group_path,
                "description": description.lstrip(),
            },
            options={
                "subcommand": ArgparseCommandOption(
                    type="positional",
                    required=True,
                    description="The subcommand to execute",
                ),
                "args": ArgparseCommandOption(
                    type="positional",
                    required=False,
                    description="The arguments to pass to the subcommand",
                ),
            },
        )


def walk_commands_root_aggregation(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
) -> Iterator[ArgparseCommandMetadata]:
    description = ""

    # Check if parser has subparsers
    has_subparsers = any(isinstance(action, argparse._SubParsersAction) for action in parser._actions)

    if has_subparsers:
        description += f"""\
# {name}

Usage: {name} [OPTIONS] SUBCOMMAND [ARGS]...
"""
        if parser_description := get_parser_description(parser):
            description += f"\n{parser_description}\n"
        if parser_options := get_parser_options_block(parser):
            description += f"\nOptions:\n{parser_options}\n"

    for command_path, subparser in walk_parser_tree(parser, name=name, include=include, exclude=exclude):
        description += f"""
## {command_path}

{get_parser_full_usage(subparser, command_path)}
"""

    yield ArgparseCommandMetadata(
        path=name,
        schema={
            "type": "object",
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
            "title": name,
            "description": description.lstrip(),
        },
        options={
            "args": ArgparseCommandOption(
                type="positional",
                required=False,
                description="The arguments to pass to the root command",
            ),
        },
    )


def walk_commands(
    parser: argparse.ArgumentParser,
    *,
    aggregate: Literal["root", "group", "none"],
    name: str,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    strict_types: bool = False,
) -> Iterator[ArgparseCommandMetadata]:
    if aggregate == "root":
        yield from walk_commands_root_aggregation(
            parser,
            name=name,
            include=include,
            exclude=exclude,
        )
    elif aggregate == "group":
        yield from walk_commands_group_aggregation(
            parser,
            name=name,
            include=include,
            exclude=exclude,
        )
    elif aggregate == "none":
        yield from walk_commands_no_aggregation(
            parser,
            name=name,
            include=include,
            exclude=exclude,
            strict_types=strict_types,
        )
    else:
        msg = f"Invalid aggregate value: {aggregate}"
        raise ValueError(msg)
