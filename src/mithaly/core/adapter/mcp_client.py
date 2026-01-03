"""McpClient - Adapter for Model Context Protocol.

This component allows Mithaly to connect to MCP servers (like filesystem, postgres, etc.)
and unify tool/resource access.
"""
import asyncio
import json
import os
import shutil
import subprocess
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Optional

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    # Fallback to avoid crash if mcp is not yet installed (e.g. during bootstrap)
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


class McpClient:
    """Client to manage connections to MCP servers."""

    def __init__(self):
        self.sessions = {} # server_name -> session
        self.exit_stack = AsyncExitStack()

    async def connect_server(self, name: str, config: Dict[str, Any]):
        """Connect to an MCP server using the provided configuration."""
        if not ClientSession:
            print("ERROR: 'mcp' package not installed.")
            return

        command = config.get('command')
        args = config.get('args', [])
        env = config.get('env', {})

        # Merge current env with config env
        full_env = os.environ.copy()
        full_env.update(env)

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=full_env
        )

        try:
            # We use the stdio_client context manager
            # Note: In a long-running app, we need to keep the context open.
            # Using AsyncExitStack to manage these generic contexts.
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            
            await session.initialize()
            print(f"Connected to MCP server: {name}")
            self.sessions[name] = session
        except Exception as e:
            print(f"Failed to connect to MCP server {name}: {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools from all connected servers."""
        all_tools = []
        for name, session in self.sessions.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    # Namespacing: server__tool
                    t_dict = tool.model_dump() if hasattr(tool, 'model_dump') else tool.__dict__
                    t_dict['name'] = f"{name}__{t_dict['name']}"
                    all_tools.append(t_dict)
            except Exception as e:
                print(f"Error listing tools from {name}: {e}")
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool on a specific server."""
        session = self.sessions.get(server_name)
        if not session:
            return {"error": f"Server {server_name} not connected"}
        
        try:
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def read_resource(self, uri: str) -> Any:
        """Read a resource from any server that supports it."""
        # Naive implementation: try all servers or route by scheme?
        # For now, let's just try all.
        for name, session in self.sessions.items():
            try:
                result = await session.read_resource(uri)
                return result
            except Exception:
                # continue to next server
                pass
        return None

    async def cleanup(self):
        """Close all connections."""
        await self.exit_stack.aclose()
