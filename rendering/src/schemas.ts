/**
 * 공유 Zod 스키마.
 *
 * CardNews, CardNewsStill, Reels 등 모든 컴포지션에서 공통으로 사용하는
 * 블록/카드/테마 스키마를 한 곳에서 정의합니다.
 */
import { z } from "zod";

// ── 카드뉴스 블록/카드 ──────────────────────────────────────

export const blockSchema = z.object({
  type: z.string(),
  data: z.record(z.string(), z.string()),
});

export const cardSchema = z.object({
  page: z.number(),
  frame: z.string(),
  blocks: z.array(blockSchema),
});

// ── 테마 ────────────────────────────────────────────────────

export const themeSchema = z.object({
  primary: z.string(),
  secondary: z.string(),
  background: z.string(),
  text: z.string(),
  accent: z.string(),
});

// ── 릴스 씬 ─────────────────────────────────────────────────

export const sceneSchema = z.object({
  type: z.enum(["hook", "body", "cta"]),
  text: z.string(),
  subtext: z.string().optional(),
  durationSeconds: z.number().default(5),
});

// ── 컴포지션 최상위 스키마 ────────────────────────────────────

export const cardNewsSchema = z.object({
  cards: z.array(cardSchema),
  theme: themeSchema,
  brandName: z.string().default(""),
  brandHandle: z.string().default(""),
});

export const cardNewsStillSchema = z.object({
  card: cardSchema,
  theme: themeSchema,
  brandName: z.string().default(""),
  brandHandle: z.string().default(""),
});

export const reelsSchema = z.object({
  scenes: z.array(sceneSchema),
  theme: themeSchema,
  brandName: z.string().default(""),
  brandHandle: z.string().default(""),
});

// ── 타입 ────────────────────────────────────────────────────

export type BlockData = z.infer<typeof blockSchema>;
export type CardData = z.infer<typeof cardSchema>;
export type ThemeData = z.infer<typeof themeSchema>;
export type SceneData = z.infer<typeof sceneSchema>;
