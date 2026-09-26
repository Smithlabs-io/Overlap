# Overlap knowledge base

Durable context for the community edition: what it is, how data moves, why it's built
this way.

**Read this before forming an opinion about a change.**

| Page | Covers |
|---|---|
| `architecture.md` | Components, runtime shape, storage |
| `data-flow.md` | Schema, routes, event and notification flows |
| `decisions.md` | Why it's built this way |
| `divergences.md` | Known gaps between docs and reality. **Read first.** |

## This repo is generated

Overlap is published from a private upstream by an rsync script. **Direct commits here
are overwritten on the next publish.** Fixes belong upstream; open an issue or PR and it
gets applied there, then republished.

Practical effect for an agent working here: you can read, test and propose, but treat
this tree as a build artifact rather than the source of truth.

## Working protocol

1. **Read before you write.** This index, then the pages for your area.
2. **Update as part of the work.** Architecture, data flow, schema or route changes
   update the relevant page in the same commit.
3. **Record divergences immediately** in `divergences.md`, before continuing.
