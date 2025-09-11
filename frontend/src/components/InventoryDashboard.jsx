import ActiveDocsCard from "./ActiveDocsCard";
import ActiveModelCard from "./ActiveModelCard";

// El modelo y sessionId deberían venir por props o contexto global
const GLOBAL_SESSION_ID = "global";
const DEFAULT_MODEL = "qwen2.5:1.5b";

export default function InventoryDashboard({ model = DEFAULT_MODEL, sessionId = GLOBAL_SESSION_ID }) {
  return (
    <div className="flex flex-col md:flex-row gap-6 w-full">
      <ActiveDocsCard sessionId={sessionId} />
      <ActiveModelCard model={model} />
    </div>
  );
}