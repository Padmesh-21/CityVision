import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await login(username, password);
      navigate("/", { replace: true });
    } catch (err) {
      if (!err.response) {
        // No HTTP response at all -- the request never reached the
        // server (backend down, wrong VITE_API_URL, or CORS blocked
        // it). This is NOT a credentials problem, so don't say it is.
        setError(
          "Could not reach the backend. Check that the Django server is running " +
            "and CORS_ALLOWED_ORIGINS includes this origin (restart the backend " +
            "after changing .env -- it doesn't hot-reload env vars)."
        );
      } else if (err.response.status === 401) {
        setError("Invalid username or password.");
      } else {
        setError(`Login failed: ${err.response.status} ${err.response.statusText}`);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>CityVision ANPR</h1>
        <p className="login-subtitle">City Traffic Intelligence Platform</p>

        <label htmlFor="username">Username</label>
        <input
          id="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoFocus
          required
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        {error && <div className="form-error">{error}</div>}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
