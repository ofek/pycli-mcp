# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import inspect
import re
from typing import TYPE_CHECKING, Any, Literal

import click

from pycli_mcp.metadata.interface import CommandMetadata

if TYPE_CHECKING:
    from collections.abc import Iterator


class ClickCommandMetadata(CommandMetadata):
    def __init__(self, *, path: str, schema: dict[str, Any], options: dict[str, ClickCommandOption]) -> None:
        super().__init__(path=path, schema=schema)

        self.__options = options

    @property
    def options(self) -> dict[str, ClickCommandOption]:
        return self.__options

    def construct(self, arguments: dict[str, Any] | None = None) -> list[str]:
        command = self.path.split()
        if arguments and self.options:
            args: list[Any] = []
            opts: list[Any] = []
            flags: list[str] = []
            for option_name, value in arguments.items():
                option = self.options[option_name]
                if option.type == "argument":
                    if isinstance(value, list):
                        args.extend(value)
                    else:
                        args.append(value)

                    continue

                if option.flag:
                    if value:
                        flags.append(option.flag_name)
                elif option.multiple:
                    if option.container:
                        for v in value:
                            opts.append(option.flag_name)
                            opts.extend(v)
                    else:
                        for v in value:
                            opts.extend((option.flag_name, v))
                elif option.container:
                    opts.append(option.flag_name)
                    opts.extend(value)
                else:
                    opts.extend((option.flag_name, value))

            command.extend(flags)
            command.extend(map(str, opts))
            if args:
                command.append("--")
                command.extend(map(str, args))

        return command


class ClickCommandOption:
    __slots__ = ("__container", "__description", "__flag", "__flag_name", "__multiple", "__required", "__type")

    def __init__(
        self,
        *,
        type: Literal["argument", "option"],  # noqa: A002
        required: bool,
        description: str,
        multiple: bool = False,
        container: bool = False,
        flag: bool = False,
        flag_name: str = "",
    ) -> None:
        self.__type = type
        self.__required = required
        self.__description = description
        self.__multiple = multiple
        self.__container = container
        self.__flag = flag
        self.__flag_name = flag_name

    @property
    def type(self) -> Literal["argument", "option"]:
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
    def container(self) -> bool:
        return self.__container

    @property
    def flag(self) -> bool:
        return self.__flag

    @property
    def flag_name(self) -> str:
        return self.__flag_name


def get_longest_flag(flags: list[str]) -> str:
    return sorted(flags, key=len)[-1]  # noqa: FURB192


def get_command_description(command: click.Command) -> str:
    # Truncate the help text to the first form feed
    return inspect.cleandoc(command.help or command.short_help or "").split("\f")[0].strip()


def get_command_options_block(ctx: click.Context) -> str:
    import textwrap

    options = ""
    for param in ctx.command.get_params(ctx):
        info = param.to_info_dict()
        if info.get("hidden", False) or "--help" in info["opts"]:
            continue

        help_record = param.get_help_record(ctx)
        if help_record is None:
            continue

        metadata, help_text = help_record
        options += f"\n{metadata}"
        help_text = textwrap.dedent(help_text).strip()
        if help_text:
            separator = " " * 2
            options += separator
            options += textwrap.indent(help_text, " " * (len(metadata) + len(separator))).strip()

    return options.lstrip()


def get_command_full_usage(ctx: click.Context) -> str:
    usage_pieces = [f"Usage: {ctx.command_path}"]
    usage_pieces.extend(ctx.command.collect_usage_pieces(ctx))
    usage = " ".join(usage_pieces)

    if description := get_command_description(ctx.command):
        usage += f"\n\n{description}"

    if options := get_command_options_block(ctx):
        usage += f"\n\nOptions:\n{options}"

    return usage


def walk_command_tree(
    command: click.Command,
    *,
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    parent: click.Context | None = None,
) -> Iterator[click.Context]:
    if command.hidden:
        return

    ctx = command.context_class(command, parent=parent, info_name=name, **command.context_settings)
    if not isinstance(command, click.Group):
        subcommand_path = " ".join(ctx.command_path.split()[1:])
        if exclude is not None and re.search(exclude, subcommand_path):
            return
        if include is not None and not re.search(include, subcommand_path):
            return

        yield ctx
        return

    for subcommand_name in command.list_commands(ctx):
        subcommand = command.get_command(ctx, subcommand_name)
        if subcommand is None:
            continue
        yield from walk_command_tree(subcommand, name=subcommand_name, include=include, exclude=exclude, parent=ctx)


