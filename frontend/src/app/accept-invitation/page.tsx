"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function AcceptInvitationPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [invitation, setInvitation] = useState<any>(null);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const t = urlParams.get("token");
    if (!t) {
      setError("No token provided");
      setLoading(false);
      return;
    }
    setToken(t);

    fetch(`http://localhost:8000/api/invitations/${t}`, {
      credentials: "include",
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || "Invalid token");
        setInvitation(data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleRegister = async () => {
    setError("");
    setSuccess("");

    if (!password || !confirmPassword) {
      setError("Please fill both password fields");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: invitation.email,
          password,
          role: invitation.role,
          organization_id: invitation.organization_id,
          token,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message);

      setSuccess("Account created successfully! Redirecting to login...");
      setTimeout(() => router.push("/login"), 2000);
    } catch (err: any) {
      setError(err.message || "Failed to register");
    }
  };

  if (loading) return <p className="p-6">Loading...</p>;
  if (error) return <p className="p-6 text-red-500">{error}</p>;

  return (
    <main className="p-6 max-w-md mx-auto">
      <h1 className="text-3xl font-bold text-blue-900 mb-6">Accept Invitation</h1>

      <div className="bg-white rounded-xl shadow p-6">
        <p className="mb-2"><strong>Email:</strong> {invitation.email}</p>
        <p className="mb-2"><strong>Role:</strong> {invitation.role}</p>
        <p className="mb-4"><strong>Organization ID:</strong> {invitation.organization_id}</p>

        {error && <p className="text-red-500 mb-2">{error}</p>}
        {success && <p className="text-green-600 mb-2">{success}</p>}

        <input type="password" placeholder="Password" className="border p-2 rounded w-full mb-3" value={password} onChange={e => setPassword(e.target.value)} />
        <input type="password" placeholder="Confirm Password" className="border p-2 rounded w-full mb-3" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />

        <button onClick={handleRegister} className="bg-blue-800 text-white px-4 py-2 rounded hover:bg-blue-700 transition w-full">
          Create Account
        </button>
      </div>
    </main>
  );
}
