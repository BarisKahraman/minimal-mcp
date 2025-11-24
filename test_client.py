#!/usr/bin/env python3
"""
MCP server'ı test etmek için basit client
"""

import subprocess
import json
import sys
from typing import Dict, Any, Optional


class MCPTestClient:
    def __init__(self, server_script: str):
        """
        Server'ı subprocess olarak başlat
        """
        self.process = subprocess.Popen(
            [sys.executable, server_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffering
        )
        self.request_id = 0
    
    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id
    
    def send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Server'a JSON-RPC request gönder
        """
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._next_id()
        }
        
        # Request gönder
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line)
        self.process.stdin.flush()
        
        # Response oku
        response_line = self.process.stdout.readline()
        
        if not response_line:
            raise RuntimeError("Server closed connection")
        
        return json.loads(response_line)
    
    def close(self):
        """Server'ı kapat"""
        self.process.terminate()
        self.process.wait(timeout=5)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def test_minimal_server():
    """
    Minimal MCP server'ın tüm method'larını test et
    """
    print("=" * 60)
    print("Testing Minimal MCP Server")
    print("=" * 60)
    
    with MCPTestClient("servers/minimal_mcp.py") as client:
        
        # Test 1: Initialize
        print("\n[TEST 1] Initialize")
        response = client.send("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })
        
        print(f"✓ Server: {response['result']['serverInfo']['name']}")
        print(f"✓ Version: {response['result']['serverInfo']['version']}")
        print(f"✓ Capabilities: {list(response['result']['capabilities'].keys())}")
        
        # Test 2: List tools
        print("\n[TEST 2] List Tools")
        response = client.send("tools/list")
        tools = response['result']['tools']
        
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Test 3: Call add tool
        print("\n[TEST 3] Call 'add' tool")
        response = client.send("tools/call", {
            "name": "add",
            "arguments": {
                "a": 15,
                "b": 27
            }
        })
        
        result_text = response['result']['content'][0]['text']
        print(f"✓ {result_text}")
        
        # Test 4: Call greet tool
        print("\n[TEST 4] Call 'greet' tool")
        response = client.send("tools/call", {
            "name": "greet",
            "arguments": {
                "name": "Barış"
            }
        })
        
        result_text = response['result']['content'][0]['text']
        print(f"✓ {result_text}")
        
        # Test 5: Error handling - unknown tool
        print("\n[TEST 5] Error Handling - Unknown Tool")
        response = client.send("tools/call", {
            "name": "nonexistent",
            "arguments": {}
        })
        
        if "error" in response:
            print(f"✓ Error caught: {response['error']['message']}")
        else:
            print("✗ Expected error but got success")
        
        # Test 6: Error handling - missing argument
        print("\n[TEST 6] Error Handling - Missing Argument")
        response = client.send("tools/call", {
            "name": "add",
            "arguments": {
                "a": 10
                # 'b' eksik
            }
        })
        
        if "error" in response:
            print(f"✓ Error caught: {response['error']['message']}")
        else:
            print("✗ Expected error but got success")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_minimal_server()