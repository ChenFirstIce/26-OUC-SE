import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { HomePage } from "../pages/HomePage";
import { useDemoStore } from "../store/use-demo-store";

describe("HomePage", () => {
  beforeEach(() => {
    localStorage.clear();
    for (const task of ["scd_interview", "moca_open_answer", "boston_naming", "trail_making"] as const) {
      useDemoStore.getState().resetTask(task);
    }
  });

  it("展示四项 C/B 阶段演示任务及对应入口", () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: "SCD 结构化访谈" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "MoCA-B 开放题" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Boston 图片命名" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "STT 形状连线" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /开始评估|开始/ })).toHaveLength(4);
  });
});
