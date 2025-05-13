import subprocess
import json
import logging
import threading
from time import sleep
import ollama


# Configure logging
logging.basicConfig(level=logging.INFO, format="[MCP] %(message)s")
logger = logging.getLogger("ServerLogger")


def log_stderr(stderr):
    """Logs and formats stderr output from the server."""
    for line in iter(stderr.readline, ""):
        logger.error(line.strip())


server_process = subprocess.Popen(
    [
        "/Users/Morgan/.local/bin/uv",
        "--directory",
        "/Users/Morgan/Programmation/python/mcp-behringer/mcp-behringer",
        "run",
        "server.py",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    stdin=subprocess.PIPE,
    text=True,
)

# Start a thread to handle stderr logging
stderr_thread = threading.Thread(target=log_stderr, args=(server_process.stderr,), daemon=True)
stderr_thread.start()


class MCPServer:
    def __init__(self, server):
        self.server = server
        self.message_id = 1
        self.initialize()

    def create_mcp_message(self, method_name, params):
        message = {
            "jsonrpc": "2.0",
            "method": method_name,
            "params": params,
            "id": self.message_id,
        }
        self.message_id += 1
        return json.dumps(message)

    def create_mcp_notification(self, method_name, params):
        message = {
            "jsonrpc": "2.0",
            "method": method_name,
            "params": params,
        }

        return json.dumps(message)

    def send_mcp_message(self, message):
        self.server.stdin.write(message + "\n")
        self.server.stdin.flush()

    def receive_mcp_message(self):
        server_output = json.loads(self.server.stdout.readline() or "{}")
        if "result" in server_output:
            return server_output["result"]
        else:
            return "Error"

    def initialize(self):
        init_message = self.create_mcp_message(
            "initialize",
            {
                "clientInfo": {"name": "Llama Agent", "version": "0.1"},
                "protocolVersion": "2024-11-05",
                "capabilities": {},
            },
        )

        self.send_mcp_message(init_message)
        response = self.receive_mcp_message()
        server_name = response["serverInfo"]["name"]
        print("Initializing  " + server_name + "...")

        init_complete_message = self.create_mcp_notification(
            "notifications/initialized", {}
        )
        self.send_mcp_message(init_complete_message)
        print("Initialization complete.")

mcp_server = MCPServer(server_process)


list_tools_message = mcp_server.create_mcp_message("tools/list", {})
mcp_server.send_mcp_message(list_tools_message)
response = mcp_server.receive_mcp_message()
# for tool in response["tools"]:
#     print(tool["name"])
#     print(tool["description"])
#     print(tool["inputSchema"]["properties"])
#     print("")
available_functions = []
for tool in response["tools"]:
    func = {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": {
                "type": "object",
                "properties": tool["inputSchema"]["properties"],
            },
        },
    }
    available_functions.append(func)


def run(question: str):
    client = ollama.Client()
    messages = [{"role": "user", "content": question}]
    done = False
    while not done:
        try:
            response = client.chat(
                model="llama3.2",
                messages=messages,
                tools=available_functions[:10],
            )
            print("======= Response =======")
            print(response)

            sleep(1)
            # wait for user to press enter
            # input("Press Enter to continue...")

            for tool in response.message.tool_calls or []:
                mcp_message = mcp_server.create_mcp_message(
                    tool.function.name,
                    tool.function.arguments,
                )
                mcp_server.send_mcp_message(mcp_message)
                response = mcp_server.receive_mcp_message()
                print("======= MCP Response =======")
                print(response)
                done = True

        except Exception as e:
            print("Error:", e)
            print("Retrying...")
            continue


run("Set the volume of the first channel to 0.5")
