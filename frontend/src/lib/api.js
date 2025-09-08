
// API helper para el frontend
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function _checkResponse(res) {
  if (res.ok) return res.json().catch(() => ({}));
  const text = await res.text().catch(() => "");
  let msg = `HTTP ${res.status}`;
  try {
    const j = JSON.parse(text);
    msg = j.detail || j.error || j.message || JSON.stringify(j);
  } catch (err) {
    void err;
    if (text) msg = text;
  }
  throw new Error(msg);
}

export async function chat({ message, model, session_id } = {}) {
  const body = { message, session_id };
  if (model) body.model = model;
  const r = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return _checkResponse(r);
}

export async function uploadPdf({ file, session_id }) {
  if (!file) throw new Error("No file provided");
  const fd = new FormData();
  fd.append("session_id", session_id);
  fd.append("file", file, file.name);
  const r = await fetch(`${API}/upload_pdf`, {
    method: "POST",
    body: fd,
  });
  return _checkResponse(r);
}
