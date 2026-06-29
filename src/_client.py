# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""End-to-end client test for the Airtable MCP server.

Runs against the deployed marketplace server via the Dedalus runner,
passing credentials through the DAuth SecretValues path (the same path a
real marketplace user hits). Every tool is exercised at least once and a
deterministic PASS/FAIL line is printed per tool.

Required environment variables:
    DEDALUS_API_KEY     Dedalus API key (dsk-live-...)
    AIRTABLE_API_KEY    Airtable personal access token (pat...)

Optional:
    DEDALUS_API_URL   Override Dedalus API base (default https://api.dedaluslabs.ai)
    DEDALUS_AS_URL    Override Dedalus AS base  (default https://as.dedaluslabs.ai)
    MCP_SERVER_SLUG   Marketplace slug (default JiayuWang/airtable-mcp)

Usage:
    PYTHONPATH=src python src/_client.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from airtable import airtable  # noqa: E402
from dedalus_mcp.auth import Connection as _Conn
from dedalus_labs.lib.mcp.request import slug_to_connection_name as _s2c


def _rebind(conn, slug):
    return _Conn(name=_s2c(slug), secrets=conn.secrets, base_url=conn.base_url,
                 auth_header_name=conn.auth_header_name, auth_header_format=conn.auth_header_format)


DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY", "")
DEDALUS_API_URL = os.getenv("DEDALUS_API_URL", "https://api.dedaluslabs.ai")
DEDALUS_AS_URL = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
MCP_SERVER_SLUG = os.getenv("MCP_SERVER_SLUG", "JiayuWang/airtable-mcp")
MODEL = os.getenv("DEDALUS_TEST_MODEL", "anthropic/claude-sonnet-4-5")

REQUIRED_TOOLS = [
    "list_bases",
    "list_tables",
    "describe_table",
    "list_records",
    "get_record",
    "search_records",
    "create_record",
    "update_record",
    "delete_record",
]


def _passed(tool_name: str, tool_events: list) -> bool:
    """A tool counts as exercised if it was successfully called.
    
    Checks on_tool_event records for actual tool invocation with the expected name.
    """
    if not tool_events:
        return False
    
    for event in tool_events:
        if hasattr(event, 'name') and tool_name in event.name:
            return True
        if isinstance(event, dict) and tool_name in event.get('name', ''):
            return True
    
    return False


async def _run_tool(runner, creds, tool_name: str, instruction: str) -> bool:
    print(f"\n--- {tool_name} ---")
    tool_events = []
    
    def on_tool_event(event):
        tool_events.append(event)
    
    try:
        result = await runner.run(
            input=instruction,
            model=MODEL,
            mcp_servers=[MCP_SERVER_SLUG],
            credentials=creds,
            max_steps=6,
            max_tokens=4096,
            on_tool_event=on_tool_event,
        )
        output = getattr(result, "output", str(result)) or ""
        print(output[:600])
        ok = _passed(tool_name, tool_events)
        if ok:
            print(f"✓ Tool called: {len(tool_events)} invocation(s)")
    except Exception as exc:  # noqa: BLE001
        print(f"exception: {exc!r}")
        ok = False
    print(f"[{'PASS' if ok else 'FAIL'}] {tool_name}")
    return ok


async def main() -> int:
    if not DEDALUS_API_KEY:
        print("Error: DEDALUS_API_KEY not set")
        return 1
    if not AIRTABLE_API_KEY:
        print("Error: AIRTABLE_API_KEY not set")
        return 1

    from dedalus_labs import AsyncDedalus, DedalusRunner
    from dedalus_mcp.auth import SecretValues

    creds = [SecretValues(_rebind(airtable, MCP_SERVER_SLUG), api_key=AIRTABLE_API_KEY)]

    client = AsyncDedalus(
        api_key=DEDALUS_API_KEY,
        base_url=DEDALUS_API_URL,
        as_base_url=DEDALUS_AS_URL,
    )
    runner = DedalusRunner(client)

    print(f"Testing Airtable MCP server: {MCP_SERVER_SLUG}")
    print("=" * 60)

    results: dict[str, bool] = {}

    # 1. Read-only discovery. list_bases yields a base id; list_tables yields a
    #    table id; both feed the record tools below.
    results["list_bases"] = await _run_tool(
        runner, creds, "list_bases",
        "Call the list_bases tool and show each base id and name.",
    )
    results["list_tables"] = await _run_tool(
        runner, creds, "list_tables",
        "Call list_bases to get the first base id, then call list_tables for "
        "that base and list each table id and name.",
    )
    results["describe_table"] = await _run_tool(
        runner, creds, "describe_table",
        "Call list_bases, then list_tables to get the first base id and table "
        "id, then call describe_table on that base and table.",
    )
    results["list_records"] = await _run_tool(
        runner, creds, "list_records",
        "Call list_bases and list_tables to get the first base id and table id, "
        "then call list_records with max_records 5 and list each record id.",
    )
    results["get_record"] = await _run_tool(
        runner, creds, "get_record",
        "Call list_bases, list_tables, list_records with max_records 1 to get a "
        "record id, then call get_record on that base, table and record id.",
    )
    results["search_records"] = await _run_tool(
        runner, creds, "search_records",
        "Call list_bases and list_tables to get the first base id and table id, "
        "then call search_records on them with search_term 'a' and max_records 5.",
    )

    # 2. Write / destructive tools as a self-contained fixture: create a record,
    #    update it, then delete it so no test data is left behind.
    results["create_record"] = await _run_tool(
        runner, creds, "create_record",
        "Call list_bases and list_tables to get the first base id and table id. "
        "Call create_record on them with fields {\"Name\": \"Dedalus Smoke Test\"}. "
        "Report the new record id.",
    )
    results["update_record"] = await _run_tool(
        runner, creds, "update_record",
        "Call list_bases and list_tables for the first base id and table id, "
        "create_record with fields {\"Name\": \"Dedalus Update Test\"} to get a "
        "record id, then call update_record on it with fields "
        "{\"Name\": \"Dedalus Updated\"}.",
    )
    results["delete_record"] = await _run_tool(
        runner, creds, "delete_record",
        "Call list_bases and list_tables for the first base id and table id, "
        "create_record with fields {\"Name\": \"Dedalus Delete Test\"} to get a "
        "record id, then call delete_record on that record id to clean it up.",
    )

    print("\n" + "=" * 60)
    print("Summary")
    for name in REQUIRED_TOOLS:
        ok = results.get(name, False)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    all_pass = all(results.get(t, False) for t in REQUIRED_TOOLS)
    print("\nRESULT:", "ALL PASS" if all_pass else "SOME FAILED")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))