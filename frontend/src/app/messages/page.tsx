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
  participants: Participant[];
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

  // Load pending invites
  useEffect(() => {
    fetch(`${API_BASE}/api/conversations`, {
      credentials: "include",
    })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setConversations(
            data.map(c => ({
              ...c,
              participants: c.participants ?? [],
            }))
          );
        }
      });
  }, []);

  function getConversationName(c: Conversation) {
    if (c.name) return c.name;

    const other = c.participants.find(p => p.email !== user?.email);
    return other?.email ?? "Direct Message";
  }

  function handleSelectConversation(id: number) {
    const conv = conversations.find(c => c.id === id) || null;
    setActiveConversation(conv);
  }

  return (
    <div className="flex h-screen bg-gray-100">
<<<<<<< Updated upstream
      <ConversationList onSelect={handleSelectConversation} />
=======
      {/* LEFT PANEL */}
      <aside className="w-80 bg-white border-r flex flex-col">
        <ConversationList
          onSelect={id => {
            setSelectedInvite(null);
            setActiveConversationId(id);
          }}
        />

        {/* Pending Invites */}
        <div className="border-t">
          <div className="p-3 text-xs font-semibold text-gray-500 uppercase">
            Pending Invites
          </div>

          {invites.length === 0 ? (
            <div className="px-4 pb-4 text-sm text-gray-400">No pending invitations</div>
          ) : (
            <ul>
              {invites.map(invite => (
                <li
                  key={invite.id}
                  onClick={() => {
                    setActiveConversationId(null);
                    setSelectedInvite(invite);
                  }}
                  className="px-4 py-3 cursor-pointer hover:bg-gray-50 flex items-center gap-3"
                >
                  <div className="w-9 h-9 rounded-full bg-gray-300 text-gray-700 flex items-center justify-center font-semibold">
                    {invite.email[0].toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{invite.email}</div>
                    <div className="text-xs text-orange-500">Invitation pending</div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
>>>>>>> Stashed changes

      <main className="flex-1 flex flex-col">
<<<<<<< Updated upstream
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
=======
        {activeConversationId && (
          <ChatWindow
            key={activeConversationId} // ⚡ force remount when conversation changes
            conversationId={activeConversationId}
          />
        )}

        {selectedInvite && (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
            <div className="text-2xl mb-2">⏳</div>
            <h2 className="text-lg font-semibold mb-1">Invitation not accepted yet</h2>
            <p className="text-sm text-gray-500 max-w-md">
              {selectedInvite.email} has been invited but hasn’t created an account yet.
              Messaging will be enabled once they accept the invitation.
            </p>
          </div>
        )}

        {!activeConversationId && !selectedInvite && (
          <div className="flex-1 flex items-center justify-center text-gray-500 text-lg">
            Select a conversation or invited user
>>>>>>> Stashed changes
          </div>
        )}
      </main>
    </div>
  );
}
