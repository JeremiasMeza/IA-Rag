export default function ModelPicker({ value, onChange, models }) {
  return (
    <div>
      <label className="block text-sm font-medium">Modelo</label>
      <select
        className="mt-1 border rounded p-2 w-full"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {models.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>
    </div>
  );
}
