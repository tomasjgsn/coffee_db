---
name: run-app
description: Starts THE COUNTER's local dev server and opens it in the real default browser at http://localhost:5173. Use this whenever the user asks to run, start, launch, preview, boot up, or open THE COUNTER (or "the coffee app") locally, or wants to see it in their browser — even phrased casually ("can you get the app running", "let's look at this in the browser", "fire up the dev server") rather than as an exact slash command. This is the canonical way to launch this project locally; prefer it over guessing a run command or starting a raw dev server directly.
---

# Run THE COUNTER locally

All the actual logic — checking whether the server's already up, safely clearing a stale process from port 5173, starting Vite, waiting for it to respond, and opening the browser — lives in one checked-in script: `app/scripts/dev-up.sh`, exposed as `npm run dev:up`. This skill is intentionally just a thin wrapper around that script. Don't reimplement any of its logic here — no separate port-checking, no killing processes yourself, no calling `open` directly. The script is exercised the same way whether a person runs it from Terminal, double-clicks `start-counter.command` at the repo root, or you invoke it here; keeping one source of truth means a fix to the script fixes every entry point at once.

## What to do

Run from the repo root:

```bash
cd app && npm run dev:up
```

Then relay exactly what it reports, in your own words:

- **Success** ("Up at http://localhost:5173" or "already running"): tell the user the server's up and their browser should have opened to `http://localhost:5173`.
- **Refusal** (it reports port 5173 is held by something that isn't THE COUNTER, and shows the offending PID/command): relay that plainly. Don't try to work around it yourself — don't kill that process, don't pick a different port. The script deliberately refuses here because it can't safely tell whether that process is safe to touch, and neither can you without the user's input. Tell them what's on the port and let them decide.
- **Timeout** (server didn't come up within its wait window): mention the log file it points to (`/tmp/the-counter-dev.log`) so a follow-up debugging pass has somewhere to look.

That's the whole skill — starting and opening. Verifying that a specific feature actually works once it's open is a different job (the existing `run`/`verify` skills cover that).
