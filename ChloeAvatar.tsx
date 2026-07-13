/**
 * ChloeAvatar — React wrapper around the dot-cloud avatar core.
 *
 * Deps: `three`, `@theatre/core` (npm). Rendering/animation logic lives in
 * ./chloe-avatar-core.js (shared with the standalone chloe-avatar.html).
 *
 * Declarative use:
 *   <ChloeAvatar state="speaking" emotion="curious" amplitude={level} />
 *
 * Imperative use (audio-rate amplitude, symbols):
 *   const ref = useRef<ChloeAvatarHandle>(null);
 *   ref.current?.setState('thinking', { emotion: 'curious' });
 *   ref.current?.setAmplitude(0.8);   // call at audio rate, no re-render
 *   ref.current?.showSymbol('?');
 */
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  type CSSProperties,
} from 'react';
import * as theatre from '@theatre/core';
import { createChloeAvatar } from './chloe-avatar-core.js';

export type AvatarState = 'idle' | 'thinking' | 'speaking' | 'listening';
export type AvatarEmotion = 'calm' | 'curious' | 'alert' | 'warm';

export interface ChloeAvatarHandle {
  setState(state: AvatarState, opts?: { amplitude?: number; emotion?: AvatarEmotion }): void;
  setAmplitude(a: number): void;
  setEmotion(e: AvatarEmotion): void;
  showSymbol(char: string): void;
  getState(): AvatarState;
  getEmotion(): AvatarEmotion;
}

export interface ChloeAvatarProps {
  state?: AvatarState;
  emotion?: AvatarEmotion;
  /** 0..1 — for audio-rate updates prefer ref.setAmplitude() over this prop */
  amplitude?: number;
  particleCount?: number;
  className?: string;
  style?: CSSProperties;
}

// Theatre.js keys projects by name; keep one project across React remounts
// (StrictMode double-mount, HMR) by reusing a single name — same name + same
// state config is a no-op on the second call.
const THEATRE_PROJECT = 'ChloeAvatar';

export const ChloeAvatar = forwardRef<ChloeAvatarHandle, ChloeAvatarProps>(
  function ChloeAvatar({ state, emotion, amplitude, particleCount, className, style }, ref) {
    const containerRef = useRef<HTMLDivElement>(null);
    const avatarRef = useRef<ReturnType<typeof createChloeAvatar> | null>(null);

    useEffect(() => {
      if (!containerRef.current) return;
      const avatar = createChloeAvatar(containerRef.current, {
        theatre,
        projectName: THEATRE_PROJECT,
        state,
        emotion,
        particleCount,
      });
      avatarRef.current = avatar;
      return () => {
        avatarRef.current = null;
        avatar.dispose();
      };
      // mount-only: state/emotion/amplitude changes flow through the effects below
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [particleCount]);

    useEffect(() => {
      if (state) avatarRef.current?.setState(state);
    }, [state]);

    useEffect(() => {
      if (emotion) avatarRef.current?.setEmotion(emotion);
    }, [emotion]);

    useEffect(() => {
      if (amplitude !== undefined) avatarRef.current?.setAmplitude(amplitude);
    }, [amplitude]);

    useImperativeHandle(ref, () => ({
      setState: (s, o) => avatarRef.current?.setState(s, o),
      setAmplitude: (a) => avatarRef.current?.setAmplitude(a),
      setEmotion: (e) => avatarRef.current?.setEmotion(e),
      showSymbol: (c) => avatarRef.current?.showSymbol(c),
      getState: () => (avatarRef.current?.getState() ?? 'idle') as AvatarState,
      getEmotion: () => (avatarRef.current?.getEmotion() ?? 'calm') as AvatarEmotion,
    }));

    return (
      <div
        ref={containerRef}
        className={className}
        style={{ width: '100%', height: '100%', background: '#05060f', ...style }}
      />
    );
  },
);

export default ChloeAvatar;
