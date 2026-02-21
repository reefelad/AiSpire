# AiSpire — Project Context for Gemini CLI

## What This Project Is
AiSpire is an MCP Server + Lua Gadget plugin for Vectric VCarve Pro v12.5.
A Lua gadget runs a non-blocking TCP socket server inside VCarve (port 9876).
A Python MCP server / Gemini script connects to it so LLMs can control VCarve.

## Key File Locations
- **Installed gadget** (what VCarve actually runs):
  - `C:\ProgramData\Vectric\VCarve Pro\V12.5\Gadgets\aispire\aispire.lua` — entry point
  - `C:\ProgramData\Vectric\VCarve Pro\V12.5\Gadgets\aispire\modules\server.inc` — socket server + SDK wrappers
  - `C:\ProgramData\Vectric\VCarve Pro\V12.5\Gadgets\aispire\modules\json.inc` — JSON encoder/decoder
- **Source repo** (edit here, copy to installed location):
  - `lua_gadget/aispire.lua` → maps to installed `aispire.lua`
  - `lua_gadget/server.lua` → maps to installed `modules/server.inc`
  - `lua_gadget/json.lua` → maps to installed `modules/json.inc`
- **Python MCP server** (for Claude Desktop): `aispire_mcp_stdio.py`
- **Gemini chat script**: `aispire_gemini.py`

## Architecture: Non-Blocking Heartbeat
VCarve's HTML_Dialog is MODAL (blocks the Lua thread). We keep the server alive using:
- JavaScript `setInterval` inside the dialog calls `btn.click()` every 200ms
- Button has `class="LuaButton"` and is off-screen (NOT `display:none` — browser skips hidden clicks)
- Each click triggers `OnLuaButton_btn_heartbeat(dialog)` in Lua
- That function calls `ServerModule.runServerTick()` — ONE non-blocking accept+receive, then returns
- **Never suggest blocking approaches** — user has rejected this multiple times

## VCarve SDK — CONFIRMED PATTERNS (do not guess)
```lua
-- Job
local vj = VectricJob()     -- constructor, call each time
local name = vj.Name         -- string PROPERTY, NOT vj:GetName()
local w    = vj.Width        -- number PROPERTY (mm)
local h    = vj.Height       -- number PROPERTY (mm)
vj:Refresh2DView()           -- refresh after geometry changes

-- Managers
local lm = vj.LayerManager   -- PROPERTY, not vj:GetLayerManager()
local tm = ToolpathManager() -- standalone constructor, not a job method
local mb = MaterialBlock()   -- standalone constructor

-- Vector creation — ONLY WORKING METHOD: DXF import
local nl = string.char(10)   -- use this for newlines, NOT "\n" (JSON mangles it)
local tmp = os.tmpname() .. ".dxf"
local f = io.open(tmp, "w")
f:write(table.concat({"0","SECTION","2","ENTITIES",
    "0","CIRCLE","8","0",
    "10","100","20","100","30","0","40","50",
    "0","ENDSEC","0","EOF",""}, nl))
f:close()
VectricJob():ImportDxfDwg(tmp)
os.remove(tmp)
```

## What Does NOT Work
- `Contour()` / `CadContour()` — not accessible from gadgets
- `vj:GetLayerManager()` — use `vj.LayerManager` property instead
- `vj:GetToolpathManager()` — use `ToolpathManager()` constructor instead
- `vj:GetName()` / `vj:GetJobWidth()` — use `.Name` / `.Width` properties
- `Box2D(x, y, w, h)` — wrong; use `Box2D(Point2D(0,0), Point2D(w,h))`
- `"\n"` in Lua strings through MCP/JSON — use `string.char(10)`

## SDK Context Architecture
`require "strict"` is active in aispire.lua. SDK globals only exist in `main()` scope.
Modules loaded via `dofile()` (like server.inc) cannot see them.
Fix: `aispire.lua` passes them via `ServerModule.setVectricContext({...rawget(_G,...)})`.
`server.inc` stores in `vectricContext`, exposes via `SDK(name)`, `getJob()`, etc.
The `_G_ref` key passes the entire VCarve global table for sandbox metatable fallback.

## execute_lua Sandbox
The sandbox has `setmetatable(sandbox, {__index = _G_ref})` so ALL VCarve globals
(VectricJob, ToolpathManager, os, io, math, etc.) are accessible without explicit listing.

## Socket Protocol
- Port: 9876, Host: 127.0.0.1
- Auth token: `a8f5f167f44f4964e6c998dee827110c`
- Command format: `{"command_type": "execute_code"|"execute_function"|"query_state", "payload": {...}, "id": "...", "auth": "..."}`
- Response: `{"status": "success"|"error", "result": {"message": "...", "data": {...}}}`

## What Currently Works
- `query_state` — returns job name, width, height, app version
- `execute_lua` — full VCarve SDK access, DXF vector creation works
- `execute_function("create_circle", [x, y, r])` — draws circle via DXF
- `execute_function("create_rectangle", [x1,y1,x2,y2])` — draws rectangle via DXF

## What Still Needs Work
- Layer enumeration (GetNumLayers/GetLayerName API not confirmed)
- Text creation (DXF TEXT entity not yet tested)
- Toolpath creation (current functions are stubs/mock)
- query_state always returns empty layers list

## Build / Deploy
When you edit source files in `lua_gadget/`, copy them to the installed location:
```
copy lua_gadget\aispire.lua "C:\ProgramData\Vectric\VCarve Pro\V12.5\Gadgets\aispire\aispire.lua"
copy lua_gadget\server.lua "C:\ProgramData\Vectric\VCarve Pro\V12.5\Gadgets\aispire\modules\server.inc"
copy lua_gadget\json.lua "C:\ProgramData\Vectric\VCarve Pro\V12.5\Gadgets\aispire\modules\json.inc"
```
Then restart VCarve and re-run the gadget.

## Gemini Script Usage
```
pip install google-generativeai
set GEMINI_API_KEY=<key from https://aistudio.google.com/apikey>
python aispire_gemini.py
```
