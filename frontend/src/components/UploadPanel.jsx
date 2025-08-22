import { useState } from "react";
import { uploadDoc } from "../lib/api";

export default function UploadPanel({ clientId }) {
  const [file, setFile] = useState(null);
  const [info, setInfo] = useState("");

  const upload = async () => {
    if (!file) return;
    try {
      const data = await uploadDoc({ file, client_id: clientId });
      setInfo(`Subido ${data.uploaded} (chunks indexados: ${data.chunks_indexed})`);
    } catch (e) {
      setInfo("Error: " + e.message);
    }
  };

  return (
    <div className="p-3 border rounded bg-white flex flex-col gap-2">
      <div className="flex gap-2 items-center">
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button onClick={upload} className="px-3 py-2 rounded border">Subir & Indexar</button>
      </div>
      <p className="text-sm text-gray-600">
        Acepta PDF o TXT. Cliente actual: <b>{clientId}</b>
      </p>
      {info && <div className="text-sm text-gray-700">{info}</div>}
    </div>
  );
}
