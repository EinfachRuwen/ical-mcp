# ical-mcp

MCP server for Apple Calendar and CalDAV providers.

Works with iCloud, Fastmail, Nextcloud, and any CalDAV-compatible calendar. No macOS dependency — runs headless on any platform, including Docker on a Raspberry Pi.

## Features

- List, create, update, and delete calendar events
- Check free/busy status for a time range
- Correct timezone handling — events are stored with a proper `TZID` (e.g. `Europe/Berlin`), not as a raw UTC `Z` value, so Apple Calendar shows the right label
- Per-calendar write protection (read-only by default)
- Bearer token authentication for the HTTP transport
- Docker support with pre-built ARM64 images for Raspberry Pi

## Quick start

```bash
# Install and run (local stdio mode)
uvx ical-mcp

# Or from source
uv sync
uv run ical-mcp
```

## Configuration

Set these environment variables (or copy `.env.example` to `.env`):

| Variable | Required | Description |
|---|---|---|
| `ICAL_MCP_URL` | Yes | CalDAV server URL (e.g. `https://caldav.icloud.com`) |
| `ICAL_MCP_USERNAME` | Yes | Your email / account ID |
| `ICAL_MCP_PASSWORD` | Yes | Password or app-specific password |
| `ICAL_MCP_TIMEZONE` | No | Your local timezone — **set this!** (e.g. `Europe/Berlin`). Default: `UTC` |
| `ICAL_MCP_WRITABLE_CALENDARS` | No | Calendars that allow writes (see [Write protection](#write-protection)) |
| `ICAL_MCP_API_KEY` | No | Bearer token for the HTTP transport (see [Security](#security)) |

### iCloud setup

1. Go to [account.apple.com](https://account.apple.com) → Sign-In and Security → App-Specific Passwords
2. Generate a new password (label it "ical-mcp")
3. Set `ICAL_MCP_URL=https://caldav.icloud.com`
4. Set `ICAL_MCP_USERNAME` to your Apple ID email
5. Set `ICAL_MCP_PASSWORD` to the generated app-specific password

## Tools

| Tool | Description |
|---|---|
| `list_calendars` | List all available calendars (shows read/write access per calendar) |
| `get_events` | Query events by date range |
| `create_event` | Create a new event |
| `update_event` | Update an existing event (partial patch, only changed fields) |
| `delete_event` | Delete an event |
| `get_freebusy` | Check busy/free status for a time range |

## Write protection

All calendars are **read-only by default**. You must explicitly opt in to writes:

```bash
# Single calendar (by name or ID)
ICAL_MCP_WRITABLE_CALENDARS=home

# Multiple calendars
ICAL_MCP_WRITABLE_CALENDARS=home,Work

# All calendars (use with caution)
ICAL_MCP_WRITABLE_CALENDARS=*
```

`list_calendars` shows `"access": "read-only"` or `"access": "read-write"` for each calendar.

## Transport

```bash
# Local use with Claude Code / Claude Desktop (default)
ical-mcp

# Shared HTTP server for remote/multi-agent access
ical-mcp --transport http --port 8093

# Bind to a specific address
ical-mcp --transport http --host 0.0.0.0 --port 8093
```

## Security

When running in HTTP mode (e.g. exposed via Cloudflare Tunnel), **always set `ICAL_MCP_API_KEY`**.

Without it, anyone who discovers your URL can read and modify your calendar. With it, every request must include the token as a Bearer header — otherwise the server responds with `401 Unauthorized`.

**Generate a secure token:**
```bash
openssl rand -hex 32
```

**Set the variable:**
```env
ICAL_MCP_API_KEY=your-generated-token-here
```

**Configure your AI client to send the token:**
```json
{
  "mcpServers": {
    "ical-mcp": {
      "url": "https://your-domain.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-generated-token-here"
      }
    }
  }
}
```

## Self-hosting with Docker

Pre-built images for AMD64 and ARM64 (Raspberry Pi) are available at `ghcr.io/einfachruwen/ical-mcp`.

1. Create a `docker-compose.yml` (copy from this repo or use the one below)
2. Fill in your credentials and a secure API key
3. Run `docker compose up -d`

The image is rebuilt automatically on every push to `main` via GitHub Actions.

### docker-compose.yml

```yaml
services:
  ical-mcp:
    image: ghcr.io/einfachruwen/ical-mcp:latest
    container_name: ical-mcp
    ports:
      - "8093:8093"
    environment:
      ICAL_MCP_URL: "https://caldav.icloud.com"
      ICAL_MCP_USERNAME: "your@icloud.com"
      ICAL_MCP_PASSWORD: "xxxx-xxxx-xxxx-xxxx"
      ICAL_MCP_TIMEZONE: "Europe/Berlin"
      ICAL_MCP_WRITABLE_CALENDARS: "*"
      ICAL_MCP_API_KEY: "your-secure-token-here"
    restart: unless-stopped
```

## Claude Code configuration

### Local (stdio)

```json
{
  "mcpServers": {
    "ical-mcp": {
      "command": "uvx",
      "args": ["ical-mcp"],
      "env": {
        "ICAL_MCP_URL": "https://caldav.icloud.com",
        "ICAL_MCP_USERNAME": "your@icloud.com",
        "ICAL_MCP_PASSWORD": "xxxx-xxxx-xxxx-xxxx",
        "ICAL_MCP_TIMEZONE": "Europe/Berlin",
        "ICAL_MCP_WRITABLE_CALENDARS": "your-calendar-id"
      }
    }
  }
}
```

### Remote (HTTP with auth)

```json
{
  "mcpServers": {
    "ical-mcp": {
      "url": "https://your-domain.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-secure-token-here"
      }
    }
  }
}
```

## Safety features

- **Per-calendar write protection** — read-only by default, explicit opt-in per calendar
- **Bearer token auth** — HTTP transport rejects all requests without a valid `ICAL_MCP_API_KEY`
- **Correct timezone handling** — events use `DTSTART;TZID=...` instead of raw UTC, fixing the "GMT+0" label in Apple Calendar
- **Backup before mutate** — every update/delete logs the full iCal data to stderr
- **ETag concurrency** — updates fail if the event was modified elsewhere since last fetch
- **Semantic errors** — clear messages for auth failures, rate limits, conflicts, and read-only violations

## License

MIT
