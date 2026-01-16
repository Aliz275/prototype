//frontend/src/components/MessageInput.tsx

"use client";

import { useState } from "react";
import { useSocket } from "../context/SocketContext";

export default function MessageInput({ conversationId }: { conversationId: number }) {
  const socket = useSocket();
  const [content, setContent] = useState("");

  async function send() {
    if (!content.trim()) return;

    await fetch(
      `http://localhost:8000/api/conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ content }),
      }
    );

    setContent("");
  }

  return (
    <div className="p-3 border-t flex gap-2">
      <input
        value={content}
        onChange={e => setContent(e.target.value)}
        className="flex-1 border rounded px-3 py-2"
        placeholder="Type a message..."
        onKeyDown={e => e.key === "Enter" && send()}
      />
      <button onClick={send} className="bg-blue-600 text-white px-4 rounded">
        Send
      </button>
    </div>
  );
}
