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
  confirmPassword: z.string().min(6, "Confirm Password must be at least 6 characters"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

export default function SignupPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: any) => {
    setError("");

    try {
      const payload = {
        email: data.email,
        password: data.password,
        organization_id: 1,
      };

      const res = await fetch("http://localhost:8000/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const result = await res.json();
        setError(result.message || "Signup failed");
        return;
      }

      const result = await res.json();

      // Auto-login
      login(result.email, result.role, result.id);

      if (result.role === "super_admin") router.push("/super/dashboard");
      else if (result.role === "org_admin") router.push("/org/dashboard");
      else if (result.role === "team_manager") router.push("/manager/dashboard");
      else router.push("/assignments");

    } catch (err) {
      console.error(err);
      setError("Failed to connect to the server.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-10 rounded-lg shadow-md w-full max-w-md">

        {/* Title Fix */}
        <h2 className="text-3xl font-bold mb-6 text-center text-green-700">Sign Up</h2>

        {error && <p className="text-red-500 mb-4 text-center">{error}</p>}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">

          {/* Email */}
          <div>
            <label className="block mb-1 font-medium text-gray-800">Email</label>
            <input
              type="email"
              placeholder="Enter your email"
              {...register("email")}
              className="w-full p-3 border rounded-md text-gray-900 placeholder-gray-500 
                         focus:outline-none focus:ring-2 focus:ring-green-400"
            />
            {errors.email && <p className="text-red-500 mt-1">{errors.email.message}</p>}
          </div>

          {/* Password */}
          <div>
            <label className="block mb-1 font-medium text-gray-800">Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              {...register("password")}
              className="w-full p-3 border rounded-md text-gray-900 placeholder-gray-500 
                         focus:outline-none focus:ring-2 focus:ring-green-400"
            />
            {errors.password && <p className="text-red-500 mt-1">{errors.password.message}</p>}
          </div>

          {/* Confirm Password */}
          <div>
            <label className="block mb-1 font-medium text-gray-800">Confirm Password</label>
            <input
              type="password"
              placeholder="Confirm your password"
              {...register("confirmPassword")}
              className="w-full p-3 border rounded-md text-gray-900 placeholder-gray-500 
                         focus:outline-none focus:ring-2 focus:ring-green-400"
            />
            {errors.confirmPassword && (
              <p className="text-red-500 mt-1">{errors.confirmPassword.message}</p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="w-full bg-green-600 text-white py-3 rounded-md hover:bg-green-700 transition-colors"
          >
            Sign Up
          </button>
        </form>

        <p className="mt-6 text-center text-gray-600">
          Already have an account?{" "}
          <a href="/login" className="text-blue-600 hover:underline">Login</a>
        </p>

      </div>
    </div>
  );
}
