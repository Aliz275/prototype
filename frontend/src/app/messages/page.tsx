"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";

type Conversation = {
  id: number;
  name: string | null;
  is_group_chat: number;
};

const API_BASE = "http://localhost:8000";

export default function ConversationList({
  onSelect,
}: {
  onSelect: (id: number) => void;
}) {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;

    async function loadConversations() {
      try {
        setLoading(true);
        setError("");

        const res = await fetch(`${API_BASE}/api/conversations`, {
          credentials: "include",
        });

        if (res.status === 401 || res.status === 403 ) {
          setError("You are not authorized. Please login again.");
          setConversations([]);
          return;
        }

        if (!res.ok) {
          throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();

        if (Array.isArray(data)) {
          setConversations(data);
        } else {
          console.warn("Unexpected conversations payload:", data);
          setConversations([]);
        }
      } catch (err: any) {
        console.error("Error loading conversations:", err);
        setError(err.message || "Failed to load conversations");
        setConversations([]);
      } finally {
        setLoading(false);
      }
    }

    loadConversations();
  }, [user]);

  return (
    <aside className="w-72 border-r bg-white flex flex-col">
      <div className="p-4 font-semibold border-b">Messages</div>

      {loading && <div className="p-4 text-sm text-gray-500">Loading…</div>}

      {error && <div className="p-4 text-sm text-red-600">{error}</div>}

      {!loading && !error && conversations.length === 0 && (
        <div className="p-4 text-sm text-gray-500">No conversations yet</div>
      )}

      <ul className="flex-1 overflow-y-auto">
        {conversations.map((c) => (
          <li
            key={c.id}
            onClick={() => onSelect(c.id)}
            className="p-3 hover:bg-gray-100 cursor-pointer border-b"
          >
            {c.name || "Direct Message"}
          </li>
        ))}
      </ul>
    </aside>
  );
}