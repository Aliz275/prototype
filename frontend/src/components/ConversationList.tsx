// File: frontend/src/components/ConversationList.tsx

"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

// =========================
// TYPES
// =========================
type Conversation = {
  id: number;
  name: string | null;
  is_group_chat: number;
};

type UserOption = {
  id: number;
  email: string;
  role?: string;
  isPending?: boolean; // mark pending invites
};

type Invite = {
  id: number;
  email: string;
  role: string;
  status: "pending" | "accepted";
};

const API_BASE = "http://localhost:8000";

// =========================
// SAFE FETCH JSON HELPER
// =========================
async function safeFetchJson(url: string, options?: RequestInit): Promise<any | null> {
  try {
    const res = await fetch(url, options);
    const text = await res.text();
    try {
      return JSON.parse(text);
    } catch {
      console.error(`Invalid JSON from ${url}:`, text);
      return null;
    }
  } catch (err) {
    console.error(`Fetch error for ${url}:`, err);
    return null;
  }
}

// =========================
// COMPONENT
// =========================
export default function ConversationList({ onSelect }: { onSelect: (id: number) => void }) {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showNewMessage, setShowNewMessage] = useState(false);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  // =========================
  // LOAD CONVERSATIONS
  // =========================
  useEffect(() => {
    if (!user) return;

    async function loadConversations() {
      setLoading(true);
      setError("");

      const data = await safeFetchJson(`${API_BASE}/api/conversations`, { credentials: "include" });
      if (data && Array.isArray(data)) {
        setConversations(data);
        if (data.length > 0) {
          setActiveId(data[0].id);
          onSelect(data[0].id);
        }
      } else {
        setError("Failed to load conversations — check backend response or rate limit");
        setConversations([]);
      }

      setLoading(false);
    }

    loadConversations();
  }, [user, onSelect]);

  // =========================
  // LOAD USERS + PENDING INVITES
  // =========================
  useEffect(() => {
    if (!user) return;

    async function loadUsersAndInvites() {
      try {
        const userId = user!.id;

        const usersRaw = await safeFetchJson(`${API_BASE}/api/users`, { credentials: "include" });
        const invitesRaw = await safeFetchJson(`${API_BASE}/api/invitations/pending`, { credentials: "include" });

        const usersData: UserOption[] = Array.isArray(usersRaw) ? usersRaw : [];
        const invitesData: UserOption[] = Array.isArray(invitesRaw)
          ? (invitesRaw as Invite[]).map(i => ({
              ...i,
              id: -i.id,
              isPending: true,
            }))
          : [];

        setUsers([...usersData.filter(u => u.id !== userId), ...invitesData]);
      } catch (err) {
        console.error("Error loading users/invites:", err);
        setUsers([]);
      }
    }

    loadUsersAndInvites();
  }, [user]);

  // =========================
  // SEARCH FILTER
  // =========================
  const filteredUsers = useMemo(() => {
    if (!search.trim()) return users;
    return users.filter(u => u.email.toLowerCase().includes(search.toLowerCase()));
  }, [search, users]);

  // =========================
  // START DIRECT CHAT
  // =========================
  async function startDirectChat() {
    if (!selectedUserId || selectedUserId < 0) return;

    const data = await safeFetchJson(`${API_BASE}/api/conversations/direct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ user_id: selectedUserId }),
    });

    if (!data || !data.conversation_id) {
      alert("Could not start conversation — check backend response");
      return;
    }

    const updated = await safeFetchJson(`${API_BASE}/api/conversations`, { credentials: "include" });
    if (updated && Array.isArray(updated)) setConversations(updated);

    setActiveId(data.conversation_id);
    onSelect(data.conversation_id);

    setShowNewMessage(false);
    setSelectedUserId(null);
    setSearch("");
  }

  // =========================
  // RENDER
  // =========================
  return (
    <aside className="w-80 border-r bg-white flex flex-col">
      <div className="p-4 flex justify-between items-center border-b">
        <span className="text-lg font-semibold">💬 Messages</span>
        <button
          onClick={() => setShowNewMessage(v => !v)}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
        >
          New
        </button>
      </div>

      {showNewMessage && (
        <div className="p-4 border-b space-y-2">
          <input
            type="text"
            placeholder="Search users..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full border rounded p-2 text-sm"
          />

          <select
            value={selectedUserId ?? ""}
            onChange={e => setSelectedUserId(Number(e.target.value))}
            className="w-full border rounded p-2 text-sm"
          >
            <option value="">Select user…</option>
            {filteredUsers.map(u => (
              <option key={u.id} value={u.id}>
                {u.email} {u.isPending ? "(Pending)" : ""}
              </option>
            ))}
          </select>

          <button
            disabled={!selectedUserId || selectedUserId < 0}
            onClick={startDirectChat}
            className={`w-full text-sm py-2 rounded text-white ${
              selectedUserId && selectedUserId > 0 ? "bg-green-600 hover:bg-green-700" : "bg-gray-400 cursor-not-allowed"
            }`}
          >
            Start Chat
          </button>
        </div>
      )}

      {loading && (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-500">
          Loading…
        </div>
      )}

      {error && (
        <div className="p-4 text-sm text-red-600 bg-red-50 border-b">{error}</div>
      )}

      {!loading && !error && conversations.length === 0 && !showNewMessage && (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-500">
          No conversations yet
        </div>
      )}

      <ul className="flex-1 overflow-y-auto divide-y">
        {conversations.map(c => {
          const isActive = c.id === activeId;
          return (
            <li
              key={c.id}
              onClick={() => {
                setActiveId(c.id);
                onSelect(c.id);
              }}
              className={`p-4 cursor-pointer flex gap-3 ${
                isActive ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
            >
              <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold">
                {(c.name || "D")[0]}
              </div>
              <div className="flex-1">
                <div className="font-medium truncate">{c.name || "Direct Message"}</div>
                <div className="text-xs text-gray-500">Click to open</div>
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
