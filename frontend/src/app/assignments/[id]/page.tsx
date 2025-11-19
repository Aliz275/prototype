"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useParams } from "next/navigation";

type Assignment = {
  id: number;
  title: string;
  description: string;
  due_date?: string | null;
  created_by_id?: number;
  is_general: number;
  team_id?: number | null;
  employee_ids?: number[];
};

type Submission = {
  id: number;
  assignment_id: number;
  user_id: number;
  file_url: string;
  submitted_at: string;
};

type UserWithId = {
  id: number;
  email: string;
  role: string;
};

export default function AssignmentDetailPage() {
  const { user } = useAuth();
  const currentUser = user as UserWithId;

  const { id } = useParams();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/assignments/${id}`, {
          credentials: "include",
        });

        if (!res.ok) throw new Error("Failed to load assignment");
        const data = await res.json();
        const assignmentData: Assignment = data.assignment;

        // EMPLOYEE ACCESS CONTROL
        if (currentUser.role === "employee") {
          const isAssignedToUser =
            assignmentData.is_general ||
            (assignmentData.employee_ids?.includes(currentUser.id) ?? false) ||
            false; // team check will be handled backend ideally

          if (!isAssignedToUser) {
            throw new Error("You do not have access to this assignment");
          }
        }

        setAssignment(assignmentData);
        setSubmissions(data.submissions || []);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id, currentUser.id, currentUser.role]);

  async function submitFile() {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(
      `http://localhost:8000/api/assignments/${id}/submit`,
      {
        method: "POST",
        body: formData,
        credentials: "include",
      }
    );

    const data = await res.json();

    if (res.ok) {
      setUploadStatus("Uploaded successfully!");
      setSubmissions([...submissions, data.submission]);
    } else {
      setUploadStatus(data.message || "Upload failed");
    }
  }

  if (!user) {
    return (
      <main className="p-6">
        <p>Please log in to view this assignment.</p>
      </main>
    );
  }

  if (loading) return <p className="p-6">Loading…</p>;
  if (error) return <p className="p-6 text-red-500">{error}</p>;
  if (!assignment) return <p className="p-6">Assignment not found.</p>;

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold">{assignment.title}</h1>

      <p className="mt-4 text-gray-700">{assignment.description}</p>

      {assignment.due_date && (
        <p className="mt-2 text-sm text-gray-500">
          Due: {assignment.due_date}
        </p>
      )}

      {/* EMPLOYEE SUBMISSION */}
      {currentUser.role === "employee" && (
        <div className="mt-6">
          <h2 className="font-semibold mb-2">Submit Work</h2>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="border p-2"
          />
          <button
            onClick={submitFile}
            className="ml-2 px-3 py-1 bg-green-600 text-white rounded"
          >
            Upload
          </button>
          {uploadStatus && <p className="mt-2">{uploadStatus}</p>}
        </div>
      )}

      {/* SUBMISSIONS FOR ADMINS / MANAGERS */}
      {(currentUser.role === "org_admin" ||
        currentUser.role === "super_admin" ||
        currentUser.role === "team_manager") && (
        <div className="mt-10">
          <h2 className="text-xl font-semibold mb-4">Submissions</h2>
          {submissions.length === 0 && <p>No submissions yet.</p>}
          {submissions.map((s) => (
            <div key={s.id} className="border p-3 rounded mb-2">
              <p>Employee ID: {s.user_id}</p>
              <a
                href={s.file_url}
                target="_blank"
                className="text-blue-600 underline"
              >
                View file
              </a>
              <p className="text-sm text-gray-500">{s.submitted_at}</p>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
