# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

import os
import asyncio
from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings
from airtable import airtable, airtable_tools


def _disable_auto_output_schemas(server: MCPServer) -> None:
    server.tools._build_output_schema = lambda _fn: None


async def main() -> None:
    server = MCPServer(
        name="dedalus-labs-airtable-mcp",
        connections=[airtable],
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
        authorization_server=os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai"),
    )
    _disable_auto_output_schemas(server)
    server.collect(*airtable_tools)
    await server.serve(port=8080)


if __name__ == "__main__":
    asyncio.run(main())