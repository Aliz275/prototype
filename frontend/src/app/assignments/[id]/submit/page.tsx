//frontend/src/app/assignements/[id]/submit/page.tsx

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AssignmentUploader from "../../../../components/AssignmentUploader";

/* ================= PAGE ================= */

export default function SubmitAssignmentPage() {
  const params = useParams();

  // ✅ SAFE extraction of id
  const assignmentId =
    params && typeof params.id === "string"
      ? Number(params.id)
      : null;

  const [loading, setLoading] = useState(true);
  const [assignment, setAssignment] = useState<any>(null);
  const [error, setError] = useState("");

  /* ================= LOAD ASSIGNMENT ================= */

  useEffect(() => {
    if (assignmentId === null) return;

    const loadAssignment = async () => {
      try {
        const res = await fetch(`/api/assignments/${assignmentId}`);

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          throw new Error(data.message || "Failed to load assignment");
        }

        setAssignment(data.assignment);
      } catch (err: any) {
        setError(err.message || "Error loading assignment");
      } finally {
        setLoading(false);
      }
    };

    loadAssignment();
  }, [assignmentId]);

  /* ================= RENDER ================= */

  if (assignmentId === null) {
    return <p className="p-6 text-red-500">Invalid assignment ID.</p>;
  }

  if (loading) return <p className="p-6">Loading...</p>;
  if (error) return <p className="p-6 text-red-500">{error}</p>;
  if (!assignment) return <p className="p-6">Assignment not found.</p>;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* -------- ASSIGNMENT HEADER -------- */}
      <h1 className="text-2xl font-bold">{assignment.title}</h1>

      <p className="text-gray-700 mt-2">{assignment.description}</p>

      {assignment.due_date && (
        <p className="mt-2 font-semibold">
          Due Date:{" "}
          <span className="text-red-500">{assignment.due_date}</span>
        </p>
      )}

      {/* -------- FILE UPLOADER -------- */}
      <div className="mt-6">
        <AssignmentUploader assignmentId={assignmentId} />
      </div>
    </div>
  );
}
