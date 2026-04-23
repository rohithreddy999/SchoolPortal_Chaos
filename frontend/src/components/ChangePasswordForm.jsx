import { useState } from "react";

const blankForm = {
  current_password: "",
  new_password: "",
  confirm_password: ""
};

export default function ChangePasswordForm({ saving, error, onSave, onClose }) {
  const [form, setForm] = useState(blankForm);
  const [localError, setLocalError] = useState("");
  const [success, setSuccess] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setLocalError("");
    setSuccess("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (form.new_password !== form.confirm_password) {
      setLocalError("New password and confirmation must match.");
      return;
    }

    setLocalError("");
    const result = await onSave({
      current_password: form.current_password,
      new_password: form.new_password
    });
    if (result) {
      setSuccess(result);
      setForm(blankForm);
    }
  }

  return (
    <section className="panel form-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Account</p>
          <h2>Change shared password</h2>
          <p className="panel-note">
            Use this when the shared admin password needs to be rotated for the staff handling admissions and payments.
          </p>
        </div>
        <button type="button" className="section-toggle" onClick={onClose}>
          Close form
        </button>
      </div>

      <form className="student-form" onSubmit={handleSubmit}>
        <div className="form-section">
          <div className="form-grid">
            <label>
              Current Password
              <input
                name="current_password"
                type="password"
                value={form.current_password}
                onChange={handleChange}
                autoComplete="current-password"
                required
              />
            </label>
            <label>
              New Password
              <input
                name="new_password"
                type="password"
                value={form.new_password}
                onChange={handleChange}
                autoComplete="new-password"
                minLength={8}
                required
              />
            </label>
            <label>
              Confirm New Password
              <input
                name="confirm_password"
                type="password"
                value={form.confirm_password}
                onChange={handleChange}
                autoComplete="new-password"
                minLength={8}
                required
              />
            </label>
          </div>
        </div>

        {localError || error ? <div className="error-banner">{localError || error}</div> : null}
        {success ? <div className="success-banner">{success}</div> : null}

        <button type="submit" className="primary-button" disabled={saving}>
          {saving ? "Updating password..." : "Update Password"}
        </button>
      </form>
    </section>
  );
}
