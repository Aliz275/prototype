'use client';
import Link from 'next/link';

export default function Home() {
  return (
    <>
      <main className="flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-4xl font-bold mb-4">Welcome to Our Prototype</h1>
        <p className="text-center text-gray-700 mb-6">Please select your login type:</p>
        <div className="space-x-4">
          {/* Employee Login */}
          <Link
            href="/login"
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
          >
            Employee Login
          </Link>

          {/* Admin / Manager Login */}
          <Link
            href="/admin/login"
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 transition"
          >
            Admin / Manager Login
          </Link>

          {/* Optional Signup */}
          <Link
            href="/signup"
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition"
          >
            Signup
          </Link>
        </div>
      </main>
    </>
  );
}
