import { useState } from "react";
import ModelPicker from "./components/ModelPicker";
import ChatBox from "./components/ChatBox";
import UploadPanel from "./components/UploadPanel";
import AdminPanel from "./components/AdminPanel";

const MODELS = ["llama3.1:8b", "qwen3:8b", "llama3.2:3b"];
const TABS = [
  { id: "chat", label: "Chat" },
  { id: "docs", label: "Documentos" },
  { id: "admin", label: "Admin" },
];

export default function App() {
  const [model, setModel] = useState(MODELS[0]);
  const [clientId, setClientId] = useState("acme");
  const [tab, setTab] = useState("chat");

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="p-4 border-b bg-white flex items-center justify-between">
        <h1 className="text-xl font-semibold">Local AI Chat (Ollama + RAG)</h1>
        <nav className="flex gap-2">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 py-1 rounded ${
                tab === t.id ? "bg-black text-white" : "bg-gray-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex-grow max-w-3xl mx-auto p-4 space-y-4 w-full">
        {tab === "chat" && (
          <>
            <div className="grid sm:grid-cols-3 gap-3">
              <ModelPicker value={model} onChange={setModel} models={MODELS} />
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium">Cliente (aislamiento)</label>
                <input
                  className="mt-1 border rounded p-2 w-full"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                />
              </div>
            </div>
            <ChatBox model={model} clientId={clientId} />
          </>
        )}

        {tab === "docs" && <UploadPanel clientId={clientId} />}

        {tab === "admin" && <AdminPanel clientId={clientId} />}
      </main>
    </div>
  );
}

