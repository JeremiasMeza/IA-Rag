import { useState } from "react";
import ModelPicker from "./components/ModelPicker";
import ChatBox from "./components/ChatBox";
import UploadPanel from "./components/UploadPanel";
import AdminPanel from "./components/AdminPanel";



const MODELS = ["llama3.1:8b", "qwen3:8b", "llama3.2:3b"];

export default function App() {
  const [model, setModel] = useState(MODELS[0]);
  const [clientId, setClientId] = useState("acme");

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="p-4 border-b bg-white">
        <h1 className="text-xl font-semibold">Local AI Chat (Ollama + RAG)</h1>
      </header>
      <UploadPanel clientId={clientId} />
<AdminPanel clientId={clientId} />

      <main className="max-w-3xl mx-auto p-4 space-y-4">
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
        <UploadPanel clientId={clientId} />
      </main>
    </div>
  );
}