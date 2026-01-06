//frontend/src/app/admin/invitations/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useRouter } from "next/navigation";

type Invitation = {
  id: number;
  email: string;
  role: string;
  organization_id: number;
  expires_at: string;
  is_used: boolean;
};

export default function AdminInvitationsPage() {
  const { user } = useAuth();
  const router = useRouter();

  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("employee");
  const [organizationId, setOrganizationId] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  /* 🔐 Protect route */
  useEffect(() => {
    if (user && user.role !== "super_admin") {
      router.push("/login");
    }
  }, [user]);

  /* 📥 Load invitations */
  useEffect(() => {
    if (user?.role === "super_admin") {
      fetchInvitations();
    }
  }, [user]);

  async function fetchInvitations() {
    try {
      const res = await fetch("http://localhost:8000/api/invitations", { // <-- make sure this port matches backend
        credentials: "include",
      });
      const data = await res.json();
      setInvitations(data.invitations || []);
    } catch {
      setError("Failed to load invitations");
    }
  }

  async function createInvitation() {
    setError("");
    setSuccess("");
  
    if (!email || !organizationId) {
      setError("Email and Organization ID are required");
      return;
    }
  
    try {
      const res = await fetch("http://localhost:8000/api/invitations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email,
          role,
          organization_id: Number(organizationId),
        }),
      });
  
      const data = await res.json();
  
      if (!res.ok) throw new Error(data.message);
  
      // ✅ SHOW TOKEN IN SUCCESS MESSAGE
      setSuccess(`Invitation created successfully. Token: ${data.token}`);
  
      setEmail("");
      setOrganizationId("");
      fetchInvitations();
    } catch (err: any) {
      setError(err.message || "Failed to create invitation");
    }
  }
  

  async function deleteInvitation(id: number) {
    if (!confirm("Delete this invitation?")) return;

    try {
      await fetch(`http://localhost:8000/api/invitations/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      fetchInvitations();
    } catch {
      setError("Failed to delete invitation");
    }
  }

  if (!user) return <p className="p-6">Loading...</p>;

  return (
    <main className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-blue-900 mb-6">
        Admin – Invitations
      </h1>

      {/* CREATE INVITATION */}
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Create Invitation</h2>
        {error && <p className="text-red-500 mb-2">{error}</p>}
        {success && <p className="text-green-600 mb-2">{success}</p>}

        <div className="grid gap-3 md:grid-cols-3">
          <input
            className="border p-2 rounded"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <select
            className="border p-2 rounded"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="employee">Employee</option>
            <option value="team_manager">Team Manager</option>
            <option value="org_admin">Org Admin</option>
          </select>
          <input
            className="border p-2 rounded"
            placeholder="Organization ID"
            value={organizationId}
            onChange={(e) => setOrganizationId(e.target.value)}
          />
        </div>

        <button
          onClick={createInvitation}
          className="mt-4 bg-blue-800 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
        >
          Create Invitation
        </button>
      </div>

      {/* INVITATION LIST */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Existing Invitations</h2>
        {invitations.length === 0 ? (
          <p className="text-gray-500">No invitations found.</p>
        ) : (
          <ul className="space-y-3">
            {invitations.map((inv) => (
              <li
                key={inv.id}
                className="border rounded p-3 flex justify-between items-center"
              >
                <div>
                  <div className="font-semibold">{inv.email}</div>
                  <div className="text-sm text-gray-500">
                    Role: {inv.role} | Org: {inv.organization_id}
                  </div>
                  <div className="text-xs text-gray-400">
                    Expires: {inv.expires_at} | Used: {inv.is_used ? "Yes" : "No"}
                  </div>
                </div>
                <button
                  onClick={() => deleteInvitation(inv.id)}
                  className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-500 transition"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
