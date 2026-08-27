import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div className="full-page-loading">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return children;
}
