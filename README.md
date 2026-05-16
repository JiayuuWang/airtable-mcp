# Airtable MCP Server

MCP server for Airtable with Type 3 DAuth authentication.

## Tools

### Schema Tools
- **`list_bases`** - List all accessible Airtable bases
- **`list_tables`** - List tables in a base (with schema)
- **`describe_table`** - Get detailed table schema information

### Records Tools
- **`list_records`** - List records from a table (supports filterByFormula, sort, pagination)
- **`get_record`** - Get a single record by ID
- **`create_record`** - Create a new record in a table
- **`update_record`** - Update a record (PATCH)
- **`delete_record`** - Delete a record

### Search Tools
- **`search_records`** - Search records by text term

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your Airtable API key (Personal Access Token):
   ```
   AIRTABLE_API_KEY=pat...
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

## Usage

```bash
python -m src.main
```

## Authentication

Uses DAuth (Dedalus Auth) for secure credential handling:
- Credentials are encrypted client-side
- Raw secrets are decrypted only in sealed execution boundaries
- Tokens are cryptographically bound to the client (DPoP)

## API Reference

Airtable REST API: https://api.airtable.com/v0