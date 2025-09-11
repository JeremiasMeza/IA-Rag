const MODEL_INFO = {
  "qwen2.5:1.5b": {
    name: "Qwen 2.5 1.5B",
    desc: "Modelo eficiente, ideal para tareas generales en español.",
    icon: "🤖"
  },
  "phi3:3.8b": {
    name: "Phi-3 3.8B",
    desc: "Modelo pequeño, rápido y económico.",
    icon: "⚡"
  },
  "qwen3:4b": {
    name: "Qwen 3 4B",
    desc: "Modelo intermedio, buen balance entre velocidad y calidad.",
    icon: "🔎"
  },
  "qwen3:8b": {
    name: "Qwen 3 8B",
    desc: "Modelo robusto para respuestas más complejas.",
    icon: "🧠"
  },
  "deepseek-r1:8b": {
    name: "DeepSeek R1 8B",
    desc: "Optimizado para comprensión y síntesis.",
    icon: "🌊"
  },
  "deepseek-r1:14b": {
    name: "DeepSeek R1 14B",
    desc: "Gran capacidad, ideal para análisis avanzados.",
    icon: "🚀"
  },
  "nomic-embed-text:latest": {
    name: "Nomic Embed",
    desc: "Especializado en embeddings y búsqueda semántica.",
    icon: "🔗"
  },
  "mixtral:latest": {
    name: "Mixtral",
    desc: "Modelo mixto, versátil para múltiples tareas.",
    icon: "🌀"
  },
  "gpt-oss:20b": {
    name: "GPT-OSS 20B",
    desc: "Modelo open source de gran tamaño.",
    icon: "🌐"
  }
};

export default function ModelPicker({ value, onChange, models }) {
  return (
    <div>
      <label className="block text-lg font-semibold mb-4">Selecciona el modelo IA</label>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {models.map((m) => {
          const info = MODEL_INFO[m] || { name: m, desc: "", icon: "🤖" };
          const selected = value === m;
          return (
            <button
              key={m}
              type="button"
              onClick={() => onChange(m)}
              className={`flex flex-col items-start p-4 rounded-xl border transition shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer bg-white ${selected ? "border-blue-600 ring-2 ring-blue-200" : "border-gray-200"}`}
            >
              <span className="text-3xl mb-2">{info.icon}</span>
              <span className="font-bold text-gray-800 mb-1">{info.name}</span>
              <span className="text-sm text-gray-500 mb-2">{info.desc}</span>
              {selected && <span className="mt-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">Seleccionado</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
