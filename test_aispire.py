#!/usr/bin/env python3
"""
Quick test script for AiSpire MCP Integration
Tests both direct socket and MCP server connections
"""

import socket
import json
import sys

def test_direct_socket():
    """Test direct connection to VCarve socket on port 9876"""
    print("=" * 60)
    print("TEST 1: Direct VCarve Socket Connection (port 9876)")
    print("=" * 60)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', 9876))
        print("✓ Connected to VCarve socket")

        # Send test command
        command = {
            'command_type': 'execute_code',
            'payload': {'code': 'return "VCarve is responding!"'},
            'id': 'direct_test',
            'auth': 'a8f5f167f44f4964e6c998dee827110c'
        }

        s.send((json.dumps(command) + '\n').encode())
        print("✓ Command sent")

        response = s.recv(4096).decode()
        result = json.loads(response)

        if result.get('status') == 'success':
            print(f"✓ SUCCESS: {result['result']['data']}")
            return True
        else:
            print(f"✗ FAILED: {result}")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    finally:
        try:
            s.close()
        except:
            pass

def test_mcp_server():
    """Test connection through Python MCP server on port 8765"""
    print("\n" + "=" * 60)
    print("TEST 2: Python MCP Server Connection (port 8765)")
    print("=" * 60)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', 8765))
        print("✓ Connected to MCP server")

        # Send test command through MCP
        command = {
            'type': 'execute_lua',
            'code': 'return 42',
            'auth': 'a8f5f167f44f4964e6c998dee827110c',
            'id': 'mcp_test'
        }

        s.send((json.dumps(command) + '\n').encode())
        print("✓ Command sent through MCP")

        response = s.recv(4096).decode()
        result = json.loads(response)

        if result.get('status') == 'success':
            data = result['result']['result']['data']
            print(f"✓ SUCCESS: Result = {data}")
            return True
        else:
            print(f"✗ FAILED: {result}")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    finally:
        try:
            s.close()
        except:
            pass

def test_query_state():
    """Test querying VCarve state"""
    print("\n" + "=" * 60)
    print("TEST 3: Query VCarve State")
    print("=" * 60)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', 9876))

        command = {
            'command_type': 'query_state',
            'payload': {},
            'id': 'state_test',
            'auth': 'a8f5f167f44f4964e6c998dee827110c'
        }

        s.send((json.dumps(command) + '\n').encode())
        response = s.recv(8192).decode()
        result = json.loads(response)

        if result.get('status') == 'success':
            state = result['result']['data']
            print(f"✓ VCarve State Retrieved:")
            print(f"  - Job info: {len(state.get('job', {}))} properties")
            print(f"  - App info: {len(state.get('app', {}))} properties")
            print(f"  - Layers: {len(state.get('layers', {}))} properties")
            return True
        else:
            print(f"✗ FAILED: {result}")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    finally:
        try:
            s.close()
        except:
            pass

if __name__ == "__main__":
    print("\nAiSpire MCP Integration Test Suite\n")

    results = []

    # Run tests
    results.append(("Direct Socket", test_direct_socket()))
    results.append(("MCP Server", test_mcp_server()))
    results.append(("Query State", test_query_state()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! AiSpire is fully operational!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check VCarve is running with AiSpire gadget active.")
        sys.exit(1)
