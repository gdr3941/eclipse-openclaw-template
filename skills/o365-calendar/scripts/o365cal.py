#!/usr/bin/env python3
"""
Office 365 Calendar - Microsoft Graph API integration
Uses device code flow for OAuth2 authentication with delegated permissions

Configuration via environment variables:
  O365_CLIENT_ID  - Azure AD application client ID
  O365_TENANT_ID  - Azure AD tenant ID
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# Get timezone from env, default to UTC
DISPLAY_TZ = ZoneInfo(os.environ.get("TZ", "UTC"))

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
TOKEN_FILE = SKILL_DIR / "token.json"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# OAuth scopes
SCOPES = ["Calendars.Read", "User.Read", "offline_access"]


def get_config():
    """Load config from environment variables"""
    client_id = os.environ.get("O365_CLIENT_ID")
    tenant_id = os.environ.get("O365_TENANT_ID")
    
    if not client_id or not tenant_id:
        print("Error: O365_CLIENT_ID and O365_TENANT_ID environment variables must be set", file=sys.stderr)
        print("\nSet them in your deployment or export locally:", file=sys.stderr)
        print("  export O365_CLIENT_ID='your-client-id'", file=sys.stderr)
        print("  export O365_TENANT_ID='your-tenant-id'", file=sys.stderr)
        sys.exit(1)
    
    return {
        "client_id": client_id,
        "tenant_id": tenant_id,
        "scopes": SCOPES
    }


def save_token(token_data):
    token_data["obtained_at"] = time.time()
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def load_token():
    if not TOKEN_FILE.exists():
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def is_token_expired(token_data):
    if not token_data:
        return True
    obtained_at = token_data.get("obtained_at", 0)
    expires_in = token_data.get("expires_in", 3600)
    return time.time() > (obtained_at + expires_in - 1800)  # 30 min buffer


def refresh_token(config, token_data):
    """Refresh the access token using refresh_token"""
    if not token_data or "refresh_token" not in token_data:
        return None
    
    url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
    # Note: Don't send client_secret for public clients (device code flow)
    data = {
        "client_id": config["client_id"],
        "refresh_token": token_data["refresh_token"],
        "grant_type": "refresh_token",
        "scope": " ".join(config["scopes"])
    }
    
    resp = requests.post(url, data=data)
    if resp.status_code == 200:
        new_token = resp.json()
        save_token(new_token)
        return new_token
    return None


def device_code_auth(config):
    """Initiate device code flow for authentication"""
    url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/devicecode"
    data = {
        "client_id": config["client_id"],
        "scope": " ".join(config["scopes"])
    }
    
    resp = requests.post(url, data=data)
    if resp.status_code != 200:
        print(f"Error initiating device code flow: {resp.text}", file=sys.stderr)
        sys.exit(1)
    
    return resp.json()


def poll_for_token(config, device_code_response):
    """Poll for token after user completes device code auth"""
    url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
    data = {
        "client_id": config["client_id"],
        "device_code": device_code_response["device_code"],
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
    }
    
    interval = device_code_response.get("interval", 5)
    expires_in = device_code_response.get("expires_in", 900)
    start_time = time.time()
    
    while time.time() - start_time < expires_in:
        time.sleep(interval)
        resp = requests.post(url, data=data)
        result = resp.json()
        
        if "access_token" in result:
            save_token(result)
            return result
        
        error = result.get("error")
        if error == "authorization_pending":
            continue
        elif error == "slow_down":
            interval += 5
        elif error == "expired_token":
            print("Device code expired. Please try again.", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Error: {result.get('error_description', error)}", file=sys.stderr)
            sys.exit(1)
    
    print("Timeout waiting for authorization.", file=sys.stderr)
    sys.exit(1)


def get_access_token(config):
    """Get a valid access token, refreshing or re-authenticating as needed"""
    token_data = load_token()
    
    if token_data and not is_token_expired(token_data):
        return token_data["access_token"]
    
    if token_data and "refresh_token" in token_data:
        new_token = refresh_token(config, token_data)
        if new_token:
            return new_token["access_token"]
    
    print("Authentication required. Run: python o365cal.py auth", file=sys.stderr)
    sys.exit(1)


def get_calendar_events(access_token, start_date=None, end_date=None, top=20):
    """Fetch calendar events from Microsoft Graph"""
    if not start_date:
        start_date = datetime.now(tz=ZoneInfo("UTC")).replace(hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = start_date + timedelta(days=7)
    
    start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = f"{GRAPH_BASE}/me/calendarView"
    params = {
        "startDateTime": start_iso,
        "endDateTime": end_iso,
        "$top": top,
        "$orderby": "start/dateTime",
        "$select": "subject,start,end,location,organizer,attendees,isAllDay,bodyPreview"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        print(f"Error fetching events: {resp.text}", file=sys.stderr)
        sys.exit(1)
    
    return resp.json().get("value", [])


def parse_graph_datetime(dt_str, tz_str=None):
    """Parse datetime from Graph API and convert to display timezone"""
    if not dt_str:
        return None
    dt_str = dt_str.split(".")[0]
    try:
        dt = datetime.fromisoformat(dt_str)
        if tz_str and tz_str != "UTC":
            try:
                source_tz = ZoneInfo(tz_str)
                dt = dt.replace(tzinfo=source_tz)
            except:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        else:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(DISPLAY_TZ)
    except:
        return None


def format_event(event):
    """Format a calendar event for display"""
    subject = event.get("subject", "No Subject")
    start = event.get("start", {})
    end = event.get("end", {})
    location = event.get("location", {}).get("displayName", "")
    is_all_day = event.get("isAllDay", False)
    
    start_dt = parse_graph_datetime(start.get("dateTime"), start.get("timeZone"))
    end_dt = parse_graph_datetime(end.get("dateTime"), end.get("timeZone"))
    
    tz_abbrev = DISPLAY_TZ.key.split("/")[-1][:3].upper() if "/" in DISPLAY_TZ.key else "LOC"
    
    if is_all_day:
        time_str = "All Day"
        date_str = start.get("dateTime", "")[:10]
    elif start_dt and end_dt:
        time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')} {tz_abbrev}"
        date_str = start_dt.strftime('%Y-%m-%d')
    else:
        time_str = start.get("dateTime", "")[11:16]
        date_str = start.get("dateTime", "")[:10]
    
    line = f"• {date_str} {time_str}: {subject}"
    if location:
        line += f" @ {location}"
    
    return line


def cmd_auth(config):
    """Initiate authentication"""
    result = device_code_auth(config)
    print(f"\n🔐 To authenticate, visit:\n{result['verification_uri']}\n")
    print(f"Enter code: {result['user_code']}\n")
    print("Waiting for authorization...", file=sys.stderr)
    
    token = poll_for_token(config, result)
    if token:
        print("✅ Authentication successful! Token saved.")


def cmd_today(config):
    """Show today's events"""
    token = get_access_token(config)
    now = datetime.now(tz=ZoneInfo("UTC"))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    
    events = get_calendar_events(token, start, end)
    
    if not events:
        print("No events today.")
        return
    
    print(f"📅 Today ({start.strftime('%Y-%m-%d')}):\n")
    for event in events:
        print(format_event(event))


