//frontend/src/components/ConversationList.tsx

"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Conversation } from "../types/conversation";

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
  conversations,
  activeConversationId,
  onSelect,
  onConversationCreated,
}: {
  conversations: Conversation[];
  activeConversationId: number | null;
  onSelect: (id: number | null) => void;
  onConversationCreated: (c: Conversation) => void;
}) {
  const { user } = useAuth();

  const [users, setUsers] = useState<UserOption[]>([]);
  const [search, setSearch] = useState("");

  const [showDirect, setShowDirect] = useState(false);
  const [showGroup, setShowGroup] = useState(false);

  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
  const [groupName, setGroupName] = useState("");

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

  /* ================= DIRECT CHAT ================= */
  async function startDirectChat() {
    if (!user || !selectedUserId) return;

    const other = users.find(u => u.id === selectedUserId);
    if (!other) return;

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

    onConversationCreated({
      id: data.conversation_id,
      name: null,
      is_group_chat: false,
      participants: [
        { id: user.id, email: user.email },
        { id: other.id, email: other.email },
      ],
    });

    reset();
  }

  /* ================= GROUP CHAT ================= */
  async function createGroupChat() {
    if (!user || user.role !== "super_admin") return;
    if (!groupName || selectedUserIds.length === 0) return;

    const data = await safeFetchJson(`${API_BASE}/api/conversations`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: groupName,
        participant_ids: selectedUserIds,
      }),
    });

    if (!data?.conversation_id) return;

    const participants = users.filter(u =>
      selectedUserIds.includes(u.id)
    );
    participants.push({ id: user.id, email: user.email });

    onConversationCreated({
      id: data.conversation_id,
      name: groupName,
      is_group_chat: true,
      participants,
    });

    reset();
  }

  function reset() {
    setShowDirect(false);
    setShowGroup(false);
    setSelectedUserId(null);
    setSelectedUserIds([]);
    setGroupName("");
    setSearch("");
  }

  /* ================= FILTER USERS ================= */
  const filteredUsers = useMemo(() => {
    if (!search) return users;
    return users.filter(u =>
      u.email.toLowerCase().includes(search.toLowerCase())
    );
  }, [search, users]);

  function getConversationName(c: Conversation) {
    if (c.is_group_chat && c.name) return c.name;
    const other = c.participants.find(p => p.email !== user?.email);
    return other?.email ?? "Direct Message";
  }

  /* ================= RENDER ================= */
  return (
    <aside className="w-80 border-r bg-white flex flex-col">
      <div className="p-4 flex justify-between items-center border-b">
        <span className="font-semibold">💬 Messages</span>

        <div className="flex gap-2">
          <button
            onClick={() => {
              reset();
              setShowDirect(true);
            }}
            className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
          >
            New
          </button>

          {user?.role === "super_admin" && (
            <button
              onClick={() => {
                reset();
                setShowGroup(true);
              }}
              className="bg-purple-600 text-white px-3 py-1 rounded text-sm"
            >
              New Group
            </button>
          )}
        </div>
      </div>

      {(showDirect || showGroup) && (
        <div className="p-4 border-b space-y-2">
          {showGroup && (
            <input
              placeholder="Group name"
              className="w-full border rounded p-2 text-sm"
              value={groupName}
              onChange={e => setGroupName(e.target.value)}
            />
          )}

          <input
            placeholder="Search users..."
            className="w-full border rounded p-2 text-sm"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />

          <div className="max-h-48 overflow-y-auto border rounded">
            {filteredUsers.map(u => (
              <label
                key={u.id}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer"
              >
                {showGroup ? (
                  <input
                    type="checkbox"
                    checked={selectedUserIds.includes(u.id)}
                    onChange={() =>
                      setSelectedUserIds(prev =>
                        prev.includes(u.id)
                          ? prev.filter(x => x !== u.id)
                          : [...prev, u.id]
                      )
                    }
                  />
                ) : (
                  <input
                    type="radio"
                    name="direct-user"
                    checked={selectedUserId === u.id}
                    onChange={() => setSelectedUserId(u.id)}
                  />
                )}
                <span className="text-sm">{u.email}</span>
              </label>
            ))}
          </div>

          {showDirect ? (
            <button
              onClick={startDirectChat}
              disabled={!selectedUserId}
              className="w-full bg-green-600 text-white rounded py-2 text-sm disabled:bg-gray-400"
            >
              Start Chat
            </button>
          ) : (
            <button
              onClick={createGroupChat}
              disabled={!groupName || selectedUserIds.length === 0}
              className="w-full bg-purple-600 text-white rounded py-2 text-sm disabled:bg-gray-400"
            >
              Create Group
            </button>
          )}
        </div>
      )}

      <ul className="flex-1 overflow-y-auto divide-y">
        {conversations.map(c => {
          const name = getConversationName(c);
          const active = activeConversationId === c.id;

          return (
            <li
              key={c.id}
              onClick={() => {
                // ✅ IMPORTANT FIX:
                // never deselect the active conversation
                if (!active) {
                  onSelect(c.id);
                }
              }}
              className={`p-4 cursor-pointer flex gap-3 ${
                active ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
            >
              <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold">
                {name[0]?.toUpperCase()}
              </div>
              <div>
                <div className="font-medium truncate">{name}</div>
                <div className="text-xs text-gray-500">
                  {c.is_group_chat ? "Group chat" : "Direct message"}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}

