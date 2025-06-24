# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import re
import shutil
from importlib import import_module
from typing import Any

import click

from click_mcp_server import ClickCommandQuery, ClickMCPServer


def parse_target_option(specs: dict[str, Any], raw_value: str) -> tuple[str, str]:
    target_spec, sep, value = raw_value.partition("=")

    if not sep:
        if len(specs) == 1:
            return next(iter(specs.keys())), raw_value

        msg = f"Multiple specs provided, but no separator found in option: {raw_value}"
        raise ValueError(msg)

    if not target_spec:
        msg = f"No target spec in option: {raw_value}"
        raise ValueError(msg)

    if target_spec not in specs:
        msg = f"Unknown target spec `{target_spec}` in option: {raw_value}"
        raise ValueError(msg)

    return target_spec, value


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": shutil.get_terminal_size().columns,
    },
)
@click.argument("specs", nargs=-1)
@click.option(
    "--name",
    "-n",
    "names",
    multiple=True,
    help="The expected name of the exposed command, multiple specs make the format: spec=name",
)
@click.option(
    "--include",
    "-i",
    "includes",
    multiple=True,
    help="The regular expression filter to include subcommands, multiple specs make the format: spec=regex",
)
@click.option(
    "--exclude",
    "-e",
    "excludes",
    multiple=True,
    help="The regular expression filter to exclude subcommands, multiple specs make the format: spec=regex",
)
@click.option("--strict-types", is_flag=True, help="Error on unknown types")
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
    help="Arbitrary server options (multiple allowed) e.g. -o key1 value1 -o key2 value2",
)
@click.pass_context
def click_mcp_server(
    ctx: click.Context,
    *,
    specs: tuple[str, ...],
    names: tuple[str, ...],
    includes: tuple[str, ...],
    excludes: tuple[str, ...],
    strict_types: bool,
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

    Filtering is supported. For example, if you have a CLI named `foo` and you only want to expose the
    subcommands `bar` and `baz`, excluding the `baz` subcommands `sub2` and `sub3`, you can do:

    \b
    ```
    click-mcp-server pkg.cli:foo -i "bar|baz" -e "baz (sub2|sub3)"
    ```
    """
    if not specs:
        click.echo(ctx.get_help())
        return

    # Deduplicate
    command_specs: dict[str, dict[str, Any]] = {spec: {} for spec in dict.fromkeys(specs)}

    for name_entry in names:
        target_spec, name = parse_target_option(command_specs, name_entry)
        command_specs[target_spec]["name"] = name

    for include_entry in includes:
        target_spec, include_pattern = parse_target_option(command_specs, include_entry)
        command_specs[target_spec]["include"] = re.compile(include_pattern)

    for exclude_entry in excludes:
        target_spec, exclude_pattern = parse_target_option(command_specs, exclude_entry)
        command_specs[target_spec]["exclude"] = re.compile(exclude_pattern)

    command_queries: list[ClickCommandQuery] = []
    spec_pattern = re.compile(r"^(?P<spec>(?P<module>[\w.]+):(?P<attr>[\w.]+))$")
    for spec, data in command_specs.items():
        match = spec_pattern.search(spec)
        if match is None:
            msg = f"Invalid spec: {spec}"
            raise ValueError(msg)

        obj = import_module(match.group("module"))
        for attr in match.group("attr").split("."):
            obj = getattr(obj, attr)

        if not isinstance(obj, click.Command):
            msg = f"Expected a Click command, got: {obj.__class__.__name__}"
            raise TypeError(msg)

        command_query = ClickCommandQuery(
            obj,
            name=data.get("name"),
            include=data.get("include"),
            exclude=data.get("exclude"),
            strict_types=strict_types,
        )
        command_queries.append(command_query)

    app_settings: dict[str, Any] = {}
    if debug:
        app_settings["debug"] = True

    server = ClickMCPServer(command_queries, stateless=True, **app_settings)
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
