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
  employee_ids?: number[];
};

type Submission = {
  id: number;
  assignment_id: number;
  employee_id: number;
  file_path: string;
  submitted_at: string;
  status: string;
  employee_email?: string;
};

export default function AssignmentDetailPage() {
  const { user } = useAuth();
  const currentUser = user ?? null;

  const { id } = useParams();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!currentUser) return;

    async function load() {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/assignments/${id}`, {
          credentials: "include",
        });
        if (!res.ok) {
          const d = await res.json().catch(() => ({}));
          throw new Error(d.message || "Failed to load assignment");
        }
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

  useEffect(() => {
    if (!currentUser) return;
    fetchSubmissions();
  }, [id, currentUser]);

  async function fetchSubmissions() {
    try {
      const res = await fetch(`http://localhost:8000/api/submissions/${id}`, {
        credentials: "include",
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.message || "Failed to load submissions");
      }
      const data = await res.json();
      setSubmissions(data.submissions ?? []);
    } catch (err: any) {
      console.error("Load submissions error:", err);
    }
  }

  function alreadySubmitted(): boolean {
    if (!currentUser) return false;
    return submissions.some((s) => s.employee_id === currentUser.id);
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!uploadFile) {
      setMessage("Please choose a file before uploading.");
      return;
    }
    setUploading(true);
    setMessage("");
    try {
      const fd = new FormData();
      fd.append("file", uploadFile);

      const res = await fetch(`http://localhost:8000/api/submissions/${id}`, {
        method: "POST",
        credentials: "include",
        body: fd,
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.message || "Upload failed");
      }

      setMessage("Uploaded successfully.");
      setUploadFile(null);
      await fetchSubmissions();
    } catch (err: any) {
      setMessage(err.message || "Upload error");
    } finally {
      setUploading(false);
    }
  }

  async function handleAccept(submissionId: number) {
    try {
      const res = await fetch(
        `http://localhost:8000/api/submissions/${submissionId}/accept`,
        { method: "POST", credentials: "include" }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Accept failed");
      await fetchSubmissions();
    } catch (err: any) {
      console.error("Accept error:", err);
    }
  }

  async function handleDelete(submissionId: number) {
    try {
      const res = await fetch(
        `http://localhost:8000/api/submissions/delete/${submissionId}`,
        { method: "DELETE", credentials: "include" }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Delete failed");
      await fetchSubmissions();
    } catch (err: any) {
      console.error("Delete error:", err);
    }
  }

  function downloadUrl(filename: string) {
    return `http://localhost:8000/api/submissions/download/${encodeURIComponent(
      filename
    )}`;
  }

  if (!currentUser) return <p className="p-6">Please log in to see this assignment.</p>;
  if (loading) return <p className="p-6">Loading…</p>;
  if (error) return <p className="p-6 text-red-500">{error}</p>;
  if (!assignment) return <p className="p-6">Assignment not found.</p>;

  return (
    <main className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">{assignment.title}</h1>
      {assignment.due_date && <p className="text-sm text-gray-400">Due: {assignment.due_date}</p>}
      <p className="mb-6">{assignment.description}</p>

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Submissions</h2>

        <p className="mb-2">
          Status:{" "}
          {alreadySubmitted() ? (
            <span className="text-green-500 font-semibold">Already submitted</span>
          ) : (
            <span className="text-gray-400">Not submitted</span>
          )}
        </p>

        <form onSubmit={handleUpload} className="mb-4">
          <label className="block mb-1 font-medium">Upload file</label>
          <input
            type="file"
            onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
            className="mb-2"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={uploading}
              className="bg-blue-800 text-white px-3 py-1 rounded hover:bg-blue-700 transition"
            >
              {uploading ? "Uploading…" : "Upload"}
            </button>
            <button
              type="button"
              onClick={() => {
                setUploadFile(null);
                setMessage("");
              }}
              className="px-3 py-1 border rounded hover:bg-gray-100 transition"
            >
              Clear
            </button>
          </div>
          {message && <p className="mt-2 text-sm">{message}</p>}
        </form>

        {submissions.length === 0 ? (
          <p>No submissions yet.</p>
        ) : (
          <ul className="space-y-2">
            {submissions.map((s) => (
              <li
                key={s.id}
                className="border p-3 rounded flex justify-between items-center bg-gray-900 text-white"
              >
                <div>
                  <div className="font-semibold">{s.employee_email ?? `User ${s.employee_id}`}</div>
                  <div className="text-sm text-gray-400">
                    {s.submitted_at ?? ""} | Status:{" "}
                    <span
                      className={
                        s.status === "accepted"
                          ? "text-green-400 font-bold"
                          : "text-yellow-400 font-bold"
                      }
                    >
                      {s.status}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2 items-center">
                  <a
                    href={downloadUrl(s.file_path)}
                    className="text-blue-400 underline"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Download
                  </a>

                  {(currentUser.role === "org_admin" ||
                    currentUser.role === "super_admin" ||
                    currentUser.role === "team_manager") && (
                    <>
                      <button
                        onClick={() => handleAccept(s.id)}
                        className="bg-green-700 px-2 py-1 rounded hover:bg-green-600 transition"
                      >
                        Accept
                      </button>
                      <button
                        onClick={() => handleDelete(s.id)}
                        className="bg-red-700 px-2 py-1 rounded hover:bg-red-600 transition"
                      >
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
