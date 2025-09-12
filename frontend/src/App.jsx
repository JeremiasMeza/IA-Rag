import React, { useState, useEffect } from "react";
import { getSelectedModel, setSelectedModel } from "./lib/api";
import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";
import ModelPicker from "./components/ModelPicker";
import UploadPanel from "./components/UploadPanel";
import ChatBox from "./components/ChatBox";
import ContextDocsCard from "./components/ContextDocsCard";
import DocumentCardList from "./components/DocumentCardList";
import PdfPreviewer from "./components/PdfPreviewer";
import InventoryDashboard from "./components/InventoryDashboard";

import { getModels } from "./lib/api";

// Modelos disponibles en el backend (Ollama)
// Se cargan dinámicamente



// Siempre usar el contexto global
const GLOBAL_SESSION_ID = "global";


export default function App() {
  // Eliminado modelStatus
  const [models, setModels] = useState([]);
  const [model, setModel] = useState("");
  const [section, setSection] = useState("Dashboard");
  const sessionId = GLOBAL_SESSION_ID;
  const [selectedDoc, setSelectedDoc] = useState(null);
  // Estado para forzar recarga de documentos (debe estar fuera del condicional)
  const [docsReloadKey, setDocsReloadKey] = useState(0);
  const reloadDocs = () => setDocsReloadKey((k) => k + 1);
  // Estado global de mensajes del chat (persistente mientras la app esté abierta)
  const [chatMessages, setChatMessages] = useState(null);


  // Al montar, obtener los modelos instalados y el modelo global seleccionado
  // Al montar, obtener modelos, modelo seleccionado y estado del modelo
  useEffect(() => {
    async function fetchAll() {
      const ms = await getModels();
      setModels(ms);
      const m = await getSelectedModel();
      if (m && ms.includes(m)) setModel(m);
      else if (ms.length > 0) setModel(ms[0]);
    }
    fetchAll();
  }, []);

  // Al cambiar el modelo, actualizar el backend
  const handleModelChange = async (m) => {
    setModel(m);
    await setSelectedModel(m);
  };

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
  <ModelPicker value={model} onChange={handleModelChange} models={models} />
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
        <ChatBox
          model={model}
          sessionId={sessionId}
          messages={chatMessages}
          setMessages={setChatMessages}
        />
      </div>
    );
  } else {
    content = <div className="text-gray-400">Próximamente...</div>;
  }
              <Navbar title={section} model={section === "Chat" ? model : undefined} />
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="flex flex-1 min-h-0">
        <Sidebar current={section} onSelect={setSection} />
        <div className="flex-1 flex flex-col p-6">
          <Navbar title={section} model={section === "Chat" ? model : undefined} />
          <div className="flex-1 bg-gray-100 rounded-xl p-6 overflow-auto">
            {content}
          </div>
        </div>
      </div>
    </div>
  );
}

