//frontend/src/app/messages/page.tsx

"use client";

import { useEffect, useState, useCallback } from "react";
import ConversationList from "../../components/ConversationList";
import ChatWindow from "../../components/ChatWindow";
import { SocketProvider } from "../../context/SocketContext";
import { useAuth } from "../../context/AuthContext";
import { Conversation } from "../../types/conversation";

const API_BASE = "http://localhost:8000";

export default function MessagesPageWrapper() {
  return (
    <SocketProvider>
      <MessagesPage />
    </SocketProvider>
  );
}

function MessagesPage() {
  const { user } = useAuth();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] =
    useState<number | null>(null);

  /* ================= LOAD CONVERSATIONS ================= */
  const loadConversations = useCallback(async () => {
    if (!user) return;

    try {
      const res = await fetch(`${API_BASE}/api/conversations`, {
        credentials: "include",
      });

      if (!res.ok) {
        console.error("Failed to load conversations:", res.status);
        setConversations([]);
        return;
      }

      const data = await res.json();

      if (Array.isArray(data)) {
        setConversations(data);
      } else {
        setConversations([]);
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setConversations([]);
    }
  }, [user]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const activeConversation =
    conversations.find(c => c.id === activeConversationId) ?? null;

  function removeConversation(id: number) {
    setConversations(prev => prev.filter(c => c.id !== id));
    setActiveConversationId(null);
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <ConversationList
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelect={setActiveConversationId}
        onConversationCreated={conv => {
          setConversations(prev =>
            prev.some(c => c.id === conv.id) ? prev : [conv, ...prev]
          );
          setActiveConversationId(conv.id);
        }}
      />

      <main className="flex-1 flex flex-col">
        {activeConversation && user ? (
          <ChatWindow
            conversation={activeConversation}
            currentUser={user}
            onDeleted={() => removeConversation(activeConversation.id)}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500 text-lg">
            Select a conversation
          </div>
        )}
      </main>
    </div>
  );
}
