'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { FaUserTie, FaComments } from 'react-icons/fa';

export default function Navbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    router.push('/login');
  }

  return (
    <nav className="bg-gray-800 text-white p-4 flex justify-between items-center">
      {/* Left side */}
      <div className="text-xl font-bold">
        <Link href="/">AuthApp</Link>
      </div>

      {/* Right side */}
      <div className="flex items-center space-x-4">
        {/* Assignments */}
        <Link href="/assignments">Assignments</Link>

        {/* 🔹 Messages tab (NEW) */}
        {user && (
          <Link
            href="/messages"
            className="flex items-center gap-1 hover:text-gray-300"
          >
            <FaComments />
            Messages
          </Link>
        )}

        {/* Admin section */}
        {(user?.role === 'org_admin' ||
          user?.role === 'super_admin' ||
          user?.role === 'team_manager') && (
          <Link href="/admin/assignments" className="flex items-center gap-1">
            <FaUserTie />
            Admin
          </Link>
        )}

        {/* Invitations – super admin only */}
        {user?.role === 'super_admin' && (
          <Link
            href="/admin/invitations"
            className="px-2 py-1 rounded hover:bg-gray-700"
          >
            Invitations
          </Link>
        )}

        {/* Auth */}
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
