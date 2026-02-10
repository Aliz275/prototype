//frontend/src/components/MessageInput.tsx

"use client";

import { useState } from "react";
import { useSocket } from "../context/SocketContext";

export default function MessageInput({
  conversationId,
}: {
  conversationId: number;
}) {
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
    socket.emit("stop_typing", { conversation_id: conversationId });
  }

  function handleTyping(e: React.ChangeEvent<HTMLInputElement>) {
    setContent(e.target.value);
    socket.emit("typing", { conversation_id: conversationId });
  }

  return (
    <div className="p-3 border-t bg-white flex gap-2">
      <input
        value={content}
        onChange={handleTyping}
        onKeyDown={e => e.key === "Enter" && send()}
        onBlur={() =>
          socket.emit("stop_typing", { conversation_id: conversationId })
        }
        className="flex-1 border rounded-full px-4 py-2 text-sm focus:outline-none focus:ring"
        placeholder="Type a message…"
        spellCheck="true"
      />
      <button
        onClick={send}
        className="bg-blue-600 text-white px-5 rounded-full text-sm hover:bg-blue-700"
      >
        Send
      </button>
    </div>
  );
}
