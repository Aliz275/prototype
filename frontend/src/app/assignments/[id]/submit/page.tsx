"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AssignmentUploader from "../../../../components/AssignmentUploader";

export default function SubmitAssignmentPage() {
  const { id } = useParams();
  const assignmentId = Number(id);

  const [loading, setLoading] = useState(true);
  const [assignment, setAssignment] = useState<any>(null);

  useEffect(() => {
    const loadAssignment = async () => {
      const res = await fetch(`/api/assignments/${assignmentId}`);
      const data = await res.json();

      if (res.ok) {
        setAssignment(data.assignment);
      }

      setLoading(false);
    };

    loadAssignment();
  }, [assignmentId]);

  if (loading) return <p>Loading...</p>;
  if (!assignment) return <p>Assignment not found.</p>;

  return (
    <div className="p-6">
      {/* -------- ASSIGNMENT HEADER -------- */}
      <h1 className="text-2xl font-bold">{assignment.title}</h1>

      <p className="text-gray-700 mt-2">{assignment.description}</p>

      {assignment.due_date && (
        <p className="mt-2 font-semibold">
          Due Date: <span className="text-red-500">{assignment.due_date}</span>
        </p>
      )}

      {/* -------- FILE UPLOADER -------- */}
      <AssignmentUploader assignmentId={assignmentId} />

    </div>
  );
}
