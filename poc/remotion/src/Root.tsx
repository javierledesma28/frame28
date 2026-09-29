import { Composition } from "remotion";
import { Poc, POC_DURATION_FRAMES, FPS } from "./Poc";
import { SceneBehindPng } from "./PocPng";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="poc" component={Poc} durationInFrames={POC_DURATION_FRAMES} fps={FPS} width={1920} height={1080} />
    <Composition id="behind-png" component={SceneBehindPng} durationInFrames={84} fps={FPS} width={1920} height={1080} />
  </>
);
