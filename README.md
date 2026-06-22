# ChurchSuite Bookings MCP

[![Tests](https://github.com/stevehaskew/churchsuite-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/stevehaskew/churchsuite-mcp/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight [FastMCP](https://gofastmcp.com) server that exposes read-only
ChurchSuite booking data as MCP tools.

## Setup

1. Create an API-enabled user or an OAuth App in ChurchSuite to obtain a
   **Client ID** and **Client Secret** (see
   [ChurchSuite auth docs](https://developer.churchsuite.com/auth)). Grant it
   the `bookings.read`, `rotas.read`, and `addressbook.read` scopes.
2. Install dependencies:

   ```bash
   uv sync
   ```

3. Copy `.env.example` to `.env` and fill in your credentials, or export the
   variables directly:

   ```bash
   export CHURCHSUITE_CLIENT_ID=...
   export CHURCHSUITE_CLIENT_SECRET=...
   ```

4. Run the server:

   ```bash
   uv run churchsuite-mcp
   ```

## Tools

- `list_bookings(status?, starts_after?, starts_before?, customer_ids?, type_ids?, q?, page?, per_page?)`
  — list bookings with optional filters.
- `get_booking(id)` — fetch a single booking by ID.
- `list_booked_resources(booking_ids?, page?, per_page?)` — list resources booked against bookings.
- `list_resources(category?, q?, status?, page?, per_page?)` — list bookable resources (rooms, equipment, etc.).
- `get_resource(id)` — fetch a single bookable resource by ID.
- `list_ministries(statuses?, q?, ids?, page?, per_page?)` — list Rotas ministries.
- `get_ministry(id)` — fetch a single ministry, including its serving days/time/rotation type.
- `list_ministry_teams(ministry_ids?, team_ids?, page?, per_page?)` — list teams within ministries.
- `get_ministry_team(id)` — fetch a single ministry team.
- `list_ministry_members(ministry_ids?, role_ids?, team_ids?, page?, per_page?)` — list ministry members.
- `list_rota_roles(member_ids?, ministry_ids?, page?, per_page?)` — list roles defined within ministries.
- `find_serving_pattern(person_id, person_type)` — find a person's ministry memberships and their
  recurring serving pattern (days/time/rotation type).

> **Note on rotas:** ChurchSuite's API v2 does not expose individual rota
> slot assignments or dates — only ministry membership and a ministry's
> recurring schedule definition. `find_serving_pattern` is the closest
> available answer to "when am I next serving?": it returns the ministries/
> teams/roles a person belongs to and how often that ministry serves, not a
> confirmed next date.

## Using with an MCP client

Add to your client's MCP config (e.g. `.mcp.json` for Claude Code):

```json
{
  "mcpServers": {
    "churchsuite-bookings": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/churchsuite-mcp", "churchsuite-mcp"],
      "env": {
        "CHURCHSUITE_CLIENT_ID": "your-client-id",
        "CHURCHSUITE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

### Claude chat (desktop app)

To add this as a local MCP server in the Claude desktop app, open
**Settings → Developer → Edit Config** to locate `claude_desktop_config.json`,
then add the same `churchsuite-bookings` entry under `mcpServers`:

```json
{
  "mcpServers": {
    "churchsuite-bookings": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/churchsuite-mcp", "churchsuite-mcp"],
      "env": {
        "CHURCHSUITE_CLIENT_ID": "your-client-id",
        "CHURCHSUITE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

Replace `/path/to/churchsuite-mcp` with the absolute path to this project
(e.g. `/Users/steve/churchsuite-mcp`), fill in your real Client ID/Secret,
then restart Claude for the change to take effect.

## Auth

Authentication uses the OAuth2 **Client Credentials** grant against
`https://login.churchsuite.com/oauth2/token`. Access tokens are cached in
memory and transparently refreshed before they expire.
