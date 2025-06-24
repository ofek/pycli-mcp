# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import inspect
import re
from typing import TYPE_CHECKING, Any, Literal

import click

if TYPE_CHECKING:
    from collections.abc import Iterator


class ClickCommandOption:
    __slots__ = ("__description", "__flag", "__multiple", "__required", "__type")

    def __init__(
        self,
        *,
        type: Literal["argument", "option"],  # noqa: A002
        required: bool,
        description: str,
        multiple: bool,
        flag: str = "",
    ) -> None:
        self.__type = type
        self.__required = required
        self.__description = description
        self.__multiple = multiple
        self.__flag = flag

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
    def flag(self) -> str:
        return self.__flag


class ClickCommandMetadata:
    __slots__ = ("__options", "__path", "__schema")

    def __init__(self, path: str, schema: dict[str, Any], options: dict[str, ClickCommandOption]) -> None:
        self.__path = path
        self.__schema = schema
        self.__options = options

    @property
    def path(self) -> str:
        return self.__path

    @property
    def schema(self) -> dict[str, Any]:
        return self.__schema

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
                elif option.type == "option":
                    if isinstance(value, bool):
                        if value:
                            flags.append(option.flag)
                        continue
                    if isinstance(value, list):
                        for v in value:
                            opts.extend((option.flag, v))
                    else:
                        opts.extend((option.flag, value))

            command.extend(flags)
            command.extend(map(str, opts))
            if args:
                command.append("--")
                command.extend(map(str, args))

        return command


def walk_command_tree(
    command: click.Command,
    *,
    name: str | None = None,
    parent: click.Context | None = None,
) -> Iterator[click.Context]:
    if command.hidden:
        return

    ctx = command.context_class(command, parent=parent, info_name=name, **command.context_settings)
    if not isinstance(command, click.Group):
        yield ctx
        return

    for subcommand_name in command.list_commands(ctx):
        subcommand = command.get_command(ctx, subcommand_name)
        if subcommand is None:
            continue
        yield from walk_command_tree(subcommand, name=subcommand_name, parent=ctx)


def walk_commands(
    command: click.Command,
    *,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
) -> Iterator[ClickCommandMetadata]:
    for ctx in walk_command_tree(command, name=command.name):
        subcommand_path = " ".join(ctx.command_path.split()[1:])
        if exclude is not None and re.search(exclude, subcommand_path):
            continue
        if include is not None and not re.search(include, subcommand_path):
            continue

        properties: dict[str, Any] = {}
        options: dict[str, ClickCommandOption] = {}
        for param in ctx.command.get_params(ctx):
            info = param.to_info_dict()
            flags = info["opts"]
            if info.get("hidden", False) or "--help" in flags:
                continue

            # Get the longest flag
            flag = sorted(flags, key=len)[-1]  # noqa: FURB192
            option_name = flag.lstrip("-").replace("-", "_")

            prop = {"title": option_name}
            if help_text := (info.get("help") or "").strip():
                prop["description"] = help_text

            type_data = info["type"]
            type_name = type_data["name"]
            if type_name == "boolean":
                prop["type"] = "boolean"
            elif type_name == "text":
                if info["nargs"] == -1 or info["multiple"]:
                    prop["type"] = "array"
                    prop["items"] = {"type": "string"}
                else:
                    prop["type"] = "string"
            elif type_name == "integer":
                if info["multiple"]:
                    prop["type"] = "array"
                    prop["items"] = {"type": "integer"}
                else:
                    prop["type"] = "integer"
            elif type_name == "float":
                if info["multiple"]:
                    prop["type"] = "array"
                    prop["items"] = {"type": "number"}
                else:
                    prop["type"] = "number"
            elif type_name == "choice":
                prop["type"] = "string"
                prop["enum"] = list(type_data["choices"])
            else:
                msg = f"Unknown type: {type_name}"
                raise ValueError(msg)

            if not info["required"]:
                prop["default"] = info["default"]

            properties[option_name] = prop

            option_data = {
                "type": info["param_type_name"],
                "required": info["required"],
                "description": prop.get("description", ""),
                "multiple": info["multiple"],
            }
            if info["param_type_name"] == "option":
                option_data["flag"] = flag

            options[option_name] = ClickCommandOption(**option_data)

        schema = {
            "type": "object",
            "properties": properties,
            "title": ctx.command_path,
            "description": inspect.cleandoc(ctx.command.help or ctx.command.short_help or "").strip(),
        }
        required = [option_name for option_name, option in options.items() if option.required]
        if required:
            schema["required"] = required

        yield ClickCommandMetadata(path=ctx.command_path, schema=schema, options=options)
