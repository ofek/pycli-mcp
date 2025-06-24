# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import re
import shutil
from importlib import import_module
from typing import Any, TypedDict

import click

from click_mcp_server import ClickCommandQuery, ClickMCPServer


class CommandSpec(TypedDict):
    command: click.Command
    include: re.Pattern | None
    exclude: re.Pattern | None


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": shutil.get_terminal_size().columns,
    },
)
@click.argument("specs", nargs=-1)
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--host", help="The host used to run the server (default: 127.0.0.1)")
@click.option("--port", type=int, help="The port used to run the server (default: 8000)")
@click.option("--log-level", help="The log level used to run the server (default: info)")
@click.option("--log-config", help="The path to a file passed to the `logging.config.fileConfig` function")
@click.option(
    "--option",
    "-o",
    "options",
    type=(str, str),
    multiple=True,
    help="Arbitrary server options (multiple allowed)",
)
@click.pass_context
def click_mcp_server(
    ctx: click.Context,
    *,
    specs: tuple[str, ...],
    debug: bool,
    host: str | None,
    port: int | None,
    log_level: str | None,
    log_config: str | None,
    options: tuple[tuple[str, str], ...],
) -> None:
    """
    \b
     _______ _  _       _        _______ _______ ______      ______
    (_______) |(_)     | |      (_______|_______|_____ \\    / _____)
     _      | | _  ____| |  _    _  _  _ _       _____) )  ( (____  _____  ____ _   _ _____  ____
    | |     | || |/ ___) |_/ )  | ||_|| | |     |  ____/    \\____ \\| ___ |/ ___) | | | ___ |/ ___)
    | |_____| || ( (___|  _ (   | |   | | |_____| |         _____) ) ____| |    \\ V /| ____| |
     \\______)\\_)_|\\____)_| \\_)  |_|   |_|\\______)_|        (______/|_____)_|     \\_/ |_____)_|

    Run an MCP server using a list of import paths to Click commands:

    \b
    ```
    click-mcp-server pkg1.cli:foo pkg2.cli:bar
    ```

    The import path can be followed by a regular expression filter to include or exclude subcommands.
    The filter may be prefixed with a `+` to include subcommands that match the regular expression or
    a `-` to exclude subcommands that match the regular expression. Exclusion filters take precedence
    over inclusion filters.

    For example, if you have a CLI named `foo` and you only want to expose the subcommands `bar` and
    `baz`, excluding the `baz` subcommands `sub2` and `sub3`, you can do:

    \b
    ```
    click-mcp-server "pkg.cli:foo+bar|baz" "pkg.cli:foo-baz (sub2|sub3)"
    ```
    """
    if not specs:
        click.echo(ctx.get_help())
        return

    command_specs: dict[str, CommandSpec] = {}
    pattern = re.compile(r"^(?P<spec>(?P<module>[\w.]+):(?P<attr>[\w.]+))((?P<filter>[-+])(?P<pattern>.+))?$")
    for raw_spec in specs:
        match = pattern.search(raw_spec)
        if match is None:
            msg = f"Invalid spec: {raw_spec}"
            raise ValueError(msg)

        spec = command_specs.setdefault(
            match.group("spec"),
            {"command": None, "include": None, "exclude": None},  # type: ignore[typeddict-item]
        )
        if spec["command"] is None:
            obj = import_module(match.group("module"))
            for attr in match.group("attr").split("."):
                obj = getattr(obj, attr)
            spec["command"] = obj

        filter_type = match.group("filter")
        if filter_type is not None:
            if filter_type == "+":
                if spec["include"] is not None:
                    msg = f"Include filter already set for {match.group('spec')}"
                    raise ValueError(msg)

                spec["include"] = re.compile(match.group("pattern"))
            elif filter_type == "-":
                if spec["exclude"] is not None:
                    msg = f"Exclude filter already set for {match.group('spec')}"
                    raise ValueError(msg)

                spec["exclude"] = re.compile(match.group("pattern"))

    commands = [
        ClickCommandQuery(spec["command"], include=spec["include"], exclude=spec["exclude"])
        for spec in command_specs.values()
    ]

    app_settings: dict[str, Any] = {}
    if debug:
        app_settings["debug"] = True

    server = ClickMCPServer(commands, stateless=True, **app_settings)
    if debug:
        for command in server.commands.values():
            print(f"Serving: {command.metadata.path}")

    server_settings: dict[str, Any] = {}
    if host is not None:
        server_settings["host"] = host
    if port is not None:
        server_settings["port"] = port
    if log_level is not None:
        server_settings["log_level"] = log_level
    if log_config is not None:
        server_settings["log_config"] = log_config

    for key, value in options:
        server_settings.setdefault(key, value)

    server.run(**server_settings)


def main() -> None:
    click_mcp_server(windows_expand_args=False)
