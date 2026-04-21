(() => {
  const app = document.getElementById("app");
  const toastRoot = document.getElementById("toast-root");
  const invoiceDialog = document.getElementById("invoice-dialog");

  const STORE = {
    token: "sfp.token",
    role: "sfp.role",
    year: "sfp.year"
  };

  const feeHeads = [
    { key: "admission", label: "Admission" },
    { key: "term1", label: "Term 1" },
    { key: "term2", label: "Term 2" },
    { key: "term3", label: "Term 3" },
    { key: "transport", label: "Transport" },
    { key: "books", label: "Books" }
  ];

  const onlineModes = [
    { value: "upi", label: "UPI" },
    { value: "card", label: "Card" },
    { value: "netbanking", label: "Net banking" },
    { value: "wallet", label: "Wallet" }
  ];

  const offlineModes = [
    { value: "cash", label: "Cash" },
    { value: "cheque", label: "Cheque" },
    { value: "bank_transfer", label: "Bank transfer" },
    { value: "offline", label: "Offline" }
  ];

  const adminNav = [
    { key: "overview", label: "Overview", icon: "dashboard" },
    { key: "students", label: "Students", icon: "users" },
    { key: "fees", label: "Fees", icon: "wallet" },
    { key: "payments", label: "Payments", icon: "receipt" }
  ];

  const parentNav = [
    { key: "overview", label: "Overview", icon: "dashboard" },
    { key: "pay", label: "Pay fees", icon: "card" },
    { key: "history", label: "History", icon: "receipt" }
  ];

  const ICONS = {
    dashboard: '<path d="M4 13h7V4H4v9Z"></path><path d="M13 20h7V4h-7v16Z"></path><path d="M4 20h7v-5H4v5Z"></path>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"></path><circle cx="9.5" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.9"></path><path d="M16 3.1a4 4 0 0 1 0 7.8"></path>',
    wallet: '<path d="M3 7a2 2 0 0 1 2-2h14v14H5a2 2 0 0 1-2-2V7Z"></path><path d="M16 11h4v4h-4a2 2 0 0 1 0-4Z"></path><path d="M5 5V3h12"></path>',
    receipt: '<path d="M6 2h12v20l-3-2-3 2-3-2-3 2V2Z"></path><path d="M9 7h6"></path><path d="M9 11h6"></path><path d="M9 15h4"></path>',
    search: '<circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path>',
    refresh: '<path d="M20 6v5h-5"></path><path d="M4 18v-5h5"></path><path d="M19 11a7 7 0 0 0-12.2-4.7L4 9"></path><path d="M5 13a7 7 0 0 0 12.2 4.7L20 15"></path>',
    logout: '<path d="M10 17 15 12 10 7"></path><path d="M15 12H3"></path><path d="M21 19V5a2 2 0 0 0-2-2h-6"></path>',
    plus: '<path d="M12 5v14"></path><path d="M5 12h14"></path>',
    check: '<path d="m20 6-11 11-5-5"></path>',
    printer: '<path d="M7 8V3h10v5"></path><path d="M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"></path><path d="M7 14h10v7H7v-7Z"></path>',
    close: '<path d="M18 6 6 18"></path><path d="m6 6 12 12"></path>',
    card: '<rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="M3 10h18"></path><path d="M7 15h2"></path><path d="M12 15h4"></path>',
    shield: '<path d="M12 2 4 5.5v5.8c0 5 3.2 8.9 8 10.7 4.8-1.8 8-5.7 8-10.7V5.5L12 2Z"></path><path d="m9 12 2 2 4-5"></path>',
    user: '<path d="M20 21a8 8 0 0 0-16 0"></path><circle cx="12" cy="7" r="4"></circle>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2"></rect><path d="M16 2v4"></path><path d="M8 2v4"></path><path d="M3 10h18"></path>',
    cash: '<rect x="3" y="6" width="18" height="12" rx="2"></rect><circle cx="12" cy="12" r="3"></circle><path d="M6 9v.01"></path><path d="M18 15v.01"></path>',
    clock: '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path>',
    warning: '<path d="M12 9v4"></path><path d="M12 17h.01"></path><path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"></path>',
    info: '<circle cx="12" cy="12" r="9"></circle><path d="M12 11v6"></path><path d="M12 7h.01"></path>'
  };

  const moneyFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  const state = {
    token: localStorage.getItem(STORE.token),
    role: localStorage.getItem(STORE.role),
    authMode: "admin",
    admin: {
      active: "overview",
      loading: false,
      year: localStorage.getItem(STORE.year) || "2024-2025",
      search: "",
      paymentStatus: "",
      students: [],
      selectedStudent: null,
      summary: null,
      allPayments: [],
      studentPayments: []
    },
    parent: {
      active: "overview",
      loading: false,
      year: localStorage.getItem(STORE.year) || "2024-2025",
      profile: null,
      summary: null,
      payments: [],
      selectedHead: "term1"
    }
  };

  let searchTimer = 0;

  function icon(name, extraClass = "") {
    return `<svg class="icon ${extraClass}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ICONS.info}</svg>`;
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    })[char]);
  }

  function numberValue(value) {
    const parsed = Number(value ?? 0);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function rawMoney(value) {
    return numberValue(value).toFixed(2);
  }

  function formatMoney(value) {
    return moneyFormatter.format(numberValue(value));
  }

  function formatDate(value) {
    if (!value) return "Not set";
    const date = new Date(`${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) return escapeHtml(value);
    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric"
    });
  }

  function todayISO() {
    return new Date().toISOString().slice(0, 10);
  }

  function feeHeadLabel(key) {
    return feeHeads.find((head) => head.key === key)?.label || key;
  }

  function percent(part, total) {
    const totalValue = numberValue(total);
    if (totalValue <= 0) return 0;
    return Math.max(0, Math.min(100, (numberValue(part) / totalValue) * 100));
  }

  function sumPayments(payments, status) {
    return payments
      .filter((payment) => !status || payment.payment_status === status)
      .reduce((total, payment) => total + numberValue(payment.amount_paid), 0);
  }

  function buildQuery(params) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        query.set(key, value);
      }
    });
    return query.toString();
  }

  async function apiFetch(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const method = options.method || "GET";
    const useAuth = options.auth !== false;
    let body = options.body;

    if (useAuth && state.token) {
      headers.Authorization = `Bearer ${state.token}`;
    }

    if (
      body &&
      typeof body === "object" &&
      !(body instanceof URLSearchParams) &&
      !(body instanceof FormData)
    ) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(body);
    }

    const response = await fetch(path, { method, headers, body });
    const text = await response.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (_) {
        data = text;
      }
    }

    if (!response.ok) {
      const error = new Error(formatApiError(data, response.status));
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  }

  function formatApiError(data, status) {
    if (data && Array.isArray(data.detail)) {
      return data.detail.map((item) => item.msg || String(item)).join("; ");
    }
    if (data && data.detail) return String(data.detail);
    if (typeof data === "string" && data.trim()) return data;
    return `Request failed with status ${status}`;
  }

  function toast(type, title, message = "") {
    const item = document.createElement("div");
    item.className = `toast ${type}`;
    const iconName = type === "success" ? "check" : type === "error" ? "warning" : "info";
    item.innerHTML = `${icon(iconName)}<div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span></div>`;
    toastRoot.appendChild(item);
    window.setTimeout(() => {
      item.style.opacity = "0";
      item.style.transform = "translateY(8px)";
      window.setTimeout(() => item.remove(), 180);
    }, 4200);
  }

  function formPayload(form) {
    const data = {};
    const formData = new FormData(form);
    formData.forEach((value, key) => {
      const clean = String(value).trim();
      if (clean !== "") data[key] = clean;
    });
    return data;
  }

  function setSession(role, token) {
    state.role = role;
    state.token = token;
    localStorage.setItem(STORE.role, role);
    localStorage.setItem(STORE.token, token);
  }

  function clearSession() {
    state.role = null;
    state.token = null;
    state.admin.selectedStudent = null;
    state.parent.profile = null;
    localStorage.removeItem(STORE.role);
    localStorage.removeItem(STORE.token);
  }

  function renderLoading(message = "Loading portal") {
    app.innerHTML = `
      <section class="boot-screen" aria-live="polite">
        <div class="brand-mark large" aria-hidden="true">${icon("shield")}</div>
        <p>${escapeHtml(message)}</p>
      </section>
    `;
  }

  function renderAuth() {
    const adminActive = state.authMode === "admin";
    app.innerHTML = `
      <section class="auth-screen">
        <div class="auth-wrap">
          <aside class="auth-identity">
            <div class="auth-title">
              <div class="brand-row">
                <div class="brand-mark" aria-hidden="true">${icon("shield")}</div>
                <div class="brand-copy">
                  <h1>School Fee Portal</h1>
                  <p>Secure fee operations for school teams and parents.</p>
                </div>
              </div>
              <h1>Fees, payments, invoices.</h1>
              <p>Admin teams can manage student fee records while parents can verify access, pay dues, and collect invoices from the same responsive workspace.</p>
            </div>
            <div class="auth-metrics" aria-label="Portal areas">
              <div class="metric-tile"><strong>6</strong><span>Fee heads</span></div>
              <div class="metric-tile"><strong>2</strong><span>Access modes</span></div>
              <div class="metric-tile"><strong>24/7</strong><span>Parent view</span></div>
            </div>
          </aside>

          <section class="auth-card">
            <div class="section-title">
              <h2>${adminActive ? "Admin sign in" : "Parent access"}</h2>
              <p>${adminActive ? "Use a school administrator account." : "Verify with student details."}</p>
            </div>
            <div class="segmented" role="tablist" aria-label="Access mode">
              <button type="button" class="${adminActive ? "active" : ""}" data-action="set-auth-mode" data-mode="admin">${icon("users")} Admin</button>
              <button type="button" class="${!adminActive ? "active" : ""}" data-action="set-auth-mode" data-mode="parent">${icon("user")} Parent</button>
            </div>
            ${adminActive ? renderAdminLoginForm() : renderParentLoginForm()}
          </section>
        </div>
      </section>
    `;
  }

  function renderAdminLoginForm() {
    return `
      <form id="admin-login-form" class="form-grid">
        <div class="field wide">
          <label for="admin-email">Email</label>
          <input id="admin-email" name="email" type="email" autocomplete="username" required value="admin@school.com">
        </div>
        <div class="field wide">
          <label for="admin-password">Password</label>
          <input id="admin-password" name="password" type="password" autocomplete="current-password" required value="Admin@12345">
        </div>
        <div class="form-actions wide">
          <button class="primary-button" type="submit">${icon("shield")} Sign in</button>
          <button class="secondary-button" type="button" data-action="fill-demo" data-demo="admin">${icon("check")} Demo admin</button>
        </div>
      </form>
    `;
  }

  function renderParentLoginForm() {
    return `
      <form id="parent-login-form" class="form-grid">
        <div class="field">
          <label for="parent-roll">Roll number</label>
          <input id="parent-roll" name="roll_number" autocomplete="off" required value="S0001">
        </div>
        <div class="field">
          <label for="parent-dob">Date of birth</label>
          <input id="parent-dob" name="date_of_birth" type="date" required max="${todayISO()}" value="2010-05-15">
        </div>
        <div class="field wide">
          <label for="parent-aadhaar">Aadhaar number</label>
          <input id="parent-aadhaar" name="aadhaar_number" inputmode="numeric" maxlength="14" autocomplete="off" required value="123412341234">
        </div>
        <div class="form-actions wide">
          <button class="primary-button" type="submit">${icon("shield")} Verify</button>
          <button class="secondary-button" type="button" data-action="fill-demo" data-demo="parent">${icon("check")} Demo parent</button>
        </div>
      </form>
    `;
  }

  function renderShell(role, content) {
    const isAdmin = role === "admin";
    const roleState = isAdmin ? state.admin : state.parent;
    const navItems = isAdmin ? adminNav : parentNav;
    const title = titleFor(role, roleState.active);
    const person = isAdmin ? state.admin.selectedStudent : state.parent.profile;
    return `
      <div class="dashboard-shell">
        <aside class="sidebar">
          <div class="sidebar-head">
            <div class="brand-mark" aria-hidden="true">${icon("shield")}</div>
            <div>
              <h2>School Fee Portal</h2>
              <p>${isAdmin ? "Administration" : "Parent workspace"}</p>
            </div>
          </div>
          <span class="role-badge">${icon(isAdmin ? "users" : "user")} ${isAdmin ? "Admin" : "Parent"}</span>
          <nav class="nav-list" aria-label="${isAdmin ? "Admin" : "Parent"} navigation">
            ${navItems.map((item) => `
              <button type="button" class="nav-button ${roleState.active === item.key ? "active" : ""}" data-action="nav" data-role="${role}" data-section="${item.key}">
                ${icon(item.icon)} ${escapeHtml(item.label)}
              </button>
            `).join("")}
          </nav>
          <div class="sidebar-spacer"></div>
          <div class="selected-mini">
            <span>${isAdmin ? "Selected student" : "Student"}</span>
            <strong>${person ? escapeHtml(person.student_name) : "None selected"}</strong>
            <span>${person ? `${escapeHtml(person.roll_number)} - Class ${escapeHtml(person.class_name)}-${escapeHtml(person.section)}` : "Choose a student to load fee details"}</span>
          </div>
          <button class="danger-button" type="button" data-action="logout">${icon("logout")} Sign out</button>
        </aside>
        <main class="main-stage">
          <header class="topbar">
            <div class="section-title">
              <h1>${escapeHtml(title.heading)}</h1>
              <p>${escapeHtml(title.copy)}</p>
            </div>
            <div class="topbar-tools">
              <div class="year-field">
                <label for="${role}-year">Academic year</label>
                <input id="${role}-year" value="${escapeHtml(roleState.year)}" inputmode="numeric" pattern="[0-9]{4}-[0-9]{4}">
              </div>
              <button class="icon-button" type="button" data-action="${role}-refresh" aria-label="Refresh">${icon("refresh")}</button>
              <button class="danger-button" type="button" data-action="logout">${icon("logout")} Sign out</button>
            </div>
          </header>
          ${content}
        </main>
      </div>
    `;
  }

  function titleFor(role, active) {
    if (role === "admin") {
      const titles = {
        overview: ["Fee control room", "Search students, inspect balances, and review recent payments."],
        students: ["Student records", "Create profiles and move directly into fee assignment."],
        fees: ["Fee setup", "Assign annual fees and approved concessions for the selected student."],
        payments: ["Payment desk", "Record offline payments and confirm pending online orders."]
      };
      const [heading, copy] = titles[active] || titles.overview;
      return { heading, copy };
    }
    const titles = {
      overview: ["Fee summary", "Track dues, concessions, paid amounts, and upcoming payments."],
      pay: ["Pay fees", "Choose a fee head, create an online payment request, and follow status."],
      history: ["Payment history", "Review orders and open invoices for successful payments."]
    };
    const [heading, copy] = titles[active] || titles.overview;
    return { heading, copy };
  }

  function renderAdmin() {
    app.innerHTML = renderShell("admin", renderAdminContent());
  }

  function renderAdminContent() {
    if (state.admin.loading) return renderSkeletonContent();
    if (state.admin.active === "students") return renderAdminStudents();
    if (state.admin.active === "fees") return renderAdminFees();
    if (state.admin.active === "payments") return renderAdminPayments();
    return renderAdminOverview();
  }

  function renderSkeletonContent() {
    return `
      <section class="stat-grid">
        <div class="skeleton"></div>
        <div class="skeleton"></div>
        <div class="skeleton"></div>
        <div class="skeleton"></div>
      </section>
      <section class="content-grid">
        <div class="skeleton"></div>
        <div class="skeleton"></div>
      </section>
    `;
  }

  function renderAdminOverview() {
    return `
      ${renderAdminStats()}
      <section class="content-grid">
        ${renderStudentPicker("Student directory", "Search and select a student.")}
        ${renderSummaryPanel(state.admin.summary, state.admin.selectedStudent)}
      </section>
      ${renderPaymentsPanel("Selected student payments", state.admin.studentPayments, "admin")}
    `;
  }

  function renderAdminStats() {
    const selectedBalance = state.admin.summary ? state.admin.summary.balance : 0;
    const collected = sumPayments(state.admin.allPayments, "success");
    const pendingCount = state.admin.allPayments.filter((payment) => payment.payment_status === "pending").length;
    return `
      <section class="stat-grid">
        ${renderStat("Students", state.admin.students.length, "Loaded records", "users")}
        ${renderStat("Selected balance", formatMoney(selectedBalance), state.admin.selectedStudent ? state.admin.selectedStudent.roll_number : "No student", "wallet")}
        ${renderStat("Recent collected", formatMoney(collected), "Latest successful payments", "cash")}
        ${renderStat("Pending online", pendingCount, "Awaiting confirmation", "clock")}
      </section>
    `;
  }

  function renderStat(label, value, detail, iconName) {
    return `
      <article class="stat-card">
        <div class="icon-wrap">${icon(iconName)}</div>
        <div>
          <strong>${escapeHtml(value)}</strong>
          <span>${escapeHtml(label)} - ${escapeHtml(detail)}</span>
        </div>
      </article>
    `;
  }

  function renderAdminStudents() {
    return `
      <section class="content-grid equal">
        ${renderCreateStudentPanel()}
        ${renderStudentPicker("Student directory", "Use the latest records or search by roll, admission, name, class, or mobile.")}
      </section>
    `;
  }

  function renderCreateStudentPanel() {
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>Create student</h2>
            <p>New profiles are immediately available for fee setup.</p>
          </div>
          ${icon("plus")}
        </div>
        <form id="student-create-form" class="form-grid">
          <div class="field">
            <label for="admission-number">Admission number</label>
            <input id="admission-number" name="admission_number" required placeholder="A0002">
          </div>
          <div class="field">
            <label for="roll-number">Roll number</label>
            <input id="roll-number" name="roll_number" required placeholder="S0002">
          </div>
          <div class="field wide">
            <label for="student-name">Student name</label>
            <input id="student-name" name="student_name" required placeholder="Student name">
          </div>
          <div class="field">
            <label for="father-name">Father name</label>
            <input id="father-name" name="father_name" placeholder="Father name">
          </div>
          <div class="field">
            <label for="mother-name">Mother name</label>
            <input id="mother-name" name="mother_name" placeholder="Mother name">
          </div>
          <div class="field">
            <label for="mobile-number">Mobile number</label>
            <input id="mobile-number" name="mobile_number" inputmode="tel" placeholder="9999999999">
          </div>
          <div class="field">
            <label for="student-dob">Date of birth</label>
            <input id="student-dob" name="date_of_birth" type="date" max="${todayISO()}" required>
          </div>
          <div class="field">
            <label for="class-name">Class</label>
            <input id="class-name" name="class_name" required placeholder="10">
          </div>
          <div class="field">
            <label for="section-name">Section</label>
            <input id="section-name" name="section" required placeholder="A">
          </div>
          <div class="field">
            <label for="student-aadhaar">Student Aadhaar</label>
            <input id="student-aadhaar" name="student_aadhaar" inputmode="numeric" maxlength="14" required placeholder="12 digits">
          </div>
          <div class="field">
            <label for="father-aadhaar">Father Aadhaar</label>
            <input id="father-aadhaar" name="father_aadhaar" inputmode="numeric" maxlength="14" placeholder="12 digits">
          </div>
          <div class="form-actions wide">
            <button class="primary-button" type="submit">${icon("plus")} Create student</button>
          </div>
        </form>
      </section>
    `;
  }

  function renderStudentPicker(title, subtitle) {
    const rows = state.admin.students.length
      ? state.admin.students.map(renderStudentRow).join("")
      : `<div class="empty-state">No students found.</div>`;
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>${escapeHtml(title)}</h2>
            <p>${escapeHtml(subtitle)}</p>
          </div>
        </div>
        <form id="admin-search-form" class="toolbar">
          <input id="admin-student-search" class="search-input" name="search" value="${escapeHtml(state.admin.search)}" placeholder="Search students">
          <button class="icon-button" type="submit" aria-label="Search students">${icon("search")}</button>
        </form>
        <div class="student-list">
          ${rows}
        </div>
      </section>
    `;
  }

  function renderStudentRow(student) {
    const active = state.admin.selectedStudent?.id === student.id;
    return `
      <button type="button" class="student-row ${active ? "active" : ""}" data-action="select-student" data-id="${student.id}">
        <strong>${escapeHtml(student.student_name)}</strong>
        <span class="student-meta">
          <span>${escapeHtml(student.roll_number)}</span>
          <span>${escapeHtml(student.admission_number)}</span>
          <span>Class ${escapeHtml(student.class_name)}-${escapeHtml(student.section)}</span>
        </span>
      </button>
    `;
  }

  function renderAdminFees() {
    if (!state.admin.selectedStudent) {
      return `
        <section class="content-grid">
          ${renderStudentPicker("Choose student", "Select a student before assigning fees.")}
          <section class="panel">${renderEmpty("No student selected", "Pick a student to manage fee structure and concessions.")}</section>
        </section>
      `;
    }
    return `
      <section class="content-grid">
        ${renderSummaryPanel(state.admin.summary, state.admin.selectedStudent)}
        <div class="main-stage">
          ${renderFeeStructureForm()}
          ${renderConcessionForm()}
        </div>
      </section>
    `;
  }

  function renderFeeStructureForm() {
    const assigned = state.admin.summary?.assigned || {};
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>Fee structure</h2>
            <p>${escapeHtml(state.admin.selectedStudent.student_name)} - ${escapeHtml(state.admin.year)}</p>
          </div>
          ${icon("wallet")}
        </div>
        <form id="fee-structure-form" class="form-grid compact">
          ${feeHeads.map((head) => `
            <div class="field">
              <label for="fee-${head.key}">${escapeHtml(head.label)}</label>
              <input id="fee-${head.key}" name="${head.key}_fee" type="number" min="0" step="0.01" value="${rawMoney(assigned[head.key])}">
            </div>
          `).join("")}
          <div class="form-actions wide">
            <button class="primary-button" type="submit">${icon("check")} Save fee structure</button>
          </div>
        </form>
      </section>
    `;
  }

  function renderConcessionForm() {
    const concessions = state.admin.summary?.concessions || {};
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>Concessions</h2>
            <p>Apply transport or general reductions.</p>
          </div>
          ${icon("cash")}
        </div>
        <form id="concession-form" class="form-grid compact">
          <div class="field">
            <label for="transport-concession">Transport concession</label>
            <input id="transport-concession" name="transport_concession" type="number" min="0" step="0.01" value="${rawMoney(concessions.transport)}">
          </div>
          <div class="field">
            <label for="other-concession">Other concession</label>
            <input id="other-concession" name="other_concession" type="number" min="0" step="0.01" value="${rawMoney(concessions.other)}">
          </div>
          <div class="form-actions wide">
            <button class="primary-button" type="submit">${icon("check")} Save concessions</button>
          </div>
        </form>
      </section>
    `;
  }

  function renderAdminPayments() {
    return `
      <section class="content-grid equal">
        ${renderOfflinePaymentForm()}
        ${renderConfirmPaymentForm()}
      </section>
      ${renderPaymentsPanel("Payment ledger", state.admin.studentPayments, "admin")}
    `;
  }

  function renderOfflinePaymentForm() {
    if (!state.admin.selectedStudent) {
      return `<section class="panel">${renderEmpty("No student selected", "Select a student before recording an offline payment.")}</section>`;
    }
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>Offline payment</h2>
            <p>${escapeHtml(state.admin.selectedStudent.student_name)} - ${escapeHtml(state.admin.year)}</p>
          </div>
          ${icon("cash")}
        </div>
        <form id="offline-payment-form" class="form-grid">
          <div class="field">
            <label for="offline-head">Fee head</label>
            <select id="offline-head" name="fee_head" required>
              ${feeHeads.map((head) => `<option value="${head.key}">${escapeHtml(head.label)}</option>`).join("")}
            </select>
          </div>
          <div class="field">
            <label for="offline-amount">Amount</label>
            <input id="offline-amount" name="amount_paid" type="number" min="0.01" step="0.01" required>
          </div>
          <div class="field">
            <label for="offline-mode">Mode</label>
            <select id="offline-mode" name="payment_mode">
              ${offlineModes.map((mode) => `<option value="${mode.value}">${escapeHtml(mode.label)}</option>`).join("")}
            </select>
          </div>
          <div class="field">
            <label for="offline-date">Payment date</label>
            <input id="offline-date" name="payment_date" type="date" max="${todayISO()}" value="${todayISO()}">
          </div>
          <div class="field">
            <label for="receipt-number">Receipt number</label>
            <input id="receipt-number" name="receipt_number" maxlength="30" placeholder="Auto if blank">
          </div>
          <div class="field">
            <label for="collected-by">Collected by</label>
            <input id="collected-by" name="collected_by" placeholder="School Administration">
          </div>
          <div class="field wide">
            <label for="offline-remarks">Remarks</label>
            <textarea id="offline-remarks" name="remarks" placeholder="Optional"></textarea>
          </div>
          <div class="form-actions wide">
            <button class="primary-button" type="submit">${icon("receipt")} Record and invoice</button>
          </div>
        </form>
      </section>
    `;
  }

  function renderConfirmPaymentForm() {
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>Confirm online payment</h2>
            <p>Successful confirmation generates the invoice.</p>
          </div>
          ${icon("check")}
        </div>
        <form id="confirm-online-form" class="form-grid">
          <div class="field">
            <label for="confirm-payment-id">Payment ID</label>
            <input id="confirm-payment-id" name="payment_id" type="number" min="1" required>
          </div>
          <div class="field">
            <label for="gateway-payment-id">Gateway payment ID</label>
            <input id="gateway-payment-id" name="razorpay_payment_id" maxlength="50" required placeholder="pay_xxxxx">
          </div>
          <div class="field wide">
            <label for="confirm-remarks">Remarks</label>
            <textarea id="confirm-remarks" name="remarks" placeholder="Optional"></textarea>
          </div>
          <div class="form-actions wide">
            <button class="primary-button" type="submit">${icon("check")} Confirm payment</button>
          </div>
        </form>
      </section>
    `;
  }

  function renderSummaryPanel(summary, student) {
    if (!student) {
      return `<section class="panel">${renderEmpty("No student selected", "Select a student to see fee summary.")}</section>`;
    }
    if (!summary) {
      return `<section class="panel"><div class="skeleton"></div></section>`;
    }
    const credited = numberValue(summary.total_paid) + numberValue(summary.total_concessions);
    const paidPct = percent(credited, summary.total_assigned);
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>${escapeHtml(student.student_name)}</h2>
            <p>${escapeHtml(student.roll_number)} - Class ${escapeHtml(student.class_name)}-${escapeHtml(student.section)} - ${escapeHtml(summary.academic_year)}</p>
          </div>
          <span class="role-badge">${escapeHtml(student.admission_number)}</span>
        </div>
        <div class="summary-meter">
          <div class="balance-hero">
            <div>
              <span>Outstanding balance</span>
              <strong>${formatMoney(summary.balance)}</strong>
            </div>
            <span class="status-badge ${numberValue(summary.balance) > 0 ? "pending" : "success"}">${numberValue(summary.balance) > 0 ? "Due" : "Clear"}</span>
          </div>
          <div class="progress-track" aria-label="Paid progress"><div class="progress-fill" style="--pct:${paidPct}%"></div></div>
          <div class="money-grid">
            <div class="money-tile"><span>Assigned</span><strong>${formatMoney(summary.total_assigned)}</strong></div>
            <div class="money-tile"><span>Concessions</span><strong>${formatMoney(summary.total_concessions)}</strong></div>
            <div class="money-tile"><span>Paid</span><strong>${formatMoney(summary.total_paid)}</strong></div>
          </div>
        </div>
        <div class="head-list">
          ${renderFeeHeadRows(summary)}
        </div>
      </section>
    `;
  }

  function renderFeeHeadRows(summary) {
    return feeHeads.map((head) => {
      const assigned = numberValue(summary.assigned?.[head.key]);
      const paid = numberValue(summary.paid?.[head.key]);
      const concession = head.key === "transport" ? numberValue(summary.concessions?.transport) : 0;
      const credited = paid + concession;
      const due = Math.max(assigned - credited, 0);
      return `
        <div class="head-row">
          <div class="head-name">
            <strong>${escapeHtml(head.label)}</strong>
            <span>${formatMoney(assigned)} assigned</span>
          </div>
          <div class="head-bar">
            <div class="progress-track"><div class="progress-fill" style="--pct:${percent(credited, assigned)}%"></div></div>
            <small>${formatMoney(paid)} paid${concession > 0 ? ` - ${formatMoney(concession)} concession` : ""}</small>
          </div>
          <div class="head-amount">${formatMoney(due)}</div>
        </div>
      `;
    }).join("");
  }

  function renderPaymentsPanel(title, payments, scope) {
    const rows = payments.length ? payments.map((payment) => renderPaymentRow(payment, scope)).join("") : "";
    const adminTools = scope === "admin" ? `
      <div class="toolbar">
        <select id="admin-payment-status" class="search-input" aria-label="Filter payments">
          <option value="" ${state.admin.paymentStatus === "" ? "selected" : ""}>All statuses</option>
          <option value="pending" ${state.admin.paymentStatus === "pending" ? "selected" : ""}>Pending</option>
          <option value="success" ${state.admin.paymentStatus === "success" ? "selected" : ""}>Success</option>
          <option value="failed" ${state.admin.paymentStatus === "failed" ? "selected" : ""}>Failed</option>
        </select>
      </div>
    ` : "";

    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>${escapeHtml(title)}</h2>
            <p>${payments.length ? `${payments.length} record${payments.length === 1 ? "" : "s"}` : "No payment records"}</p>
          </div>
          ${adminTools}
        </div>
        ${payments.length ? `
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Date</th>
                  <th>Head</th>
                  <th>Amount</th>
                  <th>Mode</th>
                  <th>Status</th>
                  <th>Reference</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        ` : renderEmpty("No payments yet", "Payment records for this view will appear here.")}
      </section>
    `;
  }

  function renderPaymentRow(payment, scope) {
    const reference = payment.receipt_number || payment.razorpay_order_id || payment.razorpay_payment_id || "-";
    const invoiceAction = scope === "admin" ? "admin-invoice" : "parent-invoice";
    const actions = payment.payment_status === "success"
      ? `<button class="icon-button" type="button" data-action="${invoiceAction}" data-id="${payment.id}" aria-label="Open invoice">${icon("receipt")}</button>`
      : scope === "admin" && payment.payment_status === "pending"
        ? `<button class="icon-button" type="button" data-action="fill-confirm" data-id="${payment.id}" aria-label="Confirm payment">${icon("check")}</button>`
        : "";
    return `
      <tr>
        <td>#${payment.id}</td>
        <td>${formatDate(payment.payment_date)}</td>
        <td>${escapeHtml(feeHeadLabel(payment.fee_head))}</td>
        <td class="amount-cell">${formatMoney(payment.amount_paid)}</td>
        <td>${escapeHtml(payment.payment_mode || "-")}</td>
        <td><span class="status-badge ${escapeHtml(payment.payment_status)}">${escapeHtml(payment.payment_status)}</span></td>
        <td>${escapeHtml(reference)}</td>
        <td><div class="row-actions">${actions}</div></td>
      </tr>
    `;
  }

  function renderEmpty(title, detail) {
    return `
      <div class="empty-state">
        <div>
          <strong>${escapeHtml(title)}</strong>
          <p>${escapeHtml(detail)}</p>
        </div>
      </div>
    `;
  }

  function renderParent() {
    app.innerHTML = renderShell("parent", renderParentContent());
  }

  function renderParentContent() {
    if (state.parent.loading) return renderSkeletonContent();
    if (state.parent.active === "pay") return renderParentPay();
    if (state.parent.active === "history") return renderParentHistory();
    return renderParentOverview();
  }

  function renderParentOverview() {
    return `
      ${renderParentStats()}
      <section class="content-grid">
        ${renderParentProfilePanel()}
        ${renderSummaryPanel(state.parent.summary, state.parent.profile)}
      </section>
      ${renderPaymentsPanel("Recent payments", state.parent.payments.slice(0, 6), "parent")}
    `;
  }

  function renderParentStats() {
    const summary = state.parent.summary || {};
    const pendingCount = state.parent.payments.filter((payment) => payment.payment_status === "pending").length;
    return `
      <section class="stat-grid">
        ${renderStat("Balance", formatMoney(summary.balance), state.parent.year, "wallet")}
        ${renderStat("Paid", formatMoney(summary.total_paid), "Successful payments", "check")}
        ${renderStat("Concessions", formatMoney(summary.total_concessions), "Applied reductions", "cash")}
        ${renderStat("Pending orders", pendingCount, "Online requests", "clock")}
      </section>
    `;
  }

  function renderParentProfilePanel() {
    const profile = state.parent.profile;
    if (!profile) return `<section class="panel">${renderEmpty("Profile unavailable", "Sign in again to load student details.")}</section>`;
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>${escapeHtml(profile.student_name)}</h2>
            <p>${escapeHtml(profile.roll_number)} - Class ${escapeHtml(profile.class_name)}-${escapeHtml(profile.section)}</p>
          </div>
          ${icon("user")}
        </div>
        <div class="money-grid">
          <div class="money-tile"><span>Admission</span><strong>${escapeHtml(profile.admission_number)}</strong></div>
          <div class="money-tile"><span>Student ID</span><strong>#${escapeHtml(profile.student_id)}</strong></div>
          <div class="money-tile"><span>Access</span><strong>Parent</strong></div>
        </div>
        <div class="timeline-list">
          <div class="timeline-item">
            <div class="timeline-icon">${icon("shield")}</div>
            <div>
              <h3>Verified parent session</h3>
              <p>Session is scoped to this student record.</p>
            </div>
            <span class="status-badge success">Active</span>
          </div>
        </div>
      </section>
    `;
  }

  function renderParentPay() {
    return `
      <section class="content-grid">
        ${renderParentHeadChooser()}
        ${renderParentPaymentForm()}
      </section>
      ${renderPaymentsPanel("Payment history", state.parent.payments, "parent")}
    `;
  }

  function renderParentHeadChooser() {
    const summary = state.parent.summary;
    if (!summary) return `<section class="panel"><div class="skeleton"></div></section>`;
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>Fee heads</h2>
            <p>Choose the fee head for this payment.</p>
          </div>
          ${icon("wallet")}
        </div>
        <div class="payment-heads">
          ${feeHeads.map((head) => {
            const allowed = allowedAmountForHead(summary, head.key);
            const active = state.parent.selectedHead === head.key;
            return `
              <button type="button" class="fee-head-card ${active ? "active" : ""}" data-action="select-parent-head" data-head="${head.key}">
                <strong>${escapeHtml(head.label)}</strong>
                <span>${formatMoney(allowed)} payable</span>
              </button>
            `;
          }).join("")}
        </div>
      </section>
    `;
  }

  function renderParentPaymentForm() {
    const summary = state.parent.summary;
    const selectedHead = state.parent.selectedHead;
    const allowed = summary ? allowedAmountForHead(summary, selectedHead) : 0;
    const disabled = allowed <= 0;
    return `
      <section class="panel">
        <div class="panel-title">
          <div>
            <h2>Online payment</h2>
            <p>${escapeHtml(feeHeadLabel(selectedHead))} - ${escapeHtml(state.parent.year)}</p>
          </div>
          ${icon("card")}
        </div>
        <form id="parent-payment-form" class="form-grid">
          <div class="field">
            <label for="parent-pay-head">Fee head</label>
            <input id="parent-pay-head" value="${escapeHtml(feeHeadLabel(selectedHead))}" disabled>
          </div>
          <div class="field">
            <label for="parent-pay-amount">Amount</label>
            <input id="parent-pay-amount" name="amount_paid" type="number" min="0.01" step="0.01" value="${disabled ? "" : rawMoney(allowed)}" ${disabled ? "disabled" : "required"}>
          </div>
          <div class="field">
            <label for="parent-pay-mode">Mode</label>
            <select id="parent-pay-mode" name="payment_mode" ${disabled ? "disabled" : ""}>
              ${onlineModes.map((mode) => `<option value="${mode.value}">${escapeHtml(mode.label)}</option>`).join("")}
            </select>
          </div>
          <div class="field">
            <label for="parent-pay-limit">Maximum</label>
            <input id="parent-pay-limit" value="${formatMoney(allowed)}" disabled>
          </div>
          <div class="field wide">
            <label for="parent-pay-remarks">Remarks</label>
            <textarea id="parent-pay-remarks" name="remarks" placeholder="Optional" ${disabled ? "disabled" : ""}></textarea>
          </div>
          <div class="form-actions wide">
            <button class="primary-button" type="submit" ${disabled ? "disabled" : ""}>${icon("card")} Create payment order</button>
          </div>
        </form>
      </section>
    `;
  }

  function renderParentHistory() {
    return `
      <section class="content-grid">
        ${renderSummaryPanel(state.parent.summary, state.parent.profile)}
        ${renderPaymentsPanel("Payment history", state.parent.payments, "parent")}
      </section>
    `;
  }

  function allowedAmountForHead(summary, headKey) {
    if (!summary) return 0;
    const assigned = numberValue(summary.assigned?.[headKey]);
    const paid = numberValue(summary.paid?.[headKey]);
    const headConcession = headKey === "transport" ? numberValue(summary.concessions?.transport) : 0;
    const headOutstanding = Math.max(assigned - paid - headConcession, 0);
    const totalBalance = numberValue(summary.balance);
    return Math.max(0, Math.min(headOutstanding, totalBalance));
  }

  async function bootstrapAdmin() {
    renderLoading("Opening admin workspace");
    state.admin.loading = true;
    await loadAdminData();
    state.admin.loading = false;
    renderAdmin();
  }

  async function loadAdminData() {
    const [students, allPayments] = await Promise.all([
      apiFetch(`/admin/students?${buildQuery({ search: state.admin.search, limit: 100 })}`),
      apiFetch("/admin/payments?limit=100")
    ]);
    state.admin.students = students || [];
    state.admin.allPayments = allPayments || [];

    if (!state.admin.selectedStudent && state.admin.students.length) {
      state.admin.selectedStudent = state.admin.students[0];
    }
    if (state.admin.selectedStudent) {
      const fresh = state.admin.students.find((student) => student.id === state.admin.selectedStudent.id);
      if (fresh) state.admin.selectedStudent = fresh;
      await loadAdminStudentContext();
    } else {
      state.admin.summary = null;
      state.admin.studentPayments = [];
    }
  }

  async function loadAdminStudentContext() {
    const student = state.admin.selectedStudent;
    if (!student) return;
    const query = buildQuery({
      student_id: student.id,
      academic_year: state.admin.year
    });
    const paymentQuery = buildQuery({
      student_id: student.id,
      status: state.admin.paymentStatus,
      limit: 100
    });
    const [summary, payments] = await Promise.all([
      apiFetch(`/admin/fee-summary?${query}`),
      apiFetch(`/admin/payments?${paymentQuery}`)
    ]);
    state.admin.summary = summary;
    state.admin.studentPayments = payments || [];
  }

  async function bootstrapParent() {
    renderLoading("Opening parent workspace");
    state.parent.loading = true;
    await loadParentData();
    state.parent.loading = false;
    renderParent();
  }

  async function loadParentData() {
    const [profile, summary, payments] = await Promise.all([
      apiFetch("/parent/me"),
      apiFetch(`/parent/fee-summary?${buildQuery({ academic_year: state.parent.year })}`),
      apiFetch("/parent/payments")
    ]);
    state.parent.profile = profile;
    state.parent.summary = summary;
    state.parent.payments = payments || [];
    if (allowedAmountForHead(summary, state.parent.selectedHead) <= 0) {
      const nextHead = feeHeads.find((head) => allowedAmountForHead(summary, head.key) > 0);
      if (nextHead) state.parent.selectedHead = nextHead.key;
    }
  }

  async function handleAdminLogin(form) {
    const body = new URLSearchParams();
    body.set("username", form.email.value.trim());
    body.set("password", form.password.value);
    const token = await apiFetch("/auth/login", {
      method: "POST",
      auth: false,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body
    });
    setSession("admin", token.access_token);
    toast("success", "Signed in", "Admin workspace loaded.");
    await bootstrapAdmin();
  }

  async function handleParentLogin(form) {
    const payload = formPayload(form);
    const token = await apiFetch("/auth/parent-access", {
      method: "POST",
      auth: false,
      body: payload
    });
    setSession("parent", token.access_token);
    toast("success", "Access verified", "Parent workspace loaded.");
    await bootstrapParent();
  }

  async function handleStudentCreate(form) {
    const payload = formPayload(form);
    const student = await apiFetch("/admin/students", {
      method: "POST",
      body: payload
    });
    state.admin.selectedStudent = student;
    state.admin.active = "fees";
    toast("success", "Student created", `${student.student_name} is selected.`);
    await loadAdminData();
    renderAdmin();
  }

  async function handleFeeStructure(form) {
    const student = state.admin.selectedStudent;
    if (!student) return;
    const payload = {
      ...formPayload(form),
      student_id: student.id,
      academic_year: state.admin.year
    };
    await apiFetch("/admin/fee-structure", {
      method: "POST",
      body: payload
    });
    toast("success", "Fee structure saved", state.admin.year);
    await loadAdminStudentContext();
    renderAdmin();
  }

  async function handleConcession(form) {
    const student = state.admin.selectedStudent;
    if (!student) return;
    const payload = {
      ...formPayload(form),
      student_id: student.id,
      academic_year: state.admin.year
    };
    await apiFetch("/admin/concessions", {
      method: "POST",
      body: payload
    });
    toast("success", "Concessions saved", state.admin.year);
    await loadAdminStudentContext();
    renderAdmin();
  }

  async function handleOfflinePayment(form) {
    const student = state.admin.selectedStudent;
    if (!student) return;
    const payload = {
      ...formPayload(form),
      student_id: student.id,
      academic_year: state.admin.year
    };
    const invoice = await apiFetch("/admin/payments/offline", {
      method: "POST",
      body: payload
    });
    toast("success", "Payment recorded", invoice.receipt_number);
    await loadAdminData();
    renderAdmin();
    openInvoice(invoice);
  }

  async function handleConfirmOnline(form) {
    const payload = formPayload(form);
    const paymentId = payload.payment_id;
    delete payload.payment_id;
    const invoice = await apiFetch(`/admin/payments/online/${paymentId}/confirm`, {
      method: "POST",
      body: payload
    });
    toast("success", "Online payment confirmed", invoice.receipt_number);
    await loadAdminData();
    renderAdmin();
    openInvoice(invoice);
  }

  async function handleParentPayment(form) {
    const payload = {
      ...formPayload(form),
      academic_year: state.parent.year,
      fee_head: state.parent.selectedHead
    };
    const payment = await apiFetch("/parent/pay-online", {
      method: "POST",
      body: payload
    });
    toast("success", "Payment order created", payment.razorpay_order_id || `Payment #${payment.id}`);
    await loadParentData();
    renderParent();
  }

  async function searchAdminStudents() {
    const query = buildQuery({ search: state.admin.search, limit: 100 });
    state.admin.students = await apiFetch(`/admin/students?${query}`);
    if (!state.admin.selectedStudent && state.admin.students.length) {
      state.admin.selectedStudent = state.admin.students[0];
      await loadAdminStudentContext();
    }
  }

  async function openAdminInvoice(paymentId) {
    const invoice = await apiFetch(`/admin/payments/${paymentId}/invoice`);
    openInvoice(invoice);
  }

  async function openParentInvoice(paymentId) {
    const invoice = await apiFetch(`/parent/invoices/${paymentId}`);
    openInvoice(invoice);
  }

  function openInvoice(invoice) {
    invoiceDialog.innerHTML = renderInvoice(invoice);
    invoiceDialog.showModal();
  }

  function renderInvoice(invoice) {
    return `
      <section class="invoice-sheet">
        <div class="invoice-head">
          <div>
            <h2>${escapeHtml(invoice.school_name)}</h2>
            <p class="muted">Receipt ${escapeHtml(invoice.receipt_number)}</p>
          </div>
          <span class="status-badge ${escapeHtml(invoice.payment_status)}">${escapeHtml(invoice.payment_status)}</span>
        </div>
        <div class="invoice-meta">
          <div class="invoice-box"><span>Student</span><strong>${escapeHtml(invoice.student_name)}</strong></div>
          <div class="invoice-box"><span>Roll number</span><strong>${escapeHtml(invoice.roll_number)}</strong></div>
          <div class="invoice-box"><span>Class</span><strong>${escapeHtml(invoice.class_name)}-${escapeHtml(invoice.section)}</strong></div>
          <div class="invoice-box"><span>Admission</span><strong>${escapeHtml(invoice.admission_number)}</strong></div>
          <div class="invoice-box"><span>Date</span><strong>${formatDate(invoice.payment_date)}</strong></div>
          <div class="invoice-box"><span>Academic year</span><strong>${escapeHtml(invoice.academic_year)}</strong></div>
          <div class="invoice-box"><span>Fee head</span><strong>${escapeHtml(feeHeadLabel(invoice.fee_head))}</strong></div>
          <div class="invoice-box"><span>Mode</span><strong>${escapeHtml(invoice.payment_mode || "-")}</strong></div>
          <div class="invoice-box"><span>Collected by</span><strong>${escapeHtml(invoice.collected_by || "-")}</strong></div>
          <div class="invoice-box"><span>Remaining balance</span><strong>${formatMoney(invoice.remaining_balance)}</strong></div>
        </div>
        <div class="invoice-total">
          <span>Amount paid</span>
          <strong>${formatMoney(invoice.amount_paid)}</strong>
        </div>
        <div class="dialog-actions">
          <button class="secondary-button" type="button" data-action="print-invoice">${icon("printer")} Print</button>
          <button class="primary-button" type="button" data-action="close-dialog">${icon("close")} Close</button>
        </div>
      </section>
    `;
  }

  async function withSubmitLock(form, action) {
    const button = form.querySelector('button[type="submit"]');
    const original = button ? button.innerHTML : "";
    if (button) {
      button.disabled = true;
      button.innerHTML = `${icon("clock")} Working`;
    }
    try {
      await action();
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        renderAuth();
      }
      toast("error", "Request failed", error.message);
    } finally {
      if (button) {
        button.disabled = false;
        button.innerHTML = original;
      }
    }
  }

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    event.preventDefault();

    const handlers = {
      "admin-login-form": () => handleAdminLogin(form),
      "parent-login-form": () => handleParentLogin(form),
      "student-create-form": () => handleStudentCreate(form),
      "fee-structure-form": () => handleFeeStructure(form),
      "concession-form": () => handleConcession(form),
      "offline-payment-form": () => handleOfflinePayment(form),
      "confirm-online-form": () => handleConfirmOnline(form),
      "parent-payment-form": () => handleParentPayment(form),
      "admin-search-form": async () => {
        state.admin.search = form.search.value.trim();
        await searchAdminStudents();
        renderAdmin();
      }
    };

    const handler = handlers[form.id];
    if (handler) withSubmitLock(form, handler);
  });

  document.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action]");
    if (!target) return;

    const action = target.dataset.action;
    if (action === "set-auth-mode") {
      state.authMode = target.dataset.mode || "admin";
      renderAuth();
      return;
    }

    if (action === "fill-demo") {
      if (target.dataset.demo === "admin") {
        document.getElementById("admin-email").value = "admin@school.com";
        document.getElementById("admin-password").value = "Admin@12345";
      } else {
        document.getElementById("parent-roll").value = "S0001";
        document.getElementById("parent-dob").value = "2010-05-15";
        document.getElementById("parent-aadhaar").value = "123412341234";
      }
      return;
    }

    if (action === "logout") {
      clearSession();
      renderAuth();
      toast("info", "Signed out", "Session cleared.");
      return;
    }

    if (action === "close-dialog") {
      invoiceDialog.close();
      return;
    }

    if (action === "print-invoice") {
      window.print();
      return;
    }

    if (action === "nav") {
      const role = target.dataset.role;
      const section = target.dataset.section;
      if (role === "admin") {
        state.admin.active = section || "overview";
        renderAdmin();
      } else {
        state.parent.active = section || "overview";
        renderParent();
      }
      return;
    }

    if (action === "select-parent-head") {
      state.parent.selectedHead = target.dataset.head || "term1";
      renderParent();
      return;
    }

    if (action === "fill-confirm") {
      state.admin.active = "payments";
      renderAdmin();
      window.requestAnimationFrame(() => {
        const input = document.getElementById("confirm-payment-id");
        if (input) input.value = target.dataset.id || "";
      });
      return;
    }

    runClickAction(action, target).catch((error) => {
      if (error.status === 401) {
        clearSession();
        renderAuth();
      }
      toast("error", "Request failed", error.message);
    });
  });

  async function runClickAction(action, target) {
    if (action === "select-student") {
      const studentId = Number(target.dataset.id);
      const student = state.admin.students.find((item) => item.id === studentId) || await apiFetch(`/admin/students/${studentId}`);
      state.admin.selectedStudent = student;
      await loadAdminStudentContext();
      renderAdmin();
      return;
    }

    if (action === "admin-refresh") {
      await loadAdminData();
      renderAdmin();
      toast("success", "Refreshed", "Admin data updated.");
      return;
    }

    if (action === "parent-refresh") {
      await loadParentData();
      renderParent();
      toast("success", "Refreshed", "Parent data updated.");
      return;
    }

    if (action === "admin-invoice") {
      await openAdminInvoice(target.dataset.id);
      return;
    }

    if (action === "parent-invoice") {
      await openParentInvoice(target.dataset.id);
    }
  }

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (target.id === "admin-student-search") {
      state.admin.search = target.value;
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(async () => {
        try {
          await searchAdminStudents();
          renderAdmin();
        } catch (error) {
          toast("error", "Search failed", error.message);
        }
      }, 260);
    }
  });

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) && !(target instanceof HTMLSelectElement)) return;

    const run = async () => {
      if (target.id === "admin-year") {
        state.admin.year = target.value.trim();
        localStorage.setItem(STORE.year, state.admin.year);
        await loadAdminStudentContext();
        renderAdmin();
        return;
      }

      if (target.id === "parent-year") {
        state.parent.year = target.value.trim();
        localStorage.setItem(STORE.year, state.parent.year);
        await loadParentData();
        renderParent();
        return;
      }

      if (target.id === "admin-payment-status") {
        state.admin.paymentStatus = target.value;
        await loadAdminStudentContext();
        renderAdmin();
      }
    };

    run().catch((error) => toast("error", "Update failed", error.message));
  });

  async function start() {
    if (!state.token || !state.role) {
      renderAuth();
      return;
    }

    try {
      if (state.role === "admin") {
        await bootstrapAdmin();
      } else {
        await bootstrapParent();
      }
    } catch (error) {
      clearSession();
      renderAuth();
      toast("error", "Session expired", error.message);
    }
  }

  start();
})();
