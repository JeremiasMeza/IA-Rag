import { useEffect, useState } from "react";

export default function ActiveDocsCard({ sessionId }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/context/docs?session_id=${sessionId || "global"}`)
      .then((r) => r.json())
      .then((data) => setDocs(data.docs || []))
      .finally(() => setLoading(false));
  }, [sessionId]);

  return (
    <div className="p-4 bg-white rounded-xl shadow flex-1 min-w-[250px]">
      <div className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
        <span className="inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
        Documentos activos
      </div>
      {loading ? (
        <div className="text-gray-400">Cargando...</div>
      ) : docs.length === 0 ? (
        <div className="text-gray-400">No hay documentos activos.</div>
      ) : (
        <ul className="list-disc pl-5 text-sm text-gray-600">
          {docs.map((doc) => (
            <li key={doc}>{doc}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
