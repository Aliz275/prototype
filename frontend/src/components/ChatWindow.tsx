//frontend/src/components/ChatWindow.tsx

"use client";

import { useEffect, useRef, useState } from "react";
import { useSocket } from "../context/SocketContext";
import MessageInput from "./MessageInput";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({ conversationId }: { conversationId: number }) {
  const socket = useSocket();
  const [messages, setMessages] = useState<any[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/conversations/${conversationId}/messages`, {
      credentials: "include",
    })
      .then(res => res.json())
      .then(setMessages);

    socket.emit("join", { conversation_id: conversationId });

    socket.on("new_message", data => {
      if (data.conversation_id === conversationId) {
        setMessages(prev => [...prev, data.message]);
      }
    });

    return () => {
      socket.emit("leave", { conversation_id: conversationId });
      socket.off();
    };
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b bg-white flex items-center justify-between">
        <div className="font-semibold">Conversation #{conversationId}</div>
        <button className="text-sm text-blue-600 hover:underline">
          View details
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(m => (
          <MessageBubble key={m.id} message={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <MessageInput conversationId={conversationId} />
    </div>
  );
}

