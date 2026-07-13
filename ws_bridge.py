#!/usr/bin/env python3
"""Chloe avatar WebSocket bridge.

Fans control messages out to every connected avatar page. Two ways in:

  1. WebSocket — connect to ws://<host>:8765/ and send JSON frames.
     Every frame is broadcast to all *other* connected clients, so the
     Python backend can hold one long-lived connection and drive all
     avatar screens at once. Avatar pages connect the same way (they
     only listen).

  2. HTTP POST — one-shot: curl -X POST http://<host>:8765/send \
       -H 'Content-Type: application/json' -d '{"state": "thinking"}'

Message keys (any combination per message):
  {"state": "idle|listening|thinking|speaking"}
  {"emotion": "neutral|happy|thinking|listening|speaking|alert"}
  {"symbol": "?|!|...|♡"}
  {"amplitude": 0.0-1.0}
  {"intensity": 0.0-1.0}

GET /status returns {"clients": n}.

No auth — bind to localhost or a tailnet/UFW-guarded interface only.

Usage:
  python ws_bridge.py [--host 0.0.0.0] [--port 8765] [--demo]
  --demo cycles states/symbols every 4 s (end-to-end smoke test).
"""

import argparse
import asyncio
import itertools
import json
import logging

from aiohttp import WSMsgType, web

log = logging.getLogger("chloe-ws-bridge")

CLIENTS_KEY = web.AppKey("clients", set)


async def broadcast(app, payload, exclude=None):
    # snapshot: clients connect/leave while we await sends
    for ws in list(app[CLIENTS_KEY]):
        if ws is exclude:
            continue
        if ws.closed:
            app[CLIENTS_KEY].discard(ws)
            continue
        try:
            await ws.send_str(payload)
        except Exception as e:  # any send failure = drop that client, never crash
            log.warning("dropping client after send failure: %s", e)
            app[CLIENTS_KEY].discard(ws)


async def ws_handler(request):
    # heartbeat pings prune silently-dead peers (phone lock, wifi drop)
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    request.app[CLIENTS_KEY].add(ws)
    peer = request.remote
    log.info("client connected: %s (%d total)", peer, len(request.app[CLIENTS_KEY]))
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    json.loads(msg.data)  # validate before fan-out
                except ValueError:
                    log.warning("dropping non-JSON frame from %s", peer)
                    continue
                await broadcast(request.app, msg.data, exclude=ws)
            elif msg.type == WSMsgType.ERROR:
                log.warning("ws error from %s: %s", peer, ws.exception())
    finally:
        request.app[CLIENTS_KEY].discard(ws)
        log.info("client left: %s (%d total)", peer, len(request.app[CLIENTS_KEY]))
    return ws


async def send_handler(request):
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "body must be JSON"}, status=400)
    await broadcast(request.app, json.dumps(body))
    return web.json_response({"ok": True, "clients": len(request.app[CLIENTS_KEY])})


async def status_handler(request):
    return web.json_response({"clients": len(request.app[CLIENTS_KEY])})


async def demo_loop(app):
    """Cycle states, emotions and symbols — visual smoke test."""
    script = itertools.cycle([
        {"state": "idle"},
        {"state": "listening"},
        {"state": "thinking"},
        {"symbol": "?"},
        {"state": "speaking", "amplitude": 0.7},
        {"emotion": "happy"},
        {"symbol": "♡"},
        {"state": "idle", "emotion": "neutral", "amplitude": 0.0},
        {"symbol": "..."},
    ])
    try:
        while True:
            step = next(script)
            log.info("demo → %s", step)
            await broadcast(app, json.dumps(step))
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--demo", action="store_true", help="cycle states every 4s")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    app = web.Application()
    app[CLIENTS_KEY] = set()
    app.router.add_get("/", ws_handler)
    app.router.add_get("/ws", ws_handler)
    app.router.add_post("/send", send_handler)
    app.router.add_get("/status", status_handler)

    async def close_clients(app):
        for ws in list(app[CLIENTS_KEY]):
            try:
                await ws.close()
            except Exception:
                pass

    app.on_shutdown.append(close_clients)

    if args.demo:
        async def start_demo(app):
            app["demo_task"] = asyncio.create_task(demo_loop(app))

        async def stop_demo(app):
            app["demo_task"].cancel()

        app.on_startup.append(start_demo)
        app.on_cleanup.append(stop_demo)

    log.info("Chloe ws bridge on ws://%s:%d/ (POST /send, GET /status)", args.host, args.port)
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
