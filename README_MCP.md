# Context7 MCP Server Setup

This repository is configured to use the [Context7 MCP Server](https://github.com/upstash/context7-mcp).

## Configuration

The configuration is located in `mcp.json` in the root of this repository.

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": [
        "-y",
        "@upstash/context7-mcp@latest"
      ]
    }
  }
}
```

## Usage

### For Cursor / VS Code / Windsurf

1.  Ensure you have Node.js installed (v18+).
2.  If your editor supports reading `mcp.json` from the workspace root, it should automatically detect the server.
3.  Otherwise, you may need to manually add the configuration to your global MCP settings.

### Manual Run

You can also run the server manually to verify it works:

```bash
npx -y @upstash/context7-mcp@latest
```
