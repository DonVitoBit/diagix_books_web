import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import AppLayout from "@/components/AppLayout";
import LoginPage from "@/pages/LoginPage";
import BooksPage from "@/pages/BooksPage";
import ParaphrasingPage from "@/pages/ParaphrasingPage";
import ResultsPage from "@/pages/ResultsPage";
import ImagesPage from "@/pages/ImagesPage";
import SettingsPage from "@/pages/SettingsPage";
import ModeratorsPage from "@/pages/ModeratorsPage";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

const ProtectedRoute: React.FC<{ children: React.ReactNode; adminOnly?: boolean }> = ({ children, adminOnly }) => {
  const { user, isAdmin } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && !isAdmin) return <Navigate to="/books" replace />;
  return <AppLayout>{children}</AppLayout>;
};

const LoginRoute: React.FC = () => {
  const { user, isAdmin } = useAuth();
  if (user) return <Navigate to={isAdmin ? "/books" : "/books"} replace />;
  return <LoginPage />;
};

const AppRoutes = () => (
  <Routes>
    <Route path="/login" element={<LoginRoute />} />
    <Route path="/books" element={<ProtectedRoute><BooksPage /></ProtectedRoute>} />
    <Route path="/paraphrasing" element={<ProtectedRoute adminOnly><ParaphrasingPage /></ProtectedRoute>} />
    <Route path="/results" element={<ProtectedRoute adminOnly><ResultsPage /></ProtectedRoute>} />
    <Route path="/images" element={<ProtectedRoute adminOnly><ImagesPage /></ProtectedRoute>} />
    <Route path="/settings" element={<ProtectedRoute adminOnly><SettingsPage /></ProtectedRoute>} />
    <Route path="/moderators" element={<ProtectedRoute adminOnly><ModeratorsPage /></ProtectedRoute>} />
    <Route path="/" element={<Navigate to="/login" replace />} />
    <Route path="*" element={<NotFound />} />
  </Routes>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
