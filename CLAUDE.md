# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Run the application**: `uv run src/main.py`
- **Install dependencies**: `uv install`
- **Run tests**: Use Jupyter notebook at `src/tests.ipynb`

## Architecture Overview

This is an autonomous browsing agent that combines OpenAI's GPT models with Model Context Protocol (MCP) for browser automation. The system coordinates between three main components:

### Core Components

- **MCPClient** (`mcp_client.py`): Handles communication with MCP server for browser automation
  - Connects to Playwright MCP server at `/Users/Morgan/.nvm/versions/node/v20.13.0/lib/node_modules/@playwright/mcp/cli.js`
  - Manages tool discovery and execution
  - Provides error handling and connection management

- **MyAgent** (`my_agent.py`): Main agent orchestrator 
  - Uses OpenAI GPT-4.1 model for reasoning
  - Maintains conversation state and message history
  - Handles tool execution flow with user confirmation prompts
  - Implements persistent conversation loop

- **ConsoleDisplay** (`console_display.py`): Rich console interface
  - Two-column layout: conversation vs internal logs
  - Live updating display with thread-safe operations
  - Separates user interaction from system internals

### Data Flow

1. User input → MyAgent processes with OpenAI
2. OpenAI returns response + tool calls
3. MyAgent executes MCP tools via MCPClient
4. Results feed back to OpenAI for next iteration
5. Process continues until task completion

### Key Configuration

- Requires OpenAI API key in `.env` file
- Python 3.13+ required
- Uses `uv` for dependency management
- MCP server path hardcoded in `main.py`

### Agent Behavior

The agent is configured as a browsing agent (see `prompts.py`) with specific behavior for:
- Shopping site automation (example: mon-marche.fr)
- Product research and cart management
- Error recovery through page reloads
- Persistent task completion until user query resolved