import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";
import ModelPicker from "./components/ModelPicker";
import UploadPanel from "./components/UploadPanel";
import ChatBox from "./components/ChatBox";
import ContextDocsCard from "./components/ContextDocsCard";
import DocumentCardList from "./components/DocumentCardList";
import PdfPreviewer from "./components/PdfPreviewer";
import InventoryDashboard from "./components/InventoryDashboard";

const MODELS = [
  "qwen2.5:1.5b", // nuevo modelo agregado
  "phi3:3.8b", // modelo pequeño y eficiente
  "qwen3:4b", // modelo intermedio solicitado
  "qwen3:8b",
  "deepseek-r1:8b",
  "deepseek-r1:14b",
  "nomic-embed-text:latest",
  "mixtral:latest",
  "gpt-oss:20b"
];



// Siempre usar el contexto global
const GLOBAL_SESSION_ID = "global";


export default function App() {
  const [model, setModel] = useState(MODELS[0]);
  const [section, setSection] = useState("Dashboard");
  const sessionId = GLOBAL_SESSION_ID;
  const [selectedDoc, setSelectedDoc] = useState(null);
  // Estado para forzar recarga de documentos (debe estar fuera del condicional)
  const [docsReloadKey, setDocsReloadKey] = useState(0);
  const reloadDocs = () => setDocsReloadKey((k) => k + 1);

  // Resetear selectedDoc al cambiar de sección
  useEffect(() => {
    if (section !== "Documentos" && selectedDoc !== null) {
      setSelectedDoc(null);
    }
  }, [section]);
  // Renderizado dinámico de contenido
  let content = null;
  if (section === "Dashboard") {
    content = (
      <div className="space-y-4">
        <InventoryDashboard model={model} sessionId={sessionId} />
      </div>
    );
  } else if (section === "Modelo IA") {
    content = (
      <div className="space-y-4">
        <ModelPicker value={model} onChange={setModel} models={MODELS} />
      </div>
    );
  } else if (section === "Documentos") {
    content = (
      <div className="space-y-4">
        <DocumentCardList sessionId={sessionId} reloadKey={docsReloadKey} />
        <UploadPanel sessionId={sessionId} onUpload={reloadDocs} />
      </div>
    );
  } else if (section === "Chat") {
    content = (
      <div className="space-y-4">
        <ChatBox model={model} sessionId={sessionId} />
      </div>
    );
  } else {
    content = <div className="text-gray-400">Próximamente...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="flex flex-1 min-h-0">
        <Sidebar current={section} onSelect={setSection} />
        <div className="flex-1 flex flex-col p-6">
          <Navbar title={section} />
          <div className="flex-1 bg-gray-100 rounded-xl p-6 overflow-auto">
            {content}
          </div>
        </div>
      </div>
    </div>
  );
}

