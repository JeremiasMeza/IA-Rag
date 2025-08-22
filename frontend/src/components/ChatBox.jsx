import { useEffect, useRef, useState } from "react";
import { chat } from "../lib/api";

export default function ChatBox({ model, clientId }) {
  const [msg, setMsg] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!msg.trim()) return;
    const userText = msg;
    setMsg("");
    setMessages((prev) => [...prev, { sender: "user", text: userText }]);
    setLoading(true);
    try {
      const data = await chat({ message: userText, model, client_id: clientId });
      let meta = "";
      if (data.citations?.length) {
        meta = `Contexto usado: ${data.citations
          .map((c) => `${c.source}#${c.chunk}`)
          .join(", ")}`;
      } else if (data.used_context === 0 && clientId) {
        meta = "Sin contexto (no hay docs indexados para este cliente).";
      }
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: data.reply || JSON.stringify(data), meta },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Error: " + e.message },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[400px] border rounded bg-white">
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`max-w-[80%] p-2 rounded ${
              m.sender === "user" ? "bg-blue-100 self-end" : "bg-gray-100 self-start"
            }`}
          >
            <pre className="whitespace-pre-wrap">{m.text}</pre>
            {m.meta && <div className="text-xs text-gray-500 mt-1">{m.meta}</div>}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <div className="p-3 border-t flex gap-2">
        <input
          className="flex-1 border rounded p-2"
          placeholder="Escribe tu mensaje..."
          value={msg}
          onChange={(e) => setMsg(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button
          onClick={send}
          disabled={loading}
          className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
        >
          {loading ? "..." : "Enviar"}
        </button>
      </div>
    </div>
  );
}

