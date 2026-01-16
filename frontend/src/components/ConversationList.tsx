//frontend/src/components/ConversationList.tsx

"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

type Conversation = {
  id: number;
  name: string | null;
  is_group_chat: number;
};

export default function ConversationList({
  onSelect,
}: {
  onSelect: (id: number) => void;
}) {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadConversations() {
      try {
        const res = await fetch("http://localhost:8000/api/conversations", {
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error("Failed to fetch conversations");
        }

        const data = await res.json();

        // ✅ Correct handling
        if (Array.isArray(data)) {
          setConversations(data);
        } else if (Array.isArray(data.conversations)) {
          setConversations(data.conversations);
        } else {
          console.warn("No conversations returned yet");
          setConversations([]);
        }
      } catch (err) {
        console.error(err);
        setError("Unable to load conversations");
      }
    }

    loadConversations();
  }, []);

  return (
    <aside className="w-72 border-r bg-white flex flex-col">
      <div className="p-4 font-bold border-b">Messages</div>

      {error && (
        <div className="p-3 text-red-600 text-sm">{error}</div>
      )}

      <ul className="flex-1 overflow-y-auto">
        {conversations.length === 0 && !error && (
          <li className="p-4 text-gray-500 text-sm">
            No conversations yet
          </li>
        )}

        {conversations.map((c) => (
          <li
            key={c.id}
            onClick={() => onSelect(c.id)}
            className="p-3 hover:bg-gray-100 cursor-pointer border-b"
          >
            {c.name || "Direct Chat"}
          </li>
        ))}
      </ul>
    </aside>
  );
}

