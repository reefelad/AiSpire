# AiSpire Testing & Integration Guide

## Quick Test

To verify AiSpire is working:

```bash
python test_aispire.py
```

This will test:
1. Direct VCarve socket connection (port 9876)
2. Python MCP server connection (port 8765)
3. VCarve state queries

## Prerequisites

Before testing, ensure:
- ✅ VCarve Pro is running
- ✅ AiSpire gadget is launched (Gadgets → AiSpire)
- ✅ You clicked "OK" on the startup message (server loop running)
- ✅ Python MCP server is running: `python -m python_mcp_server.server`

## Integration Options

### 1. Claude Desktop Integration

**Setup:**
1. Open Claude Desktop settings
2. Add MCP server configuration:
   ```json
   {
     "mcpServers": {
       "aispire": {
         "command": "python",
         "args": ["-m", "python_mcp_server.server"],
         "cwd": "C:/Users/dales/OneDrive/Documents/GitHub/AiSpire"
       }
     }
   }
   ```
3. Restart Claude Desktop

**Usage:**
Ask Claude to control VCarve:
- "What version of VCarve is running?"
- "Execute this Lua code: return 42"
- "Get the current job layers"

### 2. Gemini Integration

**Setup:**
1. Get Gemini API key from: https://makersuite.google.com/app/apikey
2. Install Gemini library:
   ```bash
   pip install google-generativeai
   ```
3. Set your API key:
   ```bash
   # Windows
   set GEMINI_API_KEY=your-api-key-here

   # Linux/Mac
   export GEMINI_API_KEY=your-api-key-here
   ```

**Usage:**
```bash
python gemini_integration.py
```

Then chat with Gemini naturally:
- "What's the Lua version in VCarve?"
- "Get the job information"
- "Execute: return string.upper('hello vcarve')"

Gemini will automatically call VCarve functions as needed!

### 3. Direct API Access

**Python Example:**
```python
import socket
import json

def vcarve_execute(lua_code):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 9876))

    command = {
        'command_type': 'execute_code',
        'payload': {'code': lua_code},
        'id': 'my_command',
        'auth': 'a8f5f167f44f4964e6c998dee827110c'
    }

    s.send((json.dumps(command) + '\n').encode())
    response = json.loads(s.recv(4096).decode())
    s.close()

    return response['result']['data']

# Use it
result = vcarve_execute('return 2 + 2')
print(result)  # 4
```

**cURL Example:**
```bash
# Via MCP server
echo '{"type":"execute_lua","code":"return 42","auth":"a8f5f167f44f4964e6c998dee827110c","id":"test"}' | nc localhost 8765
```

### 4. Custom LLM Integration

Any LLM that supports function calling or tool use can integrate:

**Required Functions:**
1. `execute_lua(code: string)` - Execute Lua code
2. `query_state()` - Get VCarve state

**Connection:**
- **MCP Server**: `localhost:8765` (recommended)
- **Direct Socket**: `localhost:9876` (advanced)

**Authentication:**
- Default token: `a8f5f167f44f4964e6c998dee827110c`
- Change in: `lua_gadget/modules/server.lua` (line 20)

## Troubleshooting

### Tests Fail with Timeout

**Problem:** Socket connection times out

**Solutions:**
1. Ensure VCarve is running
2. Ensure AiSpire gadget is active (Gadgets → AiSpire)
3. **IMPORTANT:** Click "OK" on the startup message box (this starts the server loop!)
4. Check Windows Firewall isn't blocking ports 9876 or 8765

### MCP Server Not Running

**Start it:**
```bash
cd C:/Users/dales/OneDrive/Documents/GitHub/AiSpire
python -m python_mcp_server.server
```

**Run in background:**
```bash
# Windows
start /B python -m python_mcp_server.server

# Linux/Mac
python -m python_mcp_server.server &
```

### Authentication Failed

The default auth token is: `a8f5f167f44f4964e6c998dee827110c`

Ensure your commands include:
```json
{
  "auth": "a8f5f167f44f4964e6c998dee827110c"
}
```

## Architecture

```
┌─────────────────┐
│   AI Client     │  (Claude, Gemini, Custom)
│  (Any LLM)      │
└────────┬────────┘
         │
         ↓ HTTP/WebSocket/Socket
┌─────────────────┐
│  Python MCP     │  Port 8765
│     Server      │  (Translation Layer)
└────────┬────────┘
         │
         ↓ Socket
┌─────────────────┐
│  Lua Socket     │  Port 9876
│     Server      │  (VCarve Gadget)
└────────┬────────┘
         │
         ↓ SDK Calls
┌─────────────────┐
│  VCarve Pro     │
│   (CAD/CAM)     │
└─────────────────┘
```

## Available Commands

### execute_code
Execute arbitrary Lua code:
```json
{
  "command_type": "execute_code",
  "payload": {
    "code": "return 42"
  },
  "id": "cmd1",
  "auth": "a8f5f167f44f4964e6c998dee827110c"
}
```

### query_state
Get VCarve application state:
```json
{
  "command_type": "query_state",
  "payload": {},
  "id": "cmd2",
  "auth": "a8f5f167f44f4964e6c998dee827110c"
}
```

Returns:
- Job information (materials, dimensions, etc.)
- Application info (version, paths, etc.)
- Layer information (active layers, visibility, etc.)

## Performance

- **Latency**: ~1-5ms for simple commands
- **Throughput**: 100+ commands/second
- **Concurrent Connections**: Multiple AI clients can connect simultaneously

## Security Notes

⚠️ **Important:**
- The default auth token should be changed in production
- Only bind to localhost (127.0.0.1) for security
- Don't expose ports 9876 or 8765 to the internet
- VCarve operations can modify your projects - use with caution!

## Next Steps

1. ✅ Run `python test_aispire.py` to verify everything works
2. 🤖 Set up Gemini integration for voice/text control
3. 🎯 Configure Claude Desktop for AI-assisted CAD/CAM
4. 🚀 Build custom automation scripts

Happy CNC programming with AI! 🎉
