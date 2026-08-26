"""ical-mcp: MCP server for Apple Calendar and CalDAV providers."""

import argparse
import logging
import os

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .server import mcp

__version__ = "0.1.0"

logger = logging.getLogger("ical-mcp")


class _BearerAuthMiddleware(BaseHTTPMiddleware):
    """Schützt den HTTP-Server mit einem Bearer Token (ICAL_MCP_API_KEY)."""

    def __init__(self, app, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request, call_next):
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip()
        if token != self._api_key:
            return JSONResponse(
                {"error": "Unauthorized - Bearer token required"},
                status_code=401,
            )
        return await call_next(request)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ical-mcp",
        description="MCP server for Apple Calendar and CalDAV providers",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="stdio for local (Claude Code/Desktop), http for remote/shared (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP server bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8093,
        help="HTTP server port (default: 8093)",
    )
    args = parser.parse_args()

    if args.transport == "http":
        api_key = os.environ.get("ICAL_MCP_API_KEY", "").strip()
        asgi_app = mcp.http_app(path="/mcp")

        if api_key:
            logger.info("Bearer token authentication enabled (ICAL_MCP_API_KEY is set)")
            asgi_app = _BearerAuthMiddleware(asgi_app, api_key)
        else:
            logger.warning(
                "ICAL_MCP_API_KEY is not set — the HTTP server is unprotected! "
                "Set this variable to require a Bearer token."
            )

        uvicorn.run(asgi_app, host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")

