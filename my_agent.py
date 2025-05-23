import json
from openai import OpenAI


class MyAgent:
    def __init__(self, mcp_client, prompt=None):
        self.model = "gpt-4.1"
        self.openai = OpenAI()
        self.messages = [self.format_system_message(prompt)] if prompt else []
        self.mcp_client = mcp_client

    def format_system_message(self, message):
        return {"role": "system", "content": message}
    def format_user_message(self, message):
        return {"role": "user", "content": message}
    def format_assistant_message(self, message):
        return {"role": "assistant", "content": message}

    def get_response(self, llm_input: list[str]):
        llm_response = self.openai.responses.create(
            model=self.model, input=llm_input, tools=self.mcp_client.available_tools
        )
        tool_calls = list(
            filter(lambda output: output.type == "function_call", llm_response.output)
        )
        answer = llm_response.output_text
        print("Answer: ", answer)
        print("Tool calls: ", tool_calls)
        return answer, tool_calls

    async def run_tool(self, tool_call):

        print("Running tool: ", tool_call.name)
        print("with arguments: ", tool_call.arguments)
        input("Press Enter to continue...")
        toolcall_message = tool_call.to_dict()
        result = await self.mcp_client.call_tool(
            tool_call.name, json.loads(tool_call.arguments)
        )
        complete_result_message = {
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(result),
        }
        short_result_message = {
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(result)[:100],
        }
        print("Tool result: ", complete_result_message)

        return toolcall_message, complete_result_message, short_result_message
    async def loop(self):
        tool_calls = None
        while True:
            user_input = input("User: ")
            self.messages.append(self.format_user_message(user_input))
            answer, tool_calls = self.get_response(self.messages)
            self.messages.append(self.format_assistant_message(answer))
            print("Assistant: ", answer)
            while tool_calls is not None:
                print("Tool calls: ", tool_calls)
                inner_messages = self.messages.copy()
                for tool_call in tool_calls:
                    toolcall_message, complete_result_message, short_result_message = await self.run_tool(tool_call)
                    inner_messages.append(toolcall_message)
                    self.messages.append(toolcall_message)
                    inner_messages.append(complete_result_message)
                    self.messages.append(short_result_message)
                answer, tool_calls = self.get_response(inner_messages)
                self.messages.append(self.format_assistant_message(answer))
                print("Assistant: ", answer)


