# Eclipse OpenClaw Workspace Template

Base workspace configuration for Eclipse partners running OpenClaw.

## What's Included

### Workspace Files
- `SOUL.md` — Agent personality and values
- `AGENTS.md` — Workspace conventions and rules
- `USER.md` — Partner profile (fill in after deployment)
- `TOOLS.md` — Local tool configuration notes
- `MEMORY.md` — Long-term memory store
- `HEARTBEAT.md` — Periodic checks (meeting dossiers, flight tracking)

### Proactive Features
- **Meeting Dossiers** — Auto-researches external attendees ~1hr before meetings
- **Flight Tracking** — Monitors flights from calendar, alerts on delays/changes
- **Daily Briefings** — Optional cron jobs for news, exec moves, deal sourcing

### Skills
- **weather** — Weather forecasts (bundled, no API key)
- **clawhub** — Skill marketplace (bundled, no API key)
- **flight-tracker** — Live flight tracking (included)
- **o365-calendar** — Office 365 calendar integration (included)
- **sec-filing-watcher** — SEC EDGAR alerts for watchlist tickers
- **arxiv-watcher** — Search and summarize ArXiv papers

## Deployment

### Automated
Use my local script for partner-deploy.sh

### Prerequisites
1. DigitalOcean account with `doctl` CLI installed
2. Partner's Telegram bot token (from @BotFather)
3. Partner's Anthropic API key
4. Partner's Telegram user ID (from @userinfobot)
5. Brave Search API key (from https://brave.com/search/api - free tier available)

### Quick Deploy

```bash
# 1. Copy the template
cp openclaw-appplatform.yaml openclaw-<name>.yaml

# 2. Generate unique gateway token
GATEWAY_TOKEN=$(openssl rand -hex 32)
echo "Gateway token: $GATEWAY_TOKEN"

# 3. Edit the file and replace all PARTNER_* placeholders
#    - PARTNER_NAME
#    - PARTNER_ANTHROPIC_KEY
#    - PARTNER_BOT_TOKEN
#    - PARTNER_TELEGRAM_ID
#    - PARTNER_GATEWAY_TOKEN (use generated token)
#    - PARTNER_TIMEZONE (e.g., America/Los_Angeles)
#    - PARTNER_O365_CLIENT_ID (optional)
#    - PARTNER_O365_TENANT_ID (optional)

# 4. Deploy
doctl apps create --spec openclaw-<name>.yaml
```

## Proactive Features

### Meeting Dossiers (via Heartbeat)

Automatically enabled. Before meetings with external attendees:
- Researches attendee background (role, company, career)
- Finds recent news/activity
- Identifies Eclipse portfolio connections
- Sends dossier to Telegram ~1 hour before

Requires O365 calendar integration.

### Daily Briefings (via Cron)

See `cron-templates.md` for ready-to-use templates:

| Time | Briefing |
|------|----------|
| 7:00 AM | Industry News + Tech Leader Digest |
| 7:15 AM | Executive Movement Tracker |

Partners enable by asking their assistant: *"Set up the daily industry briefing at 7am"*

## Skill Setup

### Weather
No setup needed. Uses wttr.in (free, no API key).

### ClawHub
No setup needed. Partners can install additional skills with:
```
clawhub search <query>
clawhub install <skill-name>
```

### Flight Tracker
Works out of the box for live tracking (OpenSky Network). No API key needed.

### SEC Filing Watcher
Monitors SEC EDGAR for new filings from a watchlist of tickers.

1. **Configure watchlist:**
   ```bash
   cp skills/sec-filing-watcher/assets/watchlist.example.json skills/sec-filing-watcher/watchlist.json
   # Edit with your tickers
   ```

2. **Set up cron (every 15 min):**
   ```
   Ask your assistant: "Set up SEC filing alerts for TSLA, NVDA, AMD"
   ```

### ArXiv Watcher
Search and summarize research papers. No setup needed.

```
"Find the latest ArXiv papers on robotics manipulation"
"Summarize today's AI papers"
```

### O365 Calendar
Requires Azure AD app registration:

1. **Admin creates app in Azure AD:**
   - Azure Portal → Azure AD → App registrations → New
   - Enable "Allow public client flows"
   - Add permissions: `Calendars.Read`, `User.Read`, `offline_access`
   - Grant admin consent

2. **Set environment variables:**
   - `O365_CLIENT_ID` — Application (client) ID
   - `O365_TENANT_ID` — Directory (tenant) ID

3. **Partner authenticates:**
   ```bash
   # Via Telegram, ask the bot to run:
   python skills/o365-calendar/scripts/o365cal.py auth
   ```
   Then visit the URL and enter the code.

## Customization

Partners can customize via Telegram:
- "Update my SOUL.md to be more direct"
- "Add my phone number to USER.md"
- "Set up a daily briefing at 6:30am instead"
- "Focus the startup scout on robotics only"

## Security

This template includes:
- ✅ Encrypted secrets (DO App Platform)
- ✅ Unique gateway token per instance
- ✅ Loopback-only gateway binding
- ✅ Exec in allowlist mode
- ✅ Log redaction for sensitive data
- ✅ Telegram restricted to single user

## Support

- OpenClaw docs: https://docs.openclaw.ai
- Discord: https://discord.com/invite/clawd
- GitHub: https://github.com/openclaw/openclaw
