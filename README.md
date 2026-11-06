# Reidyy Ticket System

Standalone ticket, case, application and community portal. Python 3.11+; standard library, SQLite, HTML/CSS/JavaScript. This is a rebuild from the original conversation requirements, not recovered Sites source.

## Run or test in GitHub Codespaces

Open **Code → Codespaces → Create codespace on main**. In the terminal:

```sh
HOST=0.0.0.0 python3 server.py
```

Open port 8000 in the Ports tab. **Keep the forwarded port private while demo mode is enabled.** Choose a demo group at sign-in. Management shows all settings. Use a second private browser session for a different demo player. Local Windows: `py server.py`, then http://127.0.0.1:8000. SQLite data persists in `data.sqlite3`.

Pull the newest code before testing. Stop the old process first. Back up the database before upgrading; the first v2 start migrates ticket fields and installs the full default forms/rules. Existing records remain, but the legacy default management configuration is replaced by the v2 defaults. Do not delete your database unless intentionally resetting the test site.

```sh
python -m unittest discover -s tests -v
node --check public/workflows.js
```

## Features

- Reidyy text branding, optional header and staff signature logos, purple/pink customization and responsive hover effects.
- Dashboard actions: Allowlist, Developer, Staff, App Reviewer, custom work and tickets.
- Personal tickets plus staff Open Tickets workspace; claimed/unclaimed/mine/resolved filters and ID/title/player search.
- Ticket statuses, priorities, staff assignment, participant management, private notes, evidence URLs, role badges, staff signatures and read-only resolved tickets.
- Distinct category icons and visual add/edit/remove category/template editors. Existing tickets survive category removal.
- Unique resolved-ticket counts for each staff member over a rolling 90-day period and audit-log viewer.
- Cases with primary/related/duplicate report relationships, ID/title search and multi-select attachments, removals, Discord-ID players and auto-linked staff-to-player outreach.
- Linked-case notice visible to ticket staff; case contents remain permission-restricted.
- Supplied 18 allowlist questions and community rules, including property-robbery guidance; searchable/expandable rules and management editor.
- Application question editor: add/remove, answer types, required flags, minimum lengths and no per-answer maximum. Overall HTTP requests have a 20 MB ceiling.
- Drafts saved per account/form in the browser; live answer character counters.
- Submission timestamp, previous attempts, last rejection reason, complete review decision history.
- Applications open/closed controls, dashboard availability and server-side submission restrictions.
- Approved applications block repeat submission. An allowlist applicant must actually receive and then lose the Allowlist role before reapplying. Discord role changes refresh within 60 seconds; a failed role check fails closed.
- Supplied acceptance/denial response templates. Management adds/edits/removes templates. Reviewers can combine several per answer or final decision, edit the text, save feedback and queue DMs.
- Reviewer DM-service health indicator. This tests Discord REST reachability, not the Discord client's green presence indicator.
- Allowlisted, Non Allowlisted, App Reviewer, Support, Admin and Management groups; custom groups, additive role mappings and granular action permissions.
- Optional Discord OAuth, verified account relinking with stable panel identity, bans and tickets retained across relinks. An already-owned Discord cannot be merged silently.
- Optional bot DMs for ticket responses/participants and application feedback/decisions, exclusion role IDs, persistent queue and bounded retry/backoff.
- Player notes, bans and appeal eligibility dates; backend appeal-date enforcement and live FiveM kick/ban/unban bridge resource included.

## Discord setup

The application **does not load `.env` automatically**. Export variables from `.env.example` in your shell, Codespaces secrets or hosting environment. Set `DEMO_MODE=false` for real operation, a stable random `SESSION_SECRET`, and HTTPS `PUBLIC_URL`. Configure `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_GUILD_ID` and optionally `DISCORD_BOT_TOKEN`.

OAuth redirect: `PUBLIC_URL/auth/callback`. Scopes: `identify guilds.members.read`. Users must belong to the guild. Management → Discord & FiveM maps Discord role IDs to panel groups, sets the Allowlist role, and configures excluded notification roles. Tokens stay in environment variables, never Git or the configuration editor.

Bootstrap management by configuring `BOOTSTRAP_MANAGEMENT_ROLE` to a Discord role ID before first real sign-in (see below). Demo mode permits role selection, so never expose it publicly.

Account → Verify and link a different Discord uses OAuth with the old panel session. Deauth removes Discord and permissions; keep that session open to link another Discord. Management assistance is needed if both the old session and Discord account are lost. New accounts cannot claim an existing linked profile without verification. Platform-wide duplicate-person detection is not possible: genuinely separate Discord identities cannot be identified as the same human automatically.

## FiveM resource

1. Copy `fivem/reidyy_bridge` to the FiveM resources folder.
2. In `server.cfg`, set a strong secret with `set reidyy_bridge_token "..."`, then `ensure reidyy_bridge`.
3. Set `FIVEM_BRIDGE_URL=http://YOUR_PRIVATE_SERVER:30120/reidyy_bridge/` and matching `FIVEM_BRIDGE_TOKEN` on the panel. Use private networking or an authenticated HTTPS reverse proxy.
4. Kick/ban by Discord ID from Players & bans. The bridge uses the server's `discord:` identifier. Players must have a Discord identifier for matching and reconnect ban enforcement.
5. Bridge bans persist in the resource's local `bans.json`; retain that file across resource upgrades. Panel-created live bans carry appeal dates. Revoking a live ban calls the bridge unban action before clearing the panel record. Locally recorded bans do not themselves ban a player in FiveM.

## Optional AI provider

No score is fabricated. Without `AI_CHECK_URL`, the checker reports “Not scored”. An optional trusted adapter can accept `POST {"text":"answer"}` with `Authorization: Bearer AI_CHECK_TOKEN` and return `{"score":0..100}`. The UI marks a provider score **above 65** in red, with a warning that it is an estimate and requires human review. There is no automatic rejection or ban. Provider access and external text processing must be configured intentionally.

## Known verification limits

Backend workflows have automated tests. Real Discord OAuth, role changes, DM delivery and account relinking need testing with your guild and credentials. The FiveM resource needs in-server verification; no game server was available during implementation. Browser behavior has syntax/runtime smoke checks, not a complete browser end-to-end suite. The original hosted Site is not modified by this repository.

For production, use HTTPS, a managed reverse proxy and backups. This standard-library HTTP server is intended for controlled testing and small deployments, not an independently security-audited production service. Secrets, member data, local bans and the database are excluded from Git.
