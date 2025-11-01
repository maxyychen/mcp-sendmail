"""FastAPI server with MCP Streamable HTTP transport support."""
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sse_starlette.sse import EventSourceResponse

from .mcp_handler import MCPHandler
from .email.email_operations import EmailOperations
from .jsonrpc.handler import JSONRPCHandler
from .jsonrpc.models import JSONRPCRequest, JSONRPCResponse
from .mcp_transport import MCPTransport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
mcp_handler = MCPHandler()
jsonrpc_handler = JSONRPCHandler()
mcp_transport = MCPTransport(jsonrpc_handler)

# Initialize email operations
email_ops = EmailOperations()


def register_all_tools():
    """Register all MCP email tools."""

    # Tool 1: send_email
    mcp_handler.register_tool(
        name="send_email",
        description="Send an email with optional attachments",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body content"},
                "from_addr": {
                    "type": "string",
                    "description": "Sender email address (optional, defaults to SMTP_USER)",
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of CC recipients (optional)",
                },
                "bcc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of BCC recipients (optional)",
                },
                "html": {
                    "type": "boolean",
                    "description": "Whether body is HTML (default: false for plain text)",
                },
                "attachments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content": {"type": "string", "description": "Base64 encoded content"},
                        },
                    },
                    "description": "List of attachments (optional)",
                },
            },
            "required": ["to", "subject", "body"],
        },
        handler=email_ops.send_email,
    )

    # Tool 2: send_bulk_email
    mcp_handler.register_tool(
        name="send_bulk_email",
        description="Send the same email to multiple recipients",
        input_schema={
            "type": "object",
            "properties": {
                "recipients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of recipient email addresses",
                },
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body content"},
                "from_addr": {
                    "type": "string",
                    "description": "Sender email address (optional, defaults to SMTP_USER)",
                },
                "html": {
                    "type": "boolean",
                    "description": "Whether body is HTML (default: false)",
                },
            },
            "required": ["recipients", "subject", "body"],
        },
        handler=email_ops.send_bulk_email,
    )

    # Tool 3: send_template_email
    mcp_handler.register_tool(
        name="send_template_email",
        description="Send an email using a template with variable substitution",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "template": {
                    "type": "string",
                    "description": "Email template with {variable} placeholders",
                },
                "variables": {
                    "type": "object",
                    "description": "Dictionary of variable names and values to substitute",
                },
                "from_addr": {
                    "type": "string",
                    "description": "Sender email address (optional, defaults to SMTP_USER)",
                },
                "html": {
                    "type": "boolean",
                    "description": "Whether template is HTML (default: false)",
                },
            },
            "required": ["to", "subject", "template", "variables"],
        },
        handler=email_ops.send_template_email,
    )

    # Tool 4: verify_connection
    mcp_handler.register_tool(
        name="verify_connection",
        description="Verify SMTP connection and credentials",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=email_ops.verify_connection,
    )


def register_jsonrpc_methods():
    """Register all JSON-RPC 2.0 methods."""

    # Method: initialize
    async def initialize(params: dict):
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "logging": {}
            },
            "serverInfo": {
                "name": "mcp-sendmail-server",
                "version": "1.0.0"
            }
        }

    # Method: ping
    async def ping(params: dict):
        return {}

    # Method: tools/list
    async def tools_list(params: dict):
        tools = mcp_handler.list_tools()
        return {"tools": tools}

    # Method: tools/call
    async def tools_call(params: dict):
        name = params.get("name")
        arguments = params.get("arguments", {})

        if not name:
            raise ValueError("Tool name is required")

        result = await mcp_handler.execute_tool(name, arguments)
        return {
            "content": [{"type": "text", "text": str(result)}]
        }

    # Register methods
    jsonrpc_handler.register_method("initialize", initialize)
    jsonrpc_handler.register_method("ping", ping)
    jsonrpc_handler.register_method("tools/list", tools_list)
    jsonrpc_handler.register_method("tools/call", tools_call)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    logger.info("Starting MCP server with Streamable HTTP transport...")
    register_all_tools()
    register_jsonrpc_methods()
    mcp_transport.start_cleanup()
    logger.info(f"Registered {len(mcp_handler.tools)} MCP tools")
    logger.info(f"Registered {len(jsonrpc_handler.methods)} JSON-RPC methods")
    logger.info("MCP session cleanup task started")
    yield
    logger.info("Shutting down MCP server...")
    mcp_transport.stop_cleanup()


app = FastAPI(
    title="MCP Sendmail Server",
    description="MCP server with Streamable HTTP transport for sending emails via SMTP",
    version="2.1.0",
    lifespan=lifespan,
)


# MCP Streamable HTTP Endpoint (Unified POST + GET)
@app.post("/mcp")
async def mcp_post_endpoint(request: Request, jsonrpc_request: JSONRPCRequest):
    """MCP Streamable HTTP POST endpoint.

    Per MCP spec: Every JSON-RPC message from client MUST be a new HTTP POST.
    Handles MCP headers: Mcp-Session-Id, Mcp-Protocol-Version.
    """
    return await mcp_transport.handle_post_request(request, jsonrpc_request)


@app.get("/mcp")
async def mcp_get_endpoint(request: Request):
    """MCP Streamable HTTP GET endpoint.

    Per MCP spec: Opens an SSE stream allowing server to push messages.
    Supports resumption via Last-Event-Id header.
    """
    return await mcp_transport.handle_get_request(request)


# Legacy JSON-RPC 2.0 Endpoints (for backward compatibility)
@app.post("/")
@app.post("/rpc")
@app.post("/jsonrpc")
async def jsonrpc_endpoint(request: JSONRPCRequest):
    """Legacy JSON-RPC 2.0 endpoint (no MCP headers).

    Kept for backward compatibility with non-MCP clients.
    """
    response = await jsonrpc_handler.handle_request(request)
    return response.model_dump(exclude_none=True)


# Monitoring Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mcp-sendmail-server",
        "version": "2.1.0",
        "transport": "MCP Streamable HTTP",
        "protocol_version": "2024-11-05",
        "smtp_host": email_ops.smtp_host,
        "smtp_port": email_ops.smtp_port,
    }


@app.get("/sse")
async def legacy_sse_endpoint():
    """Legacy SSE endpoint (deprecated).

    Use GET /mcp with Mcp-Session-Id header instead.
    """
    async def event_generator() -> AsyncGenerator[dict, None]:
        yield {
            "event": "message",
            "data": '{"type": "notification", "message": "Legacy SSE endpoint. Use GET /mcp instead."}',
        }

    return EventSourceResponse(event_generator())
