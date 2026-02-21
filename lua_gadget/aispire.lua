-- VECTRIC LUA SCRIPT
-- AiSpire - AI-Powered VCarve Control
-- Non-Blocking Heartbeat Architecture
-- Version: 1.1.0

require "strict"

-- Global state for server (needed for OnLuaButton callbacks which are global)
local ServerRunning = false
local ServerModule = nil
local UIModule = nil
local JsonModule = nil
local HeartbeatCount = 0

-- CRITICAL: This function is called by the JavaScript setInterval timer.
-- VCarve routes HTML button clicks to global Lua functions named OnLuaButton_<id>.
-- The button MUST be rendered (not display:none) for the click event to fire.
-- We use position:absolute off-screen so the button is rendered but invisible.
function OnLuaButton_btn_heartbeat(dialog)
    HeartbeatCount = HeartbeatCount + 1

    if ServerRunning and ServerModule then
        -- Single-pass, non-blocking server tick.
        -- runServerTick() uses settimeout(0) and does ONE accept + ONE receive, then returns.
        local success, err = pcall(function()
            ServerModule.runServerTick()
        end)

        if not success and UIModule then
            UIModule.log("ERROR", "runServerTick failed: " .. tostring(err))
        end
    end

    -- NOTE: Do NOT call dialog:SetFieldHTML() or dialog:UpdateControl() here.
    -- The dialog object in OnLuaButton_ callbacks does not support those methods.
    -- UI updates (tick counter) are handled by JavaScript directly.

    -- CRITICAL: return true keeps the dialog open
    return true
end

