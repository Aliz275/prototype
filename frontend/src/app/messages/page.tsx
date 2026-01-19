// frontend/src/app/messages/page.tsx

"use client";

import { useState, useEffect } from "react";
import ConversationList from "../../components/ConversationList";
import ChatWindow from "../../components/ChatWindow";
import { SocketProvider } from "../../context/SocketContext";

type Invite = {
  id: number;
  email: string;
  role: string;
  status: "pending" | "accepted";
};

const API_BASE = "http://localhost:8000";

// added part for socket error
export default function MessagesPageWrapper() {
  return (
    <SocketProvider>
      <MessagesPage />
    </SocketProvider>
  ); //added
}

// Keep this exactly as you have it
function MessagesPage() {
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [selectedInvite, setSelectedInvite] = useState<Invite | null>(null);
  const [invites, setInvites] = useState<Invite[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/invitations`, { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setInvites(data.filter(i => i.status === "pending"));
      })
      .catch(() => setInvites([]));
  }, []);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* LEFT PANEL */}
      <aside className="w-80 bg-white border-r flex flex-col">
        <ConversationList
          onSelect={id => {
            setSelectedInvite(null);
            setActiveConversationId(id);
          }}
        />
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

      {/* RIGHT PANEL */}
      <main className="flex-1 flex flex-col">
        {activeConversationId && <ChatWindow conversationId={activeConversationId} />}
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
          </div>
        )}
      </main>
    </div>
  );
}
