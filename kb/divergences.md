# Divergences

Gaps between docs and reality. **Add entries the moment you find one**, before
continuing. Recording is not fixing.

Format: date found · what docs say · what's true · status

---

### 2026-09-27 · `project_state.md` / `HANDOFF.md` — corrected
The previous entry here (2026-09-26) claimed these files were gitignored. They are not:
`git ls-files` shows `HANDOFF.md` tracked, and `.gitignore` has no entry for either name.
`CLAUDE.md` calls them "live working notes" that are "not committed," which has never been
true for `HANDOFF.md`. Either add both to `.gitignore` and stop tracking `HANDOFF.md`, or
fix `CLAUDE.md` to describe what actually happens.
**Status:** open — needs a decision, not just a doc fix

### 2026-09-27 · The Docker image is unverified
No Docker daemon was available while building the Dockerfile, docker-compose.yml and
publish-image.yml in OVERLAP-21 — `docker build` was never run. What was checked instead:
both dbmate release assets the image downloads resolve (HTTP 200), and copying exactly
the files the Dockerfile copies into a clean virtualenv and running its exact
`pip install ".[bot,web]"` succeeds and produces a working import of `overlap`, `fastapi`
and `discord.py` with the packaged reference data readable. That's evidence the image
*would* build, not proof it does — someone with Docker needs to actually build and run it
once before relying on it.
**Status:** open — needs a real `docker build` + `docker compose up`

### 2026-09-27 · Resolved: SQLite docs, upstream direction, stale env names
Three entries closed by the OVERLAP-14 epic (package rename, Postgres port, KB rewrite):
the KB no longer describes SQLite or a single-process runtime; this repo is now
documented as the upstream (not "generated" from a private repo via rsync); and
`.env.example` names `MAX_ACTIVE_EVENTS`, not the old `FREE_TIER_MAX_EVENTS`.
