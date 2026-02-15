-- VECTRIC LUA SCRIPT

require "strict"

-- Main function
function main(script_path)
    -- VCarve passes the directory path (without filename) as script_path
    -- Ensure it ends with a slash
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
    local json = dofile(gadget_dir .. "modules\\json.inc")
    local server = dofile(gadget_dir .. "modules\\server.inc")
    local ui = dofile(gadget_dir .. "modules\\ui_manager.inc")

    -- Set up the server
    server.setJson(json)
    server.setUiManager(ui)

    -- Log startup
    ui.log("INFO", "AiSpire Gadget starting...")
    ui.log("INFO", "Version: 0.1.0")

    -- Try to start server
    local success, err = pcall(function()
        if not server.startServer() then
            local errorMsg = server.getLastError() or "Unknown error"
            ui.log("ERROR", "Failed to start server: " .. errorMsg)
            DisplayMessageBox("AiSpire: Failed to start server:\n" .. errorMsg)
            return
        end

        ui.log("SUCCESS", "Server started on port " .. server.CONFIG.PORT)

        -- Show success message with simple HTML dialog
        local html = [[
<!DOCTYPE html>
<html>
<head>
    <title>AiSpire - Server Running</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            background-color: #f0f0f0;
        }
        h1 {
            color: #28a745;
        }
        .info {
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .success {
            color: #28a745;
            font-weight: bold;
        }
        .port {
            font-size: 20px;
            color: #007bff;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>✓ AiSpire Server Running!</h1>
    <div class="info">
        <p class="success">Socket server started successfully</p>
        <p>Listening on port: <span class="port">]] .. server.CONFIG.PORT .. [[</span></p>
        <p>The server is now ready to accept MCP connections.</p>
    </div>
    <div class="info">
        <h3>Connection Details</h3>
        <p><strong>Host:</strong> 127.0.0.1</p>
        <p><strong>Port:</strong> ]] .. server.CONFIG.PORT .. [[</p>
    </div>
    <div class="info">
        <h3>Next Steps</h3>
        <ol>
            <li>Start the Python MCP server</li>
            <li>Configure your LLM client to connect via MCP</li>
            <li>Begin controlling VCarve Pro programmatically!</li>
        </ol>
    </div>
</body>
</html>
]]

        local dialog = HTML_Dialog(true, html, 600, 500, "AiSpire Control Panel")
        dialog:ShowDialog()
    end)

    if not success then
        DisplayMessageBox("ERROR starting AiSpire:\n" .. tostring(err))
    end

    return true
end
