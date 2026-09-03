import { Route, Routes } from "react-router-dom";
import { PageShell } from "./components/PageShell";
import { HomePage } from "./pages/HomePage";
import { ScdInterviewPage } from "./pages/ScdInterviewPage";
import { MocaOpenAnswerPage } from "./pages/MocaOpenAnswerPage";
import { BostonNamingPage } from "./pages/BostonNamingPage";
import { TrailMakingPage } from "./pages/TrailMakingPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  return (
    <PageShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/demo/scd-interview" element={<ScdInterviewPage />} />
        <Route path="/demo/moca-open-answer" element={<MocaOpenAnswerPage />} />
        <Route path="/demo/boston-naming" element={<BostonNamingPage />} />
        <Route path="/demo/trail-making" element={<TrailMakingPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </PageShell>
  );
}
