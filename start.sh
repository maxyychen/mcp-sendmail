#!/bin/bash
# Convenience script to start MCP Sendmail Server with .env.sh configuration

set -e

echo "🚀 Starting MCP Sendmail Server..."
echo ""

# Check if .env.sh exists
if [ ! -f .env.sh ]; then
    echo "❌ Error: .env.sh file not found!"
    echo "   Please create .env.sh with your SMTP configuration."
    echo ""
    echo "Example .env.sh:"
    echo "  export SMTP_HOST=\"smtp.gmail.com\""
    echo "  export SMTP_PORT=\"587\""
    echo "  export SMTP_USER=\"your-email@gmail.com\""
    echo "  export SMTP_PASSWORD=\"your-password\""
    exit 1
fi

# Source environment variables
echo "📋 Loading SMTP configuration from .env.sh..."
source .env.sh

# Display configuration (hide password)
echo ""
echo "Configuration loaded:"
echo "  SMTP_HOST: ${SMTP_HOST}"
echo "  SMTP_PORT: ${SMTP_PORT}"
echo "  SMTP_USER: ${SMTP_USER}"
echo "  SMTP_PASSWORD: ********"
echo ""

# Start docker compose
echo "🐳 Starting Docker containers..."
docker compose up -d

echo ""
echo "✅ MCP Sendmail Server started successfully!"
echo ""
echo "📊 View logs:"
echo "   docker compose logs -f"
echo ""
echo "🔍 Check health:"
echo "   curl http://localhost:8085/health"
echo ""
echo "🛑 Stop server:"
echo "   docker compose down"
