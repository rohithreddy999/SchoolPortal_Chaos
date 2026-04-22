import { useEffect, useMemo, useState } from "react";
import { SCHOOL_NAME } from "../lib/branding";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2
});
const shortDate = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric"
});
const dateTime = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit"
});

const today = new Date().toISOString().slice(0, 10);

function formatCurrency(value) {
  return currency.format(Number(value || 0));
}

function maskIdentifier(value, visibleDigits = 4) {
  if (!value) {
    return "-";
  }

  const text = String(value);
  if (text.length <= visibleDigits) {
    return text;
  }

  return `${"•".repeat(Math.max(0, text.length - visibleDigits))}${text.slice(-visibleDigits)}`;
}

function formatDate(value, formatter = shortDate) {
  if (!value) {
    return "-";
  }

  const text = String(value);
  const parsed = text.includes("T") ? new Date(text) : new Date(`${text}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) {
    return text;
  }

  return formatter.format(parsed);
}

function formatComponentName(value) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getTransactionTotal(transaction) {
  return transaction.allocations.reduce((sum, allocation) => sum + Number(allocation.amount || 0), 0);
}

function makePaymentState(student) {
  const base = {
    received_on: today,
    note: ""
  };

  if (!student) {
    return base;
  }

  student.fee_summary.components.forEach((component) => {
    base[component.component] = "";
  });
  return base;
}

export default function StudentDetails({
  student,
  loading,
  loadError,
  onRecordPayment,
  onDownloadStatement,
  savingPayment,
  error,
  onEditStudent
}) {
  const [paymentForm, setPaymentForm] = useState(makePaymentState(student));
  const [showFeeSummary, setShowFeeSummary] = useState(true);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const [selectedTransactionId, setSelectedTransactionId] = useState(null);
  const [statementError, setStatementError] = useState("");
  const [downloadingStatement, setDownloadingStatement] = useState(false);

  useEffect(() => {
    setPaymentForm(makePaymentState(student));
    setSelectedTransactionId(student?.payment_transactions[0]?.id ?? null);
    setShowPaymentForm(false);
    setStatementError("");
  }, [student]);

  useEffect(() => {
    if (error) {
      setShowPaymentForm(true);
    }
  }, [error]);

  const componentBalances = useMemo(() => {
    const map = {};
    if (!student) {
      return map;
    }
    student.fee_summary.components.forEach((component) => {
      map[component.component] = Number(component.balance);
    });
    return map;
  }, [student]);

  const selectedTransaction = useMemo(() => {
    if (!student || student.payment_transactions.length === 0) {
      return null;
    }

    return (
      student.payment_transactions.find((transaction) => transaction.id === selectedTransactionId) ??
      student.payment_transactions[0]
    );
  }, [selectedTransactionId, student]);

  if (loading) {
    return (
      <section className="panel detail-panel empty-state">
        <p className="eyebrow">Student details</p>
        <h2>Loading student record</h2>
        <p className="muted-text">Fetching fee summary, balances, and payment history for the selected student.</p>
      </section>
    );
  }

  if (loadError && !student) {
    return (
      <section className="panel detail-panel empty-state">
        <p className="eyebrow">Student details</p>
        <h2>Could not load the selected record</h2>
        <div className="error-banner">{loadError}</div>
      </section>
    );
  }

  if (!student) {
    return (
      <section className="panel detail-panel empty-state">
        <p className="eyebrow">Student details</p>
        <h2>Select a student record</h2>
        <p className="muted-text">
          The selected student will appear here with fee balances and offline payment entry.
        </p>
      </section>
    );
  }

  const latestPayment = student.payment_transactions[0];

  function handleChange(event) {
    const { name, value } = event.target;
    setPaymentForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const allocations = student.fee_summary.components
      .map((component) => ({
        component: component.component,
        amount: Number(paymentForm[component.component] || 0)
      }))
      .filter((item) => item.amount > 0);

    await onRecordPayment({
      received_on: paymentForm.received_on,
      note: paymentForm.note,
      allocations
    });
  }

  async function handleStatementDownload() {
    setStatementError("");
    setDownloadingStatement(true);
    try {
      await onDownloadStatement();
    } catch (downloadError) {
      setStatementError(downloadError.message);
    } finally {
      setDownloadingStatement(false);
    }
  }

  return (
    <section className="panel detail-panel">
      <div className="student-banner">
        <div className="student-banner-copy">
          <p className="eyebrow">Student details</p>
          <h2>{student.student_name}</h2>
          <p className="muted-text">
            Admission No. {student.admission_number} | {student.academic_year} | {student.class_name} - {student.section}
          </p>
          <p className="section-note">{SCHOOL_NAME} official fee ledger and offline receipt record.</p>
        </div>
        <div className="student-banner-side">
          <div className="pending-plaque">
            <span>Current pending</span>
            <strong>{formatCurrency(student.fee_summary.total_pending)}</strong>
            <small>Updated after every receipt entry</small>
          </div>
          <div className="detail-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => setShowPaymentForm((current) => !current)}
            >
              {showPaymentForm ? "Hide payment form" : "Record Payment"}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={handleStatementDownload}
              disabled={downloadingStatement}
            >
              {downloadingStatement ? "Generating PDF..." : "Generate PDF"}
            </button>
            <button type="button" className="ghost-button" onClick={onEditStudent}>
              Edit Student
            </button>
          </div>
        </div>
      </div>

      {statementError ? <div className="error-banner">{statementError}</div> : null}

      <div className="student-chip-row">
        <div className="student-chip">
          <span>Academic year</span>
          <strong>{student.academic_year}</strong>
        </div>
        <div className="student-chip">
          <span>Admission number</span>
          <strong>{student.admission_number}</strong>
        </div>
        <div className="student-chip">
          <span>Class and section</span>
          <strong>
            {student.class_name} - {student.section}
          </strong>
        </div>
        <div className="student-chip">
          <span>Receipts recorded</span>
          <strong>{student.payment_transactions.length}</strong>
        </div>
      </div>

      <div className="identity-grid">
        <div>
          <span>Father</span>
          <strong>{student.father_name}</strong>
        </div>
        <div>
          <span>Mother</span>
          <strong>{student.mother_name || "-"}</strong>
        </div>
        <div>
          <span>Mobile</span>
          <strong>{student.mobile_number}</strong>
        </div>
        <div>
          <span>Student ID</span>
          <strong>{student.student_identifier || "-"}</strong>
        </div>
        <div>
          <span>PEN Number</span>
          <strong>{student.pen_number || "-"}</strong>
        </div>
        <div>
          <span>Student Aadhaar</span>
          <strong>{maskIdentifier(student.student_aadhaar)}</strong>
        </div>
        <div>
          <span>Father's Aadhaar</span>
          <strong>{maskIdentifier(student.father_aadhaar)}</strong>
        </div>
      </div>

      <div className="summary-grid">
        <div className="metric-card">
          <span>Total Fee</span>
          <strong>{formatCurrency(student.fee_summary.total_fee)}</strong>
        </div>
        <div className="metric-card">
          <span>Transport Concession</span>
          <strong>{formatCurrency(student.fee_summary.concession_transport)}</strong>
        </div>
        <div className="metric-card">
          <span>Adjusted Total</span>
          <strong>{formatCurrency(student.fee_summary.adjusted_total)}</strong>
        </div>
        <div className="metric-card">
          <span>Total Paid</span>
          <strong>{formatCurrency(student.fee_summary.total_paid)}</strong>
        </div>
        <div className="metric-card alert">
          <span>Pending Amount</span>
          <strong>{formatCurrency(student.fee_summary.total_pending)}</strong>
        </div>
        <div className="metric-card">
          <span>Last Payment</span>
          <strong>{latestPayment ? formatDate(latestPayment.received_on) : "Not recorded"}</strong>
        </div>
      </div>

      <section className="section-card">
        <div className="section-header">
          <div>
            <h3>Fee breakdown</h3>
            <p className="section-note">Every component shows assessed amount, received amount, and the current balance.</p>
          </div>
          <button type="button" className="section-toggle" onClick={() => setShowFeeSummary((current) => !current)}>
            {showFeeSummary ? "Hide details" : "Show details"}
          </button>
        </div>

        {showFeeSummary ? (
          <div className="component-table">
            <div className="component-table-header">
              <span>Component</span>
              <span>Assessed</span>
              <span>Paid</span>
              <span>Balance</span>
            </div>
            {student.fee_summary.components.map((component) => (
              <div key={component.component} className="component-table-row">
                <span>{component.label}</span>
                <span>{formatCurrency(component.assessed)}</span>
                <span>{formatCurrency(component.paid)}</span>
                <span>{formatCurrency(component.balance)}</span>
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section className="section-card">
        <div className="section-header">
          <div>
            <h3>Record offline payment</h3>
            <p className="section-note">
              Open this section only when a parent payment is received and assign the amount to one or more fee heads.
            </p>
          </div>
          <button type="button" className="section-toggle" onClick={() => setShowPaymentForm((current) => !current)}>
            {showPaymentForm ? "Hide payment" : "Open payment"}
          </button>
        </div>

        {showPaymentForm ? (
          <form className="payment-form" onSubmit={handleSubmit}>
            <div className="form-section">
              <div className="form-grid compact">
                <label>
                  Payment Date
                  <input name="received_on" type="date" value={paymentForm.received_on} onChange={handleChange} required />
                </label>
                <label className="full-width">
                  Note
                  <input
                    name="note"
                    value={paymentForm.note}
                    onChange={handleChange}
                    placeholder="Optional note, receipt reference, or parent remark"
                  />
                </label>
              </div>

              <div className="allocation-grid">
                {student.fee_summary.components.map((component) => (
                  <label key={component.component} className="allocation-card">
                    <span>{component.label}</span>
                    <small>Remaining {formatCurrency(component.balance)}</small>
                    <input
                      name={component.component}
                      type="number"
                      min="0"
                      max={componentBalances[component.component]}
                      step="0.01"
                      value={paymentForm[component.component] || ""}
                      onChange={handleChange}
                      disabled={componentBalances[component.component] <= 0}
                      placeholder="0.00"
                    />
                  </label>
                ))}
              </div>
            </div>

            {error ? <div className="error-banner">{error}</div> : null}

            <button type="submit" className="primary-button" disabled={savingPayment}>
              {savingPayment ? "Saving payment..." : "Save Payment"}
            </button>
          </form>
        ) : null}
      </section>

      <section className="section-card">
        <div className="section-header">
          <div>
            <h3>Payment history</h3>
            <p className="section-note">
              Select any past receipt to inspect its component-wise split, note, and total received amount.
            </p>
          </div>
          <button type="button" className="section-toggle" onClick={() => setShowHistory((current) => !current)}>
            {showHistory ? "Hide history" : "Show history"}
          </button>
        </div>

        {showHistory ? (
          student.payment_transactions.length === 0 ? (
            <p className="muted-text">No offline payments recorded yet.</p>
          ) : (
            <div className="history-layout">
              <div className="history-list">
                {student.payment_transactions.map((transaction) => (
                  <button
                    key={transaction.id}
                    type="button"
                    className={`history-item ${selectedTransaction?.id === transaction.id ? "active" : ""}`}
                    onClick={() => setSelectedTransactionId(transaction.id)}
                  >
                    <div className="history-topline">
                      <div className="history-heading-block">
                        <strong>{formatDate(transaction.received_on)}</strong>
                        <small>{transaction.receipt_number}</small>
                      </div>
                      <span>{formatCurrency(getTransactionTotal(transaction))}</span>
                    </div>
                    <p className="history-meta">
                      Recorded by {transaction.created_by_username || "Administrator"}
                    </p>
                    <div className="allocation-chip-row">
                      {transaction.allocations.map((allocation) => (
                        <span key={allocation.id} className="allocation-chip">
                          {formatComponentName(allocation.component)}: {formatCurrency(allocation.amount)}
                        </span>
                      ))}
                    </div>
                    <p>{transaction.note || "No note added."}</p>
                  </button>
                ))}
              </div>

              <aside className="history-detail-card">
                {selectedTransaction ? (
                  <>
                    <div className="history-detail-head">
                      <p className="eyebrow">Selected payment</p>
                      <h3>{selectedTransaction.receipt_number}</h3>
                    </div>

                    <div className="history-detail-grid">
                      <div>
                        <span>Receipt number</span>
                        <strong>{selectedTransaction.receipt_number}</strong>
                      </div>
                      <div>
                        <span>Received on</span>
                        <strong>{formatDate(selectedTransaction.received_on)}</strong>
                      </div>
                      <div>
                        <span>Recorded at</span>
                        <strong>{formatDate(selectedTransaction.created_at, dateTime)}</strong>
                      </div>
                      <div>
                        <span>Recorded by</span>
                        <strong>{selectedTransaction.created_by_username || "Administrator"}</strong>
                      </div>
                      <div>
                        <span>Total received</span>
                        <strong>{formatCurrency(getTransactionTotal(selectedTransaction))}</strong>
                      </div>
                      <div>
                        <span>Fee heads covered</span>
                        <strong>{selectedTransaction.allocations.length}</strong>
                      </div>
                    </div>

                    <div className="transaction-lines">
                      {selectedTransaction.allocations.map((allocation) => (
                        <div key={allocation.id} className="transaction-line">
                          <span>{formatComponentName(allocation.component)}</span>
                          <strong>{formatCurrency(allocation.amount)}</strong>
                        </div>
                      ))}
                    </div>

                    <div className="note-card">
                      <span>Note</span>
                      <p>{selectedTransaction.note || "No note added for this payment."}</p>
                    </div>
                  </>
                ) : (
                  <p className="muted-text">Select a payment entry to inspect the full receipt details.</p>
                )}
              </aside>
            </div>
          )
        ) : null}
      </section>
    </section>
  );
}
