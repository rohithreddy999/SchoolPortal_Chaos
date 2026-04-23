const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, { method = "GET", token, body } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });

  if (!response.ok) {
    let message = "Something went wrong";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json();
}

function getErrorMessageFromResponse(response) {
  return response
    .clone()
    .json()
    .then((data) => data.detail || "Something went wrong")
    .catch(() => response.statusText || "Something went wrong");
}

async function downloadFile(path, token, fallbackFilename) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  });

  if (!response.ok) {
    throw new Error(await getErrorMessageFromResponse(response));
  }

  const disposition = response.headers.get("Content-Disposition") || "";
  const matchedFileName = disposition.match(/filename="([^"]+)"/i);
  return {
    blob: await response.blob(),
    filename: matchedFileName?.[1] || fallbackFilename
  };
}

export function login(credentials) {
  return request("/auth/login", { method: "POST", body: credentials });
}

export function getCurrentUser(token) {
  return request("/auth/me", { token });
}

export function searchStudents(token, filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });

  const query = params.toString();
  return request(`/students${query ? `?${query}` : ""}`, { token });
}

export function getStudent(token, id) {
  return request(`/students/${id}`, { token });
}

export function createStudent(token, payload) {
  return request("/students", { method: "POST", token, body: payload });
}

export function updateStudent(token, id, payload) {
  return request(`/students/${id}`, { method: "PUT", token, body: payload });
}

export function recordPayment(token, id, payload) {
  return request(`/students/${id}/payments`, { method: "POST", token, body: payload });
}

export async function downloadStudentStatement(token, id) {
  return downloadFile(`/students/${id}/statement.pdf`, token, `student_${id}_statement.pdf`);
}

export function downloadPaymentReceipt(token, studentId, transactionId) {
  return downloadFile(
    `/students/${studentId}/payments/${transactionId}/receipt.pdf`,
    token,
    `payment_${transactionId}_receipt.pdf`
  );
}

export function downloadStudentPaymentHistory(token, studentId) {
  return downloadFile(`/students/${studentId}/payment-history.pdf`, token, `student_${studentId}_payment_history.pdf`);
}
