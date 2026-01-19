"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

type Participant = {
  id: number;
  email: string;
};

type Conversation = {
  id: number;
  name: string | null;
  is_group_chat: number;
  participants: Participant[];
};

type UserOption = {
  id: number;
  email: string;
};

const API_BASE = "http://localhost:8000";

async function safeFetchJson(url: string, options?: RequestInit) {
  try {
    const res = await fetch(url, options);
    const text = await res.text();
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export default function ConversationList({
  onSelect,
}: {
  onSelect: (id: number) => void;
}) {
  const { user } = useAuth();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);

  const [showNew, setShowNew] = useState(false);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  /* ================= LOAD CONVERSATIONS ================= */
  useEffect(() => {
    if (!user) return;

    safeFetchJson(`${API_BASE}/api/conversations`, {
      credentials: "include",
    }).then(data => {
      if (Array.isArray(data)) {
        setConversations(
          data.map(c => ({
            ...c,
            participants: c.participants ?? [],
          }))
        );
      }
    });
  }, [user]);

  /* ================= LOAD USERS ================= */
  useEffect(() => {
    if (!user) return;

    safeFetchJson(`${API_BASE}/api/users`, {
      credentials: "include",
    }).then(data => {
      if (Array.isArray(data)) {
        setUsers(data.filter(u => u.id !== user.id));
      }
    });
  }, [user]);

  /* ================= START CHAT ================= */
  async function startChat() {
    if (!selectedUserId || !user) return;

    const otherUser = users.find(u => u.id === selectedUserId);
    if (!otherUser) return;

    const data = await safeFetchJson(
      `${API_BASE}/api/conversations/direct`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: selectedUserId }),
      }
    );

    if (!data?.conversation_id) return;

    // 🔥 FORCE participants so name NEVER becomes "Direct Message"
    const newConversation: Conversation = {
      id: data.conversation_id,
      name: null,
      is_group_chat: 0,
      participants: [
        { id: user.id, email: user.email },
        { id: otherUser.id, email: otherUser.email },
      ],
    };

    if (!conversations.find(c => c.id === newConversation.id)) {
      setConversations(prev => [...prev, newConversation]);
    }

    setActiveId(newConversation.id);
    onSelect(newConversation.id);

    setShowNew(false);
    setSelectedUserId(null);
    setSearch("");
  }

  /* ================= DISPLAY NAME ================= */
  function getConversationName(c: Conversation) {
    if (c.name) return c.name;

    const other = c.participants.find(p => p.email !== user?.email);
    return other?.email ?? "Direct Message";
  }

  const filteredUsers = useMemo(() => {
    if (!search) return users;
    return users.filter(u =>
      u.email.toLowerCase().includes(search.toLowerCase())
    );
  }, [search, users]);

  return (
    <aside className="w-80 border-r bg-white flex flex-col">
      <div className="p-4 flex justify-between items-center border-b">
        <span className="font-semibold">💬 Messages</span>
        <button
          onClick={() => setShowNew(v => !v)}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
        >
          New
        </button>
      </div>

      {showNew && (
        <div className="p-4 border-b space-y-2">
          <input
            placeholder="Search users..."
            className="w-full border rounded p-2 text-sm"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />

          <select
            className="w-full border rounded p-2 text-sm"
            value={selectedUserId ?? ""}
            onChange={e => setSelectedUserId(Number(e.target.value))}
          >
            <option value="">Select user</option>
            {filteredUsers.map(u => (
              <option key={u.id} value={u.id}>
                {u.email}
              </option>
            ))}
          </select>

          <button
            onClick={startChat}
            disabled={!selectedUserId}
            className="w-full bg-green-600 text-white rounded py-2 text-sm disabled:bg-gray-400"
          >
            Start Chat
          </button>
        </div>
      )}

      <ul className="flex-1 overflow-y-auto divide-y">
        {conversations.map(c => {
          const name = getConversationName(c);
          return (
            <li
              key={c.id}
              onClick={() => {
                setActiveId(c.id);
                onSelect(c.id);
              }}
              className={`p-4 cursor-pointer flex gap-3 ${
                activeId === c.id ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
            >
              <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold">
                {name[0]?.toUpperCase()}
              </div>
              <div>
                <div className="font-medium truncate">{name}</div>
                <div className="text-xs text-gray-500">Click to open</div>
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
