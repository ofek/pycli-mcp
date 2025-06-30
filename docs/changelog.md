# Changelog

-----

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## 0.3.0 - 2025-06-30

***Added:***

- Add support for Typer
- Add support for Argparse
- Always set the `PYCLI_MCP_TOOL_NAME` environment variable when running commands
- Add support for referring to a callable object that returns a command

## 0.2.0 - 2025-06-28

***Changed:***

- Rename the project to `pycli-mcp`
- Rename `ClickCommandQuery` to `CommandQuery`
- Rename `ClickMCPServer` to `CommandMCPServer`

## 0.1.0 - 2025-06-26

***Changed:***

- The default aggregation level is now `root`

***Added:***

- Add support for controlling the level of command aggregation
- Increase verbosity of the CLI

***Fixed:***

- Server errors now properly return the content of the command's `stderr`

## 0.0.2 - 2025-06-24

***Added:***

- Add support for customizing the root command name
- Add support for more option types
- Add support for strict type checking

***Fixed:***

- Fix options with dynamic default values
- The CLI now errors for specs that don't refer to a Click command object

## 0.0.1 - 2025-06-24

This is the initial public release.
