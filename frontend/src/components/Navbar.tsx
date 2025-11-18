// frontend/components/Navbar.tsx
'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { FaUserTie } from 'react-icons/fa';

export default function Navbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  function handleLogout() {
    // Clear client-side auth state
    logout();
    // Optionally, call backend logout endpoint if you add one:
    // fetch('http://localhost:8000/api/logout', { method: 'POST', credentials: 'include' });
    router.push('/login');
  }

  return (
    <nav className="bg-gray-800 text-white p-4 flex justify-between items-center">
      <div className="text-xl font-bold">
        <Link href="/">AuthApp</Link>
      </div>

      <div className="flex items-center space-x-4">
        <Link href="/assignments">Assignments</Link>

        {(user?.role === 'org_admin' ||
          user?.role === 'super_admin' ||
          user?.role === 'team_manager' ||
          user?.role === 'team-manager') && (
          <Link href="/admin/assignments" className="flex items-center">
            <FaUserTie className="mr-1" />
            Admin
          </Link>
        )}

        {!user ? (
          <Link href="/login">Login</Link>
        ) : (
          <>
            <span className="text-sm px-2">{user.email}</span>
            <button
              onClick={handleLogout}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded"
            >
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
