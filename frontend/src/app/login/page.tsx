'use client';

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginForm = z.infer<typeof schema>;

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: LoginForm) => {
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(data),
      });

      const result = await res.json();

      if (!res.ok) {
        setError(result.message || "Login failed");
        return;
      }

      // login into context
      login(result.email, result.role, result.id);

      // redirect based on role
      if (result.role === "super_admin") router.push("/super/dashboard");
      else if (result.role === "org_admin") router.push("/org/dashboard");
      else if (result.role === "team_manager") router.push("/manager/dashboard");
      else router.push("/assignments");

    } catch (err) {
      console.error(err);
      setError("Server error. Please try again later.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-10 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center text-blue-700">Login</h2>

        {error && <p className="text-red-500 mb-4 text-center">{error}</p>}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block mb-1 font-medium text-gray-800">Email</label>
            <input
              type="email"
              placeholder="Enter your email"
              {...register("email")}
              className="w-full p-3 border rounded-md text-gray-900 placeholder-gray-500 
                         focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            {errors.email && <p className="text-red-500 mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block mb-1 font-medium text-gray-800">Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              {...register("password")}
              className="w-full p-3 border rounded-md text-gray-900 placeholder-gray-500 
                         focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            {errors.password && <p className="text-red-500 mt-1">{errors.password.message}</p>}
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 transition-colors"
          >
            Login
          </button>
        </form>

        <p className="mt-6 text-center text-gray-600">
          Don't have an account?{" "}
          <a href="/signup" className="text-blue-600 hover:underline">
            Sign up
          </a>
        </p>
      </div>
    </div>
  );
}
