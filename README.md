# MCP Sendmail Server

A Model Context Protocol (MCP) server with **Streamable HTTP transport** for sending emails via SMTP.

## Features

- ✅ **MCP Streamable HTTP** - Full MCP specification compliance (2024-11-05)
- ✅ **Stateful Sessions** - Session management with automatic cleanup
- ✅ **Bidirectional Communication** - SSE for server-to-client messaging
- ✅ **Stream Resumability** - Reconnect and resume from last event
- ✅ **Email Tools** - Send emails, bulk emails, and template-based emails
- ✅ **SMTP Support** - Full SMTP/TLS support with authentication
- ✅ **Attachments** - Support for email attachments (base64 encoded)
- ✅ **Docker Ready** - Multi-stage build, production-optimized
- ✅ **Type Safe** - Full Python type hints and Pydantic models
- ✅ **Async Support** - FastAPI async/await patterns
- ✅ **Backward Compatible** - Legacy JSON-RPC 2.0 endpoints still work

## Configuration

SMTP credentials are configured via environment variables. The repository includes `.env.sh` for easy configuration:

```bash
# Source SMTP settings
source .env.sh

# Your settings are now available:
# SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

## Quick Start

### Option 1: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Load SMTP settings from .env.sh
source .env.sh

# Run server
uvicorn src.server:app --reload --port 8080
```

### Option 2: Docker

```bash
# Build and run with Docker
docker build -t mcp-sendmail-server:latest .
docker run -d -p 8080:8080 \
  -e SMTP_HOST="smtp.gmail.com" \
  -e SMTP_PORT="587" \
  -e SMTP_USER="your-email@gmail.com" \
  -e SMTP_PASSWORD="your-password" \
  -v $(pwd)/logs:/app/logs \
  --name mcp-sendmail \
  mcp-sendmail-server:latest
```

### Option 3: Docker Compose (Recommended)

#### Quick Start with Convenience Scripts

```bash
# Start the server (automatically loads .env.sh)
./start.sh

# View logs
docker compose logs -f

# Stop the server
./stop.sh
```

#### Manual Start

Configure your SMTP credentials using `.env.sh`:

```bash
# 1. Edit .env.sh with your SMTP credentials (already configured in this repo)
nano .env.sh

# Example .env.sh contents:
export SMTP_HOST="mail.example.com"
export SMTP_PORT="25"
export SMTP_USER="test@example.com"
export SMTP_PASSWORD="your-password"

# 2. Source the environment variables
source .env.sh

# 3. Start services (will use variables from .env.sh)
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

**Important:** Always run `source .env.sh` before `docker compose up` to load the SMTP configuration, or use the `./start.sh` script which does this automatically.

**How it works:** The docker-compose.yml reads environment variables from your shell using `${SMTP_HOST}` syntax. If variables aren't set, it falls back to safe defaults (localhost:587).

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `localhost` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username/email | `` |
| `SMTP_PASSWORD` | SMTP password | `` |

## Testing the Server

### MCP Streamable HTTP (Recommended)

```bash
# Check health
curl http://localhost:8080/health

# Initialize MCP session (note the /mcp endpoint)
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "curl-client", "version": "1.0"}
    }
  }'

# Save the Mcp-Session-Id from response headers!
# Example: Mcp-Session-Id: 318a19a9-b757-4c0b-9ddb-a8dc1b40d240

# List available tools
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Verify SMTP connection
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "verify_connection",
      "arguments": {}
    }
  }'

# Send an email
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "send_email",
      "arguments": {
        "to": "recipient@example.com",
        "subject": "Test Email",
        "body": "This is a test email sent via MCP Sendmail Server"
      }
    }
  }'

# Send an HTML email
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {
      "name": "send_email",
      "arguments": {
        "to": "recipient@example.com",
        "subject": "HTML Test Email",
        "body": "<h1>Hello</h1><p>This is an <strong>HTML</strong> email!</p>",
        "html": true
      }
    }
  }'

# Send bulk emails
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
  -d '{
    "jsonrpc": "2.0",
    "id": 6,
    "method": "tools/call",
    "params": {
      "name": "send_bulk_email",
      "arguments": {
        "recipients": ["user1@example.com", "user2@example.com", "user3@example.com"],
        "subject": "Bulk Email",
        "body": "This email was sent to multiple recipients"
      }
    }
  }'

# Send template email
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
  -d '{
    "jsonrpc": "2.0",
    "id": 7,
    "method": "tools/call",
    "params": {
      "name": "send_template_email",
      "arguments": {
        "to": "recipient@example.com",
        "subject": "Welcome {name}!",
        "template": "Hello {name},\n\nWelcome to {company}!\n\nYour account is: {account}",
        "variables": {
          "name": "John Doe",
          "company": "Acme Corp",
          "account": "john.doe@acme.com"
        }
      }
    }
  }'
