import type { AssessmentQuestion, AnswerValue } from "../types/assessment";

interface Props {
  question: AssessmentQuestion;
  value: AnswerValue;
  onChange: (value: AnswerValue) => void;
}

function YesNoQuestion({
  value,
  onChange,
}: {
  value: AnswerValue;
  onChange: (value: AnswerValue) => void;
}) {
  const options = [
    { label: "是", value: true },
    { label: "否", value: false },
  ];

  return (
    <div className="grid gap-3">
      {options.map((option) => {
        const selected = value === option.value;
        return (
          <button
            key={option.label}
            type="button"
            onClick={() => onChange(option.value)}
            className={`min-h-16 rounded-[24px] border px-5 py-5 text-left text-lg font-medium transition ${
              selected
                ? "border-[var(--brand)] bg-[var(--brand)] text-white shadow-[0_16px_35px_rgba(15,118,110,0.18)]"
                : "border-slate-200 bg-slate-50 text-slate-800 hover:border-teal-300 hover:bg-white"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

function SingleChoiceQuestion({
  question,
  value,
  onChange,
}: {
  question: AssessmentQuestion;
  value: AnswerValue;
  onChange: (value: AnswerValue) => void;
}) {
  return (
    <div className="grid gap-3">
      {question.options?.map((option) => {
        const selected = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`min-h-16 rounded-[24px] border px-5 py-5 text-left text-lg font-medium transition ${
              selected
                ? "border-[var(--brand)] bg-[var(--brand)] text-white shadow-[0_16px_35px_rgba(15,118,110,0.18)]"
                : "border-slate-200 bg-slate-50 text-slate-800 hover:border-teal-300 hover:bg-white"
            }`}
          >
            <div className="font-medium">{option.label}</div>
            {option.description ? (
              <div className={`mt-2 text-sm leading-6 ${selected ? "text-teal-50" : "text-slate-500"}`}>
                {option.description}
              </div>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

export function QuestionRenderer({ question, value, onChange }: Props) {
  switch (question.type) {
    case "boolean":
      return <YesNoQuestion value={value} onChange={onChange} />;
    case "single-choice":
      return (
        <SingleChoiceQuestion question={question} value={value} onChange={onChange} />
      );
    default:
      return (
        <div className="rounded-2xl bg-amber-50 p-4 text-base text-amber-800">
          当前题型尚未实现。
        </div>
      );
  }
}
