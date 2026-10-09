"""
Servidor MCP (Model Context Protocol) para Azure AI Search y Blob Storage.
Ejecuta las herramientas de validación de documentos SUNAT bajo CQRS.

Uso:
  # Modo Stdio (para agentes como Claude Desktop, Antigravity, Cursor, etc.):
  python mcp_server.py

  # Modo SSE (HTTP Server):
  python mcp_server.py --transport sse --port 8000
"""
import sys
import argparse
from src.mcp.tools import create_mcp_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor MCP para validación documental SUNAT (CQRS)")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Tipo de transporte MCP (default: stdio)"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host para SSE (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Puerto para SSE (default: 8000)")

    args = parser.parse_args()

    server = create_mcp_server()

    if args.transport == "stdio":
        server.run(transport="stdio")
    elif args.transport == "sse":
        server.run(transport="sse", host=args.host, port=args.port)
    else:
        server.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
