from contextlib import AsyncExitStack
from typing import Literal
from typing_extensions import TypedDict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import re


class AvailableTool(TypedDict):
    name: str
    strict: bool
    type: Literal["function"]
    description: str
    parameters: dict[str, object]


def extract_error(log: str):
    match = re.search(r"(.*error): (.*?)(\\n|$)", log, re.IGNORECASE)
    if match:
        error_type = match.group(1)
        error_message = match.group(2)
        return error_type, error_message
    return None, None


class MCPClient:
    def __init__(self, server_script_path: str):
        # Initialize session and client objects
        self.server_script_path = server_script_path
        self.mcp_session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.available_tools: list[AvailableTool] = []
        self.stdio = None
        self.write = None

    async def connect_to_server(self):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = self.server_script_path.endswith(".py")
        is_js = self.server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[self.server_script_path], env=None
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
            parameters: dict[str, object] = {
                **tool.inputSchema,
                "required": list(tool.inputSchema["properties"].keys()),
            }
            self.available_tools.append(
                {
                    "strict": True,
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "No description provided",
                    "parameters": parameters,
                }
            )
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def call_tool(self, tool_name: str, tool_args: dict[str, str | int | float]):
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
        try:
            result = await self.mcp_session.call_tool(tool_name, tool_args)

            error = extract_error(result.content[0].text)
            if error[0] is not None:
                print(f"Error calling tool {tool_name}: {error[0]} - {error[1]}")
                return None
        except Exception as e:
            print(f"Error calling tool {tool_name}: {e}")
            return None
        return result
