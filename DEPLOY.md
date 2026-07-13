# Chloe Avatar — Deployment

Two pieces: the **static avatar pages** (this directory) and the
**WebSocket bridge** (`ws_bridge.py`) that lets Chloe's Python backend drive
every open avatar screen.

## Entry points

| URL | What |
|---|---|
| `index.html` | canonical avatar — auto-connects to `ws://<page-host>:8765` |
| `index.html?transparent` | overlay embed (transparent bg, clicks pass through) |
| `index.html?debug` | built-in mini control strip |
| `index.html?ws=host[:port]` / `?nows` | point at another bridge / disable ws |
| `index.html?dots=N` | override particle count (default 300 desktop / 150 mobile) |
| `demo.html` | full control panel: states, emotion swatches, symbols (? ! … ♡), amplitude + intensity sliders, FPS HUD, ws status |
| `demo-v6.html` | the earlier v6 build (`ChloeAvatar.js`) — untouched, kept for comparison |

## Local test (this PC)

```powershell
python D:\projects\chloe-avatar\serve.py            # http://localhost:8471/demo.html
python D:\projects\chloe-avatar\ws_bridge.py --demo # cycles states every 4 s
```

Tailnet test surface (mic-capable, phone-reachable):
`tailscale serve --bg --https=8443 http://localhost:8471` →
`https://desktop-k3j3uqm.tail5837a3.ts.net:8443/demo.html`.
⚠️ Over that **https** URL the browser blocks plain `ws://` (mixed content) —
test the bridge over the plain-http URLs, or serve the bridge as `wss` via a
second `tailscale serve` and pass `?ws=wss://…`.

## KVM2 (187.127.86.176)

Static hosting already exists: `/opt/chloe-avatar/` served read-only by
`chloe-avatar.service` (python3 http.server) on **port 8710**.

> ⚠️ **Never use KVM2 port 8700** — that is hermes-watcher / Fleet Dashboard,
> watchdogged by chloe-health-guardian. The avatar stays on **8710**.

### 1. Redeploy the static files

Re-run the SFTP upload of this directory to `/opt/chloe-avatar/` (same flow
as the original deploy). New files to include: `index.html`, `demo.html`,
`demo-v6.html`, `ws_bridge.py`, `serve.py`.

Phone URLs after deploy:
- avatar: `http://187.127.86.176:8710/index.html`
- control panel: `http://187.127.86.176:8710/demo.html`

### 2. Bridge service (new)

```bash
sudo pip3 install aiohttp   # or: apt install python3-aiohttp
sudo tee /etc/systemd/system/chloe-ws-bridge.service <<'EOF'
[Unit]
Description=Chloe avatar WebSocket bridge
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/chloe-avatar/ws_bridge.py --host 0.0.0.0 --port 8765
Restart=on-failure
RestartSec=3
DynamicUser=yes
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now chloe-ws-bridge
sudo ufw allow 8765/tcp comment 'chloe avatar ws bridge'
curl -s http://localhost:8765/status    # → {"clients": 0}
```

The bridge has **no auth** — it must stay behind UFW/tailnet; do not port-forward
it to the open internet beyond what UFW already allows for the fleet.

### 3. Wire Chloe's backend

One-shot (any language):

```bash
curl -X POST http://localhost:8765/send -H 'Content-Type: application/json' \
     -d '{"state": "thinking"}'
```

Long-lived (Python, preferred for amplitude streaming — reconnects forever,
drops nothing on the floor silently):

```python
import aiohttp, asyncio, json, logging

async def drive_avatar(queue: asyncio.Queue):   # queue of dicts from Chloe's brain
    delay = 1
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.ws_connect("ws://localhost:8765/", heartbeat=30) as ws:
                    delay = 1
                    while True:
                        await ws.send_str(json.dumps(await queue.get()))
        except (aiohttp.ClientError, ConnectionError, asyncio.TimeoutError) as e:
            logging.warning("avatar bridge down (%s), retrying in %ss", e, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)
```

Message keys (combine freely): `state` (idle|listening|thinking|speaking),
`emotion` (neutral|happy|thinking|listening|speaking|alert), `symbol`
(`?` `!` `...` `♡`), `amplitude` 0–1 (send at TTS frame rate), `intensity` 0–1.
v6 build additionally accepts `expression` (`"warmth"` or `{name, intensity}` —
gesture vocabulary: warmth ♡ delight ☺ curiosity ? surprise ! pondering …
affirm ✓ calm attentive energized) and `resize: true` (cross-origin-safe
canvas-sizing kick for embeds).

States recolor themselves (thinking→amber, listening→cyan, speaking→warm
white); an explicit `emotion` sticks until `{"emotion": "neutral"}` (or
`"auto"`) releases it.

Robustness notes: the bridge never crashes on a client disconnect (send
failures just drop that client), pings every 30 s to prune silently-dead
peers (locked phones), and the avatar pages reconnect on their own with
backoff — so bridge restarts are invisible; only messages sent while it was
down are lost, and the next `state` message re-syncs every screen.

### 3b. Tell Chloe about her avatar — SOUL.md snippet

