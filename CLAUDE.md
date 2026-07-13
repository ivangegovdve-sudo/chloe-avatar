# Chloe Avatar

## Purpose
Chloe's persistent visual identity: an animated **randomized dot cloud** (Three.js) embeddable anywhere, driven by fleet state over WebSocket.

## Stack
Vanilla JS + Three.js. Canonical deliverable: `index.html`, built by `build.ps1` from `chloe-avatar-core.js` + template — **edit core/template, never the built HTMLs**. v6 behavioral build: `ChloeAvatar.js` + `demo-v6.html` (three r128 vendored for file:// use); v6 is what Oracle serves at chloe.blumenkraft.cloud/avatar/ (via `index-v6.html` deployed as index.html). v1.1.0 (2026-07-13): per-dot morph personality (seeded offset/duration/easing — formations emerge as a wave), `setExpression(name, intensity)` gesture vocabulary (seam for the soul-server directive channel), postMessage `{expression}` + `{resize}` keys. **Deploy to Oracle pending Ivan** — `D:\output\FABLE_FACE_DEPLOY_RUNBOOK.md`. Deployed: Oracle `chloe-avatar.service` **:8710**, WS bridge `chloe-ws-bridge.service` **:8765** (`ws_bridge.py`, aiohttp, POST /send + ws, **no auth — tailnet/UFW only**). Local dev: `python -m http.server 8471` + `tailscale serve --https=8443` (mic needs HTTPS). Ports: `D:\projects\PORT_REGISTRY.md`.

Global rules: `D:\projects\CODING_PRINCIPLES.md`.

## Non-obvious rules
- **THE DESIGN IS A DOT CLOUD — NOT an orb, face, or geometric shape.** This spec has been lost and re-invented multiple times. Do not redesign it. Ivan explicitly rejected ring anchors, orbital centers, any visible circular structure (v6 murmuration physics replaced them).
- **Recruitment engine, not global animations**: states are per-dot rules; `setState` seeds 3 far-apart dots and engagement spreads by proximity contagion. Guiding principle: "deterministic per-dot rules, organic emergent whole."
- **Two implementations coexist** (open question for Ivan): v6 `ChloeAvatar.js` (richer behavior) vs the fleet/phone build `index.html`/`chloe-avatar-core.js` (window.ChloeAvatar API, ws client, Theatre.js dropped at Ivan's request — Theatre variant kept at `chloe-avatar-theatre.html` only).
- **No Theatre.js in index.html** (standing request). Theatre gotchas if touching the variant: esm.sh puts the API under `.default`; `sequence.play()` anchors to `performance.now()` — custom rafDrivers must tick that clock or one-shots stall at 0.
- Fleet control API: `setState/setEmotion/triggerSymbol/setAmplitude/setIntensity` via ws :8765 or `postMessage({chloe:{...}})`. External callers (wake-word daemon) use `showSymbol()` on the v6 build — method names differ between builds.
- `alert` emotion is **red** (old amber-alert ≈ 'thinking'). `?transparent`, `?dots=N`, `?ws=`, `?nows` URL params.
- Never deploy the avatar on **KVM2:8700** — that's the fleet watchdog (real collision; KVM2 copy lives on :8710).
- ws:// is blocked from https pages (mixed content) — see DEPLOY.md.

## Active issues
- Two-implementation split (v6 vs fleet build) awaiting Ivan's pick for the phone shell embed.
