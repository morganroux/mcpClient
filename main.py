import subprocess
import json
import logging
import threading
from time import sleep
import ollama


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ServerLogger")


def log_stderr(stderr):
    """Logs and formats stderr output from the server."""
    for line in iter(stderr.readline, ""):
        logger.error(line.strip())


server = subprocess.Popen(
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
stderr_thread = threading.Thread(target=log_stderr, args=(server.stderr,), daemon=True)
stderr_thread.start()


def create_mcp_message(method_name, params, id=None):
    message = {"jsonrpc": "2.0", "method": method_name, "params": params, "id": id}
    return json.dumps(message)


def send_mcp_message(message):
    server.stdin.write(message + "\n")
    server.stdin.flush()


def receive_mcp_message():
    server_output = json.loads(server.stdout.readline() or "{}")
    if "result" in server_output:
        return server_output["result"]
    else:
        return "Error"


message_id = 1
init_message = create_mcp_message(
    "initialize",
    {
        "clientInfo": {"name": "Llama Agent", "version": "0.1"},
        "protocolVersion": "2024-11-05",
        "capabilities": {},
    },
    message_id,
)

send_mcp_message(init_message)
response = receive_mcp_message()
server_name = response["serverInfo"]["name"]
print("Initializing  " + server_name + "...")

init_complete_message = create_mcp_message("notifications/initialized", {})
send_mcp_message(init_complete_message)
print("Initialization complete.")

# ==================

message_id += 1
list_tools_message = create_mcp_message("tools/list", {}, message_id)
send_mcp_message(list_tools_message)
response = json.loads(server.stdout.readline())["result"]
# for tool in response["tools"]:
#     print(tool["name"])
#     print(tool["description"])
#     print(tool["inputSchema"]["properties"])
#     print("")
# available_functions = []
# for tool in response["tools"]:
#     func = {
#         "type": "function",
#         "function": {
#             "name": tool["name"],
#             "description": tool["description"],
#             "parameters": {
#                 "type": "object",
#                 "properties": tool["inputSchema"]["properties"],
#             },
#         },
#     }
#     available_functions.append(func)


# def run(question: str):
#     client = ollama.Client()
#     messages = [{"role": "user", "content": question}]
#     done = False
#     while not done:
#         try:
#             response = client.chat(
#                 model="llama3.2",
#                 messages=messages,
#                 tools=available_functions,
#             )
#             print("======= Response =======")
#             print(response)

#             sleep(1)
#             # wait for user to press enter
#             # input("Press Enter to continue...")

#             for tool in response.message.tool_calls or []:
#                 mcp_message = create_mcp_message(
#                     tool.function.name,
#                     tool.function.arguments,
#                     message_id,
#                 )
#                 send_mcp_message(mcp_message)
#                 message_id += 1
#                 # Wait for the response from the server
#                 response = receive_mcp_message()
#                 # Check if the response contains a result
#                 print("======= MCP Response =======")
#                 print(response)
#                 done = True

#         except Exception as e:
#             print("Error:", e)
#             print("Retrying...")
#             continue


# run("Set the volume of the first channel to 0.5")
