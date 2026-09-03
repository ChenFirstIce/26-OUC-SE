import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/login", label: "入口" },
  { to: "/home", label: "我的任务" },
  { to: "/history", label: "历史记录" },
  { to: "/admin", label: "管理员" },
];

export function AppShell() {
  return (
    <div className="min-h-screen text-slate-800">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-4 sm:px-6 lg:px-8">
        <div className="grid flex-1 gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="rounded-[30px] border border-white/70 bg-[var(--navy)] p-5 text-white shadow-[0_20px_60px_rgba(18,48,71,0.18)]">
            <div className="rounded-[24px] border border-white/10 bg-white/6 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-teal-100/80">
                Cognitive Care
              </p>
              <h1 className="mt-3 text-2xl font-semibold tracking-tight">
                智忆患者评估端
              </h1>
              <p className="mt-3 text-sm leading-6 text-slate-200">
                参考 `shadcn-admin` 的管理外壳和 `awell-intake` 的患者流程分区，保留当前项目的评估主线。
              </p>
            </div>

            <nav className="mt-5 grid gap-2">
              {links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    `flex min-h-14 items-center rounded-2xl px-4 py-3 text-base font-medium transition ${
                      isActive
                        ? "bg-white text-[var(--navy)] shadow-sm"
                        : "text-slate-100 hover:bg-white/8"
                    }`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </nav>

            <div className="mt-6 rounded-[24px] border border-white/10 bg-white/8 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-100/80">
                Demo Scope
              </p>
              <ul className="mt-3 grid gap-2 text-sm leading-6 text-slate-200">
                <li>配置驱动问卷渲染</li>
                <li>本地草稿自动保存</li>
                <li>管理员测试派发</li>
              </ul>
            </div>
          </aside>

          <div className="flex min-h-full flex-col gap-4">
            <header className="rounded-[30px] border border-[var(--line)] bg-[var(--panel)] px-5 py-5 shadow-[0_12px_40px_rgba(15,23,42,0.06)] backdrop-blur">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-medium text-[var(--brand)]">认知健康评估</p>
                  <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">
                    面向患者的结构化评估流程
                  </h2>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-600">
                  <span className="rounded-full bg-[var(--brand-soft)] px-3 py-2 font-medium text-[var(--brand-dark)]">
                    MVP
                  </span>
                  <span className="rounded-full border border-[var(--line)] bg-white/80 px-3 py-2">
                    React + Vite
                  </span>
                </div>
              </div>
            </header>

            <main className="flex-1">
              <Outlet />
            </main>
          </div>
        </div>
      </div>
    </div>
  );
}
