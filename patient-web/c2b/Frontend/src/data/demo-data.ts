import type { TrailNode } from "../types";

export interface BostonQuestion {
  id: string;
  title: string;
  image: string;
  imageAlt: string;
  expectedAnswer: string;
  hint: string;
}

const makeDemoImage = (emoji: string, label: string) =>
  `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400"><rect width="640" height="400" rx="28" fill="#ecfdf5"/><circle cx="320" cy="175" r="115" fill="#ccfbf1"/><text x="320" y="210" text-anchor="middle" font-size="112">${emoji}</text><text x="320" y="350" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#64748b">${label}</text></svg>`)}`;

export const bostonQuestions: BostonQuestion[] = [
  { id: "demo_boston_01", title: "这是什么物品？", image: makeDemoImage("☂️", "DEMO IMAGE"), imageAlt: "演示用雨伞图标", expectedAnswer: "雨伞", hint: "下雨时常用的物品" },
  { id: "demo_boston_02", title: "这是什么交通工具？", image: makeDemoImage("🚲", "DEMO IMAGE"), imageAlt: "演示用自行车图标", expectedAnswer: "自行车", hint: "通常有两个轮子" },
  { id: "demo_boston_03", title: "这是什么水果？", image: makeDemoImage("🍎", "DEMO IMAGE"), imageAlt: "演示用苹果图标", expectedAnswer: "苹果", hint: "一种常见的红色水果" },
];

export const trailNodes: TrailNode[] = [
  { id: "1", label: "1", x: 14, y: 20 },
  { id: "A", label: "A", x: 77, y: 17 },
  { id: "2", label: "2", x: 32, y: 43 },
  { id: "B", label: "B", x: 82, y: 54 },
  { id: "3", label: "3", x: 18, y: 75 },
  { id: "C", label: "C", x: 68, y: 83 },
];

export const trailSequence = ["1", "A", "2", "B", "3", "C"];

export const scdInitialMessage = "这是一个演示访谈。最近您是否感觉自己的记忆或思考能力与以前相比发生了变化？";
export const mocaDemoQuestion = "DEMO 开放题：请用一句话说明“火车”和“自行车”有什么共同之处。";
