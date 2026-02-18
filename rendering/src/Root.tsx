import { Composition, Still } from "remotion";
import { CardNews, cardNewsSchema } from "./compositions/CardNews";
import { CardNewsStill, cardNewsStillSchema } from "./compositions/CardNewsStill";
import { Reels, reelsSchema } from "./compositions/Reels";
import { DEFAULT_CARDNEWS_THEME, DEFAULT_REELS_THEME } from "./theme";

export const Root: React.FC = () => {
  return (
    <>
      {/* 카드뉴스 슬라이드 영상 (각 카드 3초, 전환 포함) */}
      <Composition
        id="CardNews"
        component={CardNews}
        schema={cardNewsSchema}
        defaultProps={{
          cards: [],
          theme: DEFAULT_CARDNEWS_THEME,
          brandName: "",
          brandHandle: "",
        }}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1350}
      />

      {/* 카드뉴스 정지 이미지 (개별 카드 PNG) */}
      <Still
        id="CardNewsStill"
        component={CardNewsStill}
        schema={cardNewsStillSchema}
        defaultProps={{
          card: { page: 1, frame: "cover", blocks: [] },
          theme: DEFAULT_CARDNEWS_THEME,
          brandName: "",
          brandHandle: "",
        }}
        width={1080}
        height={1350}
      />

      {/* 릴스 영상 (20~30초) */}
      <Composition
        id="Reels"
        component={Reels}
        schema={reelsSchema}
        defaultProps={{
          scenes: [],
          theme: DEFAULT_REELS_THEME,
          brandName: "",
          brandHandle: "",
        }}
        durationInFrames={750}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
