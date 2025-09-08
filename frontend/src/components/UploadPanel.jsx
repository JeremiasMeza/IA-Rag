import { useState } from "react";
import { uploadPdf } from "../lib/api";

export default function UploadPanel({ sessionId }) {
  const [file, setFile] = useState(null);
  const [info, setInfo] = useState("");

  const upload = async () => {
    if (!file) return;
    try {
      const data = await uploadPdf({ file, session_id: sessionId });
      setInfo(`PDF subido. Caracteres extraídos: ${data.chars}`);
    } catch (e) {
      setInfo("Error: " + e.message);
    }
  };

  return (
    <div className="p-3 border rounded bg-white flex flex-col gap-2">
      <div className="flex gap-2 items-center">
        <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button onClick={upload} className="px-3 py-2 rounded border">Subir PDF</button>
      </div>
      <p className="text-sm text-gray-600">
        Solo PDF. Sesión actual: <b>{sessionId}</b>
      </p>
      {info && <div className="text-sm text-gray-700">{info}</div>}
    </div>
  );
}
