import { useEffect, useMemo, useRef, useState } from "react";

const blankStudent = {
  academic_year: "",
  admission_number: "",
  student_name: "",
  father_name: "",
  mother_name: "",
  mobile_number: "",
  class_name: "",
  section: "",
  student_aadhaar: "",
  father_aadhaar: "",
  student_identifier: "",
  pen_number: "",
  admission_fee: "0",
  first_term_fee: "0",
  second_term_fee: "0",
  third_term_fee: "0",
  transport_fee: "0",
  books_fee: "0",
  concession_transport: "0"
};

const feeFields = [
  ["admission_fee", "Admission Fee"],
  ["first_term_fee", "First Term Fee"],
  ["second_term_fee", "Second Term Fee"],
  ["third_term_fee", "Third Term Fee"],
  ["transport_fee", "Transport Fee"],
  ["books_fee", "Books Fee"],
  ["concession_transport", "Transport Concession"]
];

const digitFieldLengths = {
  mobile_number: 10,
  student_aadhaar: 12,
  father_aadhaar: 12
};

function toFormValue(student) {
  if (!student) {
    return blankStudent;
  }

  return {
    academic_year: student.academic_year || "",
    admission_number: student.admission_number || "",
    student_name: student.student_name || "",
    father_name: student.father_name || "",
    mother_name: student.mother_name || "",
    mobile_number: student.mobile_number || "",
    class_name: student.class_name || "",
    section: student.section || "",
    student_aadhaar: student.student_aadhaar || "",
    father_aadhaar: student.father_aadhaar || "",
    student_identifier: student.student_identifier || "",
    pen_number: student.pen_number || "",
    admission_fee: String(student.admission_fee ?? "0"),
    first_term_fee: String(student.first_term_fee ?? "0"),
    second_term_fee: String(student.second_term_fee ?? "0"),
    third_term_fee: String(student.third_term_fee ?? "0"),
    transport_fee: String(student.transport_fee ?? "0"),
    books_fee: String(student.books_fee ?? "0"),
    concession_transport: String(student.concession_transport ?? "0")
  };
}

function toNumber(value) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export default function StudentForm({ mode, student, onSave, saving, error, onClose, scrollRequestKey }) {
  const [form, setForm] = useState(blankStudent);
  const [localError, setLocalError] = useState("");
  const formRef = useRef(null);

  useEffect(() => {
    setForm(toFormValue(student));
    setLocalError("");
  }, [mode, student]);

  useEffect(() => {
    if (!scrollRequestKey) {
      return;
    }

    window.requestAnimationFrame(() => {
      formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, [scrollRequestKey]);

  function handleChange(event) {
    const { name, value } = event.target;
    setLocalError("");
    if (digitFieldLengths[name]) {
      const digitsOnly = value.replace(/\D/g, "").slice(0, digitFieldLengths[name]);
      setForm((current) => ({ ...current, [name]: digitsOnly }));
      return;
    }
    setForm((current) => ({ ...current, [name]: value }));
  }

  const totals = useMemo(() => {
    const totalFee =
      toNumber(form.admission_fee) +
      toNumber(form.first_term_fee) +
      toNumber(form.second_term_fee) +
      toNumber(form.third_term_fee) +
      toNumber(form.transport_fee) +
      toNumber(form.books_fee);
    const adjustedTotal = Math.max(0, totalFee - toNumber(form.concession_transport));
    return {
      totalFee,
      adjustedTotal
    };
  }, [form]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (form.student_aadhaar && form.father_aadhaar && form.student_aadhaar === form.father_aadhaar) {
      setLocalError("Student Aadhaar and Father's Aadhaar cannot be the same.");
      return;
    }

    setLocalError("");
    await onSave(form);
  }

  const isEditMode = mode === "edit" && student;

  return (
    <section className="panel form-panel" ref={formRef}>
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">{isEditMode ? "Edit student" : "New student"}</p>
          <h2>{isEditMode ? student.student_name : "Create student record"}</h2>
          <p className="panel-note">
            {isEditMode
              ? "Update academic, identity, and fee setup details for the selected student."
              : "Open the admission form only when you need it, complete the record, then close it again."}
          </p>
        </div>
        <button type="button" className="section-toggle" onClick={onClose}>
          Close form
        </button>
      </div>

      <form className="student-form" onSubmit={handleSubmit}>
        <div className="form-section">
          <h3>Student details</h3>
          <div className="form-grid">
            <label>
              Academic Year
              <input name="academic_year" value={form.academic_year} onChange={handleChange} required />
            </label>
            <label>
              Admission Number
              <input name="admission_number" value={form.admission_number} onChange={handleChange} required />
            </label>
            <label>
              Student Name
              <input name="student_name" value={form.student_name} onChange={handleChange} required />
            </label>
            <label>
              Father's Name
              <input name="father_name" value={form.father_name} onChange={handleChange} required />
            </label>
            <label>
              Mother's Name
              <input name="mother_name" value={form.mother_name} onChange={handleChange} />
            </label>
            <label>
              Mobile Number
              <input
                name="mobile_number"
                value={form.mobile_number}
                onChange={handleChange}
                inputMode="numeric"
                minLength={10}
                maxLength={10}
                pattern="[0-9]{10}"
                placeholder="10-digit mobile number"
                required
              />
            </label>
            <label>
              Class
              <input name="class_name" value={form.class_name} onChange={handleChange} required />
            </label>
            <label>
              Section
              <input name="section" value={form.section} onChange={handleChange} required />
            </label>
            <label>
              Student Aadhaar
              <input
                name="student_aadhaar"
                value={form.student_aadhaar}
                onChange={handleChange}
                inputMode="numeric"
                minLength={12}
                maxLength={12}
                pattern="[0-9]{12}"
                placeholder="12-digit Aadhaar"
              />
            </label>
            <label>
              Father's Aadhaar
              <input
                name="father_aadhaar"
                value={form.father_aadhaar}
                onChange={handleChange}
                inputMode="numeric"
                minLength={12}
                maxLength={12}
                pattern="[0-9]{12}"
                placeholder="12-digit Aadhaar"
              />
            </label>
            <label>
              Student ID
              <input name="student_identifier" value={form.student_identifier} onChange={handleChange} />
            </label>
            <label>
              PEN Number
              <input name="pen_number" value={form.pen_number} onChange={handleChange} />
            </label>
          </div>
        </div>

        <div className="form-section">
          <h3>Fee setup</h3>
          <div className="form-grid">
            {feeFields.map(([name, label]) => (
              <label key={name}>
                {label}
                <input name={name} type="number" min="0" step="0.01" value={form[name]} onChange={handleChange} required />
              </label>
            ))}
          </div>

          <div className="totals-strip">
            <div>
              <span>Total Fee</span>
              <strong>Rs. {totals.totalFee.toFixed(2)}</strong>
            </div>
            <div>
              <span>Adjusted Total</span>
              <strong>Rs. {totals.adjustedTotal.toFixed(2)}</strong>
            </div>
          </div>
        </div>

        {localError || error ? <div className="error-banner">{localError || error}</div> : null}

        <button type="submit" className="primary-button" disabled={saving}>
          {saving ? "Saving..." : isEditMode ? "Update Student" : "Create Student"}
        </button>
      </form>
    </section>
  );
}
