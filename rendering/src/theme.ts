/**
 * 디자인 테마 프리셋.
 *
 * 카드뉴스/릴스에서 사용하는 색상 팔레트를 중앙 관리합니다.
 * Python rendering_service.py에서 theme 키를 지정하면
 * 여기 정의된 팔레트가 적용됩니다.
 */
import type { ThemeData } from "./schemas";

// ── 기본 테마 (기존 호환) ─────────────────────────────────────

export const DEFAULT_CARDNEWS_THEME: ThemeData = {
  primary: "#D4AF37",
  secondary: "#1A1A2E",
  background: "#FFFFFF",
  text: "#1A1A2E",
  accent: "#4ECDC4",
};

export const DEFAULT_REELS_THEME: ThemeData = {
  primary: "#D4AF37",
  secondary: "#1A1A2E",
  background: "#0F0F1A",
  text: "#FFFFFF",
  accent: "#4ECDC4",
};

// ── 카드뉴스 테마 프리셋 ──────────────────────────────────────

export interface ThemePreset {
  name: string;
  description: string;
  category: "professional" | "casual" | "bold" | "minimal";
  colors: ThemeData;
}

export const THEME_PRESETS: Record<string, ThemePreset> = {
  /** 잇코노미 스타일 — 프리미엄 다크 매거진 */
  "premium-dark": {
    name: "프리미엄 다크",
    description: "다크 그라디언트 배경, 골드 포인트. 잇코노미/뉴스레터 매거진 스타일.",
    category: "professional",
    colors: {
      primary: "#C8A951",
      secondary: "#0A1628",
      background: "#121E33",
      text: "#F0EEE9",
      accent: "#2EC4B6",
    },
  },

  /** 신뢰 블루 — 금융기관/증권사 스타일 */
  "trust-blue": {
    name: "트러스트 블루",
    description: "깔끔한 화이트 배경, 로열 블루 포인트. 은행/증권사 리포트 느낌.",
    category: "professional",
    colors: {
      primary: "#1B4DFF",
      secondary: "#0D1B2A",
      background: "#FFFFFF",
      text: "#1A1A2E",
      accent: "#3B82F6",
    },
  },

  /** 웜 웰스 — Pantone 2025 Mocha Mousse 기반 */
  "warm-wealth": {
    name: "웜 웰스",
    description: "크림/베이지 톤, 모카 포인트. 따뜻하고 친근한 재테크 느낌.",
    category: "casual",
    colors: {
      primary: "#A47864",
      secondary: "#2C1810",
      background: "#FBF8F4",
      text: "#2C1810",
      accent: "#C2703E",
    },
  },

  /** 에메랄드 그로스 — 성장/투자 테마 */
  "emerald-growth": {
    name: "에메랄드 그로스",
    description: "딥 그린 배경, 에메랄드 포인트. 성장·투자·자산 축적 콘텐츠에 적합.",
    category: "bold",
    colors: {
      primary: "#10B981",
      secondary: "#0B1D1A",
      background: "#0F2A24",
      text: "#ECFDF5",
      accent: "#34D399",
    },
  },

  /** 네오 콘트라스트 — MZ세대 타겟 */
  "neo-contrast": {
    name: "네오 콘트라스트",
    description: "블랙 + 일렉트릭 옐로. MZ세대 타겟, 재테크 입문 콘텐츠에 적합.",
    category: "bold",
    colors: {
      primary: "#FFE135",
      secondary: "#1F1F1F",
      background: "#000000",
      text: "#FFFFFF",
      accent: "#FF6B6B",
    },
  },
};

/** 테마 이름으로 ThemeData를 조회. 없으면 기본 카드뉴스 테마 반환. */
export function resolveTheme(themeId?: string): ThemeData {
  if (!themeId) return DEFAULT_CARDNEWS_THEME;
  const preset = THEME_PRESETS[themeId];
  return preset ? preset.colors : DEFAULT_CARDNEWS_THEME;
}
