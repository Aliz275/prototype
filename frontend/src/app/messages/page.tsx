//frontend/src/app/messages/page.tsx

"use client";

import { useEffect, useState } from "react";
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
  useEffect(() => {
    if (!user) return;

    fetch(`${API_BASE}/api/conversations`, {
      credentials: "include",
    })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setConversations(data);
        }
      });
  }, [user]);

  /* ================= GET NAME ================= */
  function getConversationName(c: Conversation) {
    if (c.name) return c.name;
    if (!user || !Array.isArray(c.participants)) return "Direct Message";

    const other = c.participants.find(p => p.email !== user.email);
    return other?.email ?? "Direct Message";
  }

  const activeConversation =
    conversations.find(c => c.id === activeConversationId) ?? null;

  return (
    <div className="flex h-screen bg-gray-100">
      <ConversationList
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelect={setActiveConversationId}
        onConversationCreated={conv => {
          setConversations(prev => {
            if (prev.find(c => c.id === conv.id)) return prev;
            return [...prev, conv];
          });
          setActiveConversationId(conv.id);
        }}
      />

      <main className="flex-1 flex flex-col">
        {activeConversation && user ? (
          <ChatWindow
            key={activeConversation.id}
            conversationId={activeConversation.id}
            conversationName={getConversationName(activeConversation)}
            userId={user.id}
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

