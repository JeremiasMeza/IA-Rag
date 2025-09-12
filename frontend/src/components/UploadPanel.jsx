import { useState } from "react";
import { uploadPdf } from "../lib/api";

export default function UploadPanel({ sessionId, onUpload }) {
  const [file, setFile] = useState(null);
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const upload = async () => {
    if (!file) return;
    setLoading(true);
    setInfo("");
    try {
      const data = await uploadPdf({ file, session_id: sessionId });
      setInfo(`PDF subido. Caracteres extraídos: ${data.chars}`);
      if (onUpload) onUpload();
    } catch (e) {
      setInfo("Error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-3 border rounded bg-white flex flex-col gap-2">
      <div className="flex gap-2 items-center">
        <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} disabled={loading} />
        <button onClick={upload} className="px-3 py-2 rounded border" disabled={loading}>
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5 text-blue-600" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              Cargando...
            </span>
          ) : (
            "Subir PDF"
          )}
        </button>
      </div>
      <p className="text-sm text-gray-600">
        Solo PDF. Sesión actual: <b>{sessionId}</b>
      </p>
      {info && <div className="text-sm text-gray-700">{info}</div>}
    </div>
  );
}
