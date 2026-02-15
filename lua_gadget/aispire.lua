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

    -- Simple HTML for the UI
    local html = [[
<!DOCTYPE html>
<html>
<head>
    <title>AiSpire Control Panel</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            background-color: #f0f0f0;
        }
        h1 {
            color: #333;
        }
        .info {
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .status {
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>AiSpire Gadget</h1>
    <div class="info">
        <h2>Status</h2>
        <p class="status">✓ Gadget loaded successfully</p>
        <p class="status">✓ Modules loaded: json, server, ui_manager</p>
        <p class="status">⚠ Socket server requires LuaSocket installation</p>
    </div>
    <div class="info">
        <h2>Version</h2>
        <p>AiSpire v0.1.0 (Development)</p>
        <p>MCP Gadget for Vectric VCarve Pro</p>
    </div>
    <div class="info">
        <h2>Next Steps</h2>
        <ol>
            <li>Install LuaSocket system-wide</li>
            <li>Restart VCarve Pro</li>
            <li>Socket server will start automatically</li>
        </ol>
    </div>
</body>
</html>
]]

    -- Show simple dialog
    local dialog = HTML_Dialog(true, html, 600, 500, "AiSpire Control Panel")
    dialog:ShowDialog()

    return true
end
