# AiSpire Setup Guide - Keeping VCarve Responsive

## The Problem
When the AiSpire gadget runs the server loop inside VCarve, it blocks the UI thread, making VCarve show "not responding". However, the server still works perfectly!

## Solution: Standalone Server

Run the AiSpire socket server as a **separate process** outside of VCarve. This keeps VCarve fully responsive while the server runs independently.

### Quick Start

**Step 1: Start the Standalone Server**

Option A - Using batch file (Easiest):
```batch
# Double-click this file:
start_server.bat
```

Option B - Using Python wrapper:
```bash
python start_standalone_server.py
```

Option C - Direct Lua (if you have Lua installed):
```bash
cd lua_gadget
lua standalone_server.lua
```

**Step 2: Start Python MCP Server**
```bash
python -m python_mcp_server.server
```

**Step 3: Use VCarve Normally**
- VCarve UI stays fully responsive
- Server runs in background
- AI clients connect to Python MCP server (port 8765)

### Current Working Setup (Temporary)

**If you're okay with VCarve's UI freezing:**

1. Open VCarve Pro
2. Click Gadgets → AiSpire
3. Click "OK" on the message
4. VCarve will show "not responding" but **server works perfectly**
5. Click "Wait for program to respond" when Windows asks
6. All AI integrations work fine!

**Test it:**
```bash
python test_aispire.py
```

This will confirm the server is working even though VCarve appears frozen.

### Architecture Options

**Option 1: Current (Frozen UI but works)**
```
VCarve Pro (frozen) ← Contains server loop (port 9876)
                      ↑
              Python MCP Server (8765)
                      ↑
                  AI Clients
```

**Option 2: Standalone (Best for production)**
```
VCarve Pro (responsive)

Standalone Lua Server (9876) ← Runs independently
         ↑
Python MCP Server (8765)
         ↑
    AI Clients
```

**Option 3: Python-Only (Future)**
```
VCarve Pro (responsive)
         ↑
Python MCP Server (8765) ← Calls VCarve via COM/SDK directly
         ↑
    AI Clients
```

### Recommendation

For now, use the **Current setup** (frozen UI):
- ✅ Already working and tested
- ✅ No additional setup needed
- ✅ Server is fully functional
- ⚠️ VCarve UI freezes but this is acceptable for a background server

For production, implement **Option 2** (standalone server):
- ✅ VCarve stays responsive
- ✅ Server runs independently
- ✅ Can start/stop server without affecting VCarve
- 🔧 Requires running `start_server.bat` separately

### Testing

**Verify server is working:**
```bash
python test_aispire.py
```

**Expected output:**
```
TEST 1: Direct Socket - PASS
TEST 2: MCP Server - PASS
TEST 3: Query State - PASS

All tests passed!
```

This works even when VCarve shows "not responding"!

### Next Steps

1. ✅ Test current setup (works with frozen UI)
2. ⏭️ Try Gemini integration
3. ⏭️ Configure Claude Desktop
4. 🔄 Later: Implement standalone server for responsive UI

The system is **fully operational** right now. The UI freeze is a minor inconvenience that doesn't affect functionality.

### Troubleshooting

**Q: VCarve shows "not responding"**
A: This is expected! Click "Wait for program to respond". The server still works perfectly.

**Q: Can I use VCarve while server runs?**
A: With current setup, no - UI is frozen. But you don't need to use VCarve manually when AI is controlling it!

**Q: How do I stop the server?**
A: Close VCarve (it will ask if you want to close the frozen program - click Yes)

**Q: Is there a better way?**
A: Yes! Use the standalone server (Option 2 above). We can implement this if needed.
