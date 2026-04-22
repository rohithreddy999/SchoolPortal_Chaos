import { useState } from "react";
import { PORTAL_NAME, PORTAL_TAGLINE, SCHOOL_NAME } from "../lib/branding";

const defaultForm = {
  username: "",
  password: ""
};

export default function LoginForm({ onSubmit, loading, error }) {
  const [form, setForm] = useState(defaultForm);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await onSubmit(form);
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-badge">SSHS</div>
        <p className="eyebrow">{SCHOOL_NAME}</p>
        <h1>{PORTAL_NAME}</h1>
        <p className="auth-copy">
          {PORTAL_TAGLINE}. Sign in to maintain admissions, fee structures, and official payment history.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Enter username"
              autoComplete="username"
              required
            />
          </label>

          <label>
            Password
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Enter password"
              autoComplete="current-password"
              required
            />
          </label>

          {error ? <div className="error-banner">{error}</div> : null}

          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? "Signing in..." : "Access Portal"}
          </button>
        </form>
      </div>
    </div>
  );
}
