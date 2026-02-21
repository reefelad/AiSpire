"""
AiSpire MCP Server — stdio transport for Claude Desktop/CLI integration.

Connects directly to VCarve's Lua socket server on port 9876 and exposes
VCarve capabilities as MCP tools that Claude can call.

Usage:
  Configured in claude_desktop_config.json as a stdio MCP server.
  VCarve must be running with the AiSpire gadget active.
"""

import json
import socket
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

# Suppress all logging to stderr (Claude reads stdout for JSON-RPC)
logging.basicConfig(level=logging.WARNING)

# VCarve connection settings
VCARVE_HOST = "127.0.0.1"
VCARVE_PORT = 9876
AUTH_TOKEN = "a8f5f167f44f4964e6c998dee827110c"
SOCKET_TIMEOUT = 10.0

# Create the MCP server
mcp = FastMCP("AiSpire")


def send_to_vcarve(command: dict) -> dict:
    """Send a command to VCarve's Lua socket server and return the response."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(SOCKET_TIMEOUT)
    try:
        s.connect((VCARVE_HOST, VCARVE_PORT))
        s.sendall((json.dumps(command) + "\n").encode())

        # Read response (may come in chunks, delimited by newline)
        data = b""
        while True:
            chunk = s.recv(8192)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break

        response_str = data.decode().strip()
        if not response_str:
            return {"status": "error", "result": {"message": "Empty response from VCarve"}}

        try:
            return json.loads(response_str)
        except json.JSONDecodeError as je:
            # VCarve sent malformed JSON — return raw text so LLM can see what happened
            return {
                "status": "error",
                "result": {
                    "message": f"VCarve returned malformed JSON at char {je.pos}. Raw response shown in data.",
                    "raw_response": response_str[:500],
                    "data": {}
                }
            }
    except socket.timeout:
        return {"status": "error", "result": {"message": "VCarve did not respond (timeout). Is the AiSpire gadget running?"}}
    except ConnectionRefusedError:
        return {"status": "error", "result": {"message": "Cannot connect to VCarve on port 9876. Start VCarve and run the AiSpire gadget first."}}
    except Exception as e:
        return {"status": "error", "result": {"message": f"Connection error: {str(e)}"}}
    finally:
        s.close()


@mcp.tool()
def execute_lua(code: str) -> str:
    """Execute arbitrary Lua code inside VCarve and return the result.

    Use this to run any Lua code in the VCarve environment. The code runs
    in a sandboxed environment with access to VCarve's SDK functions.

    Examples:
        execute_lua('return "Hello from VCarve!"')
        execute_lua('return sdkWrapper.getJobInfo()')
        execute_lua('return math.pi * 2')

    Args:
        code: Lua code to execute. Use 'return' to get a value back.
    """
    command = {
        "command_type": "execute_code",
        "payload": {"code": code},
        "id": "mcp_exec",
        "auth": AUTH_TOKEN,
    }
    result = send_to_vcarve(command)
    return json.dumps(result, indent=2)


@mcp.tool()
def query_vcarve_state() -> str:
    """Query the current state of VCarve — job info, app info, and layers.

    Returns information about:
    - Current job (name, dimensions, material block)
    - Application info (version, whether it's Aspire or VCarve)
    - Layer information (names, count)

    Call this first to understand what's currently open in VCarve.
    """
    command = {
        "command_type": "query_state",
        "payload": {},
        "id": "mcp_state",
        "auth": AUTH_TOKEN,
    }
    result = send_to_vcarve(command)
    return json.dumps(result, indent=2)


@mcp.tool()
def execute_function(function_name: str, parameters: str = "[]") -> str:
    """Execute a named VCarve SDK function with parameters.

    Available functions:
    - Job: create_job, open_job, save_job, close_job, get_job_info, set_material_properties
    - Vectors: create_circle, create_rectangle, create_text, transform_vectors
    - Layers: create_layer, get_layers, set_active_layer, set_layer_visibility
    - Toolpaths: get_toolpaths, create_profile_toolpath, create_pocket_toolpath, save_toolpaths
    - App: get_app_info, get_file_locations

    Args:
        function_name: Name of the SDK function to call (e.g. "create_circle")
        parameters: JSON array of positional parameters (e.g. '[100, 100, 50]' for x, y, radius)
    """
    try:
        params = json.loads(parameters) if parameters else []
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "result": {"message": f"Invalid JSON parameters: {parameters}"}})

    command = {
        "command_type": "execute_function",
        "payload": {
            "function": function_name,
            "parameters": params,
        },
        "id": "mcp_func",
        "auth": AUTH_TOKEN,
    }
    result = send_to_vcarve(command)
    return json.dumps(result, indent=2)


@mcp.resource("aispire://guide")
def get_aispire_guide() -> str:
    """Complete guide for using AiSpire to control VCarve Pro via MCP tools.

    This resource tells the AI assistant everything it needs to know about
    creating jobs, vectors, layers, and toolpaths in VCarve.
    """
    return """
# AiSpire — VCarve Pro MCP Integration Guide

## IMPORTANT: You are controlling VCarve Pro through a socket connection.
The VCarve UI shows a modal server dialog — the user CANNOT interact with VCarve
directly while the server is running. ALL operations must be done through these tools.

## WORKFLOW — Always follow this order:

### Step 1: Create or verify a job exists
Before ANY vector or toolpath operations, you MUST have an open job.
Call query_vcarve_state() first. If job data is empty, create one:

    execute_function("create_job", '["JobName", 2400, 1200, 17, true, true]')
    Parameters: [name, width_mm, height_mm, thickness_mm, use_mm, origin_on_surface]

### Step 2: Set material properties (if needed)
    execute_function("set_material_properties", '[2400, 1200, 17]')
    Parameters: [width_mm, height_mm, thickness_mm]

### Step 3: Create layers to organize work
    execute_function("create_layer", '["Vectors", "0000FF", true, true]')
    Parameters: [name, hex_color, is_visible, is_active]

### Step 4: Create vectors
Rectangles:
    execute_function("create_rectangle", '[0, 0, 2400, 1200]')
    Parameters: [x1, y1, x2, y2] in mm

Circles:
    execute_function("create_circle", '[100, 100, 50]')
    Parameters: [center_x, center_y, radius] in mm

Text:
    execute_function("create_text", '["Hello", 100, 100, 20, "Arial"]')
    Parameters: [text, x, y, height, font_name]

For COMPLEX vectors (lines, polylines, arcs, rebates, custom shapes), use execute_lua:
    execute_lua('local r = sdkWrapper.createRectangle(0, 0, 100, 50) return r')

### Step 5: Create toolpaths
Profile (cut along vector edge):
    execute_function("create_profile_toolpath", '["Profile Cut", 6.0, 17.0, {}]')
    Parameters: [name, tool_diameter_mm, cut_depth_mm, extra_params]

Pocket (clear area inside vector):
    execute_function("create_pocket_toolpath", '["Pocket", 6.0, 10.0, {}]')
    Parameters: [name, tool_diameter_mm, cut_depth_mm, extra_params]

### Step 6: Save
    execute_function("save_toolpaths", '["C:/path/to/output.crv3d"]')

## EXECUTE_LUA — For advanced operations
The sandbox has: math, string, table, sdkWrapper
sdkWrapper contains ALL the functions listed above as methods:
    sdkWrapper.createNewJob(name, w, h, thickness, mm, surface)
    sdkWrapper.createCircle(x, y, r)
    sdkWrapper.createRectangle(x1, y1, x2, y2)
    sdkWrapper.createText(text, x, y, h, font)
    sdkWrapper.getJobInfo()
    sdkWrapper.getAppInfo()
    sdkWrapper.getLayerInfo()
    etc.

## UNITS
All dimensions are in millimeters when the job is created with in_mm=true.

## TIPS FOR CNC WORK
- Always create the job FIRST with correct sheet size and material thickness
- Use layers to separate different operations (vectors, profile cuts, pockets)
- For rebates/dados: use pocket toolpaths at partial depth
- For through-cuts: set cut_depth = material_thickness
- Standard CNC tool diameters: 3mm, 6mm, 8mm, 12mm end mills
- Dog-bone corners: add small circles at inside corners for CNC clearance
"""


if __name__ == "__main__":
    mcp.run(transport="stdio")
