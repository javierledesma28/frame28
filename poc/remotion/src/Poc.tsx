import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BARS, T } from "./theme";
import words from "../public/words_c.json";

export const FPS = 30;
const SCENE_A = 84; // 2.8 s  texto detrás del hablante
const SCENE_B = 180; // 6.0 s  bar chart que se construye
const SCENE_C = 138; // 4.6 s  tipografía cinética sincronizada con la voz
export const POC_DURATION_FRAMES = SCENE_A + SCENE_B + SCENE_C;

const cover: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover" };

/** Esquinas de encuadre: la firma gráfica del video de referencia. */
const Corners: React.FC<{ color?: string; size?: number; inset?: number }> = ({
  color = "#fff",
  size = 22,
  inset = -6,
}) => {
  const b = `3px solid ${color}`;
  const c = (s: React.CSSProperties) => (
    <div style={{ position: "absolute", width: size, height: size, ...s }} />
  );
  return (
    <>
      {c({ top: inset, left: inset, borderTop: b, borderLeft: b })}
      {c({ top: inset, right: inset, borderTop: b, borderRight: b })}
      {c({ bottom: inset, left: inset, borderBottom: b, borderLeft: b })}
      {c({ bottom: inset, right: inset, borderBottom: b, borderRight: b })}
    </>
  );
};

// ---------- Escena A: texto detrás del hablante ----------
const SceneBehind: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 6, fps, config: { damping: 200 }, durationInFrames: 18 });
  return (
    <AbsoluteFill style={{ background: T.black }}>
      <AbsoluteFill style={{ zIndex: 1 }}><OffthreadVideo src={staticFile("speaker_a.mp4")} muted style={cover} /></AbsoluteFill>
      <AbsoluteFill style={{ zIndex: 2, justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            fontFamily: T.sans,
            fontWeight: 700,
            fontSize: 215,
            color: "#fff",
            letterSpacing: "-0.045em",
            whiteSpace: "nowrap",
            opacity: p,
            transform: `scale(${1.12 - 0.12 * p})`,
            textShadow: "0 8px 40px rgba(0,0,0,.35)",
          }}
        >
          AUTOMATIZACIÓN
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ zIndex: 3 }}><OffthreadVideo src={staticFile("speaker_a_alpha.webm")} transparent muted style={cover} /></AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- Escena B: bar chart que se construye ----------
const SceneBars: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const max = 13;
  const titleO = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const heroP = spring({ frame: frame - 120, fps, config: { damping: 200 }, durationInFrames: 12 });
  return (
    <AbsoluteFill style={{ background: T.pink, padding: "90px 140px", fontFamily: T.sans }}>
      <div style={{ color: "#1a1a1a", fontSize: 56, fontWeight: 600, letterSpacing: "-0.03em", opacity: titleO }}>
        Tasa de error en salida estructurada
      </div>
      <div style={{ color: "#3a2530", fontFamily: T.mono, fontSize: 24, marginTop: 8, opacity: titleO }}>
        % de respuestas que rompen el esquema · menor es mejor
      </div>
      <div style={{ marginTop: 48, position: "relative" }}>
        {BARS.map((b, i) => {
          const grow = spring({ frame: frame - 12 - i * 4, fps, config: { damping: 30, stiffness: 120 }, durationInFrames: 20 });
          const w = Math.max(6, (b.value / max) * 1000) * grow;
          const rowO = interpolate(frame, [10 + i * 4, 16 + i * 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={b.model} style={{ display: "flex", alignItems: "center", height: 74, opacity: rowO, position: "relative", isolation: b.hero ? "isolate" : undefined }}>
              <div style={{ width: 200, fontFamily: T.mono, fontSize: 24 }}>
                {b.group ? (
                  <span style={{ background: "#1a1a1a", color: T.pink, padding: "2px 8px" }}>{b.group}</span>
                ) : null}
              </div>
              <div style={{ width: 300, fontFamily: T.mono, fontSize: 26, color: "#1a1a1a", textAlign: "right", paddingRight: 28 }}>
                {b.model}
              </div>
              <div style={{ position: "relative", height: 34, width: 1000 }}>
                <div style={{ position: "absolute", left: 0, top: 0, height: 34, width: w, background: b.hero ? "#1a1a1a" : "rgba(26,26,26,.55)" }} />
                <div style={{ position: "absolute", left: w + 16, top: 0, lineHeight: "34px", fontFamily: T.mono, fontSize: 26, color: "#1a1a1a", opacity: grow }}>
                  {b.value.toFixed(2)}%
                </div>
              </div>
              {b.hero ? (
                <div
                  style={{
                    position: "absolute",
                    left: -24,
                    right: -24,
                    top: 4,
                    bottom: 4,
                    background: T.offWhite,
                    opacity: heroP,
                    transform: `scale(${1.04 - 0.04 * heroP})`,
                    zIndex: -1,
                  }}
                >
                  <Corners color="#1a1a1a" />
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------- Escena C: tipografía cinética sincronizada con la voz ----------
type Word = { text: string; startMs: number; endMs: number };
const SceneKinetic: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = (frame / fps) * 1000;
  return (
    <AbsoluteFill style={{ background: T.black, justifyContent: "center", alignItems: "center" }}>
      <Audio src={staticFile("voice_c.wav")} />
      <div
        style={{
          width: 1500,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 34px",
          fontFamily: T.sans,
          fontWeight: 500,
          fontSize: 124,
          letterSpacing: "-0.04em",
          lineHeight: 1.05,
          color: "#fff",
        }}
      >
        {(words as Word[]).map((w, i) => {
          const o = interpolate(t, [w.startMs, w.startMs + 140], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const y = interpolate(o, [0, 1], [28, 0]);
          const pink = /not/.test(w.text);
          return (
            <span key={i} style={{ display: "inline-block", opacity: o, transform: `translateY(${y}px)`, color: pink ? T.pink : "#fff", marginLeft: w.text.startsWith("-") ? -34 : 0 }}>
              {w.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Poc: React.FC = () => (
  <AbsoluteFill style={{ background: T.black }}>
    <Sequence from={0} durationInFrames={SCENE_A}>
      <SceneBehind />
    </Sequence>
    <Sequence from={SCENE_A} durationInFrames={SCENE_B}>
      <SceneBars />
    </Sequence>
    <Sequence from={SCENE_A + SCENE_B} durationInFrames={SCENE_C}>
      <SceneKinetic />
    </Sequence>
  </AbsoluteFill>
);
