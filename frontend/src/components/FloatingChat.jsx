import { useState } from "react";
import ChatBox from "./ChatBox";

export default function FloatingChat({ model, clientId }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      {open && (
        <div className="fixed bottom-20 right-4 w-80 z-50 shadow-lg">
          <ChatBox model={model} clientId={clientId} />
        </div>
      )}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-4 right-4 rounded-full bg-blue-600 text-white p-4 shadow-lg"
      >
        {open ? "✕" : "Chat"}
      </button>
    </>
  );
}
