"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function AcceptInvitationPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [invitation, setInvitation] = useState<any>(null);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get("token");
    if (!t) {
      setError("No token provided");
      return;
    }
    setToken(t);

    fetch(`http://localhost:8000/api/invitations/${t}`)
      .then(res => res.json())
      .then(setInvitation)
      .catch(() => setError("Invalid invitation"));
  }, []);

  const submit = async () => {
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }

    const res = await fetch("http://localhost:8000/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: invitation.email,
        password,
        role: invitation.role,
        organization_id: invitation.organization_id,
        token
      })
    });

    const data = await res.json();
    if (!res.ok) {
      setError(data.message);
      return;
    }

    setSuccess("Account created! Redirecting...");
    setTimeout(() => router.push("/login"), 2000);
  };

  if (!invitation) return <p className="p-6">Loading...</p>;

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Accept Invitation</h1>

      {error && <p className="text-red-500">{error}</p>}
      {success && <p className="text-green-600">{success}</p>}

      <input
        type="password"
        placeholder="Password"
        className="border p-2 w-full mb-2"
        onChange={e => setPassword(e.target.value)}
      />
      <input
        type="password"
        placeholder="Confirm Password"
        className="border p-2 w-full mb-4"
        onChange={e => setConfirm(e.target.value)}
      />

      <button
        onClick={submit}
        className="bg-blue-600 text-white px-4 py-2 w-full rounded"
      >
        Create Account
      </button>
    </div>
  );
}
