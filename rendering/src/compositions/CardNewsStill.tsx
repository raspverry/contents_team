import { CardRenderer } from "../components/CardSlide";
import { cardNewsStillSchema } from "../schemas";
import type { z } from "zod";

export { cardNewsStillSchema };

export const CardNewsStill: React.FC<
  z.infer<typeof cardNewsStillSchema>
> = ({ card, theme, brandName, brandHandle }) => {
  return (
    <CardRenderer
      card={card}
      theme={theme}
      animated={false}
      brandName={brandName}
      brandHandle={brandHandle}
    />
  );
};
