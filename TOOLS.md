# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## Installed Skills

### Weather
- No API key needed
- Uses wttr.in (primary) and Open-Meteo (fallback)

### Flight Tracker
- OpenSky Network: No API key needed for basic tracking
- AviationStack: Optional API key for flight schedules (100 req/month free)
  - Set `AVIATIONSTACK_API_KEY` env var if needed

### ClawHub
- Skill marketplace for OpenClaw
- Run `clawhub login` if you need to publish skills

### O365 Calendar (if configured)
- Azure AD app for calendar access
- Run `python scripts/o365cal.py auth` to authenticate
- Tokens auto-refresh after initial setup

## What Else Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

---

Add whatever helps you do your job. This is your cheat sheet.
