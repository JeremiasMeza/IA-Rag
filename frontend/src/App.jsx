import { useState } from "react";
import ModelPicker from "./components/ModelPicker";
import UploadPanel from "./components/UploadPanel";
import ChatBox from "./components/ChatBox";

const MODELS = [
  "qwen3:8b",
  "deepseek-r1:8b",
  "deepseek-r1:14b",
  "nomic-embed-text:latest",
  "mixtral:latest",
  "gpt-oss:20b"
];

export default function App() {
  const [model, setModel] = useState(MODELS[0]);
  // Un id de sesión único por usuario/navegador
  const [sessionId] = useState(() => crypto.randomUUID());

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="p-4 border-b bg-white flex items-center justify-between">
        <h1 className="text-xl font-semibold">Chat PDF + Ollama</h1>
      </header>

      <main className="flex-grow max-w-3xl mx-auto p-4 space-y-4 w-full">
        <div className="grid sm:grid-cols-3 gap-3 mb-4">
          <ModelPicker value={model} onChange={setModel} models={MODELS} />
        </div>
        <UploadPanel sessionId={sessionId} />
        <ChatBox model={model} sessionId={sessionId} />
      </main>
    </div>
  );
}

