import { useEffect, useState } from "react";
import { API } from "../lib/api";

export default function DocumentCardList({ sessionId, reloadKey }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/context/docs?session_id=${sessionId || "global"}`)
      .then((r) => r.json())
      .then((data) => setDocs(data.docs || []))
      .finally(() => setLoading(false));
  }, [sessionId, reloadKey]);

  return (
    <div>
      <div className="mb-2 text-lg font-semibold">Documentos activos</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full text-gray-400">Cargando...</div>
        ) : docs.length === 0 ? (
          <div className="col-span-full text-gray-400">No hay documentos activos.</div>
        ) : (
          docs.map((doc) => {
            const pdfUrl = `${API}/storage/uploads/${doc}`;
            const handleDelete = async (e) => {
              e.preventDefault();
              if (!window.confirm(`¿Eliminar el documento "${doc}"?`)) return;
              try {
                const res = await fetch(`${API}/context/docs/${encodeURIComponent(doc)}?session_id=${sessionId || "global"}`, { method: "DELETE" });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.ok) {
                  setDocs((prev) => prev.filter((d) => d !== doc));
                  if (data.message) {
                    alert(data.message);
                  }
                } else {
                  alert(data.message || "Error eliminando el documento");
                }
              } catch (err) {
                alert("Error eliminando el documento: " + (err?.message || err));
              }
            };
            return (
              <div
                key={doc}
                className="flex flex-col items-start p-4 rounded-xl border transition shadow-sm hover:shadow-md focus:outline-none bg-white min-h-[80px] border-gray-200 relative"
              >
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 w-full flex flex-col items-start"
                >
                  <span className="text-2xl mb-2">📄</span>
                  <span className="font-bold text-gray-800 mb-1 break-all">{doc}</span>
                  <span className="mt-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">Abrir PDF</span>
                </a>
                <button
                  onClick={handleDelete}
                  className="absolute top-2 right-2 px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-xs"
                  title="Eliminar PDF"
                >
                  Eliminar
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
