import json
from typing import Any

from mcp.types import TextContent
from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys
from dedalus_mcp.types import ToolAnnotations

_BASE_URL = "https://api.airtable.com"

airtable = Connection(
    name="JiayuWang-airtable-mcp",
    secrets=SecretKeys(api_key="AIRTABLE_API_KEY"),
    base_url=_BASE_URL,
    auth_header_format="Bearer {api_key}",
)

Result = list[TextContent]


async def _req(
    method: HttpMethod,
    path: str,
    body: dict | None = None,
    params: dict | None = None,
) -> Result:
    ctx = get_context()
    resp = await ctx.dispatch(
        "JiayuWang-airtable-mcp",
        HttpRequest(method=method, path=path, body=body, params=params),
    )
    if resp.success:
        data = resp.response.body or {}
        return [TextContent(type="text", text=json.dumps(data, indent=2))]
    error = resp.error.message if resp.error else "Request failed"
    return [TextContent(type="text", text=json.dumps({"error": error}, indent=2))]


def _table_id_unescape(table_id: str) -> str:
    return table_id.replace("t/", "")


@tool(
    description="List all accessible Airtable bases",
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_bases() -> Result:
    return await _req(HttpMethod.GET, "/v0/meta/bases")


@tool(
    description="List tables in a base with schema information",
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_tables(base_id: str, detail_level: str = "full") -> Result:
    return await _req(HttpMethod.GET, f"/v0/meta/bases/{base_id}/tables")


@tool(
    description="Get detailed schema for a specific table",
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def describe_table(base_id: str, table_id: str, detail_level: str = "full") -> Result:
    return await _req(HttpMethod.GET, f"/v0/meta/bases/{base_id}/tables/{table_id}")


@tool(
    description="List records from a table with optional filtering and sorting",
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_records(
    base_id: str,
    table_id: str,
    view: str | None = None,
    max_records: int | None = None,
    filter_by_formula: str | None = None,
    sort: list[dict[str, str]] | None = None,
) -> Result:
    params: dict[str, Any] = {}
    if max_records is not None:
        params["maxRecords"] = max_records
    if filter_by_formula:
        params["filterByFormula"] = filter_by_formula
    if view:
        params["view"] = view
    if sort:
        params["sort"] = sort

    table_id_unescaped = _table_id_unescape(table_id)
    return await _req(HttpMethod.GET, f"/v0/{base_id}/{table_id_unescaped}", params=params if params else None)


@tool(
    description="Get a single record by ID",
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def get_record(base_id: str, table_id: str, record_id: str) -> Result:
    table_id_unescaped = _table_id_unescape(table_id)
    return await _req(HttpMethod.GET, f"/v0/{base_id}/{table_id_unescaped}/{record_id}")


@tool(
    description="Create a new record in a table",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
async def create_record(base_id: str, table_id: str, fields: dict[str, Any]) -> Result:
    table_id_unescaped = _table_id_unescape(table_id)
    return await _req(
        HttpMethod.POST,
        f"/v0/{base_id}/{table_id_unescaped}",
        body={"fields": fields, "typecast": True},
    )


@tool(
    description="Update a record (PATCH)",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
async def update_record(base_id: str, table_id: str, record_id: str, fields: dict[str, Any]) -> Result:
    table_id_unescaped = _table_id_unescape(table_id)
    return await _req(
        HttpMethod.PATCH,
        f"/v0/{base_id}/{table_id_unescaped}/{record_id}",
        body={"fields": fields, "typecast": True},
    )


@tool(
    description="Delete a record",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
async def delete_record(base_id: str, table_id: str, record_id: str) -> Result:
    table_id_unescaped = _table_id_unescape(table_id)
    return await _req(
        HttpMethod.DELETE,
        f"/v0/{base_id}/{table_id_unescaped}?records[]={record_id}",
    )


@tool(
    description="Search records by text term in all text fields",
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def search_records(
    base_id: str,
    table_id: str,
    search_term: str,
    field_ids: list[str] | None = None,
    max_records: int | None = None,
    view: str | None = None,
) -> Result:
    escaped_term = search_term.replace('"', '\\"').replace('\\', '\\\\')

    if field_ids:
        or_parts = ",".join([f'FIND("{escaped_term}", {{{fid}}})' for fid in field_ids])
        filter_formula = f"OR({or_parts})"
    else:
        filter_formula = f'OR(FIND("{escaped_term}", {{Name}}),FIND("{escaped_term}", {{Title}}))'

    params: dict[str, Any] = {"filterByFormula": filter_formula}
    if max_records:
        params["maxRecords"] = max_records
    if view:
        params["view"] = view

    table_id_unescaped = _table_id_unescape(table_id)
    return await _req(HttpMethod.GET, f"/v0/{base_id}/{table_id_unescaped}", params=params)


airtable_tools = [
    list_bases,
    list_tables,
    describe_table,
    list_records,
    get_record,
    create_record,
    update_record,
    delete_record,
    search_records,
]