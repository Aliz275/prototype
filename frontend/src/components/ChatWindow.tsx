"use client";

import { useEffect, useRef, useState } from "react";
import { useSocket } from "../context/SocketContext";
import MessageInput from "./MessageInput";

type Message = {
  id: number;
  sender_id: number;
  sender_email: string;
  content: string;
  created_at: string;
};

type ChatWindowProps = {
  conversationId: number;
  conversationName?: string;
  userId?: number; // current logged-in user
};

export default function ChatWindow({
  conversationId,
  conversationName,
  userId,
}: ChatWindowProps) {
  const socket = useSocket();
  const [messages, setMessages] = useState<Message[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Fetch messages on conversation change
  useEffect(() => {
    async function loadMessages() {
      try {
        const res = await fetch(
          `http://localhost:8000/api/conversations/${conversationId}/messages`,
          { credentials: "include" }
        );
        const data: Message[] = await res.json();
        setMessages(data || []);
      } catch (err) {
        console.error("Failed to load messages:", err);
        setMessages([]);
      }
    }

    loadMessages();

    socket.emit("join", { conversation_id: conversationId });

    socket.on("new_message", (data: { conversation_id: number; message: Message }) => {
      if (data.conversation_id === conversationId) {
        setMessages(prev => [...prev, data.message]);
      }
    });

    return () => {
      socket.emit("leave", { conversation_id: conversationId });
      socket.off("new_message");
    };
  }, [conversationId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Helper to check if message is from current user
  const isOwn = (message: Message) => message.sender_id === userId;

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b bg-white shadow-sm">
        <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center text-white font-bold">
          {conversationName?.[0] ?? "?"}
        </div>
        <div className="flex-1 font-semibold">{conversationName || "Conversation"}</div>
        <button className="text-sm text-blue-600 hover:underline">Details</button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${isOwn(msg) ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xs px-3 py-2 rounded-lg break-words ${
                isOwn(msg)
                  ? "bg-blue-600 text-white rounded-br-none"
                  : "bg-gray-200 text-gray-900 rounded-bl-none"
              }`}
            >
              {!isOwn(msg) && (
                <div className="text-xs font-semibold mb-1">{msg.sender_email}</div>
              )}
              <div className="text-sm">{msg.content}</div>
              <div className="text-xs text-gray-400 mt-1 text-right">
                {new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t bg-white p-3">
        <MessageInput conversationId={conversationId} />
      </div>
    </div>
  );
}
