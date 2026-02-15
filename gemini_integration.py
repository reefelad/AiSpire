#!/usr/bin/env python3
"""
Gemini AI Integration with AiSpire MCP
Allows Gemini to control VCarve Pro through the AiSpire MCP server
"""

import socket
import json
import os
from typing import Dict, Any

# You'll need to install: pip install google-generativeai
try:
    import google.generativeai as genai
except ImportError:
    print("⚠️  Google Generative AI library not installed.")
    print("Run: pip install google-generativeai")
    exit(1)


class AiSpireClient:
    """Client for sending commands to AiSpire MCP server"""

    def __init__(self, host='127.0.0.1', port=8765, auth_token='a8f5f167f44f4964e6c998dee827110c'):
        self.host = host
        self.port = port
        self.auth_token = auth_token

    def execute_lua(self, code: str) -> Dict[str, Any]:
        """Execute Lua code in VCarve"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((self.host, self.port))

            command = {
                'type': 'execute_lua',
                'code': code,
                'auth': self.auth_token,
                'id': 'gemini_request'
            }

            s.send((json.dumps(command) + '\n').encode())
            response = s.recv(8192).decode()
            s.close()

            return json.loads(response)

        except Exception as e:
            return {'status': 'error', 'error': str(e)}


# Define tools for Gemini to use
vcarve_tools = [
    {
        "name": "execute_vcarve_lua",
        "description": "Execute Lua code in VCarve Pro to control the CAD/CAM software. "
                      "Can create geometry, modify toolpaths, query job state, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "lua_code": {
                    "type": "string",
                    "description": "The Lua code to execute in VCarve Pro"
                }
            },
            "required": ["lua_code"]
        }
    },
    {
        "name": "get_vcarve_info",
        "description": "Get information about the current VCarve job, application, or layers",
        "parameters": {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "enum": ["job", "app", "layers"],
                    "description": "Type of information to retrieve"
                }
            },
            "required": ["info_type"]
        }
    }
]


def execute_vcarve_lua(lua_code: str, client: AiSpireClient) -> str:
    """Execute Lua code in VCarve"""
    result = client.execute_lua(lua_code)

    if result.get('status') == 'success':
        data = result['result']['result']['data']
        return f"Execution successful. Result: {data}"
    else:
        return f"Execution failed: {result.get('error', 'Unknown error')}"


def get_vcarve_info(info_type: str, client: AiSpireClient) -> str:
    """Get VCarve information"""
    lua_code = f"return sdkWrapper.get{info_type.capitalize()}Info()"
    result = client.execute_lua(lua_code)

    if result.get('status') == 'success':
        data = result['result']['result']['data']
        return json.dumps(data, indent=2)
    else:
        return f"Failed to get info: {result.get('error', 'Unknown error')}"


def chat_with_gemini():
    """Interactive chat with Gemini that can control VCarve"""

    # Set up API key (you'll need to set this environment variable)
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("\nTo use Gemini integration:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Set environment variable:")
        print("   Windows: set GEMINI_API_KEY=your-api-key-here")
        print("   Linux/Mac: export GEMINI_API_KEY=your-api-key-here")
        return

    genai.configure(api_key=api_key)

    # Initialize Gemini model with function calling
    model = genai.GenerativeModel(
        model_name='gemini-1.5-pro',
        tools=vcarve_tools
    )

    # Initialize AiSpire client
    client = AiSpireClient()

    print("🤖 Gemini + VCarve Integration Ready!")
    print("=" * 60)
    print("You can now ask Gemini to control VCarve Pro!")
    print("Examples:")
    print("  - 'What version of VCarve is running?'")
    print("  - 'Execute this Lua: return 2 + 2'")
    print("  - 'Get the current job information'")
    print("\nType 'quit' to exit\n")

    chat = model.start_chat()

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break

        if not user_input:
            continue

        try:
            # Send message to Gemini
            response = chat.send_message(user_input)

            # Check if Gemini wants to use a tool
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        # Gemini is calling a function!
                        function_call = part.function_call
                        function_name = function_call.name
                        function_args = dict(function_call.args)

                        print(f"🔧 Gemini is calling: {function_name}")

                        # Execute the function
                        if function_name == "execute_vcarve_lua":
                            result = execute_vcarve_lua(function_args['lua_code'], client)
                        elif function_name == "get_vcarve_info":
                            result = get_vcarve_info(function_args['info_type'], client)
                        else:
                            result = "Unknown function"

                        # Send result back to Gemini
                        response = chat.send_message(
                            genai.protos.Content(parts=[
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_name,
                                        response={"result": result}
                                    )
                                )
                            ])
                        )

            # Print Gemini's response
            if response.text:
                print(f"\nGemini: {response.text}\n")

        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    chat_with_gemini()
