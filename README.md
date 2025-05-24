# MCP Agent System

A Python-based agent system that combines OpenAI's GPT models with the Model Context Protocol (MCP) for automated browser interactions and tool use.

## Features

- 🤖 Integrates with OpenAI GPT-4 for advanced reasoning and decision making  
- 🌐 Uses MCP client for browser automation and tool invocation  
- 🔄 Robust error handling and automatic reconnection  
- 📝 Maintains conversation memory and agent state  
- ⚙️ Easily configurable via environment variables  

## Prerequisites

- Python 3.13+
- Node.js 20.x+
- OpenAI API key
- MCP CLI installed globally (`npm install -g @playwright/mcp`)
- [uv](https://github.com/astral-sh/uv) (for Python dependency management)

## Setup

1. **Clone the repository:**
   ```zsh
   git clone <repository-url>
   cd mcpClient
   ```

2. **Install dependencies with uv:**
   ```zsh
   uv install
   ```

3. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Start the agent system with:
```zsh
uv run src/main.py
```

The agent will:
1. Initialize the MCP server
2. Connect to OpenAI
3. Start an interactive session for user commands

## Architecture

- **MCPServer**: Manages communication with the MCP server  
- **OpenAIAgent**: Handles interactions with OpenAI's API  
- **AgentSystem**: Coordinates between MCP and OpenAI, maintaining conversation state  
- **ToolManager**: Discovers and manages available MCP tools  

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License – see the LICENSE file for details.
