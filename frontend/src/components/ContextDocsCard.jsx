import { useEffect, useState } from "react";

export default function ContextDocsCard({ sessionId, model }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/context/docs?session_id=${sessionId || "global"}`)
      .then((r) => r.json())
      .then((data) => setDocs(data.docs || []))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleDelete = async () => {
    if (!window.confirm("¿Eliminar todos los documentos de este contexto?")) return;
    setLoading(true);
    await fetch(`/context/docs?session_id=${sessionId || "global"}`, { method: "DELETE" });
    setDocs([]);
    setLoading(false);
  };

  return (
    <div className="p-4 border rounded bg-white mb-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-semibold">Documentos activos</h2>
        <button
          className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
          onClick={handleDelete}
          disabled={loading || docs.length === 0}
        >
          Eliminar todos
        </button>
      </div>
      {loading ? (
        <div>Cargando...</div>
      ) : docs.length === 0 ? (
        <div>No hay documentos activos.</div>
      ) : (
        <ul className="list-disc pl-5">
          {docs.map((doc) => (
            <li key={doc}>{doc}</li>
          ))}
        </ul>
      )}
      <div className="mt-4">
        <span className="font-semibold">Modelo IA activo:</span> {model}
      </div>
    </div>
  );
}
