import axios from "axios";

const API_BASE = "http://localhost:8000/api";

export const fetchAssignments = async () => {
  const res = await axios.get(`${API_BASE}/assignments`, { withCredentials: true });
  return res.data.assignments;
};

export const fetchSubmissions = async (assignmentId) => {
  const res = await axios.get(`${API_BASE}/submissions/${assignmentId}`, { withCredentials: true });
  return res.data.submissions;
};

export const gradeSubmission = async (submissionId) => {
  const res = await axios.post(`${API_BASE}/submissions/grade/${submissionId}`, {}, { withCredentials: true });
  return res.data;
};

export const deleteSubmission = async (submissionId) => {
  const res = await axios.delete(`${API_BASE}/submissions/${submissionId}`, { withCredentials: true });
  return res.data;
};

export const downloadSubmission = (filename) => {
  window.open(`${API_BASE}/submissions/download/${filename}`, "_blank");
};
