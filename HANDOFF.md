# Overlap Bot — Handoff Notes

_Last updated: 2026-08-17_

## What was just done

Full restructuring session:
1. Ported all non-regressive changes from Event_py → Overlap (TCP keepalive, vote system, /vote, /info, schema v6, ThreadView notify button, notification button unconditional)
2. Created Overlap-Premium private repo at `../Overlap-Premium/` — full featured with Stripe + vote gates
3. Stripped all Stripe + premium UI from this public repo
4. Added `ALL_FEATURES_ENABLED=true` config flag — all features free by default
5. Set `FREE_TIER_MAX_EVENTS=25` default
6. Added structured JSON logging (`LOG_JSON=true` for Loki/Grafana)
7. Added CLAUDE.md, HANDOFF.md, project memory

## What's next (ordered backlog)

### Immediate / unblocked

- [ ] **Create private GitHub repo** — push Overlap-Premium to `Smithlabs-io/Overlap-Premium` (private). Run: `gh repo create Smithlabs-io/Overlap-Premium --private --source=../Overlap-Premium --remote=origin --push`
- [ ] **Push public changes** — current `main` branch has 2 new commits, push to origin: `git push`
- [ ] **Test the vote system end-to-end** — /vote command, click tracking redirect, "I Voted" button, shame mechanic. The vote gate is wired in Overlap-Premium but ungated in public; verify both behave correctly.

### Observability (Loki/Grafana infra)

- [ ] **Loki + Promtail on OCI** — the bot already emits JSON logs when `LOG_JSON=true`. Need to:
  1. Add Loki + Promtail to `homecloud/docker-compose.yml` (or homecloud Terraform)
  2. Configure Promtail to tail Docker container logs (or stdout from the bot service)
  3. Point Grafana (already running on OCI) at Loki as a new datasource
  4. Build a Grafana dashboard: command usage by name, error rate, guild count, active events
- [ ] **Add `/stats` admin command** (optional, nice-to-have) — ephemeral embed showing guild count, active events total, error count from last 24h

### Features backlog

- [ ] **`/manage event` improvements** — review what's in manage.py; the Manage Event button opens a view but the edit flow may be incomplete
- [ ] **Bulletin timezone display** — bulletin headers show UTC ISO in proposed dates via Discord timestamps; verify they display correctly in all timezones
- [ ] **Event cleanup / archival cron** — archived events should be pruned from DB after N days; currently `archived_at` is set but nothing cleans them up
- [ ] **`/help` command** — basic embed listing all commands with descriptions

### Code review / cleanup (do this session's final step)

- [ ] Full code review: style, layout, simplifications — see user's request to do this after all above is done

## Known debt

- `core/votes.py` docstring mentions "Premium guilds bypass" — technically true (is_premium() returns True for all in public), but confusing; low priority
- `commands/event/recurrence.py` error message says "Premium feature" — dead code path in public (ALL_FEATURES_ENABLED=True means it never fires), but misleading if you read the source
- `scripts/publish-public.sh` — needs a `public-overrides/` directory populated with config files that differ between editions (e.g., stripped version of vote.py with updated footer text). Currently the script syncs everything and relies on git to show what changed
- Overlap-Premium has no CI/CD yet; tests only run manually
- Schema v6 migration adds user_votes table; existing production DB will migrate cleanly on next restart
