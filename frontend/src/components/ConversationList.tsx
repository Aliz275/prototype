// frontend/src/components/ConversationList.tsx
"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

type Conversation = {
  id: number;
  name: string | null;
  is_group_chat: number;
};

type UserOption = {
  id: number;
  email: string;
};

const API_BASE = "http://localhost:8000";

export default function ConversationList({
  onSelect,
}: {
  onSelect: (id: number) => void;
}) {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showNewMessage, setShowNewMessage] = useState(false);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);

  // Load conversations
  useEffect(() => {
    if (!user) return;

    async function loadConversations() {
      try {
        setLoading(true);
        setError("");

        const res = await fetch(`${API_BASE}/api/conversations`, {
          credentials: "include",
        });

        if (res.status === 401 || res.status === 403) {
          setError("Session expired. Please log in again.");
          setConversations([]);
          return;
        }

        if (!res.ok) {
          throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();

        if (Array.isArray(data)) {
          setConversations(data);
          if (data.length > 0) {
            setActiveId(data[0].id);
            onSelect(data[0].id);
          }
        } else {
          setConversations([]);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load conversations");
        setConversations([]);
      } finally {
        setLoading(false);
      }
    }

    loadConversations();
  }, [user]);

  // Load users for new conversation
  useEffect(() => {
    async function loadUsers() {
      try {
        const res = await fetch(`${API_BASE}/api/users`, {
          credentials: "include",
        });
        const data = await res.json();
        setUsers(data.filter((u: UserOption) => u.id !== user?.id));
      } catch {}
    }
    loadUsers();
  }, [user]);

  // Create new conversation
  async function createConversation() {
    if (!selectedUserId) return;

    try {
      const res = await fetch(`${API_BASE}/api/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ participant_ids: [selectedUserId] }),
      });

      if (!res.ok) throw new Error("Failed to create conversation");

      const newConv = await res.json();
      setConversations((prev) => [...prev, { id: newConv.conversation_id, name: null, is_group_chat: 0 }]);
      setActiveId(newConv.conversation_id);
      onSelect(newConv.conversation_id);
      setShowNewMessage(false);
      setSelectedUserId(null);
    } catch (err) {
      console.error(err);
      alert("Error creating conversation");
    }
  }

  return (
    <aside className="w-80 border-r bg-white flex flex-col">
      {/* Header with New Message button */}
      <div className="p-4 flex justify-between items-center border-b">
        <span className="text-lg font-semibold">💬 Messages</span>
        <button
          onClick={() => setShowNewMessage(!showNewMessage)}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
        >
          New
        </button>
      </div>

      {/* New Message UI */}
      {showNewMessage && (
        <div className="p-4 border-b flex flex-col gap-2">
          <select
            value={selectedUserId ?? ""}
            onChange={(e) => setSelectedUserId(Number(e.target.value))}
            className="border rounded p-2"
          >
            <option value="">Select user...</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.email}</option>
            ))}
          </select>
          <button
            onClick={createConversation}
            className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
          >
            Start Chat
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-500">
          Loading conversations…
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 text-sm text-red-600 bg-red-50 border-b">
          {error}
        </div>
      )}

      {/* Empty */}
      {!loading && !error && conversations.length === 0 && !showNewMessage && (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-500">
          No conversations yet
        </div>
      )}

      {/* Conversation list */}
      <ul className="flex-1 overflow-y-auto divide-y">
        {conversations.map((c) => {
          const isActive = c.id === activeId;
          return (
            <li
              key={c.id}
              onClick={() => {
                setActiveId(c.id);
                onSelect(c.id);
              }}
              className={`flex items-center gap-3 p-4 cursor-pointer transition-colors ${isActive ? "bg-blue-50" : "hover:bg-gray-50"}`}
            >
              <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold">
                {(c.name || "D")[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{c.name || "Direct Message"}</div>
                <div className="text-xs text-gray-500 truncate">Click to open conversation</div>
              </div>
              {isActive && <div className="w-2 h-2 bg-blue-600 rounded-full" />}
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
