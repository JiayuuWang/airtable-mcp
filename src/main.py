import asyncio
import os

from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from airtable import airtable, airtable_tools


async def main() -> None:
    server = MCPServer(
        name="dedalus-labs-airtable-mcp",
        connections=[airtable],
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
        authorization_server=os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai"),
    )
    server.collect(*airtable_tools)
    await server.serve(port=8080)


if __name__ == "__main__":
    asyncio.run(main())