def walk_commands_no_aggregation(
    command: click.Command,
    *,
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    strict_types: bool = False,
) -> Iterator[ClickCommandMetadata]:
    for ctx in walk_command_tree(command, name=name or command.name, include=include, exclude=exclude):
        properties: dict[str, Any] = {}
        options: dict[str, ClickCommandOption] = {}
        for param in ctx.command.get_params(ctx):
            info = param.to_info_dict()
            flags = info["opts"]
            if info.get("hidden", False) or "--help" in flags:
                continue

            flag_name = get_longest_flag(flags)
            option_name = flag_name.lstrip("-").replace("-", "_")

            option_data = {
                "type": info["param_type_name"],
                "required": info["required"],
                "multiple": info["multiple"],
            }
            if info["param_type_name"] == "option":
                option_data["flag_name"] = flag_name

            prop: dict[str, Any] = {"title": option_name}
            if help_text := (info.get("help") or "").strip():
                prop["description"] = help_text

            type_data = info["type"]
            type_name = type_data["param_type"]

            # Some types are just strings
            if type_name in {"Path", "File"}:
                type_name = "String"

            if type_name == "String":
                if info["nargs"] == -1 or info["multiple"]:
                    prop["type"] = "array"
                    prop["items"] = {"type": "string"}
                else:
                    prop["type"] = "string"
            elif type_name == "Bool":
                option_data["flag"] = True
                prop["type"] = "boolean"
            elif type_name == "Int":
                if info["multiple"]:
                    prop["type"] = "array"
                    prop["items"] = {"type": "integer"}
                else:
                    prop["type"] = "integer"
            elif type_name == "Float":
                if info["multiple"]:
                    prop["type"] = "array"
                    prop["items"] = {"type": "number"}
                else:
                    prop["type"] = "number"
            elif type_name in {"Choice", "TyperChoice"}:
                prop["type"] = "string"
                prop["enum"] = list(type_data["choices"])
            elif type_name == "Tuple":
                option_data["container"] = True
                if info["multiple"]:
                    prop["type"] = "array"
                    prop["items"] = {"type": "array", "items": {"type": "string"}}
                else:
                    prop["type"] = "array"
                    prop["items"] = {"type": "string"}
            elif strict_types:
                msg = f"Unknown type: {type_data}\n{info}"
                raise ValueError(msg)
            else:
                prop["type"] = "string"

            if not info["required"]:
                prop["default"] = None if callable(info["default"]) else info["default"]

            properties[option_name] = prop
            option_data["description"] = prop.get("description", "")
            options[option_name] = ClickCommandOption(**option_data)

        schema = {
            "type": "object",
            "properties": properties,
            "title": ctx.command_path,
            "description": get_command_description(ctx.command),
        }
        required = [option_name for option_name, option in options.items() if option.required]
        if required:
            schema["required"] = required

        yield ClickCommandMetadata(path=ctx.command_path, schema=schema, options=options)


def walk_commands_group_aggregation(
    command: click.Command,
    *,
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
) -> Iterator[ClickCommandMetadata]:
    groups: dict[str, dict[str, click.Context]] = {}
    for ctx in walk_command_tree(command, name=name or command.name, include=include, exclude=exclude):
        if ctx.parent is None:
            group_path = ctx.command_path
            command_name = ""
        else:
            group_path = ctx.parent.command_path
            command_name = ctx.command_path.split()[-1]

        groups.setdefault(group_path, {})[command_name] = ctx

    for group_path, commands in groups.items():
        # Root is a command rather than a group
        if "" in commands:
            yield ClickCommandMetadata(
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
                    "description": f"{get_command_full_usage(ctx)}\n",
                },
                options={
                    "args": ClickCommandOption(
                        type="argument",
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
        for command_name, ctx in commands.items():
            description += f"""
## {command_name}

{get_command_full_usage(ctx)}
"""

        yield ClickCommandMetadata(
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
                "subcommand": ClickCommandOption(
                    type="argument",
                    required=True,
                    description="The subcommand to execute",
                ),
                "args": ClickCommandOption(
                    type="argument",
                    required=False,
                    description="The arguments to pass to the subcommand",
                ),
            },
        )


def walk_commands_root_aggregation(
    command: click.Command,
    *,
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
) -> Iterator[ClickCommandMetadata]:
    root_command_name = name or command.name
    description = ""
    if isinstance(command, click.Group):
        ctx = command.context_class(command, info_name=root_command_name, **command.context_settings)
        description += f"""\
# {root_command_name}

Usage: {root_command_name} [OPTIONS] SUBCOMMAND [ARGS]...
"""
        if root_command_description := get_command_description(command):
            description += f"\n{root_command_description}\n"
        if root_command_options := get_command_options_block(ctx):
            description += f"\nOptions:\n{root_command_options}\n"

    for ctx in walk_command_tree(command, name=root_command_name, include=include, exclude=exclude):
        description += f"""
## {ctx.command_path}

{get_command_full_usage(ctx)}
"""

    yield ClickCommandMetadata(
        path=root_command_name,  # type: ignore[arg-type]
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
            "title": root_command_name,
            "description": description.lstrip(),
        },
        options={
            "args": ClickCommandOption(
                type="argument",
                required=False,
                description="The arguments to pass to the root command",
            ),
        },
    )


def walk_commands(
    command: click.Command,
    *,
    aggregate: Literal["root", "group", "none"],
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    strict_types: bool = False,
) -> Iterator[ClickCommandMetadata]:
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
