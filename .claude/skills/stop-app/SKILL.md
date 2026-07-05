---
name: stop-app
description: Stops THE COUNTER's local dev server, freeing port 5173. Use this whenever the user asks to stop, shut down, kill, or quit the dev server / THE COUNTER / "the coffee app" running locally — even phrased casually ("kill that server", "shut it down", "I'm done for now, close it up") rather than as an exact slash command. This is the canonical way to stop this project's dev server; prefer it over guessing a kill command or manually finding the process yourself.
---

# Stop THE COUNTER's dev server

The actual logic — finding whatever's listening on port 5173, confirming it's really THE COUNTER's Vite process before touching it, and freeing the port — lives in one checked-in script: `app/scripts/dev-down.sh`, exposed as `npm run dev:down`. This skill is a thin wrapper around it; don't reimplement the port-finding or killing here. The same script backs `npm run dev:down` from Terminal and the `stop-counter.command` double-click launcher at the repo root, so there's one place this logic lives and gets fixed.

## What to do

Run from the repo root:

```bash
cd app && npm run dev:down
```

Then relay exactly what it reports:

- **Stopped** ("Port 5173 is free"): confirm the server's down.
- **Already stopped** ("Nothing running on port 5173 — already stopped"): this is a normal, expected outcome, not an error — say so plainly, don't treat it as a failure.
- **Refusal** (port 5173 is held by something that isn't THE COUNTER, PID/command shown): relay that plainly and don't try to kill it yourself — the script can't safely confirm it's ours, and neither can you without the user weighing in.
