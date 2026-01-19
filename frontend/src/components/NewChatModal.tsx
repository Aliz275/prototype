"use client";

import { useEffect, useState } from "react";

type User = {
  id: number;
  email: string;
};

export default function NewChatModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (conversationId: number) => void;
}) {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/users", {
      credentials: "include",
    })
      .then(res => res.json())
      .then(setUsers);
  }, []);

  async function startChat(userId: number) {
    const res = await fetch("http://localhost:8000/api/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        participant_ids: [userId],
      }),
    });

    const data = await res.json();
    onCreated(data.conversation_id);
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center">
      <div className="bg-white w-96 rounded-lg shadow">
        <div className="p-4 border-b font-semibold">
          Start New Chat
        </div>

        <ul className="max-h-64 overflow-y-auto divide-y">
          {users.map(u => (
            <li
              key={u.id}
              onClick={() => startChat(u.id)}
              className="p-3 hover:bg-gray-100 cursor-pointer"
            >
              {u.email}
            </li>
          ))}
        </ul>

        <div className="p-3 text-right">
          <button
            onClick={onClose}
            className="text-sm text-gray-600 hover:underline"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
