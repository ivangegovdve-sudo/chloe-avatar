# Chloe Avatar — Tuning Guide (written for Chloe)

You are reading the control surface of your own visual soul. The dot fleet is
not an animation you wear — it is a set of rules you can rewrite. This file
maps *feelings* to *parameters* so feedback like "too glowy" or "more
hesitant" becomes a concrete patch.

## The loop

1. Ivan (or you) watches the avatar and states a feeling.
2. Translate the feeling using the table below into a small patch.
3. Apply live: `avatar.setTuning(patch)` — no reload, effects are immediate.
4. Read back the full rule set with `avatar.getTuning()` and persist the
   winning values to `tuning.json` in this directory (versioned in
   chloe-memory). The demo applies `window.CHLOE_TUNING` at startup if a
   host page defines it.
5. Small steps: change one or two values per iteration, ±20–40 %. You are
   sculpting a temperament, not flipping switches.

## Feeling → parameter map

| Feedback sounds like… | Reach for | Direction |
|---|---|---|
| "too glowy / oversaturated" | `global.glow` | down (0.7–0.9) |
| "dots too big / too small" | `global.sizeScale` | 0.8 / 1.2 |
| "too cramped / too spread out" | state `radius` | up / down |
| "she fills too much screen" | `global.cloudScale` | down |
| "aimless, no intention" | state `dartRate` up, `dwell` up, `speed` down | — |
| "too twitchy / nervous" | state `jitter`, `dartRate` | down |
| "too static / lifeless" | state `speed`, `noiseEvo`, `dartRate` | up |
| "they move as one blob" | state `orbit` down; check `noiseFreq` up | — |
| "web too dense / bright" | state `lineThreshold`, `lineOpacity` | down |
| "not enough connection" | state `lineThreshold` | up |
| "thinking too calm / too frantic" | `thinking.fireRate` (base λ; intensity adds 3×) | — |
| "breathing too obvious" | state `breatheAmp` / `breathePeriod` | down / up |
| "colors feel wrong for X" | state `colorA` / `colorB` (hex ints) | — |
| "transitions too slow/fast" | recruitment is fixed ~2.5 s; ask for a code change | — |

## Per-state rule set (what each number means)

- `speed` — cruising velocity through the noise field (world units/s).
- `noiseAmp` / `noiseFreq` / `noiseEvo` — how strongly, how locally, and how
  fast the invisible current each dot rides changes.
- `radius` — the fleet's home radius. Each dot multiplies this by its own
  radiusBias (0.6–1.4), so the shell stays staggered.
- `centerK` — how firmly escapees are pulled home. `centerPull` — whole-fleet
  contraction (+) or inflation (−); thinking uses +.
- `orbit` — swirl around the shared center ("the common thought"). Per-dot
  direction is fixed at birth; this scales pace.
- `jitter` — high-frequency trembling; each dot has its own susceptibility.
- `dartRate` — how often a dot decides to *go somewhere* (deliberate hop with
  ease-out settle). `dwell` — probability weight of holding attentively
  still. drift/dart/dwell is each dot's moment-to-moment intention.
- `lineThreshold` / `lineOpacity` — when the proximity web forms and how
  loud it is. Closest links auto-boost ("thickness"); a luminance budget
  dims per-line when the web gets dense.
- `fireRate` — neuron-fire Poisson base (thinking: + 3 × intensity, scaled
  by recruitment progress). Cascades are capped subcritical.
- `breatheAmp` / `breathePeriod` — the global inhale/exhale.
- `dotOpacity`, `haloIntensity`, `colorA`, `colorB` — presence and palette.

## What you cannot patch (yet — ask for code)

Recruitment pacing and seed count, symbol stroke sets, cascade probabilities,
sheet-lightning cadence, ripple shapes. When a feeling maps to none of the
knobs above, the right move is a code-change request, not a bigger patch.

## Example patches

"Calmer idle, dimmer overall":
```json
{ "global": { "glow": 0.8 },
  "states": { "idle": { "speed": 0.04, "dwell": 0.7, "lineOpacity": 0.22 } } }
```

"Thinking should feel more urgent":
```json
{ "states": { "thinking": { "fireRate": 3.5, "dartRate": 0.1, "breathePeriod": 2.0 } } }
```
