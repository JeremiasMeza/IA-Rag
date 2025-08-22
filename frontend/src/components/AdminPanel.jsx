import { useState } from "react";
import { deleteByClient, deleteAll } from "../lib/api";

export default function AdminPanel({ clientId }) {
  const [token, setToken] = useState(import.meta.env.VITE_ADMIN_TOKEN || "");
  const [msg, setMsg] = useState("");

  const wipeClient = async () => {
    setMsg("");
    try {
      const res = await deleteByClient({ client_id: clientId, adminToken: token });
      setMsg(`OK: borrado cliente "${clientId}"`);
    } catch (e) {
      setMsg("Error: " + e.message);
    }
  };

  const wipeAll = async () => {
    setMsg("");
    try {
      const res = await deleteAll({ adminToken: token });
      setMsg("OK: reset total");
    } catch (e) {
      setMsg("Error: " + e.message);
    }
  };

  return (
    <div className="p-3 border rounded bg-white flex flex-col gap-2">
      <div className="grid sm:grid-cols-3 gap-2 items-end">
        <div className="sm:col-span-2">
          <label className="block text-sm font-medium">Admin token</label>
          <input
            type="password"
            className="mt-1 border rounded p-2 w-full"
            placeholder="x-admin-token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
          <p className="text-xs text-gray-500 mt-1">
            Debe coincidir con <code>ADMIN_TOKEN</code> del backend (por defecto: <code>dev</code>).
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={wipeClient} className="px-3 py-2 rounded border">Borrar cliente</button>
          <button onClick={wipeAll} className="px-3 py-2 rounded border">Reset total</button>
        </div>
      </div>
      {msg && <div className="text-sm text-gray-700">{msg}</div>}
    </div>
  );
}
