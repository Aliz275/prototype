"use client";

import { useState } from "react";

export default function AssignmentUploader({ assignmentId }: { assignmentId: number }) {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please choose a file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`/api/submissions/${assignmentId}`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setMessage("Upload successful!");
      } else {
        setMessage(data.message || "Upload failed.");
      }
    } catch (err) {
      console.error(err);
      setMessage("Upload failed — server error.");
    }
  };

  return (
    <div className="border p-4 rounded mt-6">
      <h3 className="text-lg font-semibold mb-2">Upload Your Work</h3>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="mb-3"
      />

      <button
        onClick={handleUpload}
        className="bg-blue-600 text-white px-4 py-2 rounded"
      >
        Submit
      </button>

      {message && (
        <p className="mt-3 text-sm text-gray-800">{message}</p>
      )}
    </div>
  );
}
