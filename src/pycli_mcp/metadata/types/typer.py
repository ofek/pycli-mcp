# SPDX-FileCopyrightText: 2026-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

from types import NoneType, UnionType
from typing import TYPE_CHECKING, Any, Literal, Union, get_args, get_origin

from pycli_mcp.metadata.types.click import ClickCommandMetadata
from pycli_mcp.metadata.types.click import _walk_commands as walk_click_commands
from pycli_mcp.metadata.types.click import get_parameter_info as get_click_parameter_info

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator


def is_typer_app(command: Any) -> bool:
    return hasattr(command, "registered_commands") and hasattr(command, "registered_groups")


def is_typer_command(command: Any) -> bool:
    return any(cls.__module__.startswith("typer.") for cls in type(command).__mro__)


def is_typer_command_group(command: Any) -> bool:
    return hasattr(command, "list_commands") and hasattr(command, "get_command")


def get_typer_command(command: Any) -> Any:
    if is_typer_app(command):
        from typer.main import get_command

        return get_command(command)

    return command


def get_typer_command_usage_pieces(command: Any, ctx: Any) -> list[str]:
    return [piece.replace("COMMAND [ARGS]...", "SUBCOMMAND [ARGS]...") for piece in command.collect_usage_pieces(ctx)]


def get_typer_click_type(annotation: Any, parameter_info: Any) -> Any:
    from typer.main import get_click_type

    if get_origin(annotation) is tuple:
        return tuple(
            get_click_type(annotation=member, parameter_info=parameter_info) for member in get_args(annotation)
        )

    return get_click_type(annotation=annotation, parameter_info=parameter_info)


def get_typer_type_data(click_type: Any) -> dict[str, Any]:
    if isinstance(click_type, tuple):
        return {"param_type": "Tuple", "name": "tuple"}

    type_name = type(click_type).__name__.removesuffix("ParamType").removesuffix("ParameterType")
    if type_name == "TyperPath":
        type_name = "Path"

    type_data = {
        "param_type": type_name,
        "name": getattr(click_type, "name", type_name.lower()),
    }
    if (choices := getattr(click_type, "choices", None)) is not None:
        type_data["choices"] = choices

    return type_data


def get_typer_parameter_info(param: Any, ctx: Any) -> dict[str, Any]:
    if hasattr(param, "to_info_dict"):
        return get_click_parameter_info(param, ctx)

    if (click_type := getattr(param, "type", None)) is not None:
        type_data = get_typer_type_data(click_type)
    else:
        type_data = {"param_type": "String", "name": "string"}

    callback = getattr(ctx.command, "callback", None)
    if callback is not None:
        from typer.models import ArgumentInfo, OptionInfo
        from typer.utils import get_params_from_function

        param_meta = get_params_from_function(callback).get(param.name or "")
        if param_meta is not None:
            main_type = param_meta.annotation
            origin = get_origin(main_type)
            if origin in {UnionType, Union}:
                union_types = [member for member in get_args(main_type) if member is not NoneType]
                if len(union_types) == 1:
                    main_type = union_types[0]
                    origin = get_origin(main_type)

            if origin is list:
                main_type = get_args(main_type)[0]

            default = param_meta.default
            if isinstance(default, (OptionInfo, ArgumentInfo)):
                parameter_info: Any = default
            elif getattr(param, "param_type_name", "option") == "option":
                parameter_info = OptionInfo()
            else:
                parameter_info = ArgumentInfo()

            click_type = get_typer_click_type(annotation=main_type, parameter_info=parameter_info)
            type_data = get_typer_type_data(click_type)

    return {
        "name": getattr(param, "name", None),
        "param_type_name": getattr(param, "param_type_name", "option"),
        "opts": list(getattr(param, "opts", []) or []),
        "secondary_opts": list(getattr(param, "secondary_opts", []) or []),
        "type": type_data,
        "required": getattr(param, "required", False),
        "nargs": getattr(param, "nargs", 1),
        "multiple": getattr(param, "multiple", False),
        "default": param.get_default(ctx, call=False),
        "help": getattr(param, "help", None),
        "hidden": getattr(param, "hidden", False),
    }


def walk_commands(
    command: Any,
    *,
    aggregate: Literal["root", "group", "none"],
    name: str | None = None,
    include: str | re.Pattern | None = None,
    exclude: str | re.Pattern | None = None,
    strict_types: bool = False,
) -> Iterator[ClickCommandMetadata]:
    yield from walk_click_commands(
        get_typer_command(command),
        aggregate=aggregate,
        name=name,
        include=include,
        exclude=exclude,
        strict_types=strict_types,
        parameter_info_getter=get_typer_parameter_info,
        command_usage_pieces_getter=get_typer_command_usage_pieces,
        command_group_checker=is_typer_command_group,
    )
