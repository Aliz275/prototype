"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      // ❌ Backend does NOT return `message`
      // ✔ Backend returns { error: "Invalid credentials" }
      if (!response.ok) {
        setError(data.error || "Login failed");
        return;
      }

      // ✅ Store user info in localStorage
      localStorage.setItem("user", JSON.stringify(data));

      console.log("Logged in user:", data);

      // 👉 BACKEND RETURNS:
      // { id, email, role, is_admin, organization_id }

      // 🚦 Redirect logic (clean + real)
      if (data.role === "super_admin") {
        router.push("/super/dashboard");
        return;
      }

      if (data.role === "org_admin") {
        router.push("/org/dashboard");
        return;
      }

      if (data.role === "team_manager") {
        router.push("/manager/dashboard");
        return;
      }

      // Default:
      router.push("/assignments");

    } catch (err) {
      console.error(err);
      setError("Server error");
    }
  }

  return (
    <div style={{ padding: "50px" }}>
      <h1>Login</h1>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <form onSubmit={handleLogin}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        /><br /><br />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        /><br /><br />

        <button type="submit">Login</button>
      </form>
    </div>
  );
}
