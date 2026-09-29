import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { T } from "./theme";

const cover: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover" };

/** Variante de la escena A con la máscara como secuencia PNG en lugar de WebM VP9 con alfa. */
export const SceneBehindPng: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 6, fps, config: { damping: 200 }, durationInFrames: 18 });
  const idx = Math.min(frame, 83).toString().padStart(4, "0");
  return (
    <AbsoluteFill style={{ background: T.black }}>
      <AbsoluteFill style={{ zIndex: 1 }}><OffthreadVideo src={staticFile("speaker_a.mp4")} muted style={cover} /></AbsoluteFill>
      <AbsoluteFill style={{ zIndex: 2, justifyContent: "center", alignItems: "center" }}>
        <div style={{ fontFamily: T.sans, fontWeight: 700, fontSize: 215, color: "#fff", letterSpacing: "-0.045em", whiteSpace: "nowrap", opacity: p, transform: `scale(${1.12 - 0.12 * p})`, textShadow: "0 8px 40px rgba(0,0,0,.35)" }}>
          AUTOMATIZACIÓN
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ zIndex: 3 }}><Img src={staticFile(`alpha/f_${idx}.png`)} style={cover} /></AbsoluteFill>
    </AbsoluteFill>
  );
};
