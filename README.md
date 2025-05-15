# MCP Agent System

An agentic system that combines OpenAI's GPT models with Minecraft Control Protocol (MCP) for automated browser interactions.

## Features

- 🤖 OpenAI GPT-4 integration for intelligent decision making
- 🌐 MCP client for browser automation
- 🔄 Robust error handling and reconnection logic
- 📝 Conversation memory and state management
- ⚙️ Configurable through environment variables

## Prerequisites

- Python 3.13 or higher
- Node.js 20.x or higher
- OpenAI API key
- MCP CLI installed globally (`npm install -g @playwright/mcp`)

## Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd mcpclient
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -e .
```

4. Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run the agent system:

```bash
python main.py
```

The system will:
1. Initialize the MCP server
2. Connect to OpenAI
3. Start an interactive session where you can give commands to the agent

## Architecture

The system consists of several key components:

- `MCPServer`: Handles communication with the MCP server
- `OpenAIAgent`: Manages interactions with OpenAI's API
- `AgentSystem`: Coordinates between MCP and OpenAI, maintaining conversation state
- `ToolManager`: Manages available MCP tools and their execution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details
