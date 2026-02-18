import { AbsoluteFill } from "remotion";
import { z } from "zod";

// ── 스키마 ──────────────────────────────────────────────────

const blockSchema = z.object({
  type: z.string(),
  data: z.record(z.string(), z.string()),
});

const cardSchema = z.object({
  page: z.number(),
  frame: z.string(),
  blocks: z.array(blockSchema),
});

const themeSchema = z.object({
  primary: z.string(),
  secondary: z.string(),
  background: z.string(),
  text: z.string(),
  accent: z.string(),
});

export const cardNewsStillSchema = z.object({
  card: cardSchema,
  theme: themeSchema,
});

type CardData = z.infer<typeof cardSchema>;
type ThemeData = z.infer<typeof themeSchema>;

// ── 정지 이미지용 카드 렌더러 ──────────────────────────────

const CoverStill: React.FC<{ card: CardData; theme: ThemeData }> = ({
  card,
  theme,
}) => {
  const title = card.blocks[0]?.data?.title ?? "";
  const subtitle = card.blocks[0]?.data?.subtitle ?? "";
  const brand = card.blocks[0]?.data?.brand ?? "재테크는 스크루지";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.secondary,
        justifyContent: "center",
        alignItems: "center",
        padding: 60,
      }}
    >
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
      <div style={{ textAlign: "center" }}>
        <h1
          style={{
            color: "#FFFFFF",
            fontSize: 52,
            fontWeight: 800,
            lineHeight: 1.3,
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
          fontWeight: 600,
          fontFamily: "Pretendard, sans-serif",
        }}
      >
        {brand}
      </p>
    </AbsoluteFill>
  );
};

const BodyStill: React.FC<{ card: CardData; theme: ThemeData }> = ({
  card,
  theme,
}) => {
  const title = card.blocks[0]?.data?.title ?? "";
  const body = card.blocks[0]?.data?.body ?? "";
  const highlight = card.blocks.find((b) => b.type === "highlight-box");

  return (
    <AbsoluteFill
      style={{ backgroundColor: theme.background, padding: 60 }}
    >
      <h2
        style={{
          color: theme.text,
          fontSize: 40,
          fontWeight: 700,
          marginBottom: 32,
          borderLeft: `4px solid ${theme.accent}`,
          paddingLeft: 20,
          fontFamily: "Pretendard, sans-serif",
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

const CtaStill: React.FC<{ card: CardData; theme: ThemeData }> = ({
  card,
  theme,
}) => {
  const cta = card.blocks[0]?.data?.text ?? "팔로우하고 더 많은 재테크 팁 받기";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.secondary,
        justifyContent: "center",
        alignItems: "center",
        padding: 60,
      }}
    >
      <p
        style={{
          color: "#FFFFFF",
          fontSize: 36,
          fontWeight: 700,
          lineHeight: 1.5,
          textAlign: "center",
          fontFamily: "Pretendard, sans-serif",
        }}
      >
        {cta}
      </p>
      <div
        style={{
          marginTop: 48,
          backgroundColor: theme.accent,
          borderRadius: 50,
          padding: "16px 48px",
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
          @재테크는스크루지 팔로우
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ── 정지 이미지 컴포지션 ───────────────────────────────────

export const CardNewsStill: React.FC<
  z.infer<typeof cardNewsStillSchema>
> = ({ card, theme }) => {
  switch (card.frame) {
    case "cover":
      return <CoverStill card={card} theme={theme} />;
    case "cta":
      return <CtaStill card={card} theme={theme} />;
    default:
      return <BodyStill card={card} theme={theme} />;
  }
};
