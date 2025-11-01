#!/bin/bash
# Convenience script to stop MCP Sendmail Server

set -e

echo "🛑 Stopping MCP Sendmail Server..."
docker compose down

echo ""
echo "✅ MCP Sendmail Server stopped successfully!"
