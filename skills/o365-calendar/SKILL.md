---
name: o365-calendar
description: Read Office 365 calendar events via Microsoft Graph API. Uses device code flow for OAuth2 authentication with delegated permissions.
---

# Office 365 Calendar

Read calendar events from Microsoft 365 using Graph API with delegated permissions.

## Setup

### 1. Azure AD App Registration (Admin does once per tenant)

1. Go to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Name: "OpenClaw Calendar" (or similar)
4. Supported account types: "Accounts in this organizational directory only"
5. Redirect URI: Leave blank (using device code flow)
6. After creation, note the **Application (client) ID** and **Directory (tenant) ID**
7. Go to API permissions → Add permission → Microsoft Graph → Delegated:
   - `Calendars.Read`
   - `User.Read`
   - `offline_access`
8. Click "Grant admin consent" (requires admin)
9. Go to Authentication → Advanced settings → Enable "Allow public client flows"

### 2. Environment Variables

Set these in your deployment:
```
O365_CLIENT_ID=your-client-id
O365_TENANT_ID=your-tenant-id
```

Note: No client_secret needed — this is a public client using device code flow.

### 3. Authenticate

```bash
python scripts/o365cal.py auth
```

Follow the device code flow — visit the URL and enter the code.

## Commands

```bash
# Authenticate (one-time setup)
python scripts/o365cal.py auth

# Check auth status
python scripts/o365cal.py status

# Today's events
python scripts/o365cal.py today

# Tomorrow's events
python scripts/o365cal.py tomorrow

# Upcoming events (default 7 days)
python scripts/o365cal.py upcoming

# Upcoming events (custom days)
python scripts/o365cal.py upcoming 14
```

## Token Management

- Tokens are stored in `token.json` (auto-created after auth)
- Access tokens auto-refresh using the refresh token
- If refresh fails, re-run `auth` command

## Notes

- Requires `requests` Python package
- Times displayed in user's timezone (set TZ env var)
- Device code flow works well for CLI/headless scenarios
