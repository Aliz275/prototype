//frontend/src/app/messages/page.tsx

"use client";

import { useState, useEffect } from "react";
import ConversationList from "../../components/ConversationList";
import ChatWindow from "../../components/ChatWindow";
import { SocketProvider } from "../../context/SocketContext";
import { useAuth } from "../../context/AuthContext";

type Participant = {
  id: number;
  email: string;
};

type Conversation = {
  id: number;
  name: string | null;
  participants?: Participant[];
};

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
  const [activeConversation, setActiveConversation] =
    useState<Conversation | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/conversations`, {
      credentials: "include",
    })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setConversations(data);
      });
  }, []);

  function getConversationName(c: Conversation) {
    if (c.name) return c.name;
    if (!user || !Array.isArray(c.participants)) return "Direct Message";

    const other = c.participants.find(p => p.email !== user.email);
    return other?.email || "Direct Message";
  }

  function handleSelectConversation(id: number) {
    const conv = conversations.find(c => c.id === id) || null;
    setActiveConversation(conv);
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <ConversationList onSelect={handleSelectConversation} />

      <main className="flex-1 flex flex-col">
        {activeConversation && user ? (
          <ChatWindow
            key={activeConversation.id}
            conversationId={activeConversation.id}
            conversationName={getConversationName(activeConversation)}
            userId={user.id}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a conversation
          </div>
        )}
      </main>
    </div>
  );
}
