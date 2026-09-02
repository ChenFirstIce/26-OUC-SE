import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/login", label: "入口" },
  { to: "/home", label: "我的任务" },
  { to: "/admin", label: "管理员" },
];

export function AppShell() {
  return (
    <div className="min-h-screen bg-transparent text-slate-800">
      <div className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-4 py-5 sm:px-6">
        <header className="mb-5 rounded-[24px] bg-white/90 px-5 py-4 shadow-sm ring-1 ring-slate-200">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-teal-700">阿尔茨海默病评估系统</p>
              <h1 className="text-2xl font-semibold tracking-tight">患者端最小可运行版本</h1>
            </div>
            <nav className="flex flex-wrap gap-2">
              {links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    `min-h-12 rounded-full px-4 py-3 text-base font-medium transition ${
                      isActive
                        ? "bg-teal-600 text-white"
                        : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                    }`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </header>
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
