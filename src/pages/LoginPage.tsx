import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { repository } from "../repositories/mockRepository";

export function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    repository.getCurrentPatient();
  }, []);

  return (
    <section className="mx-auto max-w-3xl rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
      <p className="text-sm font-medium text-teal-700">演示登录</p>
      <h2 className="mt-2 text-3xl font-semibold">请选择进入方式</h2>
      <p className="mt-3 text-lg leading-8 text-slate-600">
        第一版不接入真实认证。系统会默认使用“演示患者”完成任务流程。
      </p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => navigate("/home")}
          className="min-h-14 rounded-2xl bg-teal-600 px-5 py-4 text-lg font-medium text-white transition hover:bg-teal-700"
        >
          进入患者端
        </button>
        <button
          type="button"
          onClick={() => navigate("/admin")}
          className="min-h-14 rounded-2xl bg-slate-100 px-5 py-4 text-lg font-medium text-slate-800 transition hover:bg-slate-200"
        >
          进入管理员模式
        </button>
      </div>
    </section>
  );
}