def cmd_upcoming(config, days=7):
    """Show upcoming events"""
    token = get_access_token(config)
    now = datetime.now(tz=ZoneInfo("UTC"))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=days)
    
    events = get_calendar_events(token, start, end, top=50)
    
    if not events:
        print(f"No events in the next {days} days.")
        return
    
    print(f"📅 Next {days} days:\n")
    current_date = None
    for event in events:
        event_date = event.get("start", {}).get("dateTime", "")[:10]
        if event_date != current_date:
            current_date = event_date
            print(f"\n{current_date}:")
        print(format_event(event))


def cmd_tomorrow(config):
    """Show tomorrow's events"""
    token = get_access_token(config)
    now = datetime.now(tz=ZoneInfo("UTC"))
    start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    
    events = get_calendar_events(token, start, end)
    
    if not events:
        print("No events tomorrow.")
        return
    
    print(f"📅 Tomorrow ({start.strftime('%Y-%m-%d')}):\n")
    for event in events:
        print(format_event(event))


def cmd_status(config):
    """Check authentication status"""
    token_data = load_token()
    if not token_data:
        print("❌ Not authenticated. Run: python o365cal.py auth")
        return
    
    if is_token_expired(token_data):
        new_token = refresh_token(config, token_data)
        if new_token:
            print("✅ Token refreshed successfully")
        else:
            print("❌ Token expired. Run: python o365cal.py auth")
            return
    else:
        print("✅ Authenticated")
    
    try:
        token = get_access_token(config)
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{GRAPH_BASE}/me", headers=headers)
        if resp.status_code == 200:
            user = resp.json()
            print(f"   User: {user.get('displayName', 'Unknown')}")
            print(f"   Email: {user.get('mail', user.get('userPrincipalName', 'Unknown'))}")
    except:
        pass


def main():
    if len(sys.argv) < 2:
        print("Usage: o365cal.py <command> [options]")
        print("\nCommands:")
        print("  auth      - Authenticate with Microsoft")
        print("  status    - Check authentication status")
        print("  today     - Show today's events")
        print("  tomorrow  - Show tomorrow's events")
        print("  upcoming  - Show next 7 days (or specify: upcoming 14)")
        sys.exit(1)
    
    config = get_config()
    cmd = sys.argv[1].lower()
    
    if cmd == "auth":
        cmd_auth(config)
    elif cmd == "status":
        cmd_status(config)
    elif cmd == "today":
        cmd_today(config)
    elif cmd == "tomorrow":
        cmd_tomorrow(config)
    elif cmd == "upcoming":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        cmd_upcoming(config, days)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
