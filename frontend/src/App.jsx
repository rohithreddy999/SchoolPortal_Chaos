import { useEffect, useState } from "react";
import LoginForm from "./components/LoginForm";
import StudentDetails from "./components/StudentDetails";
import StudentForm from "./components/StudentForm";
import StudentSearch, { emptySearchFilters } from "./components/StudentSearch";
import {
  createStudent,
  downloadStudentStatement,
  getCurrentUser,
  getStudent,
  login,
  recordPayment,
  searchStudents,
  updateStudent
} from "./lib/api";
import { PORTAL_NAME, PORTAL_TAGLINE, SCHOOL_NAME } from "./lib/branding";

const SESSION_KEY = "school-portal-session";

function loadSession() {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveSession(session) {
  if (!session) {
    window.localStorage.removeItem(SESSION_KEY);
    return;
  }
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function normalizeStudentPayload(form) {
  return {
    ...form,
    admission_fee: Number(form.admission_fee || 0),
    first_term_fee: Number(form.first_term_fee || 0),
    second_term_fee: Number(form.second_term_fee || 0),
    third_term_fee: Number(form.third_term_fee || 0),
    transport_fee: Number(form.transport_fee || 0),
    books_fee: Number(form.books_fee || 0),
    concession_transport: Number(form.concession_transport || 0)
  };
}

function toStudentListItem(student) {
  return {
    id: student.id,
    academic_year: student.academic_year,
    admission_number: student.admission_number,
    student_name: student.student_name,
    class_name: student.class_name,
    section: student.section,
    mobile_number: student.mobile_number,
    updated_at: student.updated_at
  };
}

function upsertStudent(results, student) {
  const nextItem = toStudentListItem(student);
  const otherStudents = results.filter((item) => item.id !== nextItem.id);
  return [nextItem, ...otherStudents].sort((left, right) => left.student_name.localeCompare(right.student_name));
}

export default function App() {
  const [session, setSession] = useState(loadSession);
  const [user, setUser] = useState(loadSession()?.user || null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [searchFilters, setSearchFilters] = useState(emptySearchFilters);
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [activeStudentId, setActiveStudentId] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentLoading, setStudentLoading] = useState(false);
  const [studentLoadError, setStudentLoadError] = useState("");
  const [studentFormMode, setStudentFormMode] = useState(null);
  const [saveError, setSaveError] = useState("");
  const [savingStudent, setSavingStudent] = useState(false);
  const [paymentError, setPaymentError] = useState("");
  const [savingPayment, setSavingPayment] = useState(false);

  useEffect(() => {
    if (!session?.token) {
      return;
    }

    let ignore = false;
    getCurrentUser(session.token)
      .then((currentUser) => {
        if (!ignore) {
          setUser(currentUser);
        }
      })
      .catch(() => {
        if (!ignore) {
          handleLogout();
        }
      });

    return () => {
      ignore = true;
    };
  }, [session?.token]);

  useEffect(() => {
    if (!session?.token) {
      return;
    }
    handleSearch(searchFilters);
  }, [session?.token]);

  async function handleLogin(credentials) {
    setAuthLoading(true);
    setAuthError("");
    try {
      const result = await login(credentials);
      const nextSession = { token: result.access_token, user: result.user };
      setSession(nextSession);
      setUser(result.user);
      saveSession(nextSession);
    } catch (error) {
      setAuthError(error.message);
    } finally {
      setAuthLoading(false);
    }
  }

  function handleLogout() {
    setSession(null);
    setUser(null);
    setActiveStudentId(null);
    setSelectedStudent(null);
    setStudentLoadError("");
    setStudentFormMode(null);
    setSearchResults([]);
    saveSession(null);
  }

  async function handleSearch(filters = searchFilters) {
    if (!session?.token) {
      return;
    }

    setSearchLoading(true);
    try {
      const students = await searchStudents(session.token, filters);
      setSearchResults(students);
    } finally {
      setSearchLoading(false);
    }
  }

  async function handleStudentSave(form) {
    if (!session?.token) {
      return;
    }

    const isEditMode = studentFormMode === "edit" && selectedStudent;
    setSavingStudent(true);
    setSaveError("");
    try {
      const payload = normalizeStudentPayload(form);
      const student = isEditMode
        ? await updateStudent(session.token, selectedStudent.id, payload)
        : await createStudent(session.token, payload);
      setActiveStudentId(student.id);
      setSelectedStudent(student);
      setStudentFormMode(null);
      setSearchResults((current) => upsertStudent(current, student));
    } catch (error) {
      setSaveError(error.message);
    } finally {
      setSavingStudent(false);
    }
  }

  async function handleRecordPayment(payload) {
    if (!session?.token || !selectedStudent) {
      return;
    }

    if (payload.allocations.length === 0) {
      setPaymentError("Enter at least one component amount before saving the payment.");
      return;
    }

    setStudentLoadError("");
    setSavingPayment(true);
    setPaymentError("");
    try {
      const student = await recordPayment(session.token, selectedStudent.id, payload);
      setActiveStudentId(student.id);
      setSelectedStudent(student);
      setSearchResults((current) => upsertStudent(current, student));
    } catch (error) {
      setPaymentError(error.message);
    } finally {
      setSavingPayment(false);
    }
  }

  async function handleDownloadStatement() {
    if (!session?.token || !selectedStudent) {
      return;
    }

    const { blob, filename } = await downloadStudentStatement(session.token, selectedStudent.id);
    const objectUrl = window.URL.createObjectURL(blob);
    const link = window.document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    window.document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 0);
  }

  async function handleSelectStudent(student) {
    if (!session?.token) {
      return;
    }

    setActiveStudentId(student.id);
    if (selectedStudent?.id !== student.id) {
      setSelectedStudent(null);
    }
    setStudentLoading(true);
    setStudentLoadError("");
    setSaveError("");
    setPaymentError("");
    setStudentFormMode(null);
    try {
      const fullStudent = await getStudent(session.token, student.id);
      setSelectedStudent(fullStudent);
    } catch (error) {
      setSelectedStudent(null);
      setStudentLoadError(error.message);
    } finally {
      setStudentLoading(false);
    }
  }

  function handleOpenCreateForm() {
    setSaveError("");
    setStudentFormMode("create");
  }

  function handleOpenEditForm() {
    if (!selectedStudent) {
      return;
    }
    setSaveError("");
    setStudentFormMode("edit");
  }

  function handleCloseStudentForm() {
    setSaveError("");
    setStudentFormMode(null);
  }

  if (!session?.token) {
    return <LoginForm onSubmit={handleLogin} loading={authLoading} error={authError} />;
  }

  const formStudent = studentFormMode === "edit" ? selectedStudent : null;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="school-seal">SSHS</div>
          <div>
            <p className="eyebrow">{SCHOOL_NAME}</p>
            <h1>{PORTAL_NAME}</h1>
            <p className="panel-note">{PORTAL_TAGLINE}</p>
          </div>
        </div>
        <div className="topbar-actions">
          <div className="user-chip">
            <span>Signed in as</span>
            <strong>{user?.username}</strong>
          </div>
          <button type="button" className="ghost-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-grid">
        <div className="left-column">
          <section className="panel workspace-panel">
            <div>
              <p className="eyebrow">Workspace</p>
              <h2>{selectedStudent ? `Selected: ${selectedStudent.student_name}` : "Admissions and payment records"}</h2>
              <p className="panel-note">
                {selectedStudent
                  ? "Review balances, inspect the full payment trail, or update the official student fee profile."
                  : "Search for an existing student or open a new admission record when fee details are entered."}
              </p>
            </div>
            <div className="workspace-actions">
              <button type="button" className="primary-button" onClick={handleOpenCreateForm}>
                Create Student
              </button>
              <button
                type="button"
                className="ghost-button"
                onClick={handleOpenEditForm}
                disabled={!selectedStudent}
              >
                Edit Selected
              </button>
            </div>
          </section>

          <StudentSearch
            filters={searchFilters}
            onFilterChange={setSearchFilters}
            onSearch={() => handleSearch(searchFilters)}
            onSelect={handleSelectStudent}
            results={searchResults}
            loading={searchLoading}
            selectedStudentId={activeStudentId}
          />
          {studentFormMode ? (
            <StudentForm
              mode={studentFormMode}
              student={formStudent}
              onSave={handleStudentSave}
              saving={savingStudent}
              error={saveError}
              onClose={handleCloseStudentForm}
            />
          ) : null}
        </div>

        <StudentDetails
          student={selectedStudent}
          loading={studentLoading}
          loadError={studentLoadError}
          onRecordPayment={handleRecordPayment}
          onDownloadStatement={handleDownloadStatement}
          savingPayment={savingPayment}
          error={paymentError}
          onEditStudent={handleOpenEditForm}
        />
      </main>
    </div>
  );
}
