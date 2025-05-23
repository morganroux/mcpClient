import asyncio
from dotenv import load_dotenv
from mcp_client import MCPClient
from my_agent import MyAgent

load_dotenv()

SERVER_PATH = "/Users/Morgan/.nvm/versions/node/v20.13.0/lib/node_modules/@playwright/mcp/cli.js"



async def run():
    mcp_client = MCPClient()
    await mcp_client.connect_to_server(SERVER_PATH)
    print(mcp_client.available_tools)
    agent = MyAgent(mcp_client)


def main():
    asyncio.run(run())
