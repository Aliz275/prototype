'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';

type Team = {
  id: number;
  name: string;
  manager_id: number;
};

type UserWithId = {
  id: number;
  email: string;
  role: string;
};

export default function CreateAssignmentPage() {
  const router = useRouter();
  const { user } = useAuth();
  const currentUser = user as UserWithId;

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [scope, setScope] = useState<'general' | 'team' | 'individual'>('general');
  const [teamId, setTeamId] = useState('');
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [allUsers, setAllUsers] = useState<UserWithId[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Fetch teams
  useEffect(() => {
    fetch('http://localhost:8000/api/teams', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setTeams(data))
      .catch(err => console.error(err));
  }, []);

  // Fetch all users for multiselect
  useEffect(() => {
    fetch('http://localhost:8000/api/users', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setAllUsers(data.users || []))
      .catch(err => console.error(err));
  }, []);

  if (!user) return <div className="p-6">Please log in to create assignments.</div>;
  if (!(currentUser.role === 'org_admin' || currentUser.role === 'team_manager' || currentUser.role === 'super_admin')) {
    return <div className="p-6">Access denied: you don't have permission to create assignments.</div>;
  }

  function toggleUser(id: number) {
    setSelectedUsers(prev =>
      prev.includes(id) ? prev.filter(u => u !== id) : [...prev, id]
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);

    if (!title.trim()) return setMessage('Title is required');

    const payload: any = {
      title: title.trim(),
      description: description.trim(),
      due_date: dueDate || null,
    };

    if (scope === 'team') {
      const selectedTeamId = Number(teamId);
      const team = teams.find(t => t.id === selectedTeamId);

      if (!team) return setMessage('Team not found');

      if (currentUser.role === 'team_manager' && team.manager_id !== currentUser.id) {
        return setMessage("You can only assign to teams you manage");
      }

      payload.team_id = selectedTeamId;
    }

    if (scope === 'individual') {
      if (selectedUsers.length === 0) {
        return setMessage("Select at least one user");
      }
      payload.employee_ids = selectedUsers;
    }

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/assignments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        return setMessage(data?.message || `Server error ${res.status}`);
      }

      setMessage("Assignment created successfully!");
      setTimeout(() => router.push('/assignments'), 900);

    } catch (err: any) {
      setMessage(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Create Assignment</h1>

      <form onSubmit={onSubmit} className="space-y-4">

        <div>
          <label className="block text-sm font-medium">Title</label>
          <input className="w-full p-2 border rounded" value={title} onChange={e => setTitle(e.target.value)} />
        </div>

        <div>
          <label className="block text-sm font-medium">Description</label>
          <textarea className="w-full p-2 border rounded" rows={4} value={description} onChange={e => setDescription(e.target.value)} />
        </div>

        <div>
          <label className="block text-sm font-medium">Due date</label>
          <input type="date" className="p-2 border rounded" value={dueDate} onChange={e => setDueDate(e.target.value)} />
        </div>

        <div>
          <label className="block text-sm font-medium">Scope</label>
          <select className="p-2 border rounded" value={scope} onChange={e => setScope(e.target.value as any)}>
            <option value="general">General (organization-wide)</option>
            <option value="team">Team</option>
            <option value="individual">Individual</option>
          </select>
        </div>

        {scope === 'team' && (
          <div>
            <label className="block text-sm font-medium">Team ID</label>
            <input className="w-full p-2 border rounded" value={teamId} onChange={e => setTeamId(e.target.value)} placeholder="e.g. 3" />
          </div>
        )}

        {scope === 'individual' && (
          <div className="border rounded p-3 max-h-72 overflow-auto">
            <label className="block text-sm font-medium mb-2">Select Users</label>

            <div className="grid gap-2">
              {allUsers.map(u => (
                <label key={u.id} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedUsers.includes(u.id)}
                    onChange={() => toggleUser(u.id)}
                  />
                  {u.email} (ID: {u.id})
                </label>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-3">
          <button type="submit" disabled={loading} className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-60">
            {loading ? 'Creating…' : 'Create Assignment'}
          </button>

          <button
            type="button"
            className="px-3 py-2 border rounded"
            onClick={() => {
              setTitle(''); setDescription(''); setDueDate('');
              setScope('general'); setTeamId(''); setSelectedUsers([]);
              setMessage(null);
            }}
          >
            Reset
          </button>
        </div>

        {message && <p className="text-sm mt-2">{message}</p>}
      </form>
    </main>
  );
}
