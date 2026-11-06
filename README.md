# Reidyy Ticket System — standalone testing rebuild

This is a new, runnable implementation of the agreed portal requirements, not a recovery of the original Sites source. Python 3.11+ is required; no package installation is needed.

## Run locally

```sh
python server.py
```

Open http://127.0.0.1:8000 and choose a demo role. Management can configure the panel. Data persists in `data.sqlite3`. Stop with Ctrl+C. Back up that database before upgrades.

## Implemented

- Text branding; purple/pink theme; six-action dashboard.
- Tickets, replies, internal notes, claiming, statuses, participants, closed-ticket player lock, 90-day resolved counts.
- Cases, report ID search and multiple selection, Discord ID participants, linked staff-to-player tickets.
- Four editable application forms, minimum answer lengths, attempt/rejection metadata, review decisions, form closures.
- Ban records, appeal eligibility dates enforced on submission, profile notes.
- Configurable branding, categories, forms, groups, permissions, Discord role mappings and DM exclusions.
- Discord OAuth code flow, signed expiring sessions, optional ticket DMs using a bot token.
- Permission checks are performed by the backend. Demo access is only for local testing.

## Important testing limits

- Management editing uses a JSON configuration editor, rather than the original visual editors.
- Rules initially contain a placeholder; paste your approved server rules into the `rules` field.
- The supplied allowlist questions are condensed versions of the 18 requested questions; edit their wording in configuration before public use.
- Application approval and Allowlist role handling require testing against your Discord server. Discord roles refresh at sign-in; a removed role is seen after signing in again.
- Disconnecting signs out the current session. Securely transferring an existing identity to a different Discord account is not implemented. Do not use a new account to transfer bans or bypass appeal restrictions.
- The AI Checker does not produce invented scores; no detection provider is connected.
- User-role badges, group management and notification controls are configured through management; visual member-directory tools and granular per-action permission toggles remain to be implemented.
- Optional FiveM HTTP bridge contract is documented below; an actual FiveM bridge resource is not included. Live kicks/bans cannot operate until you implement/install a compatible bridge.
- Discord DMs are best-effort and synchronous, not a durable retry queue. API failures are recorded in the audit table.
- This is a local test build, not a production deployment. Review the configuration and complete integration tests before exposing it publicly.

## Discord configuration

Export environment variables from `.env.example` (the application does not automatically load `.env` files). Register an OAuth redirect URL of `PUBLIC_URL/auth/callback`. OAuth requests `identify guilds.members.read`; the user must belong to `DISCORD_GUILD_ID`. Set the client ID, client secret, guild ID and optional bot token. In management set role mappings as role-ID arrays, for example `"admin":["123456789012345678"]`, and set `allowlistRole`. Set `dmExcludedRoles` to the Discord role IDs whose members should not receive notifications.

Bot and OAuth secrets must remain environment variables. Never commit them. Use HTTPS and a stable random SESSION_SECRET. Set DEMO_MODE=false before public deployment. When using a proxy, configure host/origin routing correctly. OAuth/DM integrations are supplied but have not been tested with real credentials.

## Optional FiveM bridge contract

`FIVEM_BRIDGE_URL` must accept authenticated JSON POST requests with `Authorization: Bearer FIVEM_BRIDGE_TOKEN` and body `{ "action":"kick|ban", "discordId":"...", "reason":"..." }`. It must verify the token server-side, locate the matching `discord:` identifier, persist bans, enforce them during player connection, execute the requested action, and return JSON. Never expose an unauthenticated game action endpoint. The portal records bans/appeal dates separately; keep live bridge ban state synchronized before use.

## GitHub

Create an empty **private** repository, then run from this directory:

```sh
git init
git add .
git commit -m "Add standalone ticket system test build"
git branch -M main
git remote add origin https://github.com/YOUR-ACCOUNT/reidyy-ticket-system.git
git push -u origin main
```

The assistant can publish after GitHub authorization is available. No credentials are included in this project.