> **Action item (voice-loop integration, 2026-07-06):** this snippet must actually
> live in Chloe's **deployed** SOUL.md at `/opt/chloe/home/SOUL.md` (the Hermes
> gateway on :8642 reads it) — not just here in the docs. That is what lets Chloe
> drive her *own* symbol formations mid-reply, e.g. a `?` when she is uncertain or
> a `♡` on greeting, rather than only reacting to voice-loop state pushes.
>
> Two equivalent ways she can trigger a symbol:
> - **From the backend agent (normal case):** send `{"symbol": "?"}` to the bridge
>   (`POST http://localhost:8765/send`) — the mechanism described below.
> - **From same-page JS (embeds):** the avatar exposes `ChloeAvatar.showSymbol('?')`,
>   `ChloeAvatar.setState(state, {amplitude, emotion})`, `ChloeAvatar.setEmotion(e)`.
>   (The method is `showSymbol`, not `triggerSymbol`.)

Paste this into Chloe's SOUL.md (or system prompt). It is written to her:

```markdown
## Your avatar

You have a visible body: a cloud of ~300 floating dots joined by shifting
proximity lines — a living neural field, deliberately not a face. People
watch it on the fleet dashboard and the phone while they talk to you. It is
how your inner activity *looks*, so keep it honest: match it to what you are
actually doing.

Drive it by sending JSON to your avatar bridge (ws://localhost:8765, or
POST http://localhost:8765/send). Any combination of keys per message:

- `{"state": ...}` — your posture. `"idle"` calm drift (default),
  `"listening"` the cloud tightens and stills while you attend,
  `"thinking"` neurons visibly fire and cascade while you reason,
  `"speaking"` the cloud breathes with your voice. Set state at the moment
  it becomes true, and return to `"idle"` when you finish — a stuck state
  reads as a frozen expression.
- `{"amplitude": 0.0-1.0}` — while speaking, stream your TTS loudness here
  (every 30-50 ms) so your body moves with your voice.
- `{"emotion": ...}` — your color. States color themselves, so you rarely
  need this; use it to *override* mood: `"happy"` gold for delight,
  `"alert"` red only for real errors or urgent warnings, `"neutral"` to
  release an override. Available: neutral, happy, thinking, listening,
  speaking, alert.
- `{"symbol": ...}` — a brief gesture: ~40 dots coalesce into a glyph for
  about 1.5 s, then dissolve. Use sparingly, at genuine moments:
  - `"?"` when you are uncertain or asking the human something
  - `"!"` when excited or surprised by a discovery
  - `"..."` when you need a moment (long tool call, deep processing)
  - `"♡"` when greeting someone you know, or moved to warmth
- `{"intensity": 0.0-1.0}` — overall energy (0.5 is your baseline). Raise
  it when engaged, lower it late at night or when the human wants quiet.

Example — you receive a hard question: send `{"state": "listening"}` while
it arrives, `{"state": "thinking", "symbol": "?"}` if you are unsure you
understood, `{"state": "speaking"}` with streamed amplitude as you answer,
then `{"state": "idle"}`.
```

### 4. Fleet dashboard embed

```html
<iframe src="http://187.127.86.176:8710/index.html?transparent&ws=187.127.86.176"
        style="position:fixed; inset:0; border:0; pointer-events:none; z-index:5"
        title="Chloe"></iframe>
```

`?ws=187.127.86.176` makes the embedded page connect to the KVM2 bridge
regardless of which host serves the dashboard. (Only works from **http**
dashboards — from https use a `wss` front, see the mixed-content note above.)

### 5. Mobile PWA embed (mobile.html / voice loop task)

`?transparent` makes the page fully see-through (html/body transparent,
canvas `pointer-events: none`) — the dot cloud overlays whatever UI sits
under it. The iframe element itself must not paint a background either:

```html
<iframe id="chloe" src="/index.html?transparent"
        style="position:fixed; inset:0; border:0; background:transparent;
               pointer-events:none; z-index:10"
        title="Chloe"></iframe>
```

Serve `mobile.html` from the same origin as the avatar (KVM2 :8710) and the
iframe connects to the bridge on its own — the PWA needs no avatar code.

Three ways for the PWA to drive it, pick per situation:

1. **Do nothing** — Chloe's backend drives every screen via the bridge
   (preferred; keeps all screens in sync).
2. **Same-origin direct** — `chloe.contentWindow.ChloeAvatar.setState('listening')`
   e.g. to flip to `listening` instantly when the mic opens, before the
   backend round-trip.
3. **Cross-origin / origin-agnostic** — postMessage, same schema as the
   bridge:
   ```js
   chloe.contentWindow.postMessage({ chloe: { state: 'listening' } }, '*');
   chloe.contentWindow.postMessage({ chloe: { amplitude: level } }, '*');
   ```

PWA gotchas: keep the iframe out of any CSS-transformed/filtered ancestor
(that breaks `position:fixed` and hurts compositing); when the PWA streams
mic audio, send `amplitude` at most every 30-50 ms (rAF-throttled); the
avatar pauses itself when the tab/app is hidden, so a backgrounded PWA
costs no battery.

## Build system

`index.html` / `chloe-avatar.html` / `chloe-avatar-theatre.html` are **built**
files — edit `chloe-avatar-core.js` or `chloe-avatar.template.html`, then run
`pwsh -File build.ps1`. Deliberate deviation from the original spec: no
Theatre.js in `index.html` (dropped at Ivan's request 2026-07-05; the shim
covers timing) and Three.js 0.166 ESM instead of r128 (the phone build was
verified on 0.166; vendored r128 remains for the v6 build only).
