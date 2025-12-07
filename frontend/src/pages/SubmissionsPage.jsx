import React, { useEffect, useState } from "react";
import {
  fetchAssignments,
  fetchSubmissions,
  gradeSubmission,
  deleteSubmission,
  downloadSubmission,
} from "../api/submissionApi";

const SubmissionsPage = () => {
  const [assignments, setAssignments] = useState([]);
  const [submissionsMap, setSubmissionsMap] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      const allAssignments = await fetchAssignments();
      setAssignments(allAssignments);

      const map = {};
      for (let a of allAssignments) {
        const subs = await fetchSubmissions(a.id);
        // sort by submitted_at descending
        subs.sort((x, y) => new Date(y.submitted_at) - new Date(x.submitted_at));
        map[a.id] = subs;
      }
      setSubmissionsMap(map);
      setLoading(false);
    };
    loadData();
  }, []);

  const handleGrade = async (subId, assignmentId) => {
    await gradeSubmission(subId);
    const updatedSubs = await fetchSubmissions(assignmentId);
    updatedSubs.sort((x, y) => new Date(y.submitted_at) - new Date(x.submitted_at));
    setSubmissionsMap((prev) => ({ ...prev, [assignmentId]: updatedSubs }));
  };

  const handleDelete = async (subId, assignmentId) => {
    if (!window.confirm("Are you sure you want to delete this submission?")) return;
    await deleteSubmission(subId);
    const updatedSubs = await fetchSubmissions(assignmentId);
    updatedSubs.sort((x, y) => new Date(y.submitted_at) - new Date(x.submitted_at));
    setSubmissionsMap((prev) => ({ ...prev, [assignmentId]: updatedSubs }));
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Assignment Submissions</h1>
      {assignments.map((a) => (
        <div key={a.id} className="mb-6 border p-4 rounded-lg shadow-sm">
          <h2 className="font-semibold text-xl mb-2">{a.title}</h2>
          <p className="mb-2">{a.description}</p>
          <p className="text-sm mb-2">Due: {a.due_date || "N/A"}</p>

          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="border p-2">Employee ID</th>
                <th className="border p-2">File</th>
                <th className="border p-2">Submitted At</th>
                <th className="border p-2">Status</th>
                <th className="border p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {submissionsMap[a.id] && submissionsMap[a.id].length > 0 ? (
                submissionsMap[a.id].map((sub, idx) => (
                  <tr
                    key={sub.id}
                    className={idx === 0 ? "bg-yellow-100" : ""} // highlight latest
                  >
                    <td className="border p-2">{sub.employee_id}</td>
                    <td className="border p-2">
                      <button
                        className="text-blue-600 underline"
                        onClick={() => downloadSubmission(sub.file_path)}
                      >
                        {sub.file_path}
                      </button>
                    </td>
                    <td className="border p-2">{sub.submitted_at}</td>
                    <td className="border p-2">{sub.status || "pending"}</td>
                    <td className="border p-2 space-x-2">
                      {sub.status !== "graded" && (
                        <button
                          className="bg-green-500 text-white px-2 py-1 rounded"
                          onClick={() => handleGrade(sub.id, a.id)}
                        >
                          Grade
                        </button>
                      )}
                      <button
                        className="bg-red-500 text-white px-2 py-1 rounded"
                        onClick={() => handleDelete(sub.id, a.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="border p-2" colSpan={5}>
                    No submissions
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
};

export default SubmissionsPage;
