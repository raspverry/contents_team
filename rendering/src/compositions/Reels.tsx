import {
  AbsoluteFill,
  interpolate,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { reelsSchema } from "../schemas";
import type { SceneData, ThemeData } from "../schemas";
import type { z } from "zod";

export { reelsSchema };

// ── 씬 컴포넌트 ─────────────────────────────────────────────

const HookScene: React.FC<{ scene: SceneData; theme: ThemeData }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 15], [1.2, 1], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.background,
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          opacity,
          textAlign: "center",
        }}
      >
        <h1
          style={{
            color: theme.text,
            fontSize: 64,
            fontWeight: 900,
            lineHeight: 1.2,
            fontFamily: "Pretendard, sans-serif",
          }}
        >
          {scene.text}
        </h1>
        {scene.subtext && (
          <p
            style={{
              color: theme.accent,
              fontSize: 28,
              marginTop: 24,
              fontFamily: "Pretendard, sans-serif",
            }}
          >
            {scene.subtext}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};

const BodyScene: React.FC<{ scene: SceneData; theme: ThemeData }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const slideIn = interpolate(frame, [0, 15], [60, 0], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.background,
        justifyContent: "center",
        padding: 80,
      }}
    >
      <div style={{ transform: `translateY(${slideIn}px)`, opacity }}>
        <div
          style={{
            width: 60,
            height: 4,
            backgroundColor: theme.accent,
            marginBottom: 32,
          }}
        />
        <p
          style={{
            color: theme.text,
            fontSize: 44,
            fontWeight: 700,
            lineHeight: 1.5,
            fontFamily: "Pretendard, sans-serif",
          }}
        >
          {scene.text}
        </p>
        {scene.subtext && (
          <p
            style={{
              color: `${theme.text}99`,
              fontSize: 26,
              marginTop: 20,
              fontFamily: "Pretendard, sans-serif",
            }}
          >
            {scene.subtext}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};

const CtaScene: React.FC<{
  scene: SceneData;
  theme: ThemeData;
  brandName: string;
}> = ({ scene, theme, brandName }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const buttonScale = interpolate(frame, [20, 35], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.secondary,
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
        opacity,
      }}
    >
      <p
        style={{
          color: "#FFFFFF",
          fontSize: 40,
          fontWeight: 700,
          textAlign: "center",
          lineHeight: 1.5,
          fontFamily: "Pretendard, sans-serif",
        }}
      >
        {scene.text}
      </p>

      <div
        style={{
          marginTop: 48,
          transform: `scale(${buttonScale})`,
          backgroundColor: theme.accent,
          borderRadius: 50,
          padding: "20px 56px",
        }}
      >
        <span
          style={{
            color: "#FFFFFF",
            fontSize: 24,
            fontWeight: 700,
            fontFamily: "Pretendard, sans-serif",
          }}
        >
          {scene.subtext ?? "팔로우"}
        </span>
      </div>

      {brandName && (
        <p
          style={{
            position: "absolute",
            bottom: 80,
            color: theme.primary,
            fontSize: 20,
            fontWeight: 600,
            fontFamily: "Pretendard, sans-serif",
          }}
        >
          {brandName}
        </p>
      )}
    </AbsoluteFill>
  );
};

// ── 씬 라우터 ────────────────────────────────────────────────

const SceneRenderer: React.FC<{
  scene: SceneData;
  theme: ThemeData;
  brandName: string;
}> = ({ scene, theme, brandName }) => {
  switch (scene.type) {
    case "hook":
      return <HookScene scene={scene} theme={theme} />;
    case "cta":
      return <CtaScene scene={scene} theme={theme} brandName={brandName} />;
    default:
      return <BodyScene scene={scene} theme={theme} />;
  }
};

// ── 메인 컴포지션 ────────────────────────────────────────────

export const Reels: React.FC<z.infer<typeof reelsSchema>> = ({
  scenes,
  theme,
  brandName,
}) => {
  const { fps } = useVideoConfig();
  let currentFrame = 0;

  return (
    <AbsoluteFill>
      {scenes.map((scene, i) => {
        const durationFrames = (scene.durationSeconds ?? 5) * fps;
        const from = currentFrame;
        currentFrame += durationFrames;

        return (
          <Sequence key={i} from={from} durationInFrames={durationFrames}>
            <SceneRenderer
              scene={scene}
              theme={theme}
              brandName={brandName}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
