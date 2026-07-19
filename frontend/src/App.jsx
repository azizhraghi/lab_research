import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Veille from "./pages/Veille";
import Bibliometrie from "./pages/Bibliometrie";
import DigitalTwin from "./pages/DigitalTwin";
import Login from "./pages/Login";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import "./index.css";

function RequireAuth({ children }) {
  const { configured, loading, session } = useAuth();

  if (loading) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center text-sm text-muted-foreground">
        Restoring session...
      </main>
    );
  }

  if (!configured || !session) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
}

function LoginRoute() {
  const { loading, session } = useAuth();

  if (loading) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center text-sm text-muted-foreground">
        Restoring session...
      </main>
    );
  }

  return session ? <Navigate to="/" replace /> : <Login />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/watch" element={<RequireAuth><Veille /></RequireAuth>} />
          <Route path="/bibliometrics" element={<RequireAuth><Bibliometrie /></RequireAuth>} />
          <Route path="/digital-twin" element={<RequireAuth><DigitalTwin /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}