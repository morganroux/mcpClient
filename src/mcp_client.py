from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.mcp_session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.available_tools = []
        self.stdio = None
        self.write = None

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.mcp_session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.mcp_session.initialize()

        # List available tools
        response = await self.mcp_session.list_tools()
        tools = response.tools
        for tool in tools:
            parameters = {
                **tool.inputSchema,
                "required": list(tool.inputSchema["properties"].keys()),
            }
            self.available_tools.append(
                {
                    "strict": True,
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters,
                }
            )
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def call_tool(self, tool_name: str, tool_args: dict):
        """Call a tool with the given name and arguments.

        Args:
            tool_name: Name of the tool to call
            tool_args: Arguments for the tool
        """
        if self.mcp_session is None:
            raise ValueError("MCP session is not initialized")
        if self.stdio is None or self.write is None:
            raise ValueError("Stdio transport is not initialized")

        # Call the tool
        result = await self.mcp_session.call_tool(tool_name, tool_args)
        return result
