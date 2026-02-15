@echo off
REM AiSpire Standalone Server Launcher for Windows
REM This starts the server independently of VCarve's UI

echo ========================================
echo    AiSpire Standalone Server Launcher
echo ========================================
echo.

REM Find Lua interpreter
set LUA_EXE=

REM Check common Lua installation locations
if exist "C:\Program Files\Lua\lua.exe" (
    set LUA_EXE=C:\Program Files\Lua\lua.exe
)
if exist "C:\Program Files (x86)\Lua\lua.exe" (
    set LUA_EXE=C:\Program Files (x86)\Lua\lua.exe
)
if exist "%ProgramFiles%\Lua\lua.exe" (
    set LUA_EXE=%ProgramFiles%\Lua\lua.exe
)

REM Check if lua is in PATH
where lua.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set LUA_EXE=lua.exe
)

REM Check VCarve's embedded Lua
if exist "C:\ProgramData\Vectric\VCarve Pro\V12.5\lua.exe" (
    set LUA_EXE=C:\ProgramData\Vectric\VCarve Pro\V12.5\lua.exe
)

if "%LUA_EXE%"=="" (
    echo ERROR: Lua interpreter not found!
    echo.
    echo Please install Lua from: https://luabinaries.sourceforge.net/
    echo Or ensure VCarve Pro is installed.
    echo.
    pause
    exit /b 1
)

echo Found Lua: %LUA_EXE%
echo.

REM Change to the lua_gadget directory
cd /d "%~dp0lua_gadget"

REM Start the standalone server
echo Starting AiSpire server...
echo.
"%LUA_EXE%" standalone_server.lua

echo.
echo Server has stopped.
pause
