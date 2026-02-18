import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { CardRenderer } from "../components/CardSlide";
import { cardNewsSchema } from "../schemas";
import type { z } from "zod";

export { cardNewsSchema };

const FRAMES_PER_CARD = 90; // 3초 @ 30fps

export const CardNews: React.FC<z.infer<typeof cardNewsSchema>> = ({
  cards,
  theme,
  brandName,
  brandHandle,
}) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      {cards.map((card, i) => (
        <Sequence
          key={card.page}
          from={i * FRAMES_PER_CARD}
          durationInFrames={FRAMES_PER_CARD}
        >
          <CardRenderer
            card={card}
            theme={theme}
            animated
            brandName={brandName}
            brandHandle={brandHandle}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