-- Main entry point
function main(script_path)
    -- VCarve passes the directory path (without filename) as script_path
    local gadget_dir = script_path
    if not gadget_dir:match("[/\\]$") then
        gadget_dir = gadget_dir .. "\\"
    end

    -- Set up lua_modules path for LuaSocket
    local version = _VERSION:match("%d+%.%d+")
    if version then
        package.path = gadget_dir .. 'lua_modules\\share\\lua\\' .. version .. '\\?.inc;' ..
                       gadget_dir .. 'lua_modules\\share\\lua\\' .. version .. '\\?\\init.inc;' .. package.path
        package.cpath = gadget_dir .. 'lua_modules\\lib\\lua\\' .. version .. '\\?.so;' ..
                        gadget_dir .. 'lua_modules\\lib\\lua\\' .. version .. '\\?.dll;' .. package.cpath
    end

    -- Try to load socket
    local socket_ok, socket = pcall(require, "socket")
    if not socket_ok then
        DisplayMessageBox("ERROR: LuaSocket failed to load:\n" .. tostring(socket))
        return true
    end

    -- Load our modules
    JsonModule = dofile(gadget_dir .. "modules\\json.inc")
    ServerModule = dofile(gadget_dir .. "modules\\server.inc")
    UIModule = dofile(gadget_dir .. "modules\\ui_manager.inc")

    -- Set up the server
    ServerModule.setJson(JsonModule)
    ServerModule.setUiManager(UIModule)

    -- Log startup
    UIModule.log("INFO", "AiSpire Gadget starting (Non-Blocking Heartbeat)...")
    UIModule.log("INFO", "Version: 1.1.0")

    -- Try to start server
    if not ServerModule.startServer() then
        local errorMsg = ServerModule.getLastError() or "Unknown error"
        UIModule.log("ERROR", "Failed to start server: " .. errorMsg)
        DisplayMessageBox("AiSpire: Failed to start server:\n" .. errorMsg)
        return true
    end

    ServerRunning = true
    UIModule.log("SUCCESS", "Server started on port " .. ServerModule.CONFIG.PORT)

    -- CRITICAL: Pass VCarve SDK objects to the server module.
    -- SDK globals (VectricJob, Global, Contour, etc.) are ONLY available in main() scope.
    -- Modules loaded via dofile() cannot access them via rawget(_G, ...).
    -- We capture them here and pass them through so server.inc can use them.
    -- NOTE: rawget(_G, name) is used instead of bare names to avoid strict mode errors.
    ServerModule.setVectricContext({
        VectricJob       = rawget(_G, "VectricJob"),
        Global           = rawget(_G, "Global"),
        Point2D          = rawget(_G, "Point2D"),
        Box2D            = rawget(_G, "Box2D"),
        Contour          = rawget(_G, "Contour"),
        Text             = rawget(_G, "Text"),
        Transformation2D = rawget(_G, "Transformation2D"),
        Tool             = rawget(_G, "Tool"),
    })

    -- Diagnostic: confirm server state
    local serverState = ServerModule.getServerState()
    if serverState then
        UIModule.log("INFO", "Server state: isRunning=" .. tostring(serverState.isRunning) ..
                             ", hasSocket=" .. tostring(serverState.hasSocket) ..
                             ", port=" .. tostring(serverState.port))
    end

    -- Build the HTML dialog with the heartbeat mechanism.
    -- KEY FIX: The trigger button uses position:absolute off-screen instead of display:none.
    -- display:none causes the browser engine to skip the click() dispatch entirely.
    -- position:absolute off-screen keeps the element rendered so click() fires properly.
    local html = [[
<!DOCTYPE html>
<html>
<head>
    <title>AiSpire Server</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
        }
        .container {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            color: #333;
        }
        h1 {
            color: #667eea;
            margin-top: 0;
            font-size: 24px;
            text-align: center;
        }
        .status-bar {
            background-color: #d4edda;
            border: 2px solid #28a745;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            text-align: center;
        }
        .status-text {
            font-size: 18px;
            font-weight: bold;
            color: #155724;
        }
        .info-box {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 14px;
        }
        .info-label {
            font-weight: bold;
            color: #666;
        }
        .info-value {
            font-family: 'Courier New', monospace;
            color: #333;
            font-weight: bold;
        }
        .stats {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        .stats h3 {
            margin-top: 0;
            color: #667eea;
            font-size: 16px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .stat-item:last-child {
            border-bottom: none;
        }
        .note {
            background-color: #d1ecf1;
            border-left: 4px solid #0c5460;
            padding: 10px;
            border-radius: 4px;
            margin-top: 15px;
            font-size: 12px;
            color: #0c5460;
        }
        /* Heartbeat button styling is inline on the element itself.
           Uses position:absolute off-screen (NOT display:none) so click events fire.
           Uses class="LuaButton" so VCarve routes clicks to OnLuaButton_btn_heartbeat(). */
    </style>
</head>
<body>
    <div class="container">
        <h1>AiSpire Control Panel</h1>

        <div class="status-bar">
            <div class="status-text">Server Running</div>
        </div>

        <div class="info-box">
            <div class="info-row">
                <span class="info-label">Server Status:</span>
                <span class="info-value" style="color: #28a745;">ACTIVE</span>
            </div>
            <div class="info-row">
                <span class="info-label">Port:</span>
                <span class="info-value">]] .. ServerModule.CONFIG.PORT .. [[</span>
            </div>
            <div class="info-row">
                <span class="info-label">Host:</span>
                <span class="info-value">127.0.0.1 (localhost)</span>
            </div>
        </div>

        <div class="stats">
            <h3>Server Activity</h3>
            <div class="stat-item">
                <span>Heartbeat Ticks:</span>
                <strong id="hb_count">0</strong>
            </div>
        </div>

        <div class="note">
            VCarve UI remains fully responsive while the server runs.<br>
            Close this dialog to stop the server.
        </div>
    </div>

    <!-- The heartbeat trigger button.
         CRITICAL: Must use class="LuaButton" for VCarve to route clicks to OnLuaButton_<id>().
         CRITICAL: Must use <input type="button">, not <button>.
         CRITICAL: Must be off-screen (not display:none) so click events still dispatch. -->
    <input type="button" class="LuaButton" id="btn_heartbeat" value="HB"
           style="position:absolute; left:-9999px; top:-9999px;" />

    <script>
        // 5Hz heartbeat: fires every 200ms.
        // JavaScript engine inside HTML_Dialog runs independently of the blocked Lua thread.
        // Each btn.click() triggers VCarve to call OnLuaButton_btn_heartbeat() in Lua.
        var tickCount = 0;
        setInterval(function() {
            var btn = document.getElementById("btn_heartbeat");
            if (btn) {
                tickCount++;
                var el = document.getElementById("hb_count");
                if (el) el.innerText = tickCount;
                btn.click();
            }
        }, 200);
    </script>
</body>
</html>
]]

    -- ShowDialog() blocks the Lua thread, but the JavaScript timer continues.
    -- Each JS btn.click() routes through VCarve's event system to OnLuaButton_btn_heartbeat().
    local dialog = HTML_Dialog(true, html, 550, 550, "AiSpire Server")
    dialog:ShowDialog()

    -- Dialog closed - clean up
    if ServerRunning then
        ServerModule.stopServer()
        ServerRunning = false
        UIModule.log("INFO", "Server stopped (dialog closed)")
    end

    return true
end
