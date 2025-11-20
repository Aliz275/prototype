"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "../../../context/AuthContext";

type Assignment = {
  id: number;
  title: string;
  description: string;
  due_date?: string | null;
  is_general: number;
  team_id?: number | null;
};

export default function AssignmentDetailPage() {
  const { user } = useAuth();
  const currentUser = user ?? null;

  const { id } = useParams();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!currentUser) return;

    async function load() {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/assignments/${id}`, {
          credentials: "include",
        });
        if (!res.ok) throw new Error("Failed to load assignment");

        const data = await res.json();
        setAssignment(data.assignment);
      } catch (err: any) {
        setError(err.message || "Error fetching assignment");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id, currentUser?.id, currentUser?.role]);

  if (!currentUser) return <p className="p-6">Please log in to see this assignment.</p>;
  if (loading) return <p className="p-6">Loading…</p>;
  if (error) return <p className="p-6 text-red-500">{error}</p>;
  if (!assignment) return <p className="p-6">Assignment not found.</p>;

  return (
    <main className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">{assignment.title}</h1>
      {assignment.due_date && <p className="text-sm text-gray-500">Due: {assignment.due_date}</p>}
      <p>{assignment.description}</p>
    </main>
  );
}
