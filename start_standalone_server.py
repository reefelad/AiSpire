#!/usr/bin/env python3
"""
Start AiSpire Standalone Server
Launches the Lua socket server as a separate process
This keeps VCarve's UI responsive
"""

import subprocess
import sys
import os
from pathlib import Path

def find_lua_exe():
    """Find Lua interpreter"""
    # Check common locations
    lua_paths = [
        r"C:\Program Files\Lua\lua.exe",
        r"C:\Program Files (x86)\Lua\lua.exe",
        r"C:\ProgramData\Vectric\VCarve Pro\V12.5\lua.exe",
        "lua.exe",  # In PATH
        "lua5.3.exe",
        "lua5.4.exe",
    ]

    for lua_path in lua_paths:
        try:
            if os.path.exists(lua_path):
                return lua_path
            # Try to run it (if in PATH)
            subprocess.run([lua_path, "-v"], capture_output=True, check=True)
            return lua_path
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    return None

def main():
    print("=" * 60)
    print("  AiSpire Standalone Server Launcher")
    print("=" * 60)
    print()

    # Find Lua
    lua_exe = find_lua_exe()
    if not lua_exe:
        print("ERROR: Lua interpreter not found!")
        print()
        print("Please install Lua from:")
        print("  https://luabinaries.sourceforge.net/")
        print()
        print("Or ensure VCarve Pro is installed.")
        return 1

    print(f"Found Lua: {lua_exe}")

    # Find standalone server script
    script_dir = Path(__file__).parent / "lua_gadget"
    server_script = script_dir / "standalone_server.lua"

    if not server_script.exists():
        print(f"ERROR: Server script not found at: {server_script}")
        return 1

    print(f"Server script: {server_script}")
    print()

    # Launch standalone server
    print("Starting AiSpire standalone server...")
    print("Press Ctrl+C to stop")
    print()

    try:
        process = subprocess.run(
            [lua_exe, str(server_script)],
            cwd=str(script_dir)
        )
        return process.returncode
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
