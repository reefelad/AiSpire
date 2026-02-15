# AiSpire VCarve Gadget Installation Guide

## Overview

AiSpire is a VCarve Pro gadget that provides an MCP (Model Context Protocol) server interface, allowing AI assistants to control VCarve Pro programmatically.

## Prerequisites

- VCarve Pro 12.5 or later (tested on 12.5)
- Windows OS
- LuaSocket library (included in installation)

## Installation Steps

### Option 1: Manual Installation (Recommended for Development)

1. **Build the gadget bundle:**
   ```bash
   cd AiSpire
   make bundle
   ```

2. **Extract to VCarve Gadgets folder:**
   ```bash
   # The gadget will be created at: VectricGadgets/aispire.gadget
   # Extract it to: C:\ProgramData\Vectric\VCarve Pro\V12.5\Gadgets\aispire\
   ```

3. **Install LuaSocket dependencies:**
   - Copy the `lua_modules` folder from the gadget bundle to the aispire folder
   - Rename all `.lua` files in `lua_modules` to `.inc` to prevent VCarve from scanning them as gadgets

   OR use the installation script (coming soon)

4. **Restart VCarve Pro**

5. **Verify installation:**
   - Open VCarve Pro
   - Go to **Gadgets** menu
   - You should see **aispire** in the list
   - Click it to open the AiSpire Control Panel

### Option 2: Automated Installation (Coming Soon)

An installation script will be provided that automates the above steps.

## Project Structure

```
AiSpire/
├── lua_gadget/
│   ├── aispire.lua          # Main gadget file (must match folder name)
│   └── modules/             # Module files (renamed to .inc during build)
│       ├── server.lua       # Socket server implementation
│       ├── ui_manager.lua   # UI panel manager
│       ├── json.lua         # JSON parser
│       └── ...
├── VectricGadgets/
│   └── aispire.gadget       # Bundled gadget (ZIP file)
└── python_mcp_server/       # MCP server implementation
```

## VCarve Gadget Requirements

For developers working on the gadget:

1. **File Structure:**
   - Folder name must match the main `.lua` file name (`aispire/aispire.lua`)
   - Only ONE `.lua` file in the root of the gadget folder
   - All other modules must use a different extension (`.inc`) or be in subdirectories

2. **Lua Script Requirements:**
   - Must start with `-- VECTRIC LUA SCRIPT` header comment
   - Must include `require "strict"`
   - Must define `function main(script_path)` not `Gadget_Action()`
   - Must return `true` from `main()`

3. **VCarve API:**
   - Use `DisplayMessageBox()` for popups
   - Use `HTML_Dialog()` for UI panels
   - The `script_path` parameter is the gadget directory (without trailing slash)

## Build Process

The Makefile includes a `bundle` target that:
1. Creates a ZIP file with all gadget files
2. Names it `aispire.gadget`
3. Places it in `VectricGadgets/`

**Note:** The `.gadget` file is a regular ZIP file. VCarve expects it to be extracted to the Gadgets folder.

## Troubleshooting

### Gadget doesn't appear in menu
- Ensure VCarve Pro has been restarted
- Check that the folder structure is correct: `.../Gadgets/aispire/aispire.lua`
- Verify the file starts with `-- VECTRIC LUA SCRIPT`

### "Script does not start with '-- VECTRIC LUA SCRIPT'" error
- ALL `.lua` files in the gadget folder tree need this header
- Solution: Rename module files to `.inc` extension

### Multiple gadgets appearing in menu
- VCarve scans ALL `.lua` files recursively and treats each as a gadget
- Solution: Only have ONE `.lua` file (the main gadget file)
- Rename all other `.lua` files to `.inc` or another extension

### Socket server not starting
- Ensure LuaSocket is properly installed (lua_modules folder present)
- Check VCarve logs at: `C:\ProgramData\Vectric\VCarve Pro\V12.5\Logs\`

## Development Notes

### Module Loading
- Modules are loaded using `dofile()` instead of `require()`
- This avoids VCarve's Lua `package.path` issues
- Modules use `.inc` extension to prevent VCarve from treating them as gadgets

### Testing
- Run `make test` to run the test suite
- End-to-end tests require VCarve Pro to be installed

## License

[To be determined]

## Support

For issues and questions, please visit the GitHub repository.
