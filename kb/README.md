# Overlap knowledge base

Durable context for Overlap: what it is, how data moves, why it's built this way.

**Read this before forming an opinion about a change.**

| Page | Covers |
|---|---|
| `architecture.md` | Components, processes, storage, the plugin seam |
| `data-flow.md` | Schema, routes, event and notification flows |
| `decisions.md` | Why it's built this way |
| `divergences.md` | Known gaps between docs and reality. **Read first.** |

## This repo is the upstream

Overlap is the source of truth for the community edition. A private overlay package adds
hosted-only features on top of it through the plugin hook (see `architecture.md`); the
overlay depends on this repo, never the other way round. Nothing private belongs here.

The database schema ships in this repo (`overlap/db/migrations`), versioned with the code.

## Working protocol

1. **Read before you write.** This index, then the pages for your area.
2. **Update as part of the work.** Architecture, data flow, schema or route changes
   update the relevant page in the same commit.
3. **Record divergences immediately** in `divergences.md`, before continuing.
