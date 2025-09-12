import React from "react";

export default function Navbar({ title, model }) {

  return (
    <nav className="bg-gray-200 rounded-xl px-6 py-3 mb-4 flex items-center justify-between">
      <span className="font-bold text-lg">{title}</span>
      {model && (
        <span className="flex items-center gap-2 ml-4">
          <span className="text-sm text-gray-700 bg-white border border-blue-200 rounded px-3 py-1">
            Modelo: <b>{model}</b>
          </span>
          
        </span>
      )}
    </nav>
  );
}
