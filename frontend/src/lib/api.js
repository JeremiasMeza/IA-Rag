
// API helper para el frontend
export const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function _checkResponse(res) {
  if (res.ok) {
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      return res.json().catch(() => ({}));
    } else {
      return res.text();
    }
  }
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

export async function chat({ message, model, session_id, answer_mode, locale, max_tokens, score_threshold } = {}) {
  const body = { message, session_id };
  if (model) body.model = model;
  if (answer_mode) body.answer_mode = answer_mode;
  if (locale) body.locale = locale;
  if (max_tokens) body.max_tokens = max_tokens;
  if (score_threshold !== undefined) body.score_threshold = score_threshold;
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

