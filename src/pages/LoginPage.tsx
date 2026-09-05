import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { repository } from "../repositories/apiRepository";

export function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    void repository.getCurrentPatient();
  }, []);

  return (
    <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <div className="rounded-[32px] border border-[var(--line)] bg-[var(--panel)] p-6 shadow-[0_12px_40px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
        <p className="text-sm font-medium text-[var(--brand)]">演示登录</p>
        <h2 className="mt-3 max-w-2xl text-4xl font-semibold tracking-tight text-slate-900">
          从患者入口开始，完成一条完整的认知评估闭环
        </h2>
        <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
          这一版不接入真实认证，默认使用演示患者。设计方向参考了患者 intake 模板，强调大字号、低信息密度和明确的下一步。
        </p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => navigate("/home")}
            className="rounded-[28px] bg-[var(--brand)] px-6 py-6 text-left text-white shadow-[0_20px_45px_rgba(15,118,110,0.24)] transition hover:bg-[var(--brand-dark)]"
          >
            <div className="text-sm font-medium text-teal-100">Patient Flow</div>
            <div className="mt-2 text-2xl font-semibold">进入患者端</div>
            <div className="mt-3 text-sm leading-6 text-teal-50/90">
              查看待办任务、继续答题、完成提交。
            </div>
          </button>
          <button
            type="button"
            onClick={() => navigate("/admin")}
            className="rounded-[28px] border border-[var(--line)] bg-white px-6 py-6 text-left text-slate-900 transition hover:border-slate-300 hover:bg-slate-50"
          >
            <div className="text-sm font-medium text-[var(--gold)]">Admin / Test Mode</div>
            <div className="mt-2 text-2xl font-semibold">进入管理员模式</div>
            <div className="mt-3 text-sm leading-6 text-slate-600">
              派发演示量表，检查提交流程和结构化数据。
            </div>
          </button>
        </div>
      </div>

      <div className="rounded-[32px] border border-[var(--line)] bg-white/80 p-6 shadow-[0_12px_40px_rgba(15,23,42,0.04)] sm:p-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">
          Current Flow
        </p>
        <ol className="mt-5 grid gap-4 text-base text-slate-700">
          <li className="rounded-2xl bg-slate-50 px-4 py-4">
            1. 管理员派发 `SCD-Q9`、`GDS-15`、`ESS`、`爱丁堡利手量表`
          </li>
          <li className="rounded-2xl bg-slate-50 px-4 py-4">2. 患者进入任务中心并开始作答</li>
          <li className="rounded-2xl bg-slate-50 px-4 py-4">3. 系统自动保存草稿与提交记录</li>
          <li className="rounded-2xl bg-slate-50 px-4 py-4">4. 完成页展示初步分数与 submission JSON</li>
        </ol>
      </div>
    </section>
  );
}
