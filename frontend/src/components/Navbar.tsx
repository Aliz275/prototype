'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function Navbar() {
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Fetch current user info from backend
    fetch('http://localhost:8000/api/user', {
      credentials: 'include'  // send cookies for session
    })
      .then(res => res.json())
      .then(data => {
        if (data.email) {
          setIsLoggedIn(true);
          setIsAdmin(data.is_admin);
        } else {
          setIsLoggedIn(false);
          setIsAdmin(false);
        }
      })
      .catch(() => {
        setIsLoggedIn(false);
        setIsAdmin(false);
      });
  }, []);

  return (
    <nav className="bg-gray-800 text-white p-4 flex justify-between">
      <Link href="/" className="text-xl font-bold">Prototype</Link>
      <div className="space-x-4">
        {isLoggedIn ? (
          <>
            {isAdmin && <Link href="/employee-section">Employees</Link>}
            <Link href="/logout">Logout</Link>
          </>
        ) : (
          <>
            <Link href="/login">Login</Link>
            <Link href="/signup">Signup</Link>
          </>
        )}
      </div>
    </nav>
  );
}
