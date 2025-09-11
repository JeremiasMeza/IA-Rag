export default function ActiveModelCard({ model }) {
  return (
    <div className="p-4 bg-white rounded-xl shadow flex-1 min-w-[250px]">
      <div className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
        <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
        Modelo IA activo
      </div>
      <div className="text-lg font-mono text-gray-800 mt-2">{model}</div>
    </div>
  );
}
