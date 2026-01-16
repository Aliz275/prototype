"use client";

import { useEffect, useState } from "react";
import { useSocket } from "../context/SocketContext";
import MessageInput from "./MessageInput";

export default function ChatWindow({ conversationId }: { conversationId: number }) {
  const socket = useSocket();
  const [messages, setMessages] = useState<any[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<number[]>([]);

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

    socket.on("message_deleted", ({ message_id }) => {
      setMessages(prev => prev.filter(m => m.id !== message_id));
    });

    socket.on("message_edited", ({ message_id, content }) => {
      setMessages(prev =>
        prev.map(m => m.id === message_id ? { ...m, content } : m)
      );
    });

    socket.on("message_read", ({ message_id }) => {
      setMessages(prev =>
        prev.map(m => m.id === message_id ? { ...m, read: true } : m)
      );
    });

    socket.on("user_status", ({ user_id, status }) => {
      setOnlineUsers(prev =>
        status === "online"
          ? [...new Set([...prev, user_id])]
          : prev.filter(id => id !== user_id)
      );
    });

    return () => {
      socket.emit("leave", { conversation_id: conversationId });
      socket.off();
    };
  }, [conversationId]);

  return (
    <section className="flex-1 flex flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map(m => (
          <div key={m.id} className="mb-2">
            <b>{m.sender_email}</b>: {m.content}
            {m.read && <span className="text-xs ml-2">✓ Read</span>}
          </div>
        ))}
      </div>

      <MessageInput conversationId={conversationId} />
    </section>
  );
}
