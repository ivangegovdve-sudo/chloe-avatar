# Chloe Avatar

Chloe's living presence: a cloud of 50–120 dots drifting through an evolving 3D
simplex-noise field, joined by an ever-shifting web of proximity lines. Not an
orb, not a face — **the dot cloud is the design**.

Pure JS + Three.js (WebGL). No React, no build step. Embeds anywhere: iframe,
web component host, plain `<div>`.

## Quick start

Open **`demo-v6.html`** — it works straight from disk (double-click), no
server needed. Keyboard: `1–5` states, `Q C E X` symbols, `Space` transmit
pulse, `S` simulated speech.

> **2026-07-06:** `demo.html` is now the control panel for the fleet build
> (`index.html`, built from `chloe-avatar-core.js` — see `DEPLOY.md`). This
> v6 build is unchanged; its demo simply moved to `demo-v6.html`.

## Embedding

```html
<script src="vendor/three.min.js"></script>
<script src="shaders/chloe-shaders.js"></script>
<script src="ChloeAvatar.js"></script>
<script>
  const avatar = new ChloeAvatar(document.getElementById('my-canvas'), {
    quality: 'high',
  });
</script>
```

The first argument is either a `<canvas>` (used directly, sized by its CSS box)
or any container element (a canvas is created inside it, filling it). The
renderer follows the container via `ResizeObserver` — never hardcode a size.

CommonJS also works (`three` resolved from node_modules):

```js
const ChloeAvatar = require('./ChloeAvatar.js');
```

## API

```js
const avatar = new ChloeAvatar(canvasOrContainer, {
  quality: 'high',   // 'high' 120 dots · 'medium' 80 · 'low' 50 (auto: low on mobile)
  cloudScale: 0.35,  // on-screen footprint (fraction of full-canvas scale);
                     // 0.35 = compact companion presence; use ~0.55 on phones
  seed: 12345,       // optional — deterministic dot layout & fire sequence
});

avatar.setState('thinking', { intensity: 0.7 });  // idle | thinking | excited | wandering | transmitting
avatar.setThinkingIntensity(0.9);  // 0–1, scales neuron-fire rate (λ = 2 + 3·intensity /s)
avatar.showSymbol('?');            // '?' | 'check' | 'ellipsis' | '!'  (aliases: '✓' '…')
avatar.hideSymbol();               // early release of a sustained symbol
avatar.pulse('transmit');          // one-shot green wave without changing state
avatar.setAudioLevel(0.8);         // 0–1, real-time — feed TTS amplitude; drives excitement
avatar.setQuality('medium');
avatar.getState();                 // current state name
avatar.getStats();                 // { fps, dots, lines, state }
avatar.destroy();                  // full teardown (RAF, observers, GPU buffers)
```

## States

| State | Behavior | Palette |
|---|---|---|
| `idle` | Slow noise drift, 4 s breathing (±5 % scale), soft proximity web | `#6B8CAE` → `#4A6FA5` |
| `thinking` | Cloud contracts to ~60 %, stochastic **neuron fire** — Poisson arrivals with cascade avalanches; coincident fires (< 100 ms, in range) flash the connecting line white | `#3D52A0` + white flashes |
| `excited` | Speed ×2.5, noise ×2, cloud expands, denser lines | `#E8A045` → `#F4C842` |
| `wandering` | 30 % speed; after ~1 s the cloud drifts into a sustained `?` | `#5C8A8A` |
| `transmitting` | Green wave radiates from center over ~1.2 s, dots brighten, then auto-returns to the previous state (1.5 s total) | `#4CAF50` |

All parameter and color changes **blend** between states (exponential smoothing,
color slower than motion) — nothing snaps.

`setAudioLevel()` continuously blends the live parameters toward the excited
profile, so Chloe visibly energizes while speaking regardless of state.

## Symbol formation

Target positions are precomputed point clouds (`?` ≈ 25 pts, `✓` 15, `…` 15,
`!` 15). Each slot is greedily paired with its nearest free dot; a spring ramps
up over 0.5 s pulling assigned dots to their slots while unassigned dots are
gently repelled to clear the stage — and recede in brightness so the glyph
reads. One-shot symbols hold ~1.8 s after forming, then release with a small
dissolve impulse. `wandering`'s `?` is sustained until the state changes.

**No two formations are identical**: each `showSymbol` applies a random tilt
(±7.5°), scale (±11 %), and per-point jaggedness (strongest on `?`), and while
held every slot target breathes with its own noise offset — the glyph is
handwritten and alive, never typeset OCR.

## Dot individuality

Every dot has its own noise-field region (no chained flocking), preferred
orbit radius, swirl direction and pace around the shared center, jitter
temperament, lightness, and a slow personal drift along the state's color
axis. State parameters `orbit` and `jitter` scale these per state; all motion
and breathing phases are integrated (not derived from absolute time), so
state transitions never snap.

## Neuron fire (thinking)

- Global Poisson process, λ = 2 + 3 × `intensity` fires/sec — never periodic.
- Each fire: dot ramps to white/electric blue over 50 ms, decays over ~220 ms.
- Cascades: a fire excites in-range neighbors with decaying probability
  (30 % → 16 % → 9 %, max depth 3) — quiet stretches punctuated by avalanches.
- Two fires within 100 ms whose dots are within line range flash the line
  (150 ms fade).

## Performance

- Desktop target 60 fps, mobile 30 fps (auto-detected; mobile defaults to
  `low` = 50 dots and a 1.5× pixel-ratio cap).
- Frame-rate independent: all motion integrates with clamped delta time.
- Adaptive: FPS is EMA-tracked; sustained shortfall sheds dots (floor 40) and
  drops proximity-line updates to alternate frames; headroom restores them.
- Single draw call each for dots (`THREE.Points`), lines
  (`THREE.LineSegments`, preallocated buffer + `drawRange`) and halo.
- Honors `prefers-reduced-motion`: speeds ×0.25, fire flashes softened.

## Files

```
chloe-avatar/
├── ChloeAvatar.js            main class — simulation, state machine, rendering
├── shaders/chloe-shaders.js  GLSL: dots (soft gaussian, fire/pulse channels),
│                             lines (per-vertex alpha + fire), ambient halo
├── vendor/three.min.js       Three.js r128 UMD (vendored so demo.html runs offline via file://)
├── demo-v6.html              interactive showcase (this build)
└── README.md
```

## Design notes

- **Why no Theatre.js**: the spec's core need — timed easing and state
  blending — is met by a purpose-built exponential parameter blender
  (~30 lines). Theatre.js is an authored-timeline tool; procedural state
  blending is outside its sweet spot, and its runtime would break the
  zero-network `file://` demo requirement. If authored cinematic sequences
  are wanted later, drive `setState`/`showSymbol` from a Theatre.js sheet —
  the API is deliberately timeline-friendly.
- **Why a vendored r128 UMD build**: browsers block ES modules on `file://`,
  and newer Three.js ships ESM-only. Everything used (Points, LineSegments,
  ShaderMaterial) is version-stable; swap in any modern Three.js via bundler
  if embedding in an app.
- Randomness is a seeded mulberry32 PRNG — identical seed ⇒ identical run,
  which makes visual bugs reproducible.
