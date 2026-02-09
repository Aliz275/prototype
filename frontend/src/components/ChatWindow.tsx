//frontend/src/components/ChatWindow.tsx

"use client";

import { useEffect, useRef, useState } from "react";
import { useSocket } from "../context/SocketContext";
import MessageInput from "./MessageInput";
import { Conversation } from "../types/conversation";

type Message = {
  id: number;
  sender_email: string;
  content: string;
  created_at: string;
};

type Participant = {
  id: number;
  email: string;
  role: string;
};

const API_BASE = "http://localhost:8000";

export default function ChatWindow({
  conversation,
  currentUser,
  onDeleted,
}: {
  conversation: Conversation;
  currentUser: { id: number; email: string; role: string };
  onDeleted: () => void;
}) {
  const socket = useSocket();
  const bottomRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [showDetails, setShowDetails] = useState(false);
  const [loading, setLoading] = useState(false);

  const conversationId = conversation.id;
  const isGroup = Boolean(conversation.is_group_chat);
  const isSuperAdmin = currentUser.role === "super_admin";

  /* ================= LOAD MESSAGES ================= */
  useEffect(() => {
    async function loadMessages() {
      try {
        const res = await fetch(
          `${API_BASE}/api/conversations/${conversationId}/messages`,
          { credentials: "include" }
        );
        if (!res.ok) return;
        const data = await res.json();
        setMessages(data);
      } catch {
        // silent fail
      }
    }

    loadMessages();

    socket.emit("join", { conversation_id: conversationId });

    socket.on("new_message", (data: any) => {
      if (data.conversation_id === conversationId) {
        setMessages(prev => [...prev, data.message]);
      }
    });

    return () => {
      socket.emit("leave", { conversation_id: conversationId });
      socket.off("new_message");
    };
  }, [conversationId, socket]);

  /* ================= AUTO SCROLL ================= */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* ================= LOAD PARTICIPANTS ================= */
  useEffect(() => {
    if (!showDetails) return;

    async function loadParticipants() {
      try {
        const res = await fetch(
          `${API_BASE}/api/conversations/${conversationId}/participants`,
          { credentials: "include" }
        );
        if (!res.ok) return;
        const data = await res.json();
        setParticipants(data);
      } catch {
        // silent
      }
    }

    loadParticipants();
  }, [showDetails, conversationId]);

  /* ================= DELETE / LEAVE ================= */
  async function handleDeleteOrLeave() {
    const confirmMsg = isSuperAdmin
      ? "Delete this conversation for everyone?"
      : isGroup
      ? "Leave this group?"
      : "Delete this chat?";

    if (!confirm(confirmMsg)) return;

    setLoading(true);

    try {
      const url = isSuperAdmin
        ? `${API_BASE}/api/conversations/${conversationId}`
        : `${API_BASE}/api/conversations/${conversationId}/leave`;

      const method = isSuperAdmin ? "DELETE" : "POST";

      const res = await fetch(url, {
        method,
        credentials: "include",
      });

      if (res.ok) {
        onDeleted();
      }
    } catch {
      // silent fail
    } finally {
      setLoading(false);
    }
  }

  const displayName = isGroup
    ? conversation.name || "Group Chat"
    : conversation.participants.find(
        p => p.email !== currentUser.email
      )?.email || "Direct Chat";

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* HEADER */}
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <div className="font-semibold truncate">{displayName}</div>

        <button
          onClick={() => setShowDetails(true)}
          className="text-sm text-blue-600 hover:underline"
        >
          Details
        </button>
      </div>

      {/* MESSAGES */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${
              msg.sender_email === currentUser.email
                ? "justify-end"
                : "justify-start"
            }`}
          >
            <div
              className={`max-w-xs rounded p-2 text-sm ${
                msg.sender_email === currentUser.email
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* INPUT */}
      <div className="border-t bg-white p-3">
        <MessageInput conversationId={conversationId} />
      </div>

      {/* DETAILS MODAL */}
      {showDetails && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
          <div className="bg-white w-96 rounded-lg p-4 space-y-4">
            <h2 className="font-bold text-lg">Conversation Details</h2>

            {isGroup && (
              <>
                <div className="font-semibold">Members</div>
                <ul className="text-sm space-y-1">
                  {participants.map(p => (
                    <li key={p.id}>
                      {p.email}
                      <span className="text-xs text-gray-500 ml-2">
                        ({p.role})
                      </span>
                    </li>
                  ))}
                </ul>
              </>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <button
                onClick={() => setShowDetails(false)}
                className="text-sm"
              >
                Close
              </button>

              <button
                onClick={handleDeleteOrLeave}
                disabled={loading}
                className="text-red-600 font-semibold text-sm disabled:opacity-50"
              >
                {isSuperAdmin
                  ? "Delete Conversation"
                  : isGroup
                  ? "Leave Group"
                  : "Delete Chat"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

