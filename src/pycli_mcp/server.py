# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import subprocess
from contextlib import asynccontextmanager
from functools import cached_property
from typing import TYPE_CHECKING, Any

import uvicorn
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    ServerResult,
    TextContent,
    Tool,
)
from starlette.applications import Starlette
from starlette.routing import Mount

from pycli_mcp.metadata.query import CommandQuery

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from mcp.server.streamable_http import EventStore

    from pycli_mcp.metadata.interface import CommandMetadata


class Command:
    __slots__ = ("__metadata", "__tool")

    def __init__(self, metadata: CommandMetadata, tool: Tool):
        self.__metadata = metadata
        self.__tool = tool

    @property
    def metadata(self) -> CommandMetadata:
        return self.__metadata

    @property
    def tool(self) -> Tool:
        return self.__tool


class CommandMCPServer:
    """
    An MCP server that can be used to run Python CLIs, backed by [Starlette](https://github.com/encode/starlette)
    and [Uvicorn](https://github.com/encode/uvicorn). Example usage:

    ```python
    from pycli_mcp import CommandMCPServer

    from mypkg.cli import cmd

    server = CommandMCPServer(commands=[cmd], stateless=True)
    server.run()
    ```

    Parameters:
        commands: The commands to expose as MCP tools.

    Other parameters:
        event_store: Optional [event store](https://github.com/modelcontextprotocol/python-sdk/blob/v1.9.4/src/mcp/server/streamable_http.py#L79)
            that allows clients to reconnect and receive missed events. If `None`, sessions are still tracked but not
            resumable.
        stateless: Whether to create a completely fresh transport for each request with no session tracking or state
            persistence between requests.
        **app_settings: Additional settings to pass to the Starlette [application][starlette.applications.Starlette].
    """

    def __init__(
        self,
        commands: Sequence[Any],
        *,
        event_store: EventStore | None = None,
        stateless: bool = False,
        **app_settings: Any,
    ) -> None:
        self.__command_queries = [c if isinstance(c, CommandQuery) else CommandQuery(c) for c in commands]
        self.__app_settings = app_settings
        self.__server: Server = Server("pycli_mcp")
        self.__session_manager = StreamableHTTPSessionManager(
            app=self.__server,
            event_store=event_store,
            stateless=stateless,
            json_response=True,
        )

        # Register handlers
        self.__server.request_handlers[ListToolsRequest] = self.list_tools_handler
        self.__server.request_handlers[CallToolRequest] = self.call_tool_handler

    @property
    def server(self) -> Server:
        """
        Returns:
            The underlying [low-level server](https://github.com/modelcontextprotocol/python-sdk/blob/v1.9.4/src/mcp/server/lowlevel/server.py)
                instance. You can use this to register additional handlers.
        """
        return self.__server

    @property
    def session_manager(self) -> StreamableHTTPSessionManager:
        """
        Returns:
            The underlying [session manager](https://github.com/modelcontextprotocol/python-sdk/blob/v1.9.4/src/mcp/server/streamable_http_manager.py#L29)
                instance. You only need to use this if you want to override the `lifetime` context manager
        """
        return self.__session_manager

    @cached_property
    def commands(self) -> dict[str, Command]:
        """
        Returns:
            Dictionary used internally to store metadata about the exposed commands. Although it should not be modified,
                the keys are the available MCP tool names and useful to know when overriding the default handlers.
        """
        commands: dict[str, Command] = {}
        for query in self.__command_queries:
            for metadata in query:
                tool_name = metadata.path.replace(" ", ".").replace("-", "_")
                tool = Tool(
                    name=tool_name,
                    description=metadata.schema["description"],
                    inputSchema=metadata.schema,
                )
                commands[tool_name] = Command(metadata, tool)

        return commands

    @cached_property
    def routes(self) -> list[Mount]:
        """
        This would only be used directly if you want to add more routes in addition to the default `/mcp` route.

        Returns:
            The [routes](https://www.starlette.io/routing/#http-routing) to mount in the Starlette
                [application][starlette.applications.Starlette].
        """
        return [Mount("/mcp", app=self.session_manager.handle_request)]

    @asynccontextmanager
    async def lifespan(self, app: Starlette) -> AsyncIterator[None]:  # noqa: ARG002
        """
        The default lifespan context manager used by the Starlette [application][starlette.applications.Starlette].
        """
        async with self.session_manager.run():
            yield

    def list_command_tools(self) -> list[Tool]:
        """
        This would only be used directly if you want to override the handler for the `ListToolsRequest`.

        Returns:
            The MCP tools for the commands.
        """
        return [command.tool for command in self.commands.values()]

    async def list_tools_handler(self, _: ListToolsRequest) -> ServerResult:
        """
        The default handler for the `ListToolsRequest`.
        """
        return ServerResult(ListToolsResult(tools=self.list_command_tools()))

    async def call_tool_handler(self, req: CallToolRequest) -> ServerResult:
        """
        The default handler for the `CallToolRequest`.
        """
        command = self.commands[req.params.name].metadata.construct(req.params.arguments)
        env_vars = dict(os.environ)
        env_vars["PYCLI_MCP_TOOL_NAME"] = req.params.name

        try:
            process = subprocess.run(  # noqa: PLW1510
                command,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env_vars,
            )
        # This can happen if the command is not found
        except subprocess.CalledProcessError as e:
            return ServerResult(CallToolResult(content=[TextContent(type="text", text=str(e))], isError=True))

        if process.returncode:
            msg = f"{process.stdout}\nThis command exited with non-zero exit code `{process.returncode}`: {command}"
            return ServerResult(CallToolResult(content=[TextContent(type="text", text=msg)], isError=True))

        return ServerResult(CallToolResult(content=[TextContent(type="text", text=process.stdout)]))

    def run(self, **kwargs: Any) -> None:
        """
        Other parameters:
            **kwargs: Additional settings to pass to the [`uvicorn.run`](https://www.uvicorn.org/#uvicornrun) function.
        """
        app_settings = self.__app_settings.copy()
        app_settings["routes"] = self.routes
        app_settings.setdefault("lifespan", self.lifespan)
        app = Starlette(**app_settings)
        uvicorn.run(app, **kwargs)
