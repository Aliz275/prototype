'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';

type Team = {
  id: number;
  name: string;
  manager_id: number; // needed for validation
};

type UserWithId = {
  id: number;
  email: string;
  role: string;
};

export default function CreateAssignmentPage() {
  const router = useRouter();
  const { user } = useAuth();
  const currentUser = user as UserWithId; // TypeScript knows id exists now

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [scope, setScope] = useState<'general' | 'team' | 'individual'>('general');
  const [teamId, setTeamId] = useState('');
  const [employeeIds, setEmployeeIds] = useState('');
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Fetch all teams (needed for team selection validation)
  useEffect(() => {
    async function loadTeams() {
      try {
        const res = await fetch('http://localhost:8000/api/teams', {
          credentials: 'include',
        });
        if (!res.ok) throw new Error('Failed to fetch teams');
        const data = await res.json();
        setTeams(data);
      } catch (err: any) {
        console.error(err);
      }
    }
    loadTeams();
  }, []);

  // Role check
  if (!user) return <div className="p-6">Please log in to create assignments.</div>;
  if (!(currentUser.role === 'org_admin' || currentUser.role === 'team_manager' || currentUser.role === 'super_admin')) {
    return <div className="p-6">Access denied: you don't have permission to create assignments.</div>;
  }

  function parseEmployeeIds(input: string): number[] {
    return input
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .map(s => Number(s))
      .filter(n => !Number.isNaN(n) && n > 0);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);

    if (!title.trim()) { setMessage('Title is required'); return; }

    const payload: any = {
      title: title.trim(),
      description: description.trim(),
      due_date: dueDate || null,
    };

    if (scope === 'team') {
      const selectedTeamId = Number(teamId);
      const team = teams.find(t => t.id === selectedTeamId);
      if (!team) { setMessage('Team not found'); return; }

      // Team Manager validation
      if (currentUser.role === 'team_manager' && team.manager_id !== currentUser.id) {
        setMessage("You can only assign to teams you manage");
        return;
      }

      payload.team_id = selectedTeamId;
    } else if (scope === 'individual') {
      const ids = parseEmployeeIds(employeeIds);
      payload.employee_ids = ids;
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
        const errMsg = data?.message || `Server error ${res.status}`;
        setMessage(`Error: ${errMsg}`);
        setLoading(false);
        return;
      }

      setMessage('Assignment created successfully!');
      setTimeout(() => router.push('/assignments'), 900);
    } catch (err: any) {
      setMessage(`Network error: ${err.message || err}`);
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
          <input value={title} onChange={e => setTitle(e.target.value)} className="w-full p-2 border rounded" />
        </div>

        <div>
          <label className="block text-sm font-medium">Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} className="w-full p-2 border rounded" rows={4} />
        </div>

        <div>
          <label className="block text-sm font-medium">Due date</label>
          <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} className="p-2 border rounded" />
        </div>

        <div>
          <label className="block text-sm font-medium">Scope</label>
          <select value={scope} onChange={e => setScope(e.target.value as any)} className="p-2 border rounded">
            <option value="general">General (organization-wide)</option>
            <option value="team">Team</option>
            <option value="individual">Individual</option>
          </select>
        </div>

        {scope === 'team' && (
          <div>
            <label className="block text-sm font-medium">Team ID</label>
            <input value={teamId} onChange={e => setTeamId(e.target.value)} placeholder="e.g. 3" className="w-full p-2 border rounded" />
            <p className="text-sm text-gray-500 mt-1">Team ID must be a number. Backend will verify manager permission.</p>
          </div>
        )}

        {scope === 'individual' && (
          <div>
            <label className="block text-sm font-medium">Employee IDs (comma separated)</label>
            <input value={employeeIds} onChange={e => setEmployeeIds(e.target.value)} placeholder="e.g. 5,7,12" className="w-full p-2 border rounded" />
            <p className="text-sm text-gray-500 mt-1">Enter user IDs separated by commas. Backend will link them to the assignment.</p>
          </div>
        )}

        <div className="flex items-center gap-3">
          <button type="submit" disabled={loading} className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-60">
            {loading ? 'Creating…' : 'Create Assignment'}
          </button>
          <button type="button" onClick={() => { setTitle(''); setDescription(''); setDueDate(''); setScope('general'); setTeamId(''); setEmployeeIds(''); setMessage(null); }} className="px-3 py-2 border rounded">
            Reset
          </button>
        </div>

        {message && <p className="mt-2 text-sm">{message}</p>}
      </form>
    </main>
  );
}
