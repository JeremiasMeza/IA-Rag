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

export async function chat({
  message,
  model,
  client_id,
  conversation_id,
  mode,
} = {}) {
  const body = { message };
  if (model) body.model = model;
  if (client_id) body.client_id = client_id;
  if (conversation_id) body.conversation_id = conversation_id;
  if (mode) body.mode = mode;

  const r = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  return _checkResponse(r);
}

export async function uploadDoc({ file, client_id }) {
  if (!file) throw new Error("No file provided");
  const fd = new FormData();
  fd.append("client_id", client_id || "default");
  fd.append("file", file, file.name);

  const r = await fetch(`${API}/documents`, {
    method: "POST",
    body: fd,
  });

  return _checkResponse(r);
}

export async function deleteByClient({ client_id, adminToken }) {
  const r = await fetch(`${API}/documents?client_id=${encodeURIComponent(client_id)}`, {
    method: "DELETE",
    headers: { "x-admin-token": adminToken ?? "" },
  });
  return _checkResponse(r);
}

export async function deleteAll({ adminToken }) {
  const r = await fetch(`${API}/documents/all`, {
    method: "DELETE",
    headers: { "x-admin-token": adminToken ?? "" },
  });
  return _checkResponse(r);
}
