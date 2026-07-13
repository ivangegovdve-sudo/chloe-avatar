# Chloe Avatar — Theatre.js build (2026-07-05)

Phone-screen avatar for the Galaxy A26: organic dot cloud + proximity lines
(synaptic look), Three.js rendering, Theatre.js keyframe loops & transitions.

> **Coexistence note:** this build lives alongside the earlier v6 build
> (`ChloeAvatar.js` + `demo-v6.html`, hand-rolled parameter blending, no
> Theatre.js). Nothing from v6 was modified. The two are independent;
> decide later which one Chloe's phone shell embeds.
>
> **2026-07-06 fleet build:** this core now also emits `index.html`
> (canonical embed: `window.ChloeAvatar` control surface + ws://:8765
> listener + 6 fleet emotions + `setIntensity` + multi-char symbols) and
> `demo.html` is its control panel. See `DEPLOY.md`.

## Files

| File | What |
|---|---|
| `chloe-avatar.html` | **Deliverable 1** — standalone, pure Three.js (single CDN import: three@0.166 via jsDelivr). **No Theatre.js at all** — timing runs on the core's built-in rAF oscillators and cubic-ease state crossfades. Open directly in a browser. |
| `chloe-avatar-theatre.html` | Same core with @theatre/core@0.7 (esm.sh) driving ambient keyframe loops + transition easing; falls back to the built-in shim if the CDN is unreachable. Fully verified this session. |
| `ChloeAvatar.tsx` | **Deliverable 2** — React component (`three` + `@theatre/core` from npm). Declarative props + imperative ref handle. |
| `chloe-avatar-core.js` | Shared engine (single source of truth). The HTML inlines it; the TSX imports it. |
| `chloe-avatar.template.html` | HTML template; `build.ps1` injects the core into it → `chloe-avatar.html`. **Edit the template/core, never the built HTML.** |
| `build.ps1` | `pwsh -File build.ps1` after any core/template change. |

## JS API (Deliverable 3 — same on both)

```js
avatar.setState('idle' | 'thinking' | 'speaking' | 'listening', { amplitude?, emotion? })
avatar.setAmplitude(a)      // 0..1, call at audio rate (speaking pulses to it)
avatar.setEmotion('calm' | 'curious' | 'alert' | 'warm')
avatar.showSymbol('?')      // any glyph; dots coalesce, hold ~1.2s, dissolve
avatar.getState() / avatar.getEmotion()
avatar.dispose()
```

HTML: `window.avatar`. Debug panel: open with `?debug` (state/emotion/symbol
buttons, amplitude slider, fake-speech oscillator).

React:

```tsx
const ref = useRef<ChloeAvatarHandle>(null);
<ChloeAvatar ref={ref} state="listening" emotion="curious" />
ref.current?.setAmplitude(level);   // no re-render
ref.current?.showSymbol('!');
```

## States / emotions

- **idle** — slow drift, gentle line pulse (Theatre "Ambient" breath loop)
- **thinking** — neuron firing: sparks travel along connections, flash dots on
  arrival, chain-propagate up to 2 hops; dots cluster toward 3 roaming
  centers and scatter
- **speaking** — dot size / spread / line opacity / spark rate track amplitude
- **listening** — cloud tightens to 0.72×, motion nearly stops, longer stable lines
- Emotions recolor dots/lines/sparks: calm indigo, curious cyan, alert amber,
  warm rose. Palette crossfades smoothly.

## Theatre.js integration (and the clock gotcha)

Hand-authored project state (`definitionVersion 0.4.0`) with two sheets:
**Ambient** (breath + shimmer keyframe loops, plays `iterationCount: Infinity`)
and **Transition** (eased 0→1 progress over 0.8s; each `setState` replays it
and crossfades state-parameter weights via `onValuesChange`).

⚠️ **Theatre anchors `sequence.play()` to `performance.now()`.** We drive it
with a custom `createRafDriver` ticked from the avatar's own render loop —
tick timestamps MUST be `performance.now()`-comparable. Ticking with a
synthetic small clock silently stalls one-shot sequences at position 0 (and
infinite loops wrap negative elapsed time, which *looks* alive but isn't
advancing properly).

## Performance (Galaxy A26 target)

200 dots, O(n²) proximity pass (~20k pairs), preallocated line buffer +
`setDrawRange` (technique from three.js example `webgl_buffergeometry_drawrange`,
MIT). Additive-blend point shader, DPR capped at 1.75, no postprocessing.
Desktop measured ~0.9 ms/frame sim+render. Adaptive quality drops particle
count (200→150→110) if sustained frame time exceeds 20 ms. Pauses on
`visibilitychange`; `prefers-reduced-motion` freezes motion (breath-only).

## Test hooks

`avatar.debugStep(dt)` advances the sim without rAF (works in hidden tabs);
`avatar.getDebugInfo()` returns blended params/weights/oscillators. Used by
the headless verification harness; harmless in production.
