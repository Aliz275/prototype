"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../../../context/AuthContext";

type Assignment = {
  id: number;
  title: string;
  description: string;
  due_date?: string | null;
  is_general: number;
  team_id?: number | null;
  employee_ids?: number[];
};

type FormShape = {
  title?: string;
  description?: string;
  due_date?: string | null;
  team_id?: number | null | string;
  employee_ids?: string;
  is_general?: number;
};

// DEFAULT TO LOCAL BACKEND IF ENV NOT SET
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function ManageAssignmentsPage() {
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState<FormShape>({});
  const [editingId, setEditingId] = useState<number | null>(null);

  // Load assignments
  const loadAssignments = async () => {
    if (!user) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/assignments`, { credentials: "include" });
      if (!res.ok) throw new Error(`Failed to load assignments: ${res.status}`);
      const data = await res.json();
      setAssignments(data.assignments ?? []);
    } catch (err: any) {
      setError(err.message || "Error fetching assignments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignments();
  }, [user]);

  if (!user) return <p className="p-6">Please log in.</p>;
  if (user.role === "employee")
    return <p className="p-6">Unauthorized: Employees cannot manage assignments.</p>;
  if (loading) return <p className="p-6">Loading…</p>;
  if (error) return <p className="p-6 text-red-500">{error}</p>;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        title: form.title?.trim(),
        description: form.description?.trim(),
        due_date: form.due_date || null,
      };

      payload.team_id = form.team_id ? Number(form.team_id) : null;

      if (form.employee_ids && form.employee_ids.trim() !== "") {
        payload.employee_ids = form.employee_ids
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
          .map(Number)
          .filter((n) => !isNaN(n) && n > 0);
      } else {
        payload.employee_ids = [];
      }

      const method = editingId ? "PUT" : "POST";
      const url = editingId
        ? `${API_BASE}/api/assignments/${editingId}`
        : `${API_BASE}/api/assignments`;

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text().catch(() => `Server error ${res.status}`);
        throw new Error(text || "Failed to save assignment");
      }

      setForm({});
      setEditingId(null);
      loadAssignments();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleEdit = (a: Assignment) => {
    setEditingId(a.id);
    setForm({
      title: a.title,
      description: a.description,
      due_date: a.due_date ?? "",
      is_general: a.is_general,
      team_id: a.team_id ?? "",
      employee_ids: Array.isArray(a.employee_ids) ? a.employee_ids.join(",") : "",
    });
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this assignment?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/assignments/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`Failed to delete assignment: ${res.status}`);
      loadAssignments();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <main className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">{editingId ? "Edit Assignment" : "Create Assignment"}</h1>

      <form onSubmit={handleSubmit} className="space-y-3 mb-6">
        <input
          type="text"
          placeholder="Title"
          className="w-full border p-2 rounded"
          value={form.title || ""}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
        />
        <textarea
          placeholder="Description"
          className="w-full border p-2 rounded"
          value={form.description || ""}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          required
        />
        <input
          type="date"
          className="w-full border p-2 rounded"
          value={form.due_date || ""}
          onChange={(e) => setForm({ ...form, due_date: e.target.value })}
        />
        <input
          type="text"
          placeholder="Team ID (optional)"
          className="w-full border p-2 rounded"
          value={String(form.team_id ?? "")}
          onChange={(e) => setForm({ ...form, team_id: e.target.value })}
        />
        <input
          type="text"
          placeholder="Employee IDs (comma separated)"
          className="w-full border p-2 rounded"
          value={form.employee_ids || ""}
          onChange={(e) => setForm({ ...form, employee_ids: e.target.value })}
        />
        <div className="flex gap-2">
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">
            {editingId ? "Update" : "Create"}
          </button>
          {editingId && (
            <button
              type="button"
              className="ml-2 bg-gray-400 text-white px-4 py-2 rounded"
              onClick={() => {
                setEditingId(null);
                setForm({});
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <h2 className="text-xl font-bold mb-2">All Assignments</h2>
      {assignments.length === 0 ? (
        <p>No assignments available.</p>
      ) : (
        <ul className="space-y-3">
          {assignments.map((a) => (
            <li key={a.id} className="border p-3 rounded flex justify-between items-start">
              <div>
                <p className="font-semibold">{a.title}</p>
                {a.due_date && <p className="text-sm text-gray-500">Due: {a.due_date}</p>}
                <p>{a.description}</p>
                <p className="text-sm text-gray-500">Team ID: {a.team_id ?? "None"}</p>
                <p className="text-sm text-gray-500">Employee IDs: {a.employee_ids?.join(", ") || "None"}</p>
              </div>
              <div className="flex flex-col space-y-1">
                <button className="bg-yellow-500 text-white px-2 py-1 rounded" onClick={() => handleEdit(a)}>
                  Edit
                </button>
                <button className="bg-red-600 text-white px-2 py-1 rounded" onClick={() => handleDelete(a.id)}>
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
