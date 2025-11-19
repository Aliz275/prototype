'use client';

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useRouter } from "next/navigation";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

export default function SignupPage() {
  const [serverMessage, setServerMessage] = useState("");
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (data: any) => {
    try {
      // AUTO-SET ORGANIZATION ID = 1
      const payload = {
        ...data,
        organization_id: 1,
      };

      const res = await fetch("http://localhost:8000/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      const result = await res.json();
      setServerMessage(result.message || "");

      if (res.ok) {
        router.push("/login");
      }
    } catch (err) {
      setServerMessage("Error connecting to server.");
    }
  };

  return (
    <main className="max-w-md mx-auto mt-20">
      <h2 className="text-2xl font-bold mb-4">Sign Up</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <input
            placeholder="Email"
            {...register("email")}
            className="w-full p-2 border rounded"
          />
          {errors.email && (
            <p className="text-red-500">
              {errors.email.message as string}
            </p>
          )}
        </div>

        <div>
          <input
            placeholder="Password"
            type="password"
            {...register("password")}
            className="w-full p-2 border rounded"
          />
          {errors.password && (
            <p className="text-red-500">
              {errors.password.message as string}
            </p>
          )}
        </div>

        <button
          type="submit"
          className="bg-green-600 text-white px-4 py-2 rounded"
        >
          Sign Up
        </button>

        {serverMessage && <p>{serverMessage}</p>}
      </form>
    </main>
  );
}
