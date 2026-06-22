"""Entry point for the ChurchSuite bookings MCP server."""

from __future__ import annotations

import os
import sys

from fastmcp import FastMCP

from .auth import TokenManager
from .client import ChurchSuiteClient
from .tools import register_tools

DEFAULT_SCOPE = "bookings.read rotas.read addressbook.read"


def build_server() -> FastMCP:
    client_id = os.environ.get("CHURCHSUITE_CLIENT_ID")
    client_secret = os.environ.get("CHURCHSUITE_CLIENT_SECRET")
    scope = os.environ.get("CHURCHSUITE_SCOPE", DEFAULT_SCOPE)

    if not client_id or not client_secret:
        sys.exit(
            "CHURCHSUITE_CLIENT_ID and CHURCHSUITE_CLIENT_SECRET environment variables must be set."
        )

    token_manager = TokenManager(client_id=client_id, client_secret=client_secret, scope=scope)
    client = ChurchSuiteClient(token_manager=token_manager)

    mcp = FastMCP("churchsuite-bookings")
    register_tools(mcp, client)
    return mcp


def main() -> None:
    server = build_server()
    server.run()


if __name__ == "__main__":
    main()
