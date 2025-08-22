import { useState } from "react";
import { chat } from "../lib/api";

export default function ChatBox({ model, clientId }) {
  const [msg, setMsg] = useState("");
  const [reply, setReply] = useState("");
  const [meta, setMeta] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!msg.trim()) return;
    setLoading(true);
    setReply(""); setMeta("");
    try {
      const data = await chat({ message: msg, model, client_id: clientId });
      setReply(data.reply || JSON.stringify(data));
      if (data.citations?.length) {
        setMeta(`Contexto usado: ${data.citations.map(c => `${c.source}#${c.chunk}`).join(", ")}`);
      } else if (data.used_context === 0 && clientId) {
        setMeta("Sin contexto (no hay docs indexados para este cliente).");
      }
    } catch (e) {
      setReply("Error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-3 border rounded bg-white flex flex-col gap-2">
      <div className="flex gap-2">
        <input
          className="flex-1 border rounded p-2"
          placeholder="Escribe tu mensaje y presiona Enter…"
          value={msg}
          onChange={(e) => setMsg(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button
          onClick={send}
          disabled={loading}
          className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
        >
          {loading ? "Enviando..." : "Enviar"}
        </button>
      </div>
      <pre className="whitespace-pre-wrap p-3 bg-gray-100 rounded min-h-[120px]">{reply}</pre>
      {meta && <div className="text-sm text-gray-600">{meta}</div>}
    </div>
  );
}
