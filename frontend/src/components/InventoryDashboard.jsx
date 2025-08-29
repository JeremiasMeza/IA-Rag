import { useEffect, useState } from "react";
import { listProducts, createProduct, deleteProduct } from "../lib/api";

export default function InventoryDashboard() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    name: "",
    category: "",
    quantity: 0,

    unit_price: "",
    entry_date: "",
    description: "",

    entry_date: "",

  });

  const load = async () => {
    try {
      const data = await listProducts();
      setItems(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async () => {
    try {

      await createProduct({
        ...form,
        quantity: Number(form.quantity),
        unit_price: form.unit_price ? Number(form.unit_price) : null,
      });
      setForm({
        name: "",
        category: "",
        quantity: 0,
        unit_price: "",
        entry_date: "",
        description: "",
      });

      await createProduct({ ...form, quantity: Number(form.quantity) });
      setForm({ name: "", category: "", quantity: 0, entry_date: "" });

      load();
    } catch (e) {
      alert(e.message);
    }
  };

  const remove = async (id) => {
    if (!confirm("¿Eliminar producto?")) return;
    await deleteProduct(id);
    load();
  };

  return (
    <div className="space-y-4">
      <div className="p-4 bg-white rounded border space-y-2">
        <h2 className="font-semibold">Nuevo producto</h2>
        <div className="grid sm:grid-cols-5 gap-2">

        <div className="grid sm:grid-cols-4 gap-2">

          <input
            className="border p-2 rounded"
            placeholder="Nombre"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <input
            className="border p-2 rounded"
            placeholder="Categoría"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          />
          <input
            type="number"
            className="border p-2 rounded"
            placeholder="Cantidad"
            value={form.quantity}
            onChange={(e) => setForm({ ...form, quantity: e.target.value })}
          />
          <input

            type="number"
            step="0.01"
            className="border p-2 rounded"
            placeholder="Precio"
            value={form.unit_price}
            onChange={(e) =>
              setForm({ ...form, unit_price: e.target.value })
            }
          />
          <input

            type="date"
            className="border p-2 rounded"
            value={form.entry_date}
            onChange={(e) => setForm({ ...form, entry_date: e.target.value })}
          />
        </div>

        <textarea
          className="border p-2 rounded w-full mt-2"
          placeholder="Descripción (opcional)"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />

        <button
          onClick={submit}
          className="mt-2 px-4 py-2 bg-black text-white rounded"
        >
          Guardar
        </button>
      </div>

      <div className="p-4 bg-white rounded border">
        <h2 className="font-semibold mb-2">Inventario</h2>
        <table className="w-full text-left text-sm">
          <thead>
            <tr>
              <th className="border-b p-2">Nombre</th>
              <th className="border-b p-2">Categoría</th>
              <th className="border-b p-2">Cantidad</th>

              <th className="border-b p-2">Precio</th>
              <th className="border-b p-2">Ingreso</th>
              <th className="border-b p-2">Descripción</th>

              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id}>
                <td className="border-b p-2">{p.name}</td>
                <td className="border-b p-2">{p.category}</td>
                <td className="border-b p-2">{p.quantity}</td>

                <td className="border-b p-2">
                  {p.unit_price != null ? p.unit_price.toFixed(2) : "-"}
                </td>
                <td className="border-b p-2">{p.entry_date}</td>
                <td className="border-b p-2">{p.description || "-"}</td>

                <td className="border-b p-2 text-right">
                  <button
                    onClick={() => remove(p.id)}
                    className="px-2 py-1 text-sm rounded border"
                  >
                    Borrar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
