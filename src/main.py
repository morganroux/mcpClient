import asyncio
from dotenv import load_dotenv
from mcp_client import MCPClient
from my_agent import MyAgent

load_dotenv()

SERVER_PATH = "/Users/Morgan/.nvm/versions/node/v20.13.0/lib/node_modules/@playwright/mcp/cli.js"



async def run():
    mcp_client = MCPClient(SERVER_PATH)
    agent = MyAgent(mcp_client)
    await agent.start()

def main():
    asyncio.run(run())

if __name__ == "__main__":
    main()
