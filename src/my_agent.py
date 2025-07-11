import json
from typing_extensions import Literal
from openai import OpenAI
from openai.types.responses import (
    ResponseInputParam,
    EasyInputMessageParam,
    FunctionToolParam,
    ResponseFunctionToolCall,
    ResponseFunctionToolCallParam,
    ResponseInputItemParam,
)

from mcp_client import MCPClient
from console import console


class MyAgent:
    def __init__(self, mcp_client: MCPClient, prompt: str | None = None):
        self.model = "gpt-4.1"
        self.openai = OpenAI()
        self.messages: ResponseInputParam = (
            [self.format_developer_message(prompt)] if prompt else []
        )
        self.mcp_client = mcp_client

    def format_message(
        self, role: Literal["user", "assistant", "system", "developer"], content: str
    ):
        return EasyInputMessageParam(role=role, content=content)

    def format_developer_message(self, message: str):
        return self.format_message(role="developer", content=message)

    def format_user_message(self, message: str):
        return self.format_message(role="user", content=message)

    def format_assistant_message(self, message: str):
        return self.format_message(role="assistant", content=message)

    def get_response(self, llm_input: ResponseInputParam):
        console.print("\nThinking...\n", style="cyan")
        llm_response = self.openai.responses.create(
            model=self.model,
            input=llm_input,
            tools=map(
                lambda tool: FunctionToolParam(**tool),
                self.mcp_client.available_tools,
            ),
        )
        tool_calls = [
            output
            for output in llm_response.output
            if isinstance(output, ResponseFunctionToolCall)
        ]
        answer = llm_response.output_text
        return answer, tool_calls

    async def run_tool(self, tool_call: ResponseFunctionToolCall):

        console.rule("Tool Call")
        console.print("Running tool: ", tool_call.name, style="magenta")
        console.print("with arguments: ", tool_call.arguments, style="magenta")
        console.input("Press Enter to continue...")
        toolcall_message = ResponseFunctionToolCallParam(**tool_call.model_dump())
        result = await self.mcp_client.call_tool(
            tool_call.name, json.loads(tool_call.arguments)
        )
        complete_result_message: ResponseInputItemParam = {
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(result),
            "status": "completed",
        }
        short_result_message: ResponseInputItemParam = {
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(result)[:100],
        }
        console.print(f"\nTool result: {short_result_message}\n")

        return toolcall_message, complete_result_message, short_result_message

    async def loop(self):
        tool_calls: list[ResponseFunctionToolCall] = []
        while True:
            user_input = console.input("User: ")
            self.messages.append(self.format_user_message(user_input))
            answer, tool_calls = self.get_response(self.messages)
            self.messages.append(self.format_assistant_message(answer))
            console.rule("Assistant")
            console.print(f"{answer}\n")

            while len(tool_calls) > 0:
                console.print(f"Tool calls: {tool_calls}", style="yellow")
                inner_messages = self.messages.copy()
                for tool_call in tool_calls:
                    toolcall_message, complete_result_message, short_result_message = (
                        await self.run_tool(tool_call)
                    )
                    inner_messages.append(toolcall_message)
                    self.messages.append(toolcall_message)
                    inner_messages.append(complete_result_message)
                    self.messages.append(short_result_message)
                answer, tool_calls = self.get_response(inner_messages)
                self.messages.append(self.format_assistant_message(answer))
                console.rule("Assistant")
                console.print(f"{answer}\n")

    async def start(self, system_prompt: str):
        console.print("Starting agent...")
        await self.mcp_client.connect_to_server()
        self.messages.append(self.format_developer_message(system_prompt))
        console.rule('Agent Started')
        await self.loop()
