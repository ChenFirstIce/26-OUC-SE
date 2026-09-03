import { ArrowLeft, BrainCircuit, Home } from "lucide-react";
import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

export function PageShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const isHome = location.pathname === "/";
  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="header-inner">
          <Link to="/" className="brand" aria-label="返回演示首页">
            <span className="brand-icon"><BrainCircuit size={23} /></span>
            <span><strong>认知评估</strong><small>患者端功能演示</small></span>
          </Link>
          {!isHome && <Link to="/" className="home-link"><Home size={18} /> 功能首页</Link>}
        </div>
      </header>
      <main className="page-container">
        {!isHome && <Link to="/" className="back-link"><ArrowLeft size={18} /> 返回功能列表</Link>}
        {children}
      </main>
      <footer>课程项目演示 · 请勿录入真实个人信息</footer>
    </div>
  );
}
