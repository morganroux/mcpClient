import subprocess
import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent.log")
    ]
)
logger = logging.getLogger("AgentSystem")

@dataclass
class AgentState:
    """Maintains the state of the agent system."""
    messages: List[Dict[str, str]]
    available_tools: List[Dict[str, Any]]
    is_initialized: bool = False
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class MCPServer:
    """Handles communication with the MCP server."""
    
    def __init__(self, node_path: str, mcp_cli_path: str):
        self.node_path = node_path
        self.mcp_cli_path = mcp_cli_path
        self.server_process = None
        self.stderr_thread = None
        self.message_id = 1
        self.initialize_server()

    def initialize_server(self) -> None:
        """Initialize the MCP server process."""
        try:
            self.server_process = subprocess.Popen(
                [self.node_path, self.mcp_cli_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
            )
            
            # Start stderr logging thread
            self.stderr_thread = threading.Thread(
                target=self._log_stderr,
                args=(self.server_process.stderr,),
                daemon=True
            )
            self.stderr_thread.start()
            
            logger.info("MCP server process started")
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            raise

    def _log_stderr(self, stderr) -> None:
        """Log stderr output from the server."""
        for line in iter(stderr.readline, ""):
            logger.error(f"MCP Server: {line.strip()}")

    def create_message(self, method_name: str, params: Dict[str, Any], is_notification: bool = False) -> str:
        """Create an MCP message."""
        message = {
            "jsonrpc": "2.0",
            "method": method_name,
            "params": params,
        }
        if not is_notification:
            message["id"] = self.message_id
            self.message_id += 1
        return json.dumps(message)

    def send_message(self, message: str) -> None:
        """Send a message to the MCP server."""
        try:
            self.server_process.stdin.write(message + "\n")
            self.server_process.stdin.flush()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def receive_message(self) -> Dict[str, Any]:
        """Receive a message from the MCP server."""
        try:
            response = self.server_process.stdout.readline()
            if not response:
                raise ConnectionError("No response from MCP server")
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MCP response: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise

    def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection."""
        try:
            # Send initialization message
            init_message = self.create_message(
                "initialize",
                {
                    "clientInfo": {"name": "Agent System", "version": "1.0.0"},
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                }
            )
            self.send_message(init_message)
            response = self.receive_message()
            
            if "result" not in response:
                raise ConnectionError("Failed to initialize MCP server")
            
            # Send initialization complete notification
            init_complete = self.create_message(
                "notifications/initialized",
                {},
                is_notification=True
            )
            self.send_message(init_complete)
            
            logger.info(f"Initialized MCP server: {response['result']['serverInfo']['name']}")
            return response["result"]
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        try:
            message = self.create_message("tools/list", {})
            self.send_message(message)
            response = self.receive_message()
            
            if "result" not in response:
                raise ConnectionError("Failed to get tools list")
            
            tools = []
            for tool in response["result"]["tools"]:
                parameters = {
                    **tool["inputSchema"],
                    "required": list(tool["inputSchema"]["properties"].keys()),
                }
                tools.append({
                    "type": "function",
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": parameters,
                })
            return tools
        except Exception as e:
            logger.error(f"Failed to get tools: {e}")
            raise

class OpenAIAgent:
    """Manages interactions with OpenAI's API."""
    
    def __init__(self, model: str = "gpt-4"):
        self.client = OpenAI()
        self.model = model
        self.state = AgentState(messages=[], available_tools=[])

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.state.messages.append({"role": role, "content": content})

    def process_tool_calls(self, tool_calls: List[Dict[str, Any]], mcp_server: MCPServer) -> None:
        """Process tool calls from the OpenAI response."""
        for tool_call in tool_calls:
            if tool_call.type != "function_call":
                continue
                
            logger.info(f"Executing tool: {tool_call.name}")
            try:
                mcp_message = mcp_server.create_message(
                    tool_call.name,
                    tool_call.arguments
                )
                mcp_server.send_message(mcp_message)
                mcp_response = mcp_server.receive_message()
                
                # Add tool response to conversation
                self.add_message(
                    "assistant",
                    f"Tool {tool_call.name} response: {json.dumps(mcp_response)}"
                )
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                self.state.last_error = str(e)
                raise

    def run_conversation(self, mcp_server: MCPServer, user_input: str) -> None:
        """Run a conversation turn with the agent."""
        self.add_message("user", user_input)
        
        while True:
            try:
                # Get response from OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.state.messages,
                    tools=self.state.available_tools,
                    tool_choice="auto"
                )
                
                # Add assistant's response to conversation
                self.add_message("assistant", response.choices[0].message.content)
                
                # Process any tool calls
                if response.choices[0].message.tool_calls:
                    self.process_tool_calls(
                        response.choices[0].message.tool_calls,
                        mcp_server
                    )
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Conversation error: {e}")
                self.state.retry_count += 1
                if self.state.retry_count >= self.state.max_retries:
                    raise
                time.sleep(1)  # Wait before retrying

class AgentSystem:
    """Main agent system coordinating MCP and OpenAI interactions."""
    
    def __init__(self):
        self.mcp_server = None
        self.openai_agent = None
        self.initialize()

    def initialize(self) -> None:
        """Initialize the agent system."""
        try:
            # Initialize MCP server
            node_path = "/Users/Morgan/.nvm/versions/node/v20.13.0/bin/node"
            mcp_cli_path = "/Users/Morgan/.nvm/versions/node/v20.13.0/lib/node_modules/@playwright/mcp/cli.js"
            
            self.mcp_server = MCPServer(node_path, mcp_cli_path)
            self.mcp_server.initialize()
            
            # Initialize OpenAI agent
            self.openai_agent = OpenAIAgent()
            self.openai_agent.state.available_tools = self.mcp_server.get_available_tools()
            self.openai_agent.state.is_initialized = True
            
            logger.info("Agent system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent system: {e}")
            raise

    def run_interactive(self) -> None:
        """Run the agent system in interactive mode."""
        print("\nAgent System Ready! Type 'exit' to quit.")
        print("Enter your command or question:")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() == "exit":
                    break
                    
                self.openai_agent.run_conversation(self.mcp_server, user_input)
                print("\nAgent:", self.openai_agent.state.messages[-1]["content"])
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error in interactive session: {e}")
                print(f"\nError: {e}")
                if self.openai_agent.state.retry_count >= self.openai_agent.state.max_retries:
                    print("Maximum retries exceeded. Exiting...")
                    break

def main():
    """Main entry point."""
    try:
        agent_system = AgentSystem()
        agent_system.run_interactive()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
