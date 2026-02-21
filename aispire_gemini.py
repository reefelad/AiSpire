#!/usr/bin/env python3
"""
Gemini integration for AiSpire.
Mirrors the 3 MCP tools from aispire_mcp_stdio.py so Gemini can control VCarve.

Setup:
    pip install google-generativeai
    set GEMINI_API_KEY=<your key from https://aistudio.google.com/apikey>
    python aispire_gemini.py
"""

import json
import socket
import os

try:
    import google.generativeai as genai
except ImportError:
    print("Google Generative AI library not installed.")
    print("Run: pip install google-generativeai")
    raise

VCARVE_HOST    = "127.0.0.1"
VCARVE_PORT    = 9876
AUTH_TOKEN     = "a8f5f167f44f4964e6c998dee827110c"
SOCKET_TIMEOUT = 10.0


def send_to_vcarve(command: dict) -> dict:
    """Send a JSON command to VCarve's Lua socket server and return the response."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(SOCKET_TIMEOUT)
    try:
        s.connect((VCARVE_HOST, VCARVE_PORT))
        s.sendall((json.dumps(command) + "\n").encode())
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
            return {
                "status": "error",
                "result": {
                    "message": f"VCarve returned malformed JSON at char {je.pos}.",
                    "raw": response_str[:500],
                },
            }
    except socket.timeout:
        return {"status": "error", "result": {"message": "VCarve did not respond (timeout). Is the AiSpire gadget running?"}}
    except ConnectionRefusedError:
        return {"status": "error", "result": {"message": "Cannot connect to VCarve on port 9876. Start VCarve and run the AiSpire gadget first."}}
    except Exception as e:
        return {"status": "error", "result": {"message": f"Connection error: {e}"}}
    finally:
        s.close()


# ── Tool implementations ────────────────────────────────────────────────────

def execute_lua(code: str) -> str:
    """Execute arbitrary Lua code inside VCarve."""
    cmd = {
        "command_type": "execute_code",
        "payload": {"code": code},
        "id": "gemini",
        "auth": AUTH_TOKEN,
    }
    return json.dumps(send_to_vcarve(cmd), indent=2)


def query_vcarve_state() -> str:
    """Query current VCarve state: job info, app version, layers."""
    cmd = {
        "command_type": "query_state",
        "payload": {},
        "id": "gemini",
        "auth": AUTH_TOKEN,
    }
    return json.dumps(send_to_vcarve(cmd), indent=2)


def execute_function(function_name: str, parameters: list) -> str:
    """Call a named AiSpire SDK function."""
    cmd = {
        "command_type": "execute_function",
        "payload": {"function": function_name, "parameters": parameters},
        "id": "gemini",
        "auth": AUTH_TOKEN,
    }
    return json.dumps(send_to_vcarve(cmd), indent=2)


# ── Gemini tool declarations ────────────────────────────────────────────────

TOOLS = [
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="execute_lua",
                description=(
                    "Execute arbitrary Lua code inside VCarve Pro. "
                    "Full VCarve SDK access: VectricJob(), ToolpathManager(), LayerManager, etc. "
                    "Use DXF import (vj:ImportDxfDwg) to create vectors. "
                    "Use string.char(10) for newlines in DXF strings."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "code": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Lua code to execute inside VCarve",
                        )
                    },
                    required=["code"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="query_vcarve_state",
                description="Get the current VCarve state: job name, width, height, app version, and layers.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={},
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="execute_function",
                description=(
                    "Call a named AiSpire SDK function. "
                    "Available functions: create_job, open_job, save_job, get_job_info, "
                    "create_circle, create_rectangle, create_text, "
                    "get_layers, create_layer, set_active_layer, "
                    "get_toolpaths, get_app_info, get_file_locations."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "function_name": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Name of the SDK function to call",
                        ),
                        "parameters": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(type=genai.protos.Type.STRING),
                            description="Positional parameters as a JSON array",
                        ),
                    },
                    required=["function_name"],
                ),
            ),
        ]
    )
]

DISPATCH = {
    "execute_lua":        lambda args: execute_lua(args["code"]),
    "query_vcarve_state": lambda args: query_vcarve_state(),
    "execute_function":   lambda args: execute_function(
        args["function_name"], args.get("parameters", [])
    ),
}


# ── Chat loop ───────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable is not set.")
        print("Get a free key at: https://aistudio.google.com/apikey")
        print("Then run:  set GEMINI_API_KEY=your-key-here")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.0-flash", tools=TOOLS)
    chat = model.start_chat()

    print("Gemini <-> AiSpire VCarve Integration")
    print("=" * 50)
    print("VCarve must be running with the AiSpire gadget active.")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not user_input:
            continue

        try:
            response = chat.send_message(user_input)

            # Handle tool call rounds (Gemini may call multiple tools before responding)
            while True:
                fn_calls = [
                    p.function_call
                    for p in response.candidates[0].content.parts
                    if hasattr(p, "function_call") and p.function_call.name
                ]
                if not fn_calls:
                    break

                parts = []
                for fc in fn_calls:
                    args = dict(fc.args)
                    print(f"  [tool] {fc.name}({args})")
                    result = DISPATCH[fc.name](args)
                    parts.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fc.name,
                                response={"result": result},
                            )
                        )
                    )
                response = chat.send_message(
                    genai.protos.Content(parts=parts)
                )

            if response.text:
                print(f"\nGemini: {response.text}\n")

        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
