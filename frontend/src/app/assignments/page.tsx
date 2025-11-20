"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "../../context/AuthContext";

type Assignment = {
  id: number;
  title: string;
  description: string;
  due_date?: string | null;
  is_general: number;
  team_id?: number | null;
  employee_ids?: number[];
};

export default function AssignmentsPage() {
  const { user } = useAuth(); // user can be null
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // runtime guard + narrowed currentUser
  useEffect(() => {
    if (!user) return; // stop if user is not logged in

    const currentUser = user; // TS now knows this is not null

    async function loadAssignments() {
      setLoading(true);
      try {
        const res = await fetch("http://localhost:8000/api/assignments", {
          credentials: "include",
        });
        if (!res.ok) throw new Error("Failed to load assignments");

        const data = await res.json();
        const allAssignments: Assignment[] = data.assignments ?? [];

        // Optional frontend filtering for employee-specific logic
        let filtered: Assignment[] = allAssignments;
        if (currentUser.role === "employee") {
          filtered = allAssignments.filter(
            (a) =>
              a.is_general ||
              (a.employee_ids?.includes(currentUser.id) ?? false)
          );
        }

        setAssignments(filtered);
      } catch (err: any) {
        setError(err.message || "Error fetching assignments");
      } finally {
        setLoading(false);
      }
    }

    loadAssignments();
  }, [user]);

  // Render guards
  if (!user) return <p className="p-6">Please log in to see assignments.</p>;
  if (loading) return <p className="p-6">Loading…</p>;
  if (error) return <p className="p-6 text-red-500">{error}</p>;

  return (
    <main className="p-6 max-w-3xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Assignments</h1>
        {(user.role === "org_admin" || user.role === "team_manager") && (
          <Link
            href="/assignments/manage"
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            Manage Assignments
          </Link>
        )}
      </div>

      {assignments.length === 0 ? (
        <p>No assignments available.</p>
      ) : (
        <ul className="space-y-3">
          {assignments.map((a) => (
            <li key={a.id} className="border p-3 rounded">
              <Link
                href={`/assignments/${a.id}`}
                className="text-lg font-semibold text-blue-600 underline"
              >
                {a.title}
              </Link>
              {a.due_date && (
                <p className="text-sm text-gray-500">Due: {a.due_date}</p>
              )}
              <p>{a.description}</p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
