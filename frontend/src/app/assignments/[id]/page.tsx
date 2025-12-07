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

      setMessage("Uploaded successfully 🎉");
      setUploadFile(null);
      await fetchSubmissions();
    } catch (err: any) {
      setMessage(err.message || "Upload error ❌");
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-200 text-yellow-800";
      case "accepted":
        return "bg-green-700 text-white";
      case "graded":
        return "bg-blue-700 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  if (!currentUser)
    return (
      <p className="p-6 text-center text-gray-400">
        Please log in to see this assignment.
      </p>
    );
  if (loading) return <p className="p-6 text-center">Loading…</p>;
  if (error) return <p className="p-6 text-center text-red-500">{error}</p>;
  if (!assignment) return <p className="p-6 text-center">Assignment not found.</p>;

  return (
    <main className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Assignment Header */}
      <div className="bg-gradient-to-r from-blue-900 to-blue-700 text-white rounded-xl p-6 shadow-lg animate-fadeIn">
        <h1 className="text-3xl font-bold">{assignment.title}</h1>
        {assignment.due_date && (
          <p className="text-sm mt-1 text-blue-200">Due: {assignment.due_date}</p>
        )}
        <p className="mt-3 text-blue-100">{assignment.description}</p>
      </div>

      {/* Upload Section */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-blue-300">Upload Your Submission</h2>
        <form
          onSubmit={handleUpload}
          className="flex flex-col md:flex-row gap-3 items-center"
        >
          <input
            type="file"
            onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
            className="border p-2 rounded-md w-full md:w-auto bg-blue-50"
          />
          <button
            type="submit"
            disabled={uploading}
            className="bg-gradient-to-r from-blue-800 to-blue-600 text-white px-5 py-2 rounded-lg shadow-lg hover:scale-105 hover:shadow-xl transform transition-all duration-300"
          >
            {uploading ? "Uploading…" : "Upload"}
          </button>
          <button
            type="button"
            onClick={() => {
              setUploadFile(null);
              setMessage("");
            }}
            className="px-4 py-2 border rounded-md hover:bg-blue-700 hover:text-white transition"
          >
            Clear
          </button>
        </form>
        {message && <p className="text-sm mt-1 text-blue-200">{message}</p>}
        <p>
          Status:{" "}
          {alreadySubmitted() ? (
            <span className="text-green-400 font-semibold">Already submitted ✅</span>
          ) : (
            <span className="text-gray-400">Not submitted ❌</span>
          )}
        </p>
      </section>

      {/* Submissions List */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-blue-300">Submissions</h2>
        {submissions.length === 0 ? (
          <p className="text-gray-400">No submissions yet 😢</p>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {submissions.map((s) => (
              <div
                key={s.id}
                className="bg-white rounded-xl p-4 shadow-lg hover:shadow-2xl transition-shadow border-l-4 border-blue-700"
              >
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold text-gray-800">
                    {s.employee_email ?? `User ${s.employee_id}`}
                  </h3>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                      s.status
                    )}`}
                  >
                    {s.status.toUpperCase()}
                  </span>
                </div>
                <p className="truncate text-gray-600">{s.file_path}</p>
                <p className="text-gray-400 text-sm mt-1">
                  {new Date(s.submitted_at).toLocaleString()}
                </p>
                <div className="flex gap-2 mt-2">
                  <a
                    href={downloadUrl(s.file_path)}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-700 underline hover:text-blue-900 transition"
                  >
                    📥 Download
                  </a>
                  {(currentUser.role === "org_admin" ||
                    currentUser.role === "super_admin" ||
                    currentUser.role === "team_manager") && (
                    <>
                      <button
                        onClick={() => handleAccept(s.id)}
                        className="bg-green-700 px-3 py-1 rounded hover:bg-green-600 hover:-translate-y-1 transform transition-all duration-200 shadow"
                      >
                        Accept
                      </button>
                      <button
                        onClick={() => handleDelete(s.id)}
                        className="bg-red-700 px-3 py-1 rounded hover:bg-red-600 hover:-translate-y-1 transform transition-all duration-200 shadow"
                      >
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
