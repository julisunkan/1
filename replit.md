# DevTools Suite

## Overview

A mobile-styled Flask web application housing 5 independent developer tools, unified under a central admin panel. Each tool runs as a Flask Blueprint in its own directory and shares a single SQLite database.

## User Preferences

Preferred communication style: Simple, everyday language.

## Routes

| Route | Tool |
|-------|------|
| `/` | Home — app launcher grid |
| `/rename` | Cloud-Based File Renamer |
| `/programcheat` | Programming Cheatsheet Generator (Groq AI) |
| `/ndagen` | NDA Generator with e-sign (Groq AI) |
| `/reslayout` | Responsive Layout Tester |
| `/webscreen` | Web Page Screenshot Tool (Playwright) |
| `/admin` | Central Admin Panel |

## Architecture

- **Framework**: Flask with Blueprint-based modular structure
- **Database**: SQLite via Flask-SQLAlchemy (`data.db`)
- **AI**: Groq API (llama3-8b-8192) for cheatsheet and NDA generation
- **Screenshots**: Playwright headless Chromium
- **UI**: Custom mobile-first CSS — 430px max-width phone shell with status bar, bottom nav, dark theme

## App Structure

```
apps/
  admin/       Admin panel (login, dashboard, settings)
  rename/      ZIP upload + batch file renaming rules
  programcheat/ AI cheatsheet generation + print
  ndagen/      AI NDA generation + digital signature pads
  reslayout/   URL preview at different device sizes
  webscreen/   Playwright screenshot capture + gallery
templates/     Jinja2 templates per blueprint
static/css/    mobile.css — full phone-shell UI system
```

## Admin Panel

- URL: `/admin`  
- Default password: `admin123` (change in Settings)
- Manages: Groq API key, admin password, app name, theme
- Shows usage stats for all 5 tools
