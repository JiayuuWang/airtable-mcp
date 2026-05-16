import asyncio
import os

from dedalus_mcp import MCPServer, get_context
from dedalus_mcp.testing import TestRunner

from airtable import airtable, airtable_tools
from airtable.tools import (
    list_bases,
    list_tables,
    describe_table,
    list_records,
    get_record,
    create_record,
    update_record,
    delete_record,
    search_records,
)


def create_server() -> MCPServer:
    from dedalus_mcp.server import TransportSecuritySettings
    return MCPServer(
        name="dedalus-labs-airtable-mcp",
        connections=[airtable],
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
    )


async def test_schema_tools():
    print("\n=== Testing Schema Tools ===")

    print("\n1. Listing bases...")
    result = await list_bases()
    print(f"   Result: {result[0].text[:300]}...")


async def test_record_tools():
    print("\n=== Testing Record Tools ===")
    print("\nNote: Record operations require specific base_id, table_id, record_id values")
    print("Skipping live tests to avoid side effects")


async def main():
    token = os.environ.get("AIRTABLE_API_KEY")
    if not token:
        print("Error: AIRTABLE_API_KEY environment variable is not set")
        print("Please set it and try again:")
        print("  export AIRTABLE_API_KEY=pat...")
        return

    print("Airtable MCP Client Test")
    print("=" * 50)
    print(f"Using API key: {token[:8]}...")

    server = create_server()
    runner = TestRunner(server)

    async with runner:
        ctx = get_context()
        print(f"Connected to server: {server.name}")
        print(f"Available tools: {[t.name for t in airtable_tools]}")

        await test_schema_tools()
        await test_record_tools()

        print("\n" + "=" * 50)
        print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())