import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { AssessmentPage } from "./pages/AssessmentPage";
import { AssessmentCompletePage } from "./pages/AssessmentCompletePage";
import { AssessmentIntroPage } from "./pages/AssessmentIntroPage";
import { AdminPage } from "./pages/AdminPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route element={<AppShell />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/assessment/:id/intro" element={<AssessmentIntroPage />} />
        <Route path="/assessment/:id" element={<AssessmentPage />} />
        <Route
          path="/assessment/:id/complete"
          element={<AssessmentCompletePage />}
        />
      </Route>
    </Routes>
  );
}
