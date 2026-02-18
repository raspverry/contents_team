/**
 * 카드뉴스 슬라이드 공용 컴포넌트.
 *
 * CardNews(영상)와 CardNewsStill(정지)에서 동일하게 사용합니다.
 * animated=true → 프레임 기반 인터폴레이션 적용
 * animated=false → 최종 상태로 즉시 렌더링
 */
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { CardData, ThemeData } from "../schemas";

interface CardProps {
  card: CardData;
  theme: ThemeData;
  animated?: boolean;
  brandName?: string;
  brandHandle?: string;
}

// ── 표지 카드 ─────────────────────────────────────────────────

export const CoverCard: React.FC<CardProps> = ({
  card,
  theme,
  animated = true,
  brandName = "",
}) => {
  const frame = useCurrentFrame();
  const opacity = animated
    ? interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" })
    : 1;
  const titleY = animated
    ? interpolate(frame, [0, 20], [40, 0], { extrapolateRight: "clamp" })
    : 0;

  const title = card.blocks[0]?.data?.title ?? "";
  const subtitle = card.blocks[0]?.data?.subtitle ?? "";
  const brand = card.blocks[0]?.data?.brand || brandName;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.secondary,
        justifyContent: "center",
        alignItems: "center",
        padding: 60,
        opacity,
      }}
    >
      {/* 상단 악센트 바 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 6,
          background: `linear-gradient(90deg, ${theme.accent}, ${theme.primary})`,
        }}
      />

      <div
        style={{
          transform: `translateY(${titleY}px)`,
          textAlign: "center",
        }}
      >
        <h1
          style={{
            color: "#FFFFFF",
            fontSize: 52,
            fontWeight: 800,
            lineHeight: 1.3,
            margin: 0,
            fontFamily: "Pretendard, sans-serif",
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              color: "#B0B0B0",
              fontSize: 24,
              marginTop: 24,
              fontFamily: "Pretendard, sans-serif",
            }}
          >
            {subtitle}
          </p>
        )}
      </div>

      <p
        style={{
          position: "absolute",
          bottom: 60,
          color: theme.primary,
          fontSize: 18,
          fontFamily: "Pretendard, sans-serif",
          fontWeight: 600,
        }}
      >
        {brand}
      </p>
    </AbsoluteFill>
  );
};

// ── 본문 카드 ─────────────────────────────────────────────────

export const BodyCard: React.FC<CardProps> = ({
  card,
  theme,
  animated = true,
}) => {
  const frame = useCurrentFrame();
  const opacity = animated
    ? interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" })
    : 1;

  const title = card.blocks[0]?.data?.title ?? "";
  const body = card.blocks[0]?.data?.body ?? "";
  const highlight = card.blocks.find((b) => b.type === "highlight-box");

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.background,
        padding: 60,
        opacity,
      }}
    >
      <h2
        style={{
          color: theme.text,
          fontSize: 40,
          fontWeight: 700,
          marginBottom: 32,
          fontFamily: "Pretendard, sans-serif",
          borderLeft: `4px solid ${theme.accent}`,
          paddingLeft: 20,
        }}
      >
        {title}
      </h2>

      <p
        style={{
          color: theme.text,
          fontSize: 26,
          lineHeight: 1.7,
          fontFamily: "Pretendard, sans-serif",
        }}
      >
        {body}
      </p>

      {highlight && (
        <div
          style={{
            marginTop: 40,
            backgroundColor: `${theme.accent}15`,
            border: `1px solid ${theme.accent}40`,
            borderRadius: 12,
            padding: "20px 24px",
          }}
        >
          <span
            style={{
              color: theme.accent,
              fontSize: 16,
              fontWeight: 700,
              fontFamily: "Pretendard, sans-serif",
            }}
          >
            {highlight.data.label ?? "TIP"}
          </span>
          <p
            style={{
              color: theme.text,
              fontSize: 22,
              marginTop: 8,
              fontFamily: "Pretendard, sans-serif",
            }}
          >
            {highlight.data.text ?? ""}
          </p>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ── CTA 카드 ──────────────────────────────────────────────────

export const CtaCard: React.FC<CardProps> = ({
  card,
  theme,
  animated = true,
  brandName = "",
  brandHandle = "",
}) => {
  const frame = useCurrentFrame();
  const scale = animated
    ? interpolate(frame, [0, 20], [0.9, 1], { extrapolateRight: "clamp" })
    : 1;

  const cta =
    card.blocks[0]?.data?.text ?? "팔로우하고 더 많은 재테크 팁 받기";
  const handle = brandHandle || card.blocks[0]?.data?.handle || "";
  const brand = brandName || card.blocks[0]?.data?.brand || "";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.secondary,
        justifyContent: "center",
        alignItems: "center",
        padding: 60,
      }}
    >
      <div style={{ transform: `scale(${scale})`, textAlign: "center" }}>
        <p
          style={{
            color: "#FFFFFF",
            fontSize: 36,
            fontWeight: 700,
            lineHeight: 1.5,
            fontFamily: "Pretendard, sans-serif",
          }}
        >
          {cta}
        </p>

        {handle && (
          <div
            style={{
              marginTop: 48,
              backgroundColor: theme.accent,
              borderRadius: 50,
              padding: "16px 48px",
              display: "inline-block",
            }}
          >
            <span
              style={{
                color: "#FFFFFF",
                fontSize: 22,
                fontWeight: 700,
                fontFamily: "Pretendard, sans-serif",
              }}
            >
              {handle} 팔로우
            </span>
          </div>
        )}
      </div>

      {brand && (
        <p
          style={{
            position: "absolute",
            bottom: 60,
            color: theme.primary,
            fontSize: 18,
            fontFamily: "Pretendard, sans-serif",
          }}
        >
          {brand}
        </p>
      )}
    </AbsoluteFill>
  );
};

// ── 카드 라우터 ──────────────────────────────────────────────

export const CardRenderer: React.FC<CardProps> = (props) => {
  switch (props.card.frame) {
    case "cover":
      return <CoverCard {...props} />;
    case "cta":
      return <CtaCard {...props} />;
    default:
      return <BodyCard {...props} />;
  }
};