```

## Available MCP Tools

### 1. `send_email`
Send an email with optional attachments, CC, and BCC.

**Parameters:**
- `to` (string, required): Recipient email address
- `subject` (string, required): Email subject
- `body` (string, required): Email body content
- `from_addr` (string, optional): Sender email address (defaults to SMTP_USER)
- `cc` (array, optional): List of CC recipients
- `bcc` (array, optional): List of BCC recipients
- `html` (boolean, optional): Whether body is HTML (default: false)
- `attachments` (array, optional): List of attachments with filename and base64 content

**Example:**
```json
{
  "to": "recipient@example.com",
  "subject": "Meeting Tomorrow",
  "body": "Hi, let's meet tomorrow at 10 AM.",
  "cc": ["manager@example.com"],
  "html": false
}
```

### 2. `send_bulk_email`
Send the same email to multiple recipients.

**Parameters:**
- `recipients` (array, required): List of recipient email addresses
- `subject` (string, required): Email subject
- `body` (string, required): Email body content
- `from_addr` (string, optional): Sender email address (defaults to SMTP_USER)
- `html` (boolean, optional): Whether body is HTML (default: false)

**Example:**
```json
{
  "recipients": ["user1@example.com", "user2@example.com", "user3@example.com"],
  "subject": "System Maintenance Notice",
  "body": "The system will be down for maintenance on Saturday."
}
```

### 3. `send_template_email`
Send an email using a template with variable substitution.

**Parameters:**
- `to` (string, required): Recipient email address
- `subject` (string, required): Email subject
- `template` (string, required): Email template with {variable} placeholders
- `variables` (object, required): Dictionary of variable names and values
- `from_addr` (string, optional): Sender email address (defaults to SMTP_USER)
- `html` (boolean, optional): Whether template is HTML (default: false)

**Example:**
```json
{
  "to": "customer@example.com",
  "subject": "Order Confirmation",
  "template": "Dear {customer_name},\n\nYour order #{order_id} has been confirmed.\n\nTotal: ${total}",
  "variables": {
    "customer_name": "Jane Smith",
    "order_id": "12345",
    "total": "99.99"
  }
}
```

### 4. `verify_connection`
Verify SMTP connection and credentials.

**Parameters:** None

**Returns:** Connection status, server details, and port information

## API Endpoints

### MCP Streamable HTTP (Primary)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mcp` | MCP requests with session management |
| GET | `/mcp` | Open SSE stream for server notifications |
| GET | `/health` | Health check |

**Required Headers:**
- `Mcp-Session-Id`: Session ID (after initialize)
- `Mcp-Protocol-Version`: `2024-11-05`
- `Accept`: `application/json, text/event-stream`

### Legacy Endpoints (Backward Compatible)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/`, `/rpc`, `/jsonrpc` | Plain JSON-RPC 2.0 (no sessions) |
| GET | `/sse` | Legacy SSE (deprecated) |

### JSON-RPC Methods

| Method | Description |
|--------|-------------|
| `initialize` | Initialize MCP session (returns session ID) |
| `ping` | Keep-alive ping |
| `tools/list` | List available tools |
| `tools/call` | Execute a tool |

## Project Structure

```
mcp-mail/
├── src/
│   ├── server.py              # FastAPI server with tool registration
│   ├── mcp_handler.py         # MCP protocol implementation
│   ├── mcp_transport.py       # MCP transport layer
│   ├── mcp_session.py         # Session management
│   ├── email/
│   │   ├── __init__.py
│   │   └── email_operations.py # Email sending via SMTP
│   ├── jsonrpc/
│   │   ├── __init__.py
│   │   ├── handler.py         # JSON-RPC handler
│   │   └── models.py          # JSON-RPC models
│   └── utils/
│       ├── errors.py          # Custom exceptions
│       ├── validation.py      # Input validation
│       └── security.py        # Security utilities
├── tests/                     # Test suite
├── logs/                      # Application logs
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Docker Compose setup
└── requirements.txt           # Python dependencies
```

## SMTP Configuration Examples

### Gmail

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"  # Use App Password, not regular password
```

### Outlook/Office 365

```bash
export SMTP_HOST="smtp.office365.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@outlook.com"
export SMTP_PASSWORD="your-password"
```

### SendGrid

```bash
export SMTP_HOST="smtp.sendgrid.net"
export SMTP_PORT="587"
export SMTP_USER="apikey"
export SMTP_PASSWORD="your-sendgrid-api-key"
```

### Mailgun

```bash
export SMTP_HOST="smtp.mailgun.org"
export SMTP_PORT="587"
export SMTP_USER="postmaster@your-domain.mailgun.org"
export SMTP_PASSWORD="your-mailgun-smtp-password"
```

### Amazon SES

```bash
export SMTP_HOST="email-smtp.us-east-1.amazonaws.com"
export SMTP_PORT="587"
export SMTP_USER="your-ses-smtp-username"
export SMTP_PASSWORD="your-ses-smtp-password"
```

## Security Features

- **TLS Encryption**: All SMTP connections use TLS by default
- **Secure Credentials**: SMTP credentials stored in environment variables
- **Input Validation**: Email addresses and content validated
- **Non-root User**: Docker runs as `mcpuser` (UID 1000)

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Type checking
mypy src/

# Linting
ruff check src/

# Code formatting
black src/
```

## Docker Image Details

- **Base Image**: `python:3.11-slim`
- **Size**: ~150-200MB (optimized with multi-stage build)
- **User**: Non-root `mcpuser`
- **Health Checks**: Built-in
- **Volumes**: `/app/logs` (logs)

## Troubleshooting

### Gmail Authentication Issues

If you're using Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an App Password (not your regular password)
3. Use the App Password in `SMTP_PASSWORD`

### Connection Timeouts

If you get connection timeouts:
1. Check your firewall settings
2. Verify the SMTP host and port
3. Try port 465 (SSL) instead of 587 (TLS)
4. Use the `verify_connection` tool to test

### Certificate Errors

If you get SSL certificate errors:
1. Make sure you're using a valid SMTP server
2. Check if your network has SSL inspection enabled
3. Verify the server's certificate is valid

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues and questions, please open an issue on GitHub.
