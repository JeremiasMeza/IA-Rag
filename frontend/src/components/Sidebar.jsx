import React from "react";

const menuItems = [
  { label: "Dashboard", icon: "🧭" },
  { label: "Modelo IA", icon: "🤖" },
  { label: "Documentos", icon: "📄" },
  { label: "Chat", icon: "💬" },
  { label: "Prompt", icon: "💭" },
];

export default function Sidebar({ current, onSelect }) {
  return (
    <aside className="bg-gray-100 rounded-xl p-4 flex flex-col gap-2 w-56 min-h-full">
      {menuItems.map((item) => (
        <button
          key={item.label}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-left font-medium transition-colors ${
            current === item.label
              ? "bg-gray-300 text-black"
              : "hover:bg-gray-200 text-gray-700"
          }`}
          onClick={() => onSelect(item.label)}
          disabled={item.label === "Prompt"}
        >
          <span>{item.icon}</span>
          {item.label}
        </button>
      ))}
    </aside>
  );
}
