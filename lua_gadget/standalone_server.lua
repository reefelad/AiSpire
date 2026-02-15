-- VECTRIC LUA SCRIPT
-- Standalone AiSpire Server
-- This runs independently of VCarve's UI thread
-- Can be launched from command line or by the gadget

-- Get the directory where this script is located
local script_dir = arg[0]:match("(.+)[/\\][^/\\]+$") or "."
if not script_dir:match("[/\\]$") then
    script_dir = script_dir .. "\\"
end

print("AiSpire Standalone Server")
print("Script directory: " .. script_dir)

-- Set up lua_modules path for LuaSocket
local version = _VERSION:match("%d+%.%d+")
if version then
    package.path = script_dir .. 'lua_modules\\share\\lua\\' .. version .. '\\?.inc;' ..
                   script_dir .. 'lua_modules\\share\\lua\\' .. version .. '\\?\\init.inc;' .. package.path
    package.cpath = script_dir .. 'lua_modules\\lib\\lua\\' .. version .. '\\?.so;' ..
                    script_dir .. 'lua_modules\\lib\\lua\\' .. version .. '\\?.dll;' .. package.cpath
end

-- Try to load socket
local socket_ok, socket = pcall(require, "socket")
if not socket_ok then
    print("ERROR: LuaSocket failed to load: " .. tostring(socket))
    os.exit(1)
end

print("LuaSocket loaded successfully")

-- Load JSON module
local json = dofile(script_dir .. "modules\\json.lua")
print("JSON module loaded")

-- Load server module
local server = dofile(script_dir .. "modules\\server.lua")
print("Server module loaded")

-- Set up the server with JSON
server.setJson(json)

-- Create a minimal UI manager stub (since we're running standalone)
local ui_stub = {
    log = function(level, message)
        print(string.format("[%s] %s", level, message))
    end,
    setConnectionStatus = function(status, message)
        print(string.format("Connection: %s - %s", status, message))
    end,
    startCommandExecution = function() end,
    endCommandExecution = function() end,
    isExecutingCommand = false,
    showAlert = function(title, message, type)
        print(string.format("ALERT [%s]: %s - %s", type or "info", title, message))
    end
}

server.setUiManager(ui_stub)

-- Start the server
print("\nStarting server...")
if not server.startServer() then
    local errorMsg = server.getLastError() or "Unknown error"
    print("ERROR: Failed to start server: " .. errorMsg)
    os.exit(1)
end

print("SUCCESS: Server started on port " .. server.CONFIG.PORT)
print("Listening on: 127.0.0.1:" .. server.CONFIG.PORT)
print("\nServer is running. Press Ctrl+C to stop.\n")

-- Run the server loop
local running = true

-- Set up Ctrl+C handler (if available)
if os.execute then
    -- Try to set up signal handler on Unix-like systems
    local signal_ok = pcall(function()
        local signal = require("posix.signal")
        signal.signal(signal.SIGINT, function()
            running = false
            print("\nShutting down server...")
        end)
    end)
end

-- Main server loop
while running and server.isRunning() do
    server.runServer()
end

-- Cleanup
print("Server stopped.")
server.stopServer()
os.exit(0)
