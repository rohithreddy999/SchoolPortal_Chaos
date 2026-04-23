import { useState } from "react";

const initialFilters = {
  admission_number: "",
  academic_year: "",
  student_name: "",
  class_name: ""
};

export function emptySearchFilters() {
  return { ...initialFilters };
}

function formatUpdatedDate(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric"
  }).format(parsed);
}

export default function StudentSearch({
  filters,
  onFilterChange,
  onSearch,
  onSelect,
  results,
  hasSearched,
  loading,
  selectedStudentId
}) {
  const [isOpen, setIsOpen] = useState(true);

  function handleChange(event) {
    const { name, value } = event.target;
    onFilterChange({ ...filters, [name]: value });
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSearch();
  }

  return (
    <section className="panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Search</p>
          <h2>Student ledger lookup</h2>
          <p className="panel-note">
            {results.length > 0
              ? `${results.length} record${results.length === 1 ? "" : "s"} ready to inspect.`
              : hasSearched
                ? "No student matched the search you entered."
                : "Search by admission number, academic year, student name, or class."}
          </p>
        </div>
        <button type="button" className="section-toggle" onClick={() => setIsOpen((current) => !current)}>
          {isOpen ? "Hide search" : "Open search"}
        </button>
      </div>

      {isOpen ? (
        <>
          <form className="search-grid" onSubmit={handleSubmit}>
            <label>
              Admission Number
              <input
                name="admission_number"
                value={filters.admission_number}
                onChange={handleChange}
                placeholder="Example: ADM-2025-014"
              />
            </label>

            <label>
              Academic Year
              <input
                name="academic_year"
                value={filters.academic_year}
                onChange={handleChange}
                placeholder="Example: 2026-2027"
              />
            </label>

            <label>
              Student Name
              <input
                name="student_name"
                value={filters.student_name}
                onChange={handleChange}
                placeholder="Partial name"
              />
            </label>

            <label>
              Class
              <input name="class_name" value={filters.class_name} onChange={handleChange} placeholder="Class" />
            </label>

            <button type="submit" className="secondary-button" disabled={loading}>
              {loading ? "Searching..." : "Search records"}
            </button>
          </form>

          <div className="results-list">
            {results.length === 0 ? (
              <p className="muted-text">
                {hasSearched
                  ? "No such student found for the entered search."
                  : "Search for a student to load matching records here."}
              </p>
            ) : null}

            {results.map((student) => (
              <button
                key={student.id}
                type="button"
                className={`result-card ${selectedStudentId === student.id ? "active" : ""}`}
                onClick={() => onSelect(student)}
              >
                <div>
                  <strong>{student.student_name}</strong>
                  <span>
                    {student.class_name} - {student.section}
                  </span>
                </div>
                <div>
                  <span>{student.admission_number}</span>
                  <span>{student.academic_year}</span>
                  <small>Updated {formatUpdatedDate(student.updated_at)}</small>
                </div>
              </button>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}
