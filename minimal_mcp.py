#!/usr/bin/env python3
"""
MCP protokolüne uygun minimal server
Sadece zorunlu method'ları implement eder:
- initialize
- tools/list
- tools/call
"""

import json
import sys
from typing import Any, Dict, Optional


class MinimalMCPServer:
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.initialized = False
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        İlk çağrı: Client ile handshake
        Client protokol versiyonunu gönderir, server desteklediğini döner
        """
        self.initialized = True
        
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": self.server_name,
                "version": "0.1.0"
            },
            "capabilities": {
                "tools": {}  # Bu server tool'ları destekliyor
            }
        }
    
    def handle_tools_list(self) -> Dict[str, Any]:
        """
        Server'ın sunduğu tool'ların listesi
        """
        if not self.initialized:
            raise RuntimeError("Server not initialized")
        
        return {
            "tools": [
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {
                                "type": "number",
                                "description": "First number"
                            },
                            "b": {
                                "type": "number",
                                "description": "Second number"
                            }
                        },
                        "required": ["a", "b"]
                    }
                },
                {
                    "name": "greet",
                    "description": "Greet a person",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Person's name"
                            }
                        },
                        "required": ["name"]
                    }
                }
            ]
        }
    
    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Belirli bir tool'u çalıştır
        """
        if not self.initialized:
            raise RuntimeError("Server not initialized")
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        # Tool implementasyonları
        if tool_name == "add":
            result = arguments["a"] + arguments["b"]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Result: {result}"
                    }
                ]
            }
        
        elif tool_name == "greet":
            name = arguments["name"]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Hello, {name}! Welcome to MCP."
                    }
                ]
            }
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON-RPC request'i route et
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            # Method routing
            if method == "initialize":
                result = self.handle_initialize(params)
            
            elif method == "tools/list":
                result = self.handle_tools_list()
            
            elif method == "tools/call":
                result = self.handle_tools_call(params)
            
            else:
                raise ValueError(f"Method not found: {method}")
            
            # Success response
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        
        except Exception as e:
            # Error response
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,  # Server error
                    "message": str(e)
                }
            }
    
    def run(self):
        """
        Ana server loop: stdin -> process -> stdout
        """
        # Startup log (stderr'a yazılır, stdout kirlenmez)
        print(f"[{self.server_name}] Server started", file=sys.stderr)
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                
                # stdout'a JSON yaz
                print(json.dumps(response), flush=True)
            
            except json.JSONDecodeError as e:
                # JSON parse hatası
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,  # Parse error
                        "message": f"Invalid JSON: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    server = MinimalMCPServer("minimal-mcp-server")
    server.run()