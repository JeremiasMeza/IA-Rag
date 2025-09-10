import React from "react";

export default function Navbar({ title }) {
  return (
    <nav className="bg-gray-200 rounded-xl px-6 py-3 mb-4">
      <span className="font-bold text-lg">{title}</span>
    </nav>
  );
}
