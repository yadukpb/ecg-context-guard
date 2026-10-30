import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { Sidebar } from "./components/Sidebar";
import { Login } from "./pages/Login";
import { ProjectOverview } from "./pages/ProjectOverview";
import { PatientList } from "./pages/PatientList";
import { PatientDashboard } from "./pages/PatientDashboard";
import { Alerts } from "./pages/Alerts";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-page text-ink-muted">Loading…</div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppShell({ children }) {
  return (
    <div className="flex min-h-screen bg-page">
      <Sidebar />
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <AppShell>
              <Routes>
                <Route path="/" element={<ProjectOverview />} />
                <Route path="/patients" element={<PatientList />} />
                <Route path="/patients/:id" element={<PatientDashboard />} />
                <Route path="/alerts" element={<Alerts />} />
              </Routes>
            </AppShell>
          </RequireAuth>
        }
      />
    </Routes>
  );
}